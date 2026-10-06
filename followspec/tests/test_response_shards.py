import hashlib,json
from pathlib import Path
import pytest
from atlas.run_cell import sha256,write_new
from atlas.workloads import prompt_hash
from atlas.generate_magpie import request_seeds
from followspec.generate_responses import make_sample
from followspec.production_pipeline import jsonl,read,finish


def source_shards(tmp_path):
    queries=[dict(prompt_id=f'p{i}',prompt=f'Explain example {i}.',split='training') for i in range(65)]
    q=tmp_path/'queries.jsonl';jsonl(q,queries)
    rendered=tmp_path/'rendered';rendered.mkdir();r=rendered/'prompts.jsonl'
    rows=[dict(prompt_id=x['prompt_id'],raw_prompt_sha256=prompt_hash(x['prompt']),rendered_token_ids=[1,i+2]) for i,x in enumerate(queries)]
    jsonl(r,rows);meta=dict(schema='followspec_rendered_training_v1',rendered_sha256=sha256(r),prompt_target_id='base',tokenizer_sha256='t',prompt_sha256=sha256(q),n=65)
    write_new(rendered/'config.json',meta)
    cfg=dict(schema='followspec_response_tokens_v1',engine_version='0.31.0',acceptance_only=True,base_revision='a'*40,
        derivative_id='base',derivative_revision='a'*40,prompt_target='base',seed=11,temperature=.6,top_p=.95,max_new_tokens=64,
        max_lora_rank=256,batch_size=32,gpu_type='NVIDIA A40',prompts=str(q),prompt_sha256=sha256(q),rendered_inputs=str(r),
        tokenizer_sha256='t',rendered_input_provenance=meta,rendered_tokens_sha256=hashlib.sha256(json.dumps([{'prompt_token_ids':x['rendered_token_ids']} for x in rows],sort_keys=True).encode()).hexdigest())
    paths=[];seeds=request_seeds(11,0,65)
    for index,(start,end) in enumerate([(0,32),(32,64),(64,65)]):
        p=tmp_path/f'shard{index}';p.mkdir();data=[]
        for i in range(start,end):
            sample=make_sample(queries[i],rows[i]['rendered_token_ids'],[100+i],target_id='base',revision='a'*40,acceptance_only=True)
            sample['sampling_seed']=seeds[i];data.append(sample)
        write_new(p/'config.json',cfg|dict(output=str(p),n=end-start,response_shard=dict(index=index,count=3,start=start,end=end,total_n=65)))
        jsonl(p/'per_prompt.jsonl',data);write_new(p/'results.json',dict(n=end-start,assistant_tokens=end-start,wall_s=1))
        paths.append(p)
    return paths


def test_partition_preserves_every_original_batch_and_global_index():
    from followspec.response_shards import response_partition
    for n in [1,32,33,65,10512]:
        batches=(n+31)//32;count=min(8,batches);ranges=[response_partition(n,32,i,count) for i in range(count)]
        assert [j for start,end in ranges for j in range(start,end)]==list(range(n))
        assert all(start%32==0 and (end==n or end%32==0) for start,end in ranges)
    assert response_partition(65,32,None,None)==(0,65)
    for index,count in [(None,2),(0,None),(3,3),(-1,2),(0,4)]:
        with pytest.raises(ValueError):response_partition(65,32,index,count)


def test_join_validates_full_coverage_order_seeds_and_masks(tmp_path):
    from followspec.response_shards import join_parent_shards
    from followspec.token_data import response_run
    paths=source_shards(tmp_path);out=join_parent_shards(list(reversed(paths)),tmp_path/'joined')
    rows,cfg,_=response_run(out)
    assert [r['sample_id'] for r in rows]==[f'p{i}' for i in range(65)]
    assert [r['sampling_seed'] for r in rows]==request_seeds(11,0,65)
    assert cfg['n']==65 and 'response_shard' not in cfg and cfg['acceptance_only']
    assert len(cfg['parallel_response_sources'])==3 and read(out/'results.json')['assistant_tokens']==65


def test_join_refuses_missing_shards(tmp_path):
    from followspec.response_shards import join_parent_shards
    paths=source_shards(tmp_path)
    with pytest.raises(ValueError,match='complete shard'):join_parent_shards(paths[:2],tmp_path/'joined')
    assert not (tmp_path/'joined').exists()


def test_join_refuses_local_instead_of_global_seeds(tmp_path):
    from followspec.response_shards import join_parent_shards
    paths=source_shards(tmp_path);p=paths[1]/'per_prompt.jsonl';rows=[json.loads(s) for s in p.read_text().splitlines()];rows[0]['sampling_seed']=request_seeds(11,0,1)[0];p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    with pytest.raises(ValueError,match='global seed'):join_parent_shards(paths,tmp_path/'joined')


def test_join_refuses_changed_generation_controls(tmp_path):
    from followspec.response_shards import join_parent_shards
    paths=source_shards(tmp_path);p=paths[1]/'config.json';c=read(p);c['temperature']=.7;p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='controls'):join_parent_shards(paths,tmp_path/'joined')


def test_parallel_parent_plan_preserves_other_sources_and_commands(tmp_path):
    from followspec.response_shards import parallel_parent
    from followspec.tests.test_training_jobs import final_stage
    from followspec.production import launcher_job
    final=final_stage(tmp_path);spec=read(final/'config.json')['spec']
    q=tmp_path/'parent.jsonl';jsonl(q,[dict(prompt_id=str(i),prompt='text') for i in range(65)])
    rendered=tmp_path/'rendered.jsonl';jsonl(rendered,[{'rendered_token_ids':[1]}])
    plan=tmp_path/'plan';plan.mkdir();parent=plan/'old-parent';other=plan/'other'
    write_new(plan/'assignment.json',{'queries':{'base':[],'child':[]}})
    write_new(plan/'response_runs.json',{'base':{'child':str(parent),'base':str(parent)},'child':{'child':str(other),'base':str(other)}})
    cmd=['-m','followspec.generate_responses','--derivative-id','base','--prompt-target','base','--prompts',str(q),'--rendered-inputs',str(rendered),'--seed','3','--output',str(parent)]
    jobs=[launcher_job(spec,'parent','M2',q,cmd),launcher_job(spec,'other','M2',q,['echo','--output',str(other)])]
    jsonl(plan/'jobs.jsonl',jobs);finish(plan,dict(stage='responses',spec=spec),dict(n_gpu_jobs=2))
    out=parallel_parent(plan,tmp_path/'parallel',count=3,code_repo=spec['code_repo'])
    runmap=read(out/'response_runs.json');assert runmap['base']['base']==runmap['base']['child'] and runmap['child']['child']==str(other)
    new=[json.loads(s) for s in (out/'jobs.jsonl').read_text().splitlines()];assert len(new)==3
    for i,j in enumerate(new):
        a=j['args'];assert a[a.index('--shard-index')+1]==str(i) and a[a.index('--shard-count')+1]=='3'
        assert a[a.index('--prompts')+1]==str(q)
    assert len((out/'effective_jobs.jsonl').read_text().splitlines())==4
