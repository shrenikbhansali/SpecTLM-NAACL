"""D-44 small trace KL diagnostic, reusing atlas.covariates KL computation.

Supports explicitly reported child-only vocabulary additions. Full KL is then
infinite under zero-extension of the base distribution; the finite conditional
common-vocabulary KL is a separate diagnostic, never substituted silently.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import torch
from atlas.covariates import compare_tokens, draft_mask, load_sequences
from atlas.run_cell import ensure_unpaused, sha256, write_new


def compare_distributions(base, child, mask):
    if base.ndim!=2 or child.ndim!=2 or child.shape[0]!=base.shape[0] or child.shape[1]<base.shape[1]:
        raise ValueError('same positions and identical or extended child vocabulary required')
    shared=base.shape[1]
    result=compare_tokens(base,child[:,:shared],{}, {},mask)
    extra=child.shape[1]>shared
    extra_mass=float(child.float().softmax(-1)[:,shared:].sum(-1).mean()) if extra else 0.
    value=result['kl_child_base']
    return dict(n_tokens=len(base),kl_child_base=None if extra else value,
        conditional_common_vocab_kl=value,child_extra_vocab_mass=extra_mass,
        full_kl_infinite_under_zero_extension=extra,support='child_extended' if extra else 'identical',
        base_vocab_size=shared,child_vocab_size=child.shape[1])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['base','base-revision','child','child-revision','drafter','sequences','output']:
        p.add_argument('--'+key,required=True)
    p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    rows,source=load_sequences(a.sequences,True)
    for path,rev in [(a.base,a.base_revision),(a.child,a.child_revision)]:
        if Path(path).name!=rev or len(rev)!=40:raise ValueError('pin snapshots')
    if source['derivative_revision']!=a.child_revision:raise ValueError('wrong trace source')
    bc=json.loads((Path(a.base)/'config.json').read_text());cc=json.loads((Path(a.child)/'config.json').read_text())
    if any(bc[k]!=cc[k] for k in ['model_type','hidden_size','num_hidden_layers']):raise ValueError('incompatible model geometry')
    cfg=vars(a)|dict(source=source,n=len(rows),dtype='bfloat16',attention='eager',seed=0,K=source.get('K'),
        backend={k:importlib.metadata.version(k) for k in ['torch','transformers']},
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_sha256=sha256(__file__),
        prompt_sha256=source['prompt_sha256'],scope='D44 exploratory fixed eight SPEED traces; not atlas own-query n64',
        averaging='token-weighted KL(child||base) on saved child-completion prediction positions; no sampling',
        added_vocab_policy='report full KL undefined/infinite under zero-extension; separately report conditional shared-token KL and extra child probability mass')
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    ensure_unpaused();ensure_unpaused(Path.cwd())
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit first')
    from transformers import AutoModelForCausalLM
    from safetensors import safe_open
    cfg['gpu_type']=torch.cuda.get_device_name(0)
    if 'A40' not in cfg['gpu_type']:raise ValueError('A40 required')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write_new(out/'config.json',cfg)
    started=time.perf_counter();torch.manual_seed(0)
    try:
        with safe_open(str(Path(a.drafter)/'model.safetensors'),framework='pt') as f:mask=draft_mask(f.get_tensor('t2d'),f.get_tensor('d2t'))
        def load(path):return AutoModelForCausalLM.from_pretrained(path,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda').eval().requires_grad_(False)
        def capture(model,row):
            ids=torch.tensor([row['input_ids']],device='cuda');start=row['response_start']-1;end=ids.shape[1]-1
            with torch.no_grad():
                hidden=model.model(input_ids=ids,use_cache=False).last_hidden_state[:,start:end]
                # CPU storage bounds GPU projection memory; no logits are serialized.
                return torch.cat([model.lm_head(x)[0].cpu() for x in hidden.split(32,dim=1)],0)
        base=load(a.base);child=load(a.child);reports=[]
        with (out/'per_prompt.jsonl').open('x') as f:
            for row in rows:
                ensure_unpaused();r=dict(prompt_id=row['prompt_id'],**compare_distributions(capture(base,row),capture(child,row),mask))
                f.write(json.dumps(r,allow_nan=False)+'\n');f.flush();reports.append(r);print(r,flush=True)
        n=sum(r['n_tokens'] for r in reports)
        mean=lambda key:sum(r[key]*r['n_tokens'] for r in reports)/n
        result={k:mean(k) for k in ['conditional_common_vocab_kl','child_extra_vocab_mass']}
        result.update(n_prompts=len(rows),n_tokens=n,kl_child_base=mean('kl_child_base') if reports[0]['support']=='identical' else None,
            support=reports[0]['support'],full_kl_infinite_under_zero_extension=reports[0]['full_kl_infinite_under_zero_extension'],wall_s=time.perf_counter()-started)
        write_new(out/'results.json',result)
    except Exception as e:write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__=='__main__':main()
