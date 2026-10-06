"""Five matched trimmed examples per arm; fresh/zero target checks on A40."""
import argparse
from contextlib import nullcontext
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import torch
from safetensors import safe_open
from transformers import AutoModelForCausalLM
from atlas.run_cell import sha256,write_new
from atlas.generate_magpie import unpaused
from atlas.covariates import tap_layers
from followspec.online_bank import FrozenAdapterBank
from followspec.paired_data import shift_paired
from followspec.token_data import OnlineResponseDataset,validate_arm_set


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['base','drafter','manifests','sample-audit','output']:p.add_argument('--'+key,required=True)
    a=p.parse_args();unpaused()
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit first')
    arms={name:json.loads((Path(a.manifests)/f'{name}.json').read_text()) for name in ['FS','MVD','PO-D','PO-T']}
    matched=validate_arm_set(arms)
    if any(m['base_revision']!=Path(a.base).name or m['initialization_revision']!=Path(a.drafter).name for m in arms.values()):raise ValueError('manifest/model pins differ')
    if any(not m['acceptance_only'] or len(m['samples'])!=5 for m in arms.values()):raise ValueError('exactly five acceptance-only examples per arm required')
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 required')
    digests={name:sha256(Path(a.manifests)/f'{name}.json') for name in arms}
    audit=json.loads(Path(a.sample_audit).read_text())
    if not audit.get('decoded_and_masks_inspected') or audit.get('manifest_sha256')!=digests:raise ValueError('inspect the five trimmed examples per arm first')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();torch.manual_seed(0)
    cfg=dict(acceptance_only=True,base=a.base,base_revision=Path(a.base).name,drafter=a.drafter,drafter_revision=Path(a.drafter).name,
        manifest_sha256=digests,sample_audit_sha256=sha256(a.sample_audit),registry=arms['FS']['registry'],seed=0,K=None,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),gpu_type=torch.cuda.get_device_name(0),
        generation_engine='0.31.0',versions={n:importlib.metadata.version(n) for n in ['torch','transformers','peft']},
        tolerance=dict(atol=0,rtol=0),scope='B5 trimmed bank-data acceptance; no production quotas, mixture data or training')
    write_new(out/'config.json',cfg)
    try:
        target=AutoModelForCausalLM.from_pretrained(a.base,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda')
        with safe_open(str(Path(a.drafter)/'model.safetensors'),framework='pt',device='cpu') as f:d2t=f.get_tensor('d2t')
        taps=tap_layers(json.loads((Path(a.drafter)/'config.json').read_text()),target.config.num_hidden_layers)
        bank=FrozenAdapterBank(target,arms['FS']['registry'],taps,torch.arange(len(d2t))+d2t)
        datasets={name:OnlineResponseDataset(m,split='train',bank=bank,shift=lambda r:r,allow_acceptance=True) for name,m in arms.items()}
        def fresh(raw,base):
            last=[];hook=target.model.norm.register_forward_pre_hook(lambda m,args:last.append(args[0].detach()))
            try:
                with (bank.model.disable_adapter() if base else nullcontext()),torch.no_grad():
                    result=target.model(input_ids=raw['input_ids'][None],output_hidden_states=True,use_cache=False)
                    features=torch.cat([result.hidden_states[i][0] for i in taps],-1)
                return features,last[0][0]
            finally:
                hook.remove();bank.model.requires_grad_(False)
        records=[]
        with (out/'per_prompt.jsonl').open('x') as log:
            for i in range(5):
                unpaused();reference=datasets['FS'][i]['tensors'];assert not torch.equal(reference['hidden_states'],reference['base_hidden_states'])
                if i<3:
                    for base in [False,True]:
                        f,last=fresh(reference,base);prefix='base_' if base else ''
                        torch.testing.assert_close(f,reference[prefix+'hidden_states'],atol=0,rtol=0)
                        torch.testing.assert_close(last,reference[prefix+'verifier_last_hidden_states'],atol=0,rtol=0)
                    del f,last
                for name,ds in datasets.items():
                    raw=reference if name=='FS' else ds[i]['tensors']
                    if name=='MVD':
                        assert all(torch.equal(raw[k],reference[k]) for k in reference)
                    if name=='PO-T':
                        assert torch.equal(raw['hidden_states'],reference['base_hidden_states'])
                        assert torch.equal(raw['child_target_logits'],reference['base_target_logits'])
                    if name in ['PO-D','PO-T']:
                        assert torch.equal(raw['hidden_states'],raw['base_hidden_states'])
                        assert torch.equal(raw['child_target_logits'],raw['base_target_logits'])
                    shifted=shift_paired(raw)
                    assert len(shifted['input_ids'])==ds.approx_lengths[i]
                    item=dict(arm=name,sample_id=ds.rows[i]['sample_id'],raw_tokens=len(raw['input_ids']),
                        shifted_tokens=len(shifted['input_ids']),assistant_tokens=int(raw['loss_mask'].sum()),
                        response_view=ds.rows[i]['response_view'],feature_route=ds.rows[i]['feature_target'],fresh_exact=(i<3 and name=='FS'))
                    log.write(json.dumps(item)+'\n');log.flush();records.append(item);del raw,shifted
                del reference
        factors=[m.weight for module in bank.model.modules() if hasattr(module,'lora_B') for m in module.lora_B.values()]
        assert factors;copies=[x.detach().clone() for x in factors]
        try:
            with torch.no_grad():
                for x in factors:x.zero_()
            for i in range(3):
                raw=datasets['FS'][i]['tensors']
                for key in ['hidden_states','verifier_last_hidden_states','child_target_logits']:
                    other='base_target_logits' if key=='child_target_logits' else 'base_'+key
                    assert torch.equal(raw[key],raw[other])
                del raw
        finally:
            with torch.no_grad():
                for x,y in zip(factors,copies,strict=True):x.copy_(y)
        assert all(not p.requires_grad and p.grad is None for p in bank.model.parameters())
        result=dict(passed=True,n_per_arm=5,matched=matched,fresh_pair_checks=3,zero_update_exact_checks=3,
            target_frozen=True,feature_shards_written=0,wall_s=time.perf_counter()-start,
            max_gpu_allocated_gb=torch.cuda.max_memory_allocated()/1024**3,uncertainty='deterministic equality checks; one seed, no performance inference')
        write_new(out/'results.json',result)
        write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
            what_why='Verify approved paired response prefix matching in the real online feature loader',new='All four arm routes, three fresh and zero-update comparisons',
            artifacts=str(out.resolve()),config_results=dict(config=cfg,results=result),caveats=cfg['scope']))
        print(json.dumps(result))
    except Exception as e:write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__=='__main__':main()
