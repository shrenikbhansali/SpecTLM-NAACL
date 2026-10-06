"""Owner-approved fresh candidate plan; historical scores cannot leak into it."""
import csv
import json
from pathlib import Path
import pytest
from atlas.run_cell import sha256
from followspec.production import sample_candidates,allocate_queries
from followspec.production_pipeline import finish,write_new,jsonl,read,bank_eligibility
from followspec.tests.test_bank_eligibility import fixture as prompt_fixture
from followspec.tests.test_production import queries


def fixture(tmp_path):
    registry={};runs={};spec=None
    for i in range(4):
        child=tmp_path/f'child{i}';child.mkdir();reg,spec,run=prompt_fixture(child,short=i==3)
        name=f'b{i}';root=Path(run['child']);registry[name]=reg['child']|dict(rank=32,path=str(child/'weights'))
        cfg=read(root/'config.json');cfg['derivative_id']=name;(root/'config.json').write_text(json.dumps(cfg))
        file=root/('partial_queries.jsonl' if i==3 else 'prompts.jsonl')
        rows=[json.loads(s)|dict(derivative_id=name) for s in file.read_text().splitlines()]
        file.write_text(''.join(json.dumps(r)+'\n' for r in rows));runs[name]=str(root)
    pool=tmp_path/'pool.csv'
    with pool.open('w') as f:
        w=csv.DictWriter(f,fieldnames=['model_id','in_bank','revision']);w.writeheader()
        w.writerows(dict(model_id=k,in_bank='True',revision=v['revision']) for k,v in registry.items())
    spec|=dict(pool_manifest=str(pool),seed=101,max_lora_rank=128)
    plan=tmp_path/'plan';plan.mkdir()
    for name,value in [('bank_registry.json',registry),('bank_metadata.json',{k:dict(tokenizer='base') for k in registry}),
                       ('candidates.json',sample_candidates(registry,seed=101,max_lora_rank=128))]:write_new(plan/name,value)
    jsonl(plan/'reference_queries.jsonl',queries(128))
    finish(plan,dict(stage='prepare',spec=spec,inputs_sha256={str(pool):sha256(pool)}),dict(n_bank=4))
    mapping=tmp_path/'runs.json';write_new(mapping,runs)
    audit=bank_eligibility(str(plan),str(mapping),str(tmp_path/'audit'))
    return plan,audit


def test_fresh_plan_drops_sources_recomputes_universe_and_keeps_all_history(tmp_path):
    from followspec.production_pipeline import replan_d28
    plan,audit=fixture(tmp_path)
    before={p:p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    fresh=replan_d28(str(plan),str(audit),str(tmp_path/'fresh'))
    again=replan_d28(str(plan),str(audit),str(tmp_path/'again'))
    registry=read(fresh/'bank_registry.json');candidates=read(fresh/'candidates.json')
    assert set(registry)=={'b0','b1','b2'} and len(candidates)==60
    assert candidates==read(again/'candidates.json')
    assert not {r['id'] for r in candidates}&{r['id'] for r in read(plan/'candidates.json')}
    assert all(set(r['source_ids'])<=registry.keys() for r in candidates)
    assert [r['round'] for r in candidates]==[1]*30+[2]*30
    assert (fresh/'reference_queries.jsonl').read_bytes()==(plan/'reference_queries.jsonl').read_bytes()
    cfg=read(fresh/'config.json');assert cfg['stage']=='prepare' and cfg['spec']['d28_eligible_bank']==['b0','b1','b2']
    with open(cfg['spec']['pool_manifest']) as f:assert {r['model_id'] for r in csv.DictReader(f) if r['in_bank']=='True'}==set(registry)
    excluded=read(fresh/'superseded_candidates.json')
    assert any(r['dropped_source_ids']==['b3'] for r in excluded)
    assert all(p.read_bytes()==b for p,b in before.items())
    assert not any('admission' in v for v in registry.values())


def test_replan_rechecks_raw_evidence_and_refuses_wrong_audit_plan(tmp_path):
    from followspec.production_pipeline import replan_d28
    plan,audit=fixture(tmp_path)
    evidence=read(audit/'eligibility.json');raw=next(Path(p) for p in evidence['evidence_sha256'] if p.endswith('raw_queries.jsonl'))
    raw.write_text('{}\n')
    with pytest.raises(ValueError):replan_d28(str(plan),str(audit),str(tmp_path/'bad'))
    assert not (tmp_path/'bad').exists()
