"""FIX-4 acceptance: recipe, leakage, dependencies and exact tail matching."""
import copy
import json
from pathlib import Path
import pytest
from followspec.production import (sample_candidates, allocate_queries, match_tails,
                                  launcher_job, admission_selection, validate_spec)


def banks(n=33):
    return {f'b{i:02}': {'kind': 'bank', 'rank': 32} for i in range(n)}


def queries(n, prefix='g'):
    return [dict(prompt_id=f'{prefix}-{i}', prompt=f'Unique {prefix} question {i}', split='training') for i in range(n)]


def test_sampling_is_fixed_before_scores_two_rounds_and_rank_limited():
    reg=banks(); a=sample_candidates(reg,seed=101,max_lora_rank=128)
    assert a==sample_candidates(dict(reversed(list(reg.items()))),seed=101,max_lora_rank=128)
    assert len(a)==60 and [r['round'] for r in a]==[1]*30+[2]*30
    for r in a:
        assert len(set(r['source_ids'])) in (2,3)
        assert 0<=r['scale']<=1.5 and sum(r['weights'])==pytest.approx(1)
        assert sum(reg[x]['rank'] for x in r['source_ids'])<=128
    with pytest.raises(ValueError,match='rank'):sample_candidates(banks(3),seed=1,max_lora_rank=32)


def test_admission_uses_first_passing_candidates_and_requires_second_round_if_needed():
    ids=[f'm{i}' for i in range(60)]
    r=admission_selection(ids,dict.fromkeys(ids[:30],True))
    assert r['ready'] and r['admitted']==ids[:30] and not r['next_round']
    results={k:i<22 for i,k in enumerate(ids[:30])}
    r=admission_selection(ids,results)
    assert not r['ready'] and r['next_round']==2
    results.update(dict.fromkeys(ids[30:],False))
    assert admission_selection(ids,results)['ready']
    results[ids[0]]=False;results[ids[1]]=False;results[ids[2]]=False
    assert not admission_selection(ids,results)['ready']
    with pytest.raises(ValueError,match='complete'):admission_selection(ids,{ids[0]:True})


def allocation():
    reg=banks()|{f'm{i:02}':{'kind':'mixture'} for i in range(30)}
    mag={k:queries(500,k) for k in reg}
    return allocate_queries(reg,queries(20000),mag,queries(4,'val'),seed=101,forbidden=queries(4,'eval'))


def test_d27_queries_reuse_bank_generation_and_isolate_parent_general_validation():
    a=allocation(); assert a==allocation()
    assert a['counts']['fs_per_target']==524
    assert sum(len(x) for x in a['arm_ids']['MVD'].values())==33000
    assert sum(len(x) for x in a['arm_ids']['FS'].values())==33012
    assert len(a['parent_ids']['MVD'])==11000 and len(a['parent_ids']['FS'])==11004
    general=set();parent={q['prompt_id'] for q in a['queries']['base'] if q['role']=='parent'}
    for target, rows in a['queries'].items():
        if target=='base':continue
        selected=set(a['arm_ids']['FS'][target]); train=[q for q in rows if q['prompt_id'] in selected]
        assert sum(q['kind']=='magpie' for q in train)==sum(q['kind']=='general' for q in train)
        general.update(q['prompt_id'] for q in rows if q['kind']=='general' and q['role']=='child')
        assert len({q['prompt_id'] for q in rows})==len(rows)
    assert not general&parent
    assert not ({q['prompt_id'] for q in a['validation']} & (parent|general))
    for target in banks():assert set(a['arm_ids']['FS'][target])<=set(a['arm_ids']['MVD'][target])


def test_assignment_refuses_short_magpie_test_contamination_and_duplicates():
    reg=banks(3);mag={k:queries(500,k) for k in reg}
    with pytest.raises(ValueError,match='mixture'):allocate_queries(reg,queries(20000),mag,queries(4,'val'),seed=1,forbidden=[])
    reg=banks()|{f'm{i}':{'kind':'mixture'} for i in range(20)};mag={k:queries(500,k) for k in reg}
    mag['b00']=mag['b00'][:5]
    with pytest.raises(ValueError,match='Magpie'):allocate_queries(reg,queries(20000),mag,queries(4,'val'),seed=1,forbidden=[])
    mag['b00']=queries(500,'b00')
    with pytest.raises(ValueError,match='overlap'):allocate_queries(reg,queries(20000),mag,queries(4,'val'),seed=1,forbidden=[queries(1)[0]])


def test_tail_matching_only_drops_suffixes_and_checks_real_seed_steps():
    def batch_check(lengths):
        if sum(lengths['FS'])==12:raise ValueError('optimizer steps differ')
        return {'optimizer_steps':1,'token_budget':sum(lengths['FS'])}
    lengths={'FS':[2,3,7],'MVD':[5,7],'PO-D':[2,3,7],'PO-T':[2,3,7]}
    r=match_tails(lengths,batch_check=batch_check)
    assert r['token_budget']==5 and r['kept']=={'FS':2,'PO-D':2,'PO-T':2,'MVD':1}
    assert r['dropped_indices']=={'FS':[2],'MVD':[1],'PO-D':[2],'PO-T':[2]}
    assert r['attempts'][0]['error']=='optimizer steps differ'
    with pytest.raises(ValueError,match='prefix'):match_tails({'FS':[2],'MVD':[3],'PO-D':[2],'PO-T':[2]},batch_check=batch_check)


def test_queue_jobs_keep_paths_as_argv_and_fresh_compile_without_launching(tmp_path):
    spec=dict(code_repo=str(tmp_path/'repo space'),python='/env/bin/python',base_id='base',base_revision='a'*40,seed=101)
    j=launcher_job(spec,'method-one','M2','/prompts space/p.jsonl',['-m','followspec.generate_responses','--output','/out path/new'])
    args=j['args']; cmd=args[args.index('--')+1:]
    assert cmd==['/env/bin/python','-u','-m','followspec.generate_responses','--output','/out path/new']
    assert 'VLLM_CACHE_ROOT={out_dir}/vllm_cache' in args and 'HF_HUB_OFFLINE=1' in args
    assert '--allow-branch' not in args and '--skip-preflight' not in args
    assert args[args.index('--config-name')+1]=='launcher.json'


def test_block_order_preserves_composition_and_parent_share_at_every_allowed_end():
    from followspec.production_assembly import balanced_order
    child=[dict(pair_id=f'p{i}',data_kind='magpie' if i%2==0 else 'general') for i in range(24)]
    parent=[dict(pair_id=f'b{i}',data_kind='general') for i in range(8)]
    ordered,dropped=balanced_order(child,parent,seed=10)
    assert not dropped
    assert ordered==balanced_order(child,parent,seed=10)[0]
    for end in range(8,len(ordered)+1,8):
        subset=ordered[:end];parents=[r for r in subset if r['data_role']=='parent']
        assert len(parents)*4==end
        counts=[sum(r['data_role']=='child' and r['data_kind']==kind for r in subset) for kind in ['magpie','general']]
        assert counts[0]==counts[1]


def test_readiness_requires_actual_mask_review_and_rejects_short_capacity_check(tmp_path):
    from followspec.production_assembly import readiness
    masks=tmp_path/'masks.jsonl';masks.write_text('{}\n')
    from atlas.run_cell import sha256
    proof=tmp_path/'features.json';proof.write_text(json.dumps(dict(passed=True)))
    evidence=dict(feature_acceptance=str(proof),feature_acceptance_sha256=sha256(proof),mask_review_sha256={'FS':sha256(masks)})
    r=readiness(evidence,{'FS':masks})
    assert r['data_ready'] and not r['training_capacity_verified']
    masks.write_text('{"changed":true}\n')
    assert not readiness(evidence,{'FS':masks})['data_ready']


def test_parent_prefix_stays_matched_when_arms_have_different_child_counts():
    from followspec.production_assembly import balanced_order
    child=[dict(pair_id=f'c{i}',data_kind='magpie' if i%2==0 else 'general') for i in range(24)]
    parents=[dict(pair_id=f'p{i}',data_kind='general') for i in range(8)]
    a,_=balanced_order(child,parents,seed=1)
    b,_=balanced_order(child[:12],parents[:4],seed=1)
    ap=[r['pair_id'] for r in a if r['data_role']=='parent']
    bp=[r['pair_id'] for r in b if r['data_role']=='parent']
    assert ap[:len(bp)]==bp
