"""D-35 permits only proven training shortfalls sufficient for actual D-27 use."""
import json
import random

import pytest
from atlas.run_cell import sha256, write_new
from followspec.production import allocate_queries
from followspec.production_pipeline import jsonl
from followspec.tests.test_production import banks, queries


def evidence(n=364):
    return dict(status='shortfall', n=n, attempted=6400, candidate_budget=6400)


def allocate(n=364, *, nbank=30, proof=None):
    bank=banks(nbank)
    registry=bank | {f'm{i:02}':dict(kind='mixture') for i in range(30)}
    magpie={k:queries(n if k=='m03' else 500,k) for k in registry}
    return allocate_queries(registry,queries(20000),magpie,queries(4,'val'),seed=101,
                            forbidden=[],eligible_bank=sorted(bank),
                            magpie_shortfalls={'m03':evidence(n) if proof is None else proof})


@pytest.mark.parametrize('nbank,n,need',[(30,364,250),(24,250,222),(30,250,250)])
def test_accepts_shortfall_and_records_actual_need_with_same_seed_rule(nbank,n,need):
    a=allocate(n,nbank=nbank)
    assert a==allocate(n,nbank=nbank)
    assert a['magpie_shortfalls']=={'m03':dict(count=n,need=need,decision='D-35')}
    chosen=[q for q in a['queries']['m03'] if q['kind']=='magpie']
    rng=random.Random('101/m03')
    parent_ids=set(a['parent_ids']['MVD'])
    child=[q for q in queries(20000) if q['prompt_id'] not in parent_ids]
    # General sampling advances the same target-seeded RNG before own-query shuffle.
    rng.sample(child,need)
    own=queries(n,'m03');rng.shuffle(own)
    assert [q['prompt_id'] for q in chosen]==[q['prompt_id'] for q in own[:need]]
    assert len(a['arm_ids']['MVD'])==nbank


def test_rejects_shortfall_below_actual_need():
    with pytest.raises(ValueError,match='need'):allocate(249)


def test_rejects_shortfall_with_unexhausted_budget():
    with pytest.raises(ValueError,match='exhaust'):allocate(proof=evidence()|dict(attempted=6399))


def fixture(tmp_path):
    staging=tmp_path/'staging.csv';staging.write_text('pin')
    root=tmp_path/'admission';root.mkdir();write_new(root/'registry.json',{})
    registry={'m03':dict(kind='mixture',revision='b'*40)}
    spec=dict(staging_manifest=str(staging),base_revision='a'*40)
    run=tmp_path/'run';run.mkdir()
    cfg=dict(derivative_id='m03',split='training',acceptance_only=False,revision='a'*40,
             pool_sha256=sha256(root/'registry.json'),count=500,d23_oversampling=True,candidate_budget=6400)
    res=evidence()|dict(requested=500,valid_before_truncation=364,acceptance_only=False)
    write_new(run/'config.json',cfg);write_new(run/'results.json',res)
    rows=[q|dict(derivative_id='m03',revision='b'*40) for q in queries(364,'m03')]
    jsonl(run/'partial_queries.jsonl',rows)
    return root,registry,spec,run


@pytest.mark.parametrize("filename", ["partial_queries.jsonl", "prompts.jsonl"])
def test_missing_prompts_resolves_only_proven_partial_and_hashes_evidence(tmp_path,filename):
    from followspec.production_pipeline import response_magpie_inputs
    root,reg,spec,run=fixture(tmp_path)
    if filename=='prompts.jsonl':
        (run/'partial_queries.jsonl').rename(run/filename)
    rows,shortfalls,hashes=response_magpie_inputs(reg,spec,root,{'m03':str(run/'prompts.jsonl')})
    assert len(rows['m03'])==364 and shortfalls['m03']['n']==364
    for source in ('config.json','results.json',filename):
        assert hashes[str(run/source)]==sha256(run/source)
    assert (run/'prompts.jsonl').exists()==(filename=='prompts.jsonl')


@pytest.mark.parametrize('mutation',['unexhausted','budget','count','eval','acceptance','pin','target_pin',
                                     'failure','status','missing_result','pool','requested'])
def test_shortfall_cannot_bypass_production_checks(tmp_path,mutation):
    from followspec.production_pipeline import response_magpie_inputs
    root,reg,spec,run=fixture(tmp_path)
    cfg=json.loads((run/'config.json').read_text());res=json.loads((run/'results.json').read_text())
    if mutation=='unexhausted':res['attempted']=6399
    if mutation=='budget':cfg['candidate_budget']=1280
    if mutation=='count':res['n']=363
    if mutation=='eval':cfg['split']='evaluation'
    if mutation=='acceptance':cfg['acceptance_only']=True
    if mutation=='pin':cfg['revision']='c'*40
    if mutation=='target_pin':reg['m03']['revision']='c'*40
    if mutation=='pool':cfg['pool_sha256']='wrong'
    if mutation=='requested':cfg['count']=364
    if mutation=='failure':write_new(run/'failure.json',dict(error='infrastructure'))
    if mutation=='status':res['status']='complete'
    (run/'config.json').write_text(json.dumps(cfg));(run/'results.json').write_text(json.dumps(res))
    if mutation=='missing_result':(run/'results.json').unlink()
    with pytest.raises((ValueError,FileNotFoundError)):
        response_magpie_inputs(reg,spec,root,{'m03':str(run/'prompts.jsonl')})


@pytest.mark.parametrize('mutation', ['short_complete', 'long_complete', 'excluded_bank', 'mixture_bound',
                                     'validation', 'forbidden', 'evaluation_row', 'acceptance_row'])
def test_shortfall_does_not_relax_other_allocation_checks(mutation):
    bank=banks(30);reg=bank | {f'm{i:02}':dict(kind='mixture') for i in range(30)}
    mag={k:queries(364 if k=='m03' else 500,k) for k in reg}
    val=queries(4,'val');forbidden=[];eligible=sorted(bank)
    if mutation=='short_complete':mag['m04']=mag['m04'][:499]
    if mutation=='long_complete':mag['m04']=queries(501,'m04')
    if mutation=='excluded_bank':eligible.remove('b00')
    if mutation=='mixture_bound':reg['extra']=dict(kind='mixture');mag['extra']=queries(500,'extra')
    if mutation=='validation':val=[mag['m03'][0]]
    if mutation=='forbidden':forbidden=[mag['m03'][0]]
    if mutation=='evaluation_row':mag['m03'][0]['split']='evaluation'
    if mutation=='acceptance_row':mag['m03'][0]['acceptance_only']=True
    with pytest.raises(ValueError):
        allocate_queries(reg,queries(20000),mag,val,seed=101,forbidden=forbidden,
                         eligible_bank=eligible,magpie_shortfalls={'m03':evidence()})
