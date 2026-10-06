"""Paired native EAGLE3 offline diagnostics on exact child-generated sequences."""
import argparse
from collections import defaultdict
from datetime import date
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import time
import numpy as np
from atlas.transport import score_distribution,decompose_grid
from atlas.run_cell import ensure_unpaused,sha256,write_new

BACKEND='261a82dd44ca05ff73006938c0614111bb2dd2b7'
PRIMARY='first-position top-1 agreement'


def aggregate_cells(rows):
    grouped=defaultdict(list)
    for row in rows:
        if row.get('diagnostic') is not True or row['n']<=0:raise ValueError('positive diagnostic cells required')
        grouped[tuple(row[k] for k in ('feature_source','label_source','head','unroll_position'))].append(row)
    result=[]
    for key,group in sorted(grouped.items()):
        n=sum(r['n'] for r in group);infinite=any(r['forward_kl_infinite'] for r in group)
        out=dict(zip(('feature_source','label_source','head','unroll_position'),key))
        out.update(n=n,n_prompts=len(group),diagnostic=True,forward_kl_infinite=infinite,
                   infinite_kl_positions=sum(r['infinite_kl_positions'] for r in group),
                   forward_kl=None if infinite else sum(r['forward_kl']*r['n'] for r in group)/n)
        for metric in ('top1_agreement','overlap'):out[metric]=sum(r[metric]*r['n'] for r in group)/n
        result.append(out)
    return result


def load_drafter(path,base,taps):
    from speculators import SpeculatorModel,SpeculatorModelConfig
    from speculators.version import git_commit
    import torch
    if git_commit!=BACKEND:raise ValueError('native backend differs from pinned source')
    cfg=SpeculatorModelConfig.from_pretrained(path,local_files_only=True)
    if cfg.speculators_model_type!='eagle3':raise ValueError('EAGLE3 checkpoint required')
    # In-memory config override pins inherited verifier weights. Snapshot unchanged.
    cfg.speculators_config.verifier.name_or_path=base
    cfg.eagle_aux_hidden_state_layer_ids=taps
    cfg.transformer_layer_config._attn_implementation='eager'
    model=SpeculatorModel.from_pretrained(path,config=cfg,local_files_only=True,torch_dtype=torch.bfloat16).to('cuda').eval()
    return model


def target_pass(model,row,taps):
    import torch
    core=model.get_base_model() if hasattr(model,'get_base_model') else model
    ids=torch.tensor([row['input_ids']],device='cuda')
    with torch.inference_mode():
        output=core.model(input_ids=ids,output_hidden_states=True,use_cache=False)
        features=torch.cat([output.hidden_states[i] for i in taps],dim=-1).detach()
        # Transfer bounded chunks so a long response does not allocate full-vocab
        # float32 logits for the whole sequence on the GPU at once.
        logits=torch.cat([core.lm_head(chunk)[0].float().cpu() for chunk in output.last_hidden_state.split(64,dim=1)])
    return features,logits


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('base','base-revision','drafter','drafter-revision','derivative-id','derivative-revision','sequences','source-cell','output'):
        p.add_argument('--'+key,required=True)
    g=p.add_mutually_exclusive_group();g.add_argument('--adapter');g.add_argument('--child')
    p.add_argument('--steps',type=int,required=True);p.add_argument('--seed',type=int,default=0)
    p.add_argument('--acceptance-smoke',action='store_true');p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    from atlas.covariates import load_sequences,tap_layers
    for name in ('base','drafter'):
        rev=getattr(a,name+'_revision')
        if not re.fullmatch('[a-f0-9]{40}',rev) or Path(getattr(a,name)).name!=rev:raise ValueError('pinned local snapshots required')
    if a.child and (Path(a.child).name!=a.derivative_revision or not re.fullmatch('[a-f0-9]{40}',a.derivative_revision)):
        raise ValueError('child snapshot must be pinned')
    if not a.child and not a.adapter and a.derivative_id!='base':raise ValueError('missing child weights')
    if not 1<=a.steps<=8:raise ValueError('supported diagnostic unroll depths1–8')
    rows,source=load_sequences(a.sequences,a.acceptance_smoke)
    if (source['derivative_id'],source['derivative_revision'])!=(a.derivative_id,a.derivative_revision):raise ValueError('wrong generating derivative')
    source_cell=Path(a.source_cell).resolve()
    if sha256(source_cell/'config.json')!=source['source_config_sha256']:raise ValueError('wrong source cell')
    record_name='samples.jsonl' if source['workload']=='general acceptance only' else 'per_prompt.jsonl'
    if sha256(source_cell/record_name)!=source['source_records_sha256']:raise ValueError('source generation changed')
    bc=json.loads((Path(a.base)/'config.json').read_text());dc=json.loads((Path(a.drafter)/'config.json').read_text())
    taps=tap_layers(dc,bc['num_hidden_layers'])
    cfg=vars(a)|dict(scope='offline diagnostic',diagnostic=True,source=source,source_cell=str(source_cell),
        sequences_sha256=sha256(a.sequences),prompt_sha256=source['prompt_sha256'],K=source.get('K'),
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),backend_commit=BACKEND,
        source_sha256=sha256(__file__),tap_indices=taps,dtype='bfloat16',attention='eager',compile=False,
        primary_validation_metric=PRIMARY,averaging='token-weighted over generated bonus-token anchors; no predictions beyond saved response',
        backend={name:importlib.metadata.version(name) for name in ('torch','transformers','speculators','numpy','scipy')})
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    ensure_unpaused();ensure_unpaused(Path.cwd())
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit source before real diagnostics')
    if os.environ.get('TORCH_COMPILE_DISABLE')!='1':raise ValueError('set TORCH_COMPILE_DISABLE=1 for explicit eager offline backend')
    import torch
    from transformers import AutoModelForCausalLM
    from peft import PeftModel
    from atlas.quantized_targets import load_child
    from atlas.transport_native import capture_eagle_unroll,align_eagle_step,expanded_logprobs
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('offline diagnostics require A40')
    torch.manual_seed(a.seed)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write_new(out/'config.json',cfg);start=time.perf_counter()
    try:
        base=AutoModelForCausalLM.from_pretrained(a.base,local_files_only=True,trust_remote_code=False,torch_dtype=torch.bfloat16,attn_implementation='eager').to('cuda').eval()
        if a.adapter:child=PeftModel.from_pretrained(base,a.adapter,autocast_adapter_dtype=False).eval()
        elif a.child:
            child,quant=load_child(a.child);write_new(out/'child_backend.json',quant)
        else:child=base
        drafter=load_drafter(a.drafter,a.base,taps);all_rows=[]
        with (out/'per_prompt.jsonl').open('x') as f:
            for row in rows:
                ensure_unpaused()
                if a.adapter:
                    with child.disable_adapter():bf,bp=target_pass(child,row,taps)
                else:bf,bp=target_pass(base,row,taps)
                cf,cp=target_pass(child,row,taps)
                ids=torch.tensor([row['input_ids']],device='cuda')
                prompt_rows=[]
                for feature,features in [('base',bf),('child',cf)]:
                    predictions=capture_eagle_unroll(drafter,features,ids,a.steps)
                    for depth,draft_logits in enumerate(predictions):
                        for label,logits in [('base',bp),('child',cp)]:
                            pl,ql,anchors=align_eagle_step(logits,draft_logits,row['response_start'],depth)
                            q=expanded_logprobs(ql,drafter.d2t.cpu(),bp.shape[-1]).numpy()
                            metrics=score_distribution(pl.double().log_softmax(-1).numpy(),q,np.ones(len(pl),dtype=bool))
                            scored=dict(prompt_id=row['prompt_id'],feature_source=feature,label_source=label,head='frozen_drafter',
                                unroll_position=depth,first_anchor=int(anchors[0]),last_anchor=int(anchors[-1]),**metrics)
                            f.write(json.dumps(scored,allow_nan=False)+'\n');f.flush();prompt_rows.append(scored)
                all_rows.extend(prompt_rows);del bf,bp,cf,cp
        cells=aggregate_cells(all_rows);decomposition=decompose_grid(cells)
        report=dict(diagnostic=True,scope='offline diagnostic',cells=cells,decomposition=decomposition,
            primary_validation_metric=PRIMARY,n_prompts=len(rows),wall_s=time.perf_counter()-start,
            uncertainty='per-prompt records retained; no run-to-run noise estimate from one diagnostic',
            validation='requires matched native-vLLM diagonal checks on at least10 derivatives before use')
        write_new(out/'results.json',report)
        write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=str(date.today()),status='pilot',
            what_why='Offline EAGLE3 feature/label transport diagnostics',new='Native pinned teacher-forced unroll; exact saved child sequences',
            artifacts=str(out.resolve()),config_results=dict(config=cfg,results=report),caveats='Diagnostic, not native acceptance. Ten-derivative validation required.'))
    except Exception as exc:
        write_new(out/'failure.json',dict(error=str(exc),type=type(exc).__name__));raise

if __name__=='__main__':main()
