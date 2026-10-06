"""Five-response native DFlash composition and delta backward; no optimizer."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import torch
from transformers import AutoModelForCausalLM
from speculators.losses import resolve_loss_config
from atlas.run_cell import sha256,write_new
from atlas.generate_magpie import unpaused
from followspec.online_bank import FrozenAdapterBank
from followspec.paired_data import PairedCollator
from followspec.dflash_loader import load_released_dflash
from followspec.dflash_extension import install_follow_spec_dflash,prepare_block_sample,align_targets


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['base','drafter','registry','responses','output']:p.add_argument('--'+key,required=True)
    a=p.parse_args();unpaused()
    if os.environ.get('TORCH_COMPILE_DISABLE')!='1':raise ValueError('bounded eager-backbone check requires compile disabled')
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 required')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit first')
    rows=[json.loads(s) for s in Path(a.responses).read_text().splitlines()]
    if len(rows)!=5 or any(not r['acceptance_only'] for r in rows):raise ValueError('exactly five acceptance responses required')
    registry=json.loads(Path(a.registry).read_text());out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();torch.manual_seed(101)
    cfg=vars(a)|dict(acceptance_only=True,seed=101,K=None,engine_version='0.31.0',
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        base_revision=Path(a.base).name,drafter_revision=Path(a.drafter).name,
        registry_sha256=sha256(a.registry),responses_sha256=sha256(a.responses),max_anchors=2,
        native_loss='fused KL; native gamma4 decay',scope='fixed5 bounded eager-backbone DFlash acceptance; no training capacity or overfit claim')
    write_new(out/'config.json',cfg)
    try:
        target=AutoModelForCausalLM.from_pretrained(a.base,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda')
        draft=load_released_dflash(a.drafter,a.base,attention='eager').train()
        tokens=torch.arange(len(draft.d2t))+draft.d2t.cpu() if draft.d2t is not None else torch.arange(target.config.vocab_size)
        bank=FrozenAdapterBank(target,registry,list(draft.target_layer_ids),tokens)
        items=[]
        for row in rows:
            unpaused();raw=bank.capture(row['generation_target'],torch.tensor(row['input_ids']),torch.tensor(row['loss_mask']))
            items.append(dict(tensors=prepare_block_sample(raw),sample_id=row['sample_id'],target_id=row['generation_target']))
        actual=sum(len(r['input_ids']) for r in rows);length=((actual+127)//128)*128
        batch=PairedCollator(length,target.config.hidden_size,len(draft.target_layer_ids),draft.block_size)(items)
        batch={k:v.to('cuda') if isinstance(v,torch.Tensor) else v for k,v in batch.items()}
        common={k:batch[k] for k in ['input_ids','loss_mask','document_ids','position_ids']}
        call=dict(max_anchors=2,loss_config=resolve_loss_config('kl_div','fused'))
        native=draft.forward;backbone=draft._backbone_forward;keys=set(draft.state_dict())
        cpu_rng=torch.get_rng_state();cuda_rng=torch.cuda.get_rng_state();refs=[]
        for base in [False,True]:
            torch.set_rng_state(cpu_rng);torch.cuda.set_rng_state(cuda_rng)
            prefix='base_' if base else '';labels=batch['base_target_logits' if base else 'child_target_logits']
            def projected(*args,**kw):
                h,q,p,mask,indices=backbone(*args,**kw)
                return h,q,align_targets(labels,indices,sample_from_anchor=draft.config.sample_from_anchor),mask,indices
            draft._backbone_forward=projected
            try:
                with torch.no_grad(),torch.autocast('cuda',dtype=torch.bfloat16):
                    _,loss,_=native(**common,hidden_states=batch[prefix+'hidden_states'],verifier_last_hidden_states=batch[prefix+'verifier_last_hidden_states'],**call)
                refs.append(loss.detach())
            finally:draft._backbone_forward=backbone
        torch.set_rng_state(cpu_rng);torch.cuda.set_rng_state(cuda_rng)
        install_follow_spec_dflash(draft,delta_lambda=0,top_k=32)
        with torch.autocast('cuda',dtype=torch.bfloat16):_,paired,_=draft(**batch,**call)
        error=float(abs(paired.detach()-(refs[0]+refs[1])));assert error<=1e-6,error
        paired.backward();assert all(torch.isfinite(p.grad).all() for p in draft.parameters() if p.grad is not None)
        draft.zero_grad(set_to_none=True)
        # Restore the exact saved native method before installing the second
        # bounded loss setting. No weight or optimizer update occurs here.
        draft.forward=native;draft._followspec_installed=False
        install_follow_spec_dflash(draft,delta_lambda=.1,top_k=32)
        with torch.autocast('cuda',dtype=torch.bfloat16):_,loss,metrics=draft(**batch,**call)
        assert torch.isfinite(loss);loss.backward()
        grads=[p.grad for p in draft.parameters() if p.grad is not None]
        assert grads and all(torch.isfinite(g).all() for g in grads)
        assert all(p.grad is None and not p.requires_grad for p in bank.model.parameters())
        assert set(draft.state_dict())==keys and draft._backbone_forward==backbone
        positions={str(i):dict(delta=float(metrics[f'delta_position_{i}_sum']),scored=bool(metrics[f'delta_position_{i}_total'])) for i in range(draft.block_size)}
        assert not positions['0']['scored'] and all(positions[str(i)]['scored'] for i in range(1,draft.block_size))
        result=dict(passed=True,n=5,raw_tokens=actual,padded_tokens=length,block_size=draft.block_size,
            lambda_zero_abs_error=error,delta_loss=float(metrics['delta_loss_sum']),positions=positions,
            finite_drafter_gradients=True,frozen_teacher=True,state_keys_unchanged=True,
            max_gpu_allocated_gb=torch.cuda.max_memory_allocated()/1024**3,wall_s=time.perf_counter()-start)
        write_new(out/'results.json',result)
        with (out/'per_prompt.jsonl').open('x') as f:
            for row in rows:f.write(json.dumps(dict(sample_id=row['sample_id'],raw_tokens=len(row['input_ids']),assistant_tokens=sum(row['loss_mask'])))+'\n')
        write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
            what_why='Verify native DFlash paired loss and backward',new='Unshifted paired features and replayed anchors',artifacts=str(out.resolve()),
            config_results=dict(config=cfg,results=result),caveats=cfg['scope']))
        print(json.dumps(result))
    except Exception as e:write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__=='__main__':main()
