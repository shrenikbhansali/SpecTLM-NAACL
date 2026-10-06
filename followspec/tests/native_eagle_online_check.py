"""Real pinned EAGLE3 fixed-batch composition/backward with online targets."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import torch
from safetensors import safe_open
from transformers import AutoModelForCausalLM
from speculators import SpeculatorModel,SpeculatorModelConfig
from speculators.version import git_commit
from speculators.losses import resolve_loss_config
from atlas.run_cell import sha256,write_new
from atlas.generate_magpie import unpaused
from atlas.covariates import tap_layers
from followspec.online_bank import FrozenAdapterBank
from followspec.paired_data import shift_paired,PairedCollator
from followspec.eagle3_extension import install_follow_spec

BACKEND='261a82dd44ca05ff73006938c0614111bb2dd2b7'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['base','drafter','registry','responses','output']:p.add_argument('--'+key,required=True)
    p.add_argument('--loss-implementation',choices=['eager','fused'],default='fused');a=p.parse_args()
    unpaused();assert git_commit==BACKEND
    if os.environ.get('TORCH_COMPILE_DISABLE')!='1':raise ValueError('fixed eager-backbone acceptance requires TORCH_COMPILE_DISABLE=1')
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 required')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit first')
    registry=json.loads(Path(a.registry).read_text());rows=[json.loads(s) for s in Path(a.responses).read_text().splitlines()]
    if not 1<=len(rows)<=5 or any(not r['acceptance_only'] for r in rows):raise ValueError('fixed batch requires bounded acceptance data')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();torch.manual_seed(101)
    cfg=vars(a)|dict(acceptance_only=True,backend_commit=BACKEND,base_revision=Path(a.base).name,drafter_revision=Path(a.drafter).name,
        seed=101,K=None,generation_engine='0.31.0',gpu_type=torch.cuda.get_device_name(0),
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),responses_sha256=sha256(a.responses),registry_sha256=sha256(a.registry),
        scope='B6 real fixed-batch native loss and backward; not64-sample overfit or production training')
    write_new(out/'config.json',cfg)
    try:
        target=AutoModelForCausalLM.from_pretrained(a.base,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda')
        with safe_open(str(Path(a.drafter)/'model.safetensors'),framework='pt',device='cpu') as f:d2t=f.get_tensor('d2t')
        taps=tap_layers(json.loads((Path(a.drafter)/'config.json').read_text()),target.config.num_hidden_layers)
        bank=FrozenAdapterBank(target,registry,taps,torch.arange(len(d2t))+d2t)
        items=[]
        for r in rows:
            raw=bank.capture(r['generation_target'],torch.tensor(r['input_ids']),torch.tensor(r['loss_mask']))
            items.append(dict(tensors=shift_paired(raw),sample_id=r['sample_id'],target_id=r['generation_target']))
        actual_tokens=sum(len(r['input_ids'])-1 for r in rows)
        # Small fixed tensor batch only; production preset8192 is unchanged.
        length=((actual_tokens+127)//128)*128
        batch=PairedCollator(length,target.config.hidden_size,len(taps),3)(items)
        batch={k:v.to('cuda') if isinstance(v,torch.Tensor) else v for k,v in batch.items()}
        config=SpeculatorModelConfig.from_pretrained(a.drafter,local_files_only=True)
        config.speculators_config.verifier.name_or_path=a.base
        config.eagle_aux_hidden_state_layer_ids=taps
        config.transformer_layer_config._attn_implementation='eager'
        draft=SpeculatorModel.from_pretrained(a.drafter,config=config,local_files_only=True,torch_dtype=torch.float32).to('cuda').train()
        keys=set(draft.state_dict());native=draft.forward
        call=dict(ttt_steps=3,ttt_step_loss_decay=1.,loss_config=resolve_loss_config('kl_div',a.loss_implementation))
        common={k:batch[k] for k in ['input_ids','loss_mask','document_ids','position_ids']}
        references=[]
        for base in [False,True]:
            prefix='base_' if base else '';labels=batch['base_target_logits' if base else 'child_target_logits']
            h=draft.verifier_lm_head.register_forward_hook(lambda m,args,output,labels=labels:labels.detach())
            try:
                with torch.no_grad(),torch.autocast('cuda',dtype=torch.bfloat16):
                    _,loss,_=native(**common,hidden_states=batch[prefix+'hidden_states'],verifier_last_hidden_states=batch[prefix+'verifier_last_hidden_states'],**call)
                references.append(loss.detach())
            finally:h.remove()
        install_follow_spec(draft,beta=1.,delta_lambda=0.,top_k=32,shared_verifier_head=False)
        with torch.autocast('cuda',dtype=torch.bfloat16):_,paired,metrics=draft(**batch,**call)
        difference=abs(float(paired.detach()-(references[0]+references[1])))
        assert difference<=1e-6, difference
        paired.backward()
        gradients=[p.grad for p in draft.parameters() if p.grad is not None]
        assert gradients and all(torch.isfinite(g).all() for g in gradients)
        assert all(p.grad is None and not p.requires_grad for p in bank.model.parameters())
        assert set(draft.state_dict())==keys
        assert not draft.lm_head._forward_hooks and not draft.verifier_lm_head._forward_hooks
        result=dict(passed=True,n=len(rows),shifted_tokens=actual_tokens,padded_tokens=length,steps=3,
            lambda_zero_abs_error=difference,child_native=float(references[0]),base_native=float(references[1]),paired=float(paired.detach()),
            finite_drafter_gradients=True,frozen_target=True,unchanged_state_dict_keys=True,wall_s=time.perf_counter()-start,
            max_gpu_allocated_gb=torch.cuda.max_memory_allocated()/1024**3,scope=cfg['scope'])
        write_new(out/'results.json',result)
        with (out/'per_prompt.jsonl').open('x') as f:
            for r in rows:f.write(json.dumps(dict(sample_id=r['sample_id'],shifted_tokens=len(r['input_ids'])-1,assistant_tokens=sum(r['loss_mask'])))+'\n')
        write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
            what_why='Native EAGLE3 paired loss equivalence and backward',new='Actual released drafter with online bank target features',
            artifacts=str(out.resolve()),config_results=dict(config=cfg,results=result),caveats=cfg['scope']))
        print(json.dumps(result))
    except Exception as e:write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__=='__main__':main()
