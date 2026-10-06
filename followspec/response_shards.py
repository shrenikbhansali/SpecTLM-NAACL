"""Parallel parent responses with original batches, global seeds and strict join."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from atlas.generate_magpie import request_seeds
from atlas.run_cell import sha256,write_new
from atlas.workloads import prompt_hash
from followspec.production_pipeline import checked_stage,execution_spec,finish,jsonl,lines,new_output,read


def response_partition(n, batch_size, index=None, count=None):
    if n<=0 or batch_size<=0:raise ValueError('nonempty input and positive batch size required')
    if index is None and count is None:return 0,n
    batches=(n+batch_size-1)//batch_size
    if type(index) is not int or type(count) is not int or not 1<=count<=batches or not 0<=index<count:
        raise ValueError('valid shard index/count required; no empty shards')
    return (batches*index//count)*batch_size,min(n,(batches*(index+1)//count)*batch_size)


def join_parent_shards(shards, output):
    from followspec.token_data import response_run
    from followspec.render_inputs import load_bundle
    loaded=[response_run(p) for p in shards]
    if not loaded:raise ValueError('complete shard set required')
    loaded.sort(key=lambda item:item[1].get('response_shard',{}).get('index',-1))
    reference=loaded[0][1];parts=[c.get('response_shard',{}) for _,c,_ in loaded]
    count=parts[0].get('count')
    if count!=len(loaded) or [m.get('index') for m in parts]!=list(range(count)):
        raise ValueError('complete shard set required exactly once')
    if reference['derivative_id']!='base' or reference['prompt_target']!='base':raise ValueError('parent responses only')
    queries=lines(reference['prompts']);n=len(queries)
    if sha256(reference['prompts'])!=reference['prompt_sha256']:raise ValueError('parent prompts changed')
    if read(Path(reference['rendered_inputs']).parent/'config.json')!=reference['rendered_input_provenance']:
        raise ValueError('rendered input provenance changed')
    inputs=load_bundle(reference['rendered_inputs'],queries,prompt_target='base',base_tokenizer_sha256=reference['tokenizer_sha256'],prompt_sha256=reference['prompt_sha256'])
    digest=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()
    if digest!=reference['rendered_tokens_sha256']:raise ValueError('full rendered token hash differs')
    ignored={'output','n','response_shard'}
    controls=lambda c:{k:v for k,v in c.items() if k not in ignored}
    seeds=request_seeds(reference['seed'],0,n);merged=[];proof=[];wall=0.
    for rows,cfg,provenance in loaded:
        if controls(cfg)!=controls(reference):raise ValueError('shard generation controls differ')
        m=cfg['response_shard'];start,end=response_partition(n,cfg['batch_size'],m['index'],count)
        if m!=dict(index=m['index'],count=count,start=start,end=end,total_n=n) or cfg['n']!=end-start or len(rows)!=end-start:
            raise ValueError('shard coverage/batch boundaries differ')
        for j,row in enumerate(rows,start):
            if row.get('sampling_seed')!=seeds[j]:raise ValueError('global seed differs')
            if row['sample_id']!=queries[j]['prompt_id'] or row['prompt_sha256']!=prompt_hash(queries[j]['prompt']) or row['prompt_token_ids']!=inputs[j]['prompt_token_ids']:
                raise ValueError('global query identity/order or exact tokens differ')
        merged.extend(rows);proof.append(provenance);wall+=read(Path(provenance['path'])/'results.json')['wall_s']
    out=new_output(output)
    cfg={k:v for k,v in reference.items() if k!='response_shard'}
    cfg.update(output=str(out),n=n,parallel_response_sources=proof)
    write_new(out/'config.json',cfg);jsonl(out/'per_prompt.jsonl',merged)
    counts=[len(r['completion_token_ids']) for r in merged]
    result=dict(n=n,assistant_tokens=sum(counts),per_sample_assistant_tokens=counts,wall_s=wall,
        wall_s_definition='sum of shard engine wall times, not end-to-end latency',acceptance_only=cfg['acceptance_only'],
        training_ready=False,n_shards=count,caveat='Complete parent response union; matched assembly and decoded mask review still required')
    write_new(out/'results.json',result)
    write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
        what_why='Parallel execution of unchanged parent response batches',new='Global query order/seeds/coverage and exact-token union verified',
        artifacts=str(out),config_results=dict(config=cfg,results=result),caveats=result['caveat']))
    return out


def parallel_parent(plan, output, *, count, code_repo):
    root,cfg=checked_stage(plan)
    if cfg['stage']!='responses':raise ValueError('response plan required')
    runs=read(root/'response_runs.json');pair=runs['base']
    if pair['base']!=pair['child']:raise ValueError('parent aliases must identify the same source')
    source=Path(pair['base']).resolve()
    if (source/'results.json').exists():raise ValueError('parent already complete; reuse it')
    original=lines(root/('effective_jobs.jsonl' if (root/'effective_jobs.jsonl').exists() else 'jobs.jsonl'))
    selected=[];others=[]
    for job in original:
        a=job['args'];cmd=a[a.index('--')+1:]
        (selected if Path(cmd[cmd.index('--output')+1]).resolve()==source else others).append(job)
    if len(selected)!=1:raise ValueError('one original parent command required')
    template=selected[0];a=template['args'];cmd=a[a.index('--')+1:]
    if 'followspec.generate_responses' not in cmd or cmd[cmd.index('--derivative-id')+1]!='base' or cmd[cmd.index('--prompt-target')+1]!='base':
        raise ValueError('only canonical base parent generation can be parallelized')
    prompts=Path(cmd[cmd.index('--prompts')+1]);rendered=Path(cmd[cmd.index('--rendered-inputs')+1])
    n=len(lines(prompts));batch=int(cmd[cmd.index('--batch-size')+1]) if '--batch-size' in cmd else 32
    response_partition(n,batch,0,count)
    spec=execution_spec(cfg['spec'],code_repo);out=Path(output).resolve();jobs=[];paths=[]
    for index in range(count):
        job=copy.deepcopy(template);args=job['args'];split=args.index('--');command=args[split+1:]
        dest=out/'shards'/f'part-{index:03}';paths.append(str(dest));job['name']=f'{out.name}-parent-{index:03}'
        args[args.index('--tag')+1]=job['name'];args[args.index('--code-repo')+1]=spec['code_repo']
        args[args.index('--engine-lock')+1]=str(Path(spec['code_repo'])/'atlas/env/requirements.lock')
        args[split+1+command.index('--output')+1]=str(dest)
        args+=['--shard-index',str(index),'--shard-count',str(count)]
        job['allowed_nodes']=[f'heck-srv{i}' for i in range(1,6)];jobs.append(job)
    inputs=cfg.get('input_sha256',{})|{str(prompts):sha256(prompts),str(rendered):sha256(rendered)}
    out=new_output(out);joined=out/'joined-parent';runs['base']={'child':str(joined),'base':str(joined)}
    write_new(out/'response_runs.json',runs);write_new(out/'assignment.json',read(root/'assignment.json'))
    jsonl(out/'jobs.jsonl',jobs);jsonl(out/'effective_jobs.jsonl',jobs+others);write_new(out/'shard_runs.json',paths)
    write_new(out/'render_commands.json',[])
    write_new(out/'join_command.json',[spec['python'],'-m','followspec.response_shards','join','--shards',*paths,'--output',str(joined)])
    finish(out,cfg|dict(spec=spec,parallel_parent_of=str(root),parallel_parent_stage_sha256=sha256(root/'stage_files.json'),
        superseded_parent_source=str(source),input_sha256=inputs),dict(n_gpu_jobs=count,n_effective_gpu_jobs=count+len(others),
        n_parent_queries=n,production_ready=False,next='Run shards and strict join, then assemble this overlay with unchanged other sources'))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('plan');a.add_argument('--plan',required=True);a.add_argument('--output',required=True);a.add_argument('--count',type=int,required=True);a.add_argument('--code-repo',required=True)
    a=sub.add_parser('join');a.add_argument('--shards',nargs='+',required=True);a.add_argument('--output',required=True)
    a=p.parse_args()
    print(parallel_parent(a.plan,a.output,count=a.count,code_repo=a.code_repo) if a.mode=='plan' else join_parent_shards(a.shards,a.output))


if __name__=='__main__':main()
