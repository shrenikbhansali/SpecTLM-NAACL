"""Operator entrypoint for derivative-specific Magpie queries; print-only dry run.

Query sampling follows pinned Magpie Llama-3.1 (0.8/1.0) or Qwen2 (1.0/1.0)
settings. Qwen3 reuses the published Qwen-family settings, explicitly recorded.
The template is always the selected derivative's; Qwen rendering disables thinking.
"""
import argparse
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


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--derivative-id',required=True);p.add_argument('--pool-manifest',required=True)
    p.add_argument('--target',required=True);p.add_argument('--revision',required=True)
    p.add_argument('--adapter');p.add_argument('--tokenizer',required=True);p.add_argument('--tokenizer-revision',required=True)
    p.add_argument('--family',choices=['llama','qwen3'],required=True)
    p.add_argument('--split',choices=['training','evaluation'],required=True);p.add_argument('--seed',required=True,type=int)
    p.add_argument('--forbidden-files',nargs='+',required=True);p.add_argument('--output',required=True)
    p.add_argument('--near-threshold',type=float,default=.9);p.add_argument('--dry-run',action='store_true')
    args=p.parse_args()
    for value in (args.revision,args.tokenizer_revision):
        if not re.fullmatch('[a-f0-9]{40}',value):raise ValueError('model/tokenizer revisions must be SHA pins')
    with open(args.pool_manifest) as f:rows=list(csv.DictReader(f))
    matches=[r for r in rows if r['model_id']==args.derivative_id]
    if len(matches)!=1:raise ValueError('derivative must occur exactly once in pool manifest')
    row=matches[0]
    if row['exclusion']:raise ValueError('excluded derivative')
    if args.split=='training' and row['pool']!='bank':raise ValueError('training prompts require a bank derivative')
    if not args.adapter and (args.target!=row['model_id'] or args.revision!=row['revision']):
        raise ValueError('target must match pinned derivative')
    if args.adapter and (args.target!=row['base_id'] or args.revision!=row['base_revision']):
        raise ValueError('adapter base must match pool provenance')
    count=500 if args.split=='training' else 64
    config=vars(args)|dict(count=count,temperature=.8 if args.family=='llama' else 1.,top_p=1.,max_tokens=1024,
        engine_version='0.31.0',enable_thinking=False,
        magpie_revision=MAGPIE_REV,recipe='magpie-llama3.1-8b.sh' if args.family=='llama' else 'magpie-qwen2-7b.sh',
        deviations=['Derivative template replaces hard-coded upstream prefix','No optional de-markdown logits processor; length/exact/MinHash filtering applied'],
        pool_sha256=file_hash(args.pool_manifest),forbidden_sha256={p:file_hash(p) for p in args.forbidden_files},
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    if args.dry_run:print(json.dumps(config,indent=2));return
    unpaused()
    if importlib.metadata.version('vllm')!=config['engine_version']:raise ValueError('engine differs from pin')
    from transformers import AutoTokenizer
    from vllm import LLM,SamplingParams
    import torch
    if not any(x in torch.cuda.get_device_name(0) for x in ['H100','H200']):raise ValueError('Magpie data generation requires H100/H200 under sprint policy')
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
    llm=LLM(model=args.target,revision=args.revision,tokenizer=args.tokenizer,tokenizer_revision=args.tokenizer_revision,
        dtype='bfloat16',enable_lora=bool(args.adapter),max_lora_rank=512,seed=args.seed,enable_prefix_caching=False)
    kwargs={}
    if args.adapter:
        from vllm.lora.request import LoRARequest
        kwargs['lora_request']=LoRARequest(args.derivative_id,1,args.adapter)
    candidates=[];kept=[]
    with (out/'raw_queries.jsonl').open('x') as f:
        for iteration in range(20):
            unpaused()
            seeds=request_seeds(args.seed,iteration,min(64,count*2))
            sampling=[SamplingParams(temperature=config['temperature'],top_p=1.,max_tokens=1024,
                stop_token_ids=[stop_id],seed=seed) for seed in seeds]
            outputs=llm.generate([prefix]*len(seeds),sampling,use_tqdm=False,**kwargs)
            for o,sampling_seed in zip(outputs,seeds,strict=True):
                completion=o.outputs[0]
                if completion.finish_reason=='length':continue
                r=dict(prompt_id=f'{args.derivative_id}-{args.split}-{len(candidates)}',prompt=completion.text,
                       derivative_id=args.derivative_id,revision=row['revision'],split=args.split,seed=args.seed,
                       sampling_seed=sampling_seed,token_ids=list(completion.token_ids))
                f.write(json.dumps(r)+'\n');f.flush();candidates.append(r)
            kept,report=filter_prompts(candidates,forbidden,args.near_threshold)
            if len(kept)>=count:break
    if len(kept)<count:raise RuntimeError(f'Only {len(kept)} valid queries; require {count}. Raw output preserved.')
    kept=kept[:count]
    for r in kept:r['language']=language(r['prompt'])
    write_jsonl(out/'prompts.jsonl',kept)
    (out/'filter_report.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'ledger_draft.json').write_text(json.dumps(dict(id='EXP-ATL-UNASSIGNED',title=out.name,
        status='pilot',landed=__import__('datetime').date.today().isoformat(),what_why='Derivative Magpie query generation',
        new='Pinned derivative-specific workloads',artifacts=str(out.resolve()),config_results={'config':config,'filters':report},
        caveats='Operator must audit global train/evaluation hashes before use.'),indent=2)+'\n')

if __name__=='__main__':main()
