"""One pinned, greedy atlas cell. --dry-run prints a plan and writes nothing."""
from __future__ import annotations
import argparse
from dataclasses import asdict, is_dataclass
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def ensure_unpaused(start=ROOT):
    for root in (Path(start).resolve(), *Path(start).resolve().parents):
        for rel in ('EXPERIMENTS_PAUSED.json', 'tlm-spec-maintenance/EXPERIMENTS_PAUSED.json'):
            marker=root/rel
            if marker.exists(): raise RuntimeError(f'Experiments paused: {marker}')


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024**2),b''): h.update(chunk)
    return h.hexdigest()


def load_prompts(path):
    rows=[json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    if not rows: raise ValueError('empty prompt file')
    ids=set()
    for r in rows:
        if not isinstance(r.get('prompt'),str) or not r['prompt'].strip(): raise ValueError('missing prompt text')
        if not isinstance(r.get('prompt_id'),str): raise ValueError('missing prompt_id')
        if r['prompt_id'] in ids: raise ValueError('duplicate prompt_id')
        ids.add(r['prompt_id'])
    return rows


def engine_prompts(rows,use_token_ids=False):
    if not use_token_ids:return [r['prompt'] for r in rows]
    result=[]
    for row in rows:
        ids=row.get('rendered_token_ids')
        if not isinstance(ids,list) or not ids or any(type(i) is not int or i<0 for i in ids):
            raise ValueError('explicit token input requires nonempty integer rendered_token_ids; raw token_ids are not chat context')
        result.append({'prompt_token_ids':list(ids)})
    return result


def lora_enabled(adapter,explicit=False):return bool(adapter) or bool(explicit)


def metrics(accepted, drafted, k):
    if not isinstance(accepted,list) or not isinstance(drafted,list) or len(accepted)!=len(drafted): raise ValueError('missing or mismatched per-step counters')
    if type(k) is not int or k<=0:raise ValueError('positive integer K required')
    if any(type(a) is not int or type(d) is not int or not 0 <= a <= d <= k or d==0 for a,d in zip(accepted,drafted)):
        raise ValueError('invalid accepted/draft counters')
    steps=len(accepted); total=sum(accepted)
    counts=[sum(a>=i+1 for a in accepted) for i in range(k)]
    # Condition on surviving earlier positions AND on this position being proposed.
    opportunities=[sum(a>=i and d>=i+1 for a,d in zip(accepted,drafted)) for i in range(k)]
    return dict(zero_step=steps==0,num_drafts=steps,num_draft_tokens=sum(drafted),num_accepted_tokens=total,
        accepted_lengths=[a+1 for a in accepted],per_step_accepted=accepted,per_step_drafted=drafted,
        acceptance_length=1+total/steps if steps else None,draft_token_acceptance_rate=total/sum(drafted) if steps else None,
        per_position_acceptance=[c/steps if steps else None for c in counts],
        per_position_conditional_acceptance=[c/n if n else None for c,n in zip(counts,opportunities)],
        per_position_accepted=counts,per_position_opportunities=opportunities)


def request_metrics(raw,k):
    """An empty detailed array is zero-step only if all engine counters agree."""
    if raw is None:raise RuntimeError('missing per-request speculative metrics')
    raw=asdict(raw) if is_dataclass(raw) else raw
    result=metrics(raw['per_step_accepted'],raw['per_step_drafted'],k)
    expected=[raw['per_step_accepted'].count(i) for i in range(k+1)]
    histogram=raw['histogram']
    if (raw.get('num_spec_tokens')!=k or not isinstance(histogram,list) or
        any(type(n) is not int or n<0 for n in histogram) or histogram!=expected or
        type(raw['num_draft_tokens']) is not int or raw['num_draft_tokens']!=result['num_draft_tokens']):
        raise RuntimeError('inconsistent engine counters')
    return result


def aggregate(rows):
    if not rows: raise ValueError('no prompt results')
    values=[r['acceptance_length'] for r in rows if r['num_drafts']>0]
    zeros=[r for r in rows if r['num_drafts']==0]
    if any(r.get('zero_step') is not True or r['acceptance_length'] is not None or r['num_accepted_tokens'] or r['num_draft_tokens'] for r in zeros):raise ValueError('invalid zero-step record')
    if not all(math.isfinite(v) for v in values): raise ValueError('nonfinite acceptance')
    # Deterministic prompt bootstrap for descriptive uncertainty, not independent runs.
    import random
    rng=random.Random(20261005)
    means=sorted(statistics.mean(rng.choices(values,k=len(values))) for _ in range(2000)) if values else []
    return dict(n=len(values),n_total=len(rows),n_zero_step=len(zeros),macro_acceptance_length=statistics.mean(values) if values else None,
        prompt_bootstrap_95_ci=[means[49],means[1949]] if values else None,
        uncertainty_unit='prompts; 2000 bootstrap resamples; not run-to-run noise',
        total_drafts=sum(r['num_drafts'] for r in rows),total_accepted_draft_tokens=sum(r['num_accepted_tokens'] for r in rows))


def compare_golden(base,repeat,lora,merged):
    cells=[base,repeat,lora,merged]
    keys=['drafter','drafter_revision','method','K','prompt_sha256','seed','max_new_tokens','batch_size','engine_version']
    for cell in cells:
        if cell['results']['n'] != 128 or cell['config']['K'] != 4: raise ValueError('golden requires 128 prompts and K=4')
        if any(cell['config'].get(k)!=base['config'].get(k) for k in keys): raise ValueError('golden configs must be matched')
    if any(base['config'].get(k)!=repeat['config'].get(k) for k in ('target','target_revision','adapter')):
        raise ValueError('repeat target must be matched')
    values=[c['results']['macro_acceptance_length'] for c in cells]
    repeat_delta=abs(values[1]-values[0]); drift=values[2]-values[0]
    parity=abs(values[3]-values[2])
    return dict(base=values[0],historical_base=3.0559,repeat_difference=repeat_delta,
        repeat_within_ledger_noise_floor=repeat_delta<=0.0138,child_shift=drift,
        historical_child_shift=-0.248,child_shift_difference_from_history=drift+0.248,
        child_negative_shift=drift<0,lora_merged_difference=parity,
        lora_merged_within_repeat_difference=parity<=repeat_delta,
        note='Similar drift size requires operator review; no new tolerance invented.')


def write_new(path,value):
    with Path(path).open('x') as f: json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')


def local_files(path):
    root=Path(path)
    return {str(p.relative_to(root)):sha256(p) for p in sorted(root.rglob('*')) if p.is_file() and '.cache' not in p.parts}


def read_drafter_config(model,revision):
    # Speculators checkpoints have speculators_model_type, not HF model_type.
    # Reading metadata must not instantiate AutoConfig or execute remote code.
    if Path(model).is_dir():path=Path(model)/'config.json'
    else:
        from huggingface_hub import hf_hub_download
        path=Path(hf_hub_download(model,'config.json',revision=revision))
    return json.loads(path.read_text())


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',required=True);p.add_argument('--target-revision',required=True)
    p.add_argument('--adapter');p.add_argument('--adapter-revision')
    p.add_argument('--drafter',required=True);p.add_argument('--drafter-revision',required=True)
    p.add_argument('--method',choices=['eagle3','eagle','dflash','draft_model'],required=True)
    p.add_argument('--draft-vocab-mapping',action='store_true',help='I1 opt-in token-level vocabulary mapping; requires --method draft_model')
    p.add_argument('--K',type=int,default=4);p.add_argument('--prompts',required=True)
    p.add_argument('--seed',type=int,default=0);p.add_argument('--max-new-tokens',type=int,default=512)
    p.add_argument('--batch-size',type=int,default=1);p.add_argument('--max-model-len',type=int,default=4096)
    p.add_argument('--gpu-memory-utilization',type=float,default=0.75)
    p.add_argument('--max-lora-rank',type=int,default=64)
    p.add_argument('--capture-prompt-token-ids',action='store_true',help='save engine prompt IDs for exact offline covariates')
    p.add_argument('--use-prompt-token-ids',action='store_true',help='use saved rendered_token_ids without text retokenization')
    p.add_argument('--enable-lora',action='store_true',help='enable LoRA engine setting on a matched base/control cell')
    p.add_argument('--output',required=True);p.add_argument('--dry-run',action='store_true')
    return p


def speculative_options(a):
    mapping=getattr(a,'draft_vocab_mapping',False)
    if mapping and a.method!='draft_model':raise ValueError('--draft-vocab-mapping requires draft_model')
    result=dict(model=a.drafter,revision=a.drafter_revision,method=a.method,num_speculative_tokens=a.K)
    if mapping:result['use_heterogeneous_vocab']=True
    return result


def main():
    a=parser().parse_args()
    speculative=speculative_options(a)
    for key in ('target_revision','drafter_revision'):
        if not re.fullmatch('[a-f0-9]{40}',getattr(a,key)): raise ValueError(f'{key} must be a commit hash')
    if min(a.K,a.batch_size,a.max_new_tokens,a.max_model_len)<=0: raise ValueError('positive counts required')
    if not 0 < a.gpu_memory_utilization < 1: raise ValueError('GPU memory fraction must be between 0 and 1')
    prompts=load_prompts(a.prompts)
    engine_prompts(prompts,a.use_prompt_token_ids)  # Validate before engine startup or artifact creation.
    engine=json.loads((ROOT/'atlas/env/engine.json').read_text())
    cfg=vars(a).copy();cfg.pop('dry_run');cfg.update(engine_version=engine['vllm_version'],temperature=0.0,
        top_p=1.0,prompt_sha256=sha256(a.prompts),n=len(prompts),dtype='bfloat16',enable_prefix_caching=False,
        per_request_spec_decode_metrics='detailed',metric_definition='1 + accepted draft tokens / speculative steps; macro over nonzero-step prompts',
        zero_step_policy='D32: null per-prompt AL; exclude from cell macro; pairwise shared nonzero IDs for comparisons',
        enable_lora_requested=a.enable_lora,enable_lora=lora_enabled(a.adapter,a.enable_lora))
    if a.method!='draft_model':cfg.pop('draft_vocab_mapping',None)
    cfg['code_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    cfg['code_dirty']=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip())
    cfg['source_sha256']=sha256(__file__)
    if a.adapter:
        if not a.adapter_revision: raise ValueError('adapter revision/provenance ID required')
        cfg['adapter_files_sha256']=local_files(a.adapter)
        if not cfg['adapter_files_sha256']: raise ValueError('adapter path empty')
    for name in ('target','drafter'):
        if Path(getattr(a,name)).is_dir(): cfg[name+'_files_sha256']=local_files(getattr(a,name))
    if a.dry_run:
        print(json.dumps({'dry_run':True,'config':cfg},indent=2));return
    ensure_unpaused();ensure_unpaused(Path.cwd())
    if importlib.metadata.version('vllm')!=engine['vllm_version']: raise RuntimeError('engine differs from lock')
    if cfg['code_dirty']: raise RuntimeError('commit tracked source changes before real cells')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    write_new(out/'config.json',cfg)
    started=time.perf_counter()
    try:
        from vllm import LLM,SamplingParams
        import torch
        dcfg=read_drafter_config(a.drafter,a.drafter_revision)
        write_new(out/'drafter_config.json',dcfg)
        block=dcfg.get('block_size',dcfg.get('dflash_config',{}).get('block_size'))
        cfg['dflash_block_size']=block if a.method=='dflash' else None
        # Source and resolved config are retained; engine validates each model's K.
        cfg['gpu_type']=torch.cuda.get_device_name(0)
        ensure_unpaused()
        llm=LLM(model=a.target,revision=a.target_revision,tokenizer_revision=a.target_revision,
            dtype='bfloat16',trust_remote_code=False,seed=a.seed,disable_log_stats=False,
            enable_prefix_caching=False,max_model_len=a.max_model_len,
            gpu_memory_utilization=a.gpu_memory_utilization,
            enable_lora=cfg['enable_lora'],max_lora_rank=a.max_lora_rank,
            per_request_spec_decode_metrics='detailed',
            speculative_config=speculative)
        startup=time.perf_counter()-started
        kwargs={}
        if a.adapter:
            from vllm.lora.request import LoRARequest
            kwargs['lora_request']=LoRARequest('target_child',1,str(Path(a.adapter).resolve()))
        sampling=SamplingParams(temperature=0.0,top_p=1.0,max_tokens=a.max_new_tokens,seed=a.seed)
        rows=[];generation_wall=0.0
        with (out/'per_prompt.jsonl').open('x') as f:
            for i in range(0,len(prompts),a.batch_size):
                ensure_unpaused();batch=prompts[i:i+a.batch_size]
                t=time.perf_counter();outputs=llm.generate(engine_prompts(batch,a.use_prompt_token_ids),sampling,use_tqdm=False,**kwargs)
                wall=time.perf_counter()-t;generation_wall+=wall
                if len(outputs)!=len(batch): raise RuntimeError('engine omitted outputs')
                for record,output in zip(batch,outputs):
                    if a.use_prompt_token_ids and list(output.prompt_token_ids)!=record['rendered_token_ids']:
                        raise RuntimeError('engine changed explicit prompt token IDs')
                    if len(output.outputs)!=1: raise RuntimeError('one completion required')
                    completion=output.outputs[0]
                    result=request_metrics(completion.spec_decode_metrics,a.K)
                    row=dict(prompt_id=record['prompt_id'],completion=completion.text,
                        completion_token_ids=list(completion.token_ids),batch_wall_s=wall,batch_index=i//a.batch_size,**result)
                    if a.capture_prompt_token_ids:row['prompt_token_ids']=list(output.prompt_token_ids)
                    f.write(json.dumps(row,allow_nan=False)+'\n');f.flush();rows.append(row)
        result=aggregate(rows)|dict(startup_s=startup,generation_wall_s=generation_wall,
            cell_wall_s=time.perf_counter()-started,gpu_type=cfg['gpu_type'],engine_version=engine['vllm_version'],
            dflash_block_size=cfg['dflash_block_size'],K=a.K)
        write_new(out/'resolved_config.json',cfg)
        write_new(out/'results.json',result)
        write_new(out/'ledger_draft.json',{'id':'EXP-ATL-UNASSIGNED','title':out.name,
            'landed':time.strftime('%Y-%m-%d'),'status':'pilot','what_why':'Single matched-protocol atlas cell; operator to assign ledger ID.',
            'new':'Pinned engine atlas harness','artifacts':str(out.resolve()),'config_results':{'config':cfg,'results':result},
            'caveats':'GPU acceptance pending operator verification; prompt uncertainty is not repeat noise.'})
    except BaseException as exc:
        write_new(out/'failure.json',dict(error_type=type(exc).__name__,error=str(exc)))
        raise

if __name__=='__main__': main()
