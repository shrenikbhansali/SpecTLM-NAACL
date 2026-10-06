"""Operator entrypoint for derivative-specific Magpie queries; print-only dry run.

Query sampling follows pinned Magpie Llama-3.1 (0.8/1.0) or Qwen2 (1.0/1.0)
settings. Qwen3 reuses the published Qwen-family settings, explicitly recorded.
The template is always the selected derivative's; Qwen rendering disables thinking.
"""
import argparse
from contextlib import contextmanager
import sys
import warnings
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
from atlas.workloads import MAGPIE_REV,filter_prompts,language,magpie_prefix,write_jsonl,file_hash


def unpaused():
    roots=set(Path(__file__).resolve().parents)|set(Path.cwd().resolve().parents)|{Path.cwd()}
    for root in roots:
        for rel in ['EXPERIMENTS_PAUSED.json','tlm-spec-maintenance/EXPERIMENTS_PAUSED.json']:
            if (root/rel).exists():raise RuntimeError(f'Experiments paused: {root/rel}')


def request_seeds(seed,iteration,count):
    return [int.from_bytes(hashlib.sha256(f'{seed}/{iteration}/{i}'.encode()).digest()[:8],'big') & ((1<<63)-1) for i in range(count)]


def generation_count(split, smoke):
    return 10 if smoke else 500 if split=='training' else 64


def validate_hardware(name, smoke, allow_a40_production=False):
    if not any(x in name for x in ('H100','H200')) and not ((smoke or allow_a40_production) and 'A40' in name):
        raise ValueError('Production generation requires H100/H200 or explicit --allow-a40-production (D-19); bounded acceptance smoke permits A40')


def verify_inputs(row, adapter, tokenizer, tokenizer_revision):
    expected_revision=row['base_revision'] if row['tokenizer_source']=='inherited_base' else row['revision']
    if tokenizer_revision!=expected_revision:raise ValueError('tokenizer revision does not match pool provenance')
    tok=Path(tokenizer)
    if not tok.is_dir():raise ValueError('use a pinned local tokenizer snapshot for offline reproducibility')
    if file_hash(tok/'tokenizer.json')!=row['tokenizer_sha256']:raise ValueError('tokenizer hash mismatch')
    tc=json.loads((tok/'tokenizer_config.json').read_text())
    template=(tok/'chat_template.jinja').read_bytes() if (tok/'chat_template.jinja').exists() else json.dumps(tc.get('chat_template'),sort_keys=True).encode()
    if hashlib.sha256(template).hexdigest()!=row['template_sha256']:raise ValueError('chat template hash mismatch')
    hashes={}
    if adapter:
        files=json.loads(row['files']) if isinstance(row['files'],str) else row['files']
        specs=[f for f in files if f['path'].startswith('adapter_') and f['path'].endswith(('.json','.safetensors','.bin'))]
        if not any(f['path'].startswith('adapter_model.') for f in specs):raise ValueError('missing adapter weights provenance')
        for spec in specs:
            path=Path(adapter)/spec['path']
            if not path.is_file() or path.stat().st_size!=spec['size']:raise ValueError('adapter file size mismatch')
            actual=file_hash(path);hashes[spec['path']]=actual
            if spec.get('sha256'):
                if actual!=spec['sha256']:raise ValueError('adapter hash mismatch')
            elif spec.get('blob_id'):
                data=path.read_bytes();blob=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
                if blob!=spec['blob_id']:raise ValueError('adapter blob hash mismatch')
            else:raise ValueError('missing adapter file hash provenance')
    return hashes


def candidate_budget(count, smoke, oversample):
    """D-23: at most five times the original attempted-candidate budget."""
    return (12 if smoke else 20)*min(64,count*2)*(5 if oversample else 1)


@contextmanager
def managed_engine(factory):
    llm=factory()
    try:
        yield llm
    finally:
        pending=sys.exc_info()[0] is not None
        try:
            # Pinned vLLM0.31.0 LLM has no public shutdown method. Its core
            # client terminates worker processes with this bounded timeout.
            llm.llm_engine.engine_core.shutdown(timeout=10.)
        except BaseException as error:
            if not pending:raise
            warnings.warn(f'Engine cleanup also failed: {error}',RuntimeWarning)


def collect_queries(generate,config,out,forbidden,pause_check):
    count=config['count'];smoke=config['acceptance_smoke']
    budget=candidate_budget(count,smoke,config['d23_oversampling'])
    candidates=[];kept=[];attempted=0;iteration=0;length_terminated=0
    with (out/'raw_queries.jsonl').open('x') as f:
        while attempted<budget and len(kept)<count:
            pause_check()
            seeds=request_seeds(config['seed'],iteration,min(64,count*2,budget-attempted))
            outputs=generate(seeds)
            for output,sampling_seed in zip(outputs,seeds,strict=True):
                completion=output.outputs[0]
                finished=completion.finish_reason!='length'
                r=dict(prompt_id=f"{config['derivative_id']}-{config['split']}-{len(candidates)}",
                       prompt=completion.text,derivative_id=config['derivative_id'],revision=config['revision'],
                       split=config['split'],seed=config['seed'],sampling_seed=sampling_seed,
                       acceptance_only=smoke,token_ids=list(completion.token_ids))
                f.write(json.dumps(r|dict(attempt_index=attempted,finish_reason=completion.finish_reason))+'\n');f.flush()
                attempted+=1
                if finished:candidates.append(r)
                else:length_terminated+=1
            kept,report=filter_prompts(candidates,forbidden,config['near_threshold'])
            iteration+=1
            progress=report|dict(attempted=attempted,budget=budget,rounds=iteration,length_terminated=length_terminated)
            with (out/'rounds.jsonl').open('a') as log:log.write(json.dumps(progress)+'\n')
    return kept,progress


def finish_generation(out,config,kept,report):
    count=config['count'];complete=len(kept)>=count
    selected=kept[:count]
    for r in selected:r['language']=language(r['prompt'])
    write_jsonl(out/('prompts.jsonl' if complete else 'partial_queries.jsonl'),selected)
    result=dict(status='complete' if complete else 'shortfall',requested=count,n=len(selected),
        valid_before_truncation=len(kept),attempted=report['attempted'],candidate_budget=report['budget'],
        own_domain=('available' if complete else 'unavailable') if config['split']=='evaluation' else None,
        training_ready=complete and config['split']=='training' and not config['acceptance_smoke'],
        acceptance_only=config['acceptance_smoke'],engine_version=config['engine_version'])
    (out/'filter_report.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'ledger_draft.json').write_text(json.dumps(dict(id='EXP-ATL-UNASSIGNED',title=out.name,
        status='pilot',landed=__import__('datetime').date.today().isoformat(),what_why='Derivative Magpie query generation',
        new='Pinned derivative-specific workloads',artifacts=str(out.resolve()),config_results={'config':config,'filters':report,'results':result},
        caveats='Operator must audit global train/evaluation hashes before use. Shortfalls are diagnostic only; no partial production workload. Counts from one deterministic seed, no inferential interval.'),indent=2)+'\n')
    if not complete and not config['d23_oversampling']:
        raise RuntimeError(f'Only {len(kept)} valid queries; require {count}. Raw output preserved.')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--derivative-id',required=True)
    origin=p.add_mutually_exclusive_group(required=True);origin.add_argument('--pool-manifest');origin.add_argument('--target-registry')
    p.add_argument('--target',required=True);p.add_argument('--revision',required=True)
    p.add_argument('--adapter');p.add_argument('--tokenizer',required=True);p.add_argument('--tokenizer-revision',required=True)
    p.add_argument('--family',choices=['llama','qwen3'],required=True)
    p.add_argument('--split',choices=['training','evaluation'],required=True);p.add_argument('--seed',required=True,type=int)
    p.add_argument('--forbidden-files',nargs='+',required=True);p.add_argument('--output',required=True)
    p.add_argument('--d23-oversampling',action='store_true',help='up to5 times original candidate budget; shortfall exits0 with unavailable workload and no prompts.jsonl')
    p.add_argument('--near-threshold',type=float,default=.9);p.add_argument('--dry-run',action='store_true')
    p.add_argument('--acceptance-smoke',action='store_true',help='10 queries only, diagnostic output; permits owner-authorized A40')
    p.add_argument('--allow-a40-production',action='store_true',help='owner decision D-19 permits full counts on A40s while ICE is unavailable')
    p.add_argument('--max-model-len',type=int,default=4096);p.add_argument('--gpu-memory-utilization',type=float,default=.70)
    args=p.parse_args()
    for value in (args.revision,args.tokenizer_revision):
        if not re.fullmatch('[a-f0-9]{40}',value):raise ValueError('model/tokenizer revisions must be SHA pins')
    if args.target_registry:
        from followspec.mixture_targets import registry_row
        row=registry_row(args.target_registry,args.derivative_id,args.tokenizer,args.target,args.revision,allow_acceptance=args.acceptance_smoke)
        if Path(args.adapter or '').resolve()!=Path(row['local_adapter']):raise ValueError('mixture adapter path differs from registry')
    else:
        csv.field_size_limit(max(csv.field_size_limit(),16*1024**2))
        with open(args.pool_manifest) as f:rows=list(csv.DictReader(f))
        matches=[r for r in rows if r['model_id']==args.derivative_id]
        if len(matches)!=1:raise ValueError('derivative must occur exactly once in pool manifest')
        row=matches[0]
        if row['exclusion']:raise ValueError('excluded derivative')
    if args.split=='training' and row['pool'] not in {'bank','mixture'}:raise ValueError('training prompts require a bank derivative')
    if not args.adapter and (args.target!=row['model_id'] or args.revision!=row['revision']):
        raise ValueError('target must match pinned derivative')
    if args.adapter and (args.target!=row['base_id'] or args.revision!=row['base_revision']):
        raise ValueError('adapter base must match pool provenance')
    count=generation_count(args.split,args.acceptance_smoke)
    adapter_hashes=verify_inputs(row,args.adapter,args.tokenizer,args.tokenizer_revision)
    rank=int(row['r']) if args.adapter else 1
    max_rank=next((r for r in (8,16,32,64,128,256,320,512) if r>=rank),None)
    if max_rank is None:raise ValueError('adapter exceeds engine rank cap')
    config=vars(args)|dict(count=count,acceptance_only=args.acceptance_smoke,adapter_sha256=adapter_hashes,max_lora_rank=max_rank,temperature=.8 if args.family=='llama' else 1.,top_p=1.,max_tokens=1024,
        engine_version='0.31.0',enable_thinking=False,
        hardware_policy='D-19 A40 production opt-in' if args.allow_a40_production else 'original H100/H200 production; bounded A40 smoke',
        magpie_revision=MAGPIE_REV,recipe='magpie-llama3.1-8b.sh' if args.family=='llama' else 'magpie-qwen2-7b.sh',
        deviations=['Derivative template replaces hard-coded upstream prefix','No optional de-markdown logits processor; length/exact/MinHash filtering applied'],
        pool_sha256=file_hash(args.pool_manifest or args.target_registry),forbidden_sha256={p:file_hash(p) for p in args.forbidden_files},
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    config['candidate_budget']=candidate_budget(count,args.acceptance_smoke,args.d23_oversampling)
    if args.target_registry:config['mixture_registry']=row['mixture_registry']
    if args.dry_run:print(json.dumps(config,indent=2));return
    unpaused()
    if importlib.metadata.version('vllm')!=config['engine_version']:raise ValueError('engine differs from pin')
    from transformers import AutoTokenizer
    from vllm import LLM,SamplingParams
    import torch
    validate_hardware(torch.cuda.get_device_name(0),args.acceptance_smoke,args.allow_a40_production)
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit tracked code before generation')
    tokenizer=AutoTokenizer.from_pretrained(args.tokenizer,revision=args.tokenizer_revision,trust_remote_code=False)
    prefix=magpie_prefix(tokenizer,args.family)
    stop='<|eot_id|>' if args.family=='llama' else '<|im_end|>'
    stop_id=tokenizer.convert_tokens_to_ids(stop)
    if stop_id is None or stop_id==tokenizer.unk_token_id:raise ValueError('missing end-of-turn token')
    forbidden=[]
    for path in args.forbidden_files:
        records=[json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
        forbidden.extend(r['prompt'] for r in records)
        for r in records:
            if r.get('derivative_id')==args.derivative_id and r.get('seed')==args.seed:
                raise ValueError('training and evaluation generation seeds must differ')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    config.update(prefix=prefix,prefix_sha256=__import__('hashlib').sha256(prefix.encode()).hexdigest(),stop_token_id=stop_id,gpu_type=torch.cuda.get_device_name(0))
    (out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    unpaused()
    def create_engine():
        return LLM(model=args.target,revision=args.revision,tokenizer=args.tokenizer,tokenizer_revision=args.tokenizer_revision,
            dtype='bfloat16',enable_lora=bool(args.adapter),max_lora_rank=max_rank,seed=args.seed,enable_prefix_caching=False,
            max_model_len=args.max_model_len,gpu_memory_utilization=args.gpu_memory_utilization)
    try:
        with managed_engine(create_engine) as llm:
            kwargs={}
            if args.adapter:
                from vllm.lora.request import LoRARequest
                kwargs['lora_request']=LoRARequest(args.derivative_id,1,args.adapter)
            def generate(seeds):
                sampling=[SamplingParams(temperature=config['temperature'],top_p=1.,max_tokens=1024,
                    stop_token_ids=[stop_id],seed=seed) for seed in seeds]
                return llm.generate([prefix]*len(seeds),sampling,use_tqdm=False,**kwargs)
            kept,report=collect_queries(generate,config|dict(revision=row['revision']),out,forbidden,unpaused)
            result=finish_generation(out,config,kept,report)
        print(json.dumps(result))
    except BaseException as error:
        with (out/'failure.json').open('x') as f:json.dump(dict(type=type(error).__name__,error=str(error)),f,indent=2)
        raise

if __name__=='__main__':main()
