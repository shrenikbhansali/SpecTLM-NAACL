"""CPU fixture through real paired assembly and readiness, with no GPU claims."""
import json
from pathlib import Path
import sys
import types
import pytest
from atlas.run_cell import sha256, write_new
from atlas.workloads import prompt_hash
from followspec.production_pipeline import finish,jsonl,read,checked_stage
from followspec.production_assembly import assemble,finalize
from followspec.audit_batches import inspect_batches


def source(out,target,origin,queries):
    out.mkdir(parents=True)
    answer=[4,5,6,7] if target!='base' else [8,9]
    revision='b'*40 if target!='base' else 'a'*40
    rows=[]
    for q in queries:
        rows.append(dict(sample_id=q['prompt_id'],prompt_id=q['prompt_id'],raw_prompt=q['prompt'],
            prompt_sha256=prompt_hash(q['prompt']),split='train',generation_target=target,generation_revision=revision,
            input_ids=[1,2,3]+answer,prompt_token_ids=[1,2,3],completion_token_ids=answer,response_start=3,
            loss_mask=[False]*3+[True]*len(answer),acceptance_only=False,sampling_seed=101))
    cfg=dict(schema='followspec_response_tokens_v1',engine_version='0.31.0',acceptance_only=False,base_revision='a'*40,
             derivative_id=target,derivative_revision=revision,prompt_target=origin,seed=1,temperature=.6,top_p=.95,
             max_new_tokens=512,max_lora_rank=128,batch_size=32,gpu_type='NVIDIA A40')
    write_new(out/'config.json',cfg);write_new(out/'results.json',dict(n=len(rows),assistant_tokens=len(answer)*len(rows)))
    jsonl(out/'per_prompt.jsonl',rows)
    return str(out)


def fixture(tmp_path):
    def q(i,role,kind):return dict(prompt_id=i,prompt='Fixture query '+i,split='training',role=role,kind=kind)
    child=[q(f'c{i}','child','magpie' if i%2==0 else 'general') for i in range(12)]
    parent=[q(f'p{i}','parent','general') for i in range(4)]
    val=[q(f'v{i}','validation','general') for i in range(2)]
    admission=tmp_path/'admission';admission.mkdir()
    write_new(admission/'registry.json',{'c':dict(kind='bank',revision='b'*40)})
    finish(admission,dict(stage='admit'),dict(ready=True))
    assignment=dict(queries={'c':child+val,'base':parent+val},arm_ids={a:{'c':[q['prompt_id'] for q in child]} for a in ['FS','MVD']},
                    parent_ids={a:[q['prompt_id'] for q in parent] for a in ['FS','MVD']},validation=val)
    runs={'c':dict(child=source(tmp_path/'child','c','c',child+val),base=source(tmp_path/'base','base','c',child+val))}
    p=source(tmp_path/'parent','base','base',parent+val);runs['base']=dict(child=p,base=p)
    plan=tmp_path/'plan';plan.mkdir();write_new(plan/'assignment.json',assignment);write_new(plan/'response_runs.json',runs)
    spec=dict(seed=101,base_revision='a'*40,drafter_revision='d'*40,max_lora_rank=128,base_snapshot=str(tmp_path/('a'*40)))
    finish(plan,dict(stage='responses',admission=str(admission),spec=spec,input_sha256={},forbidden_files=[]),dict(production_ready=False))
    return plan


class Sampler:
    def __init__(self,**kw):self.n=len(kw['lengths'])
    def set_epoch(self,epoch):pass
    def __iter__(self):return iter([list(range(self.n))])


def mock_runtime(monkeypatch):
    class Tokenizer:
        def decode(self,ids):return 'TOKENS '+str(ids)
    monkeypatch.setitem(sys.modules,'transformers',types.SimpleNamespace(AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *a,**kw:Tokenizer())))
    monkeypatch.setattr('followspec.production_assembly.native_auditor',lambda lengths:inspect_batches(lengths,factory=Sampler,
        batch_max_length=8192,seeds=[0,1,2],epochs=1,replicas=1))


def test_complete_paired_assembly_keeps_sources_and_finalizes_only_after_review(tmp_path,monkeypatch):
    plan=fixture(tmp_path);mock_runtime(monkeypatch)
    sources={p:p.read_bytes() for dirname in ['child','base','parent'] for p in (tmp_path/dirname).iterdir()}
    out=assemble(str(plan),str(tmp_path/'assembled'));result=read(out/'results.json')
    assert not result['production_ready'] and result['matched']['shifted_sequence_tokens']==64
    assert len((out/'paired_trims.jsonl').read_text().splitlines())==20
    for arm in ['FS','MVD','PO-D','PO-T']:
        m=read(out/arm/'manifest.json')
        assert m['parent_sample_share']==.25 and m['optimizer_steps']==1 and not m['data_acceptance_passed']
        assert result['arms'][arm]['n_train']==16 and result['arms'][arm]['n_val']==4
        decoded=[json.loads(x) for x in (out/arm/'decoded_masks.jsonl').read_text().splitlines()]
        assert len(decoded)==5
        assert all(r['loss_mask']==[False]*3+[True]*2 for r in decoded)
    assert all(p.read_bytes()==b for p,b in sources.items())
    proof=tmp_path/'features.json';write_new(proof,dict(passed=True,scope='CPU fixture only'))
    evidence=tmp_path/'evidence.json';write_new(evidence,dict(feature_acceptance=str(proof),feature_acceptance_sha256=sha256(proof),
        mask_review_sha256={a:sha256(out/a/'decoded_masks.jsonl') for a in ['FS','MVD','PO-D','PO-T']}))
    final=finalize(str(out),str(evidence),str(tmp_path/'final'))
    assert read(final/'results.json')['data_ready']
    assert not read(final/'results.json')['production_ready']
    for a in ['FS','MVD','PO-D','PO-T']:
        assert read(final/a/'manifest.json')['data_acceptance_passed']
        assert read(final/a/'training_config.json')['token_budget']==64
    with pytest.raises(FileExistsError):assemble(str(plan),str(out))
    assert not (out/'failure.json').exists()


def test_changed_generation_recipe_and_changed_stage_are_refused(tmp_path,monkeypatch):
    plan=fixture(tmp_path);mock_runtime(monkeypatch)
    p=tmp_path/'child'/'config.json';c=read(p);c['max_new_tokens']=64;p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='recipe'):assemble(str(plan),str(tmp_path/'refused'))
    assert not (tmp_path/'refused').exists()
    (plan/'assignment.json').write_text('{}')
    with pytest.raises(ValueError,match='stage changed'):checked_stage(plan)


def test_response_job_pairs_share_rendering_seed_and_rank_but_use_correct_templates(tmp_path,monkeypatch):
    """Isolate CLI construction; quota logic is tested on the full33+30 fixture."""
    from followspec.production_pipeline import responses
    import followspec.production_pipeline as pipeline
    staging=tmp_path/'staging.csv';staging.write_text('fixture provenance')
    general=tmp_path/'general.jsonl';validation=tmp_path/'val.jsonl';forbidden=tmp_path/'eval.jsonl'
    q=dict(prompt_id='g',prompt='Training general',split='training')
    val=dict(prompt_id='v',prompt='Held-out training validation',split='training')
    mag=dict(prompt_id='m',prompt='Own Magpie query',split='training',derivative_id='c',revision='b'*40)
    jsonl(general,[q,val]);jsonl(validation,[val]);jsonl(forbidden,[dict(prompt_id='e',prompt='Public evaluation')])
    base=str(tmp_path/('a'*40));own=str(tmp_path/('b'*40))
    spec=dict(seed=101,base_id='base',base_snapshot=base,base_revision='a'*40,python=sys.executable,
        code_repo=str(tmp_path/'repo'),staging_manifest=str(staging),downloads=str(tmp_path/'downloads.jsonl'),
        general_prompts=str(general),forbidden_files=[str(forbidden)],max_lora_rank=128)
    prepared=tmp_path/'prepared';prepared.mkdir()
    write_new(prepared/'bank_metadata.json',{'c':dict(tokenizer=own,tokenizer_revision='b'*40,filter_run='/A2/accepted')})
    finish(prepared,dict(stage='prepare',spec=spec),{})
    admission=tmp_path/'admission';admission.mkdir()
    write_new(admission/'registry.json',{'c':dict(kind='bank',path=own,revision='b'*40,files_sha256={'adapter_config.json':'hash'})})
    finish(admission,dict(stage='admit',plan=str(prepared),spec=spec),dict(ready=True))
    magdir=tmp_path/'magpie';magdir.mkdir();jsonl(magdir/'prompts.jsonl',[mag])
    write_new(magdir/'config.json',dict(derivative_id='c',split='training',acceptance_only=False,
        pool_sha256=sha256(staging),revision='a'*40,count=500))
    paths=tmp_path/'paths.json';write_new(paths,{'c':str(magdir/'prompts.jsonl')})
    assignment=dict(queries={'c':[mag|dict(role='child',kind='magpie')], 'base':[q|dict(role='parent',kind='general')]},counts={})
    monkeypatch.setattr(pipeline,'allocate_queries',lambda *a,**kw:assignment)
    out=responses(str(admission),str(paths),str(validation),str(tmp_path/'responses'),[])
    commands=read(out/'render_commands.json')
    bank_render=next(c for c in commands if c[c.index('--derivative-id')+1]=='c')
    assert bank_render[bank_render.index('--tokenizer')+1]==own
    jobs=[json.loads(s) for s in (out/'jobs.jsonl').read_text().splitlines()]
    paired=[]
    for j in jobs:
        cmd=j['args'][j['args'].index('--')+1:]
        assert '--allow-a40-production' in cmd and '--acceptance-smoke' not in cmd
        if cmd[cmd.index('--prompt-target')+1]=='c':paired.append(cmd)
    assert len(paired)==2
    for key in ['--rendered-inputs','--prompts','--seed','--max-lora-rank']:
        assert paired[0][paired[0].index(key)+1]==paired[1][paired[1].index(key)+1]
    for cmd in paired:
        target=cmd[cmd.index('--derivative-id')+1]
        assert cmd[cmd.index('--tokenizer')+1]==(base if target=='base' else own)
        assert cmd[cmd.index('--filter-run')+1]=='/A2/accepted'
