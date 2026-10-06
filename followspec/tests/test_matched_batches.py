import pytest
from followspec.matched_batches import subdivide_batches, StepMatchedSampler, inspect_matched_batches


def test_subdivision_preserves_order_coverage_tokens_and_capacity():
    original=[[2,0,1],[3,4]];lengths=[3,4,2,6,1]
    batches,events=subdivide_batches(original,lengths,4,9)
    assert len(batches)==4 and len(events)==2 and original==[[2,0,1],[3,4]]
    assert [i for b in batches for i in b]==[2,0,1,3,4]
    assert all(b and sum(lengths[i] for i in b)<=9 for b in batches)
    assert (batches,events)==subdivide_batches(original,lengths,4,9)
    assert subdivide_batches(original,lengths,2,9)==(original,[])


@pytest.mark.parametrize('batches,lengths,target,cap',[
    ([[0],[1]],[3,4],1,8), ([[0],[1]],[3,4],3,8),
    ([[0,0],[1]],[3,4],2,8), ([[0]],[3,4],1,8),
    ([[0,1]],[3,6],2,8), ([[],[0,1]],[3,4],2,8),
])
def test_impossible_or_invalid_batches_fail(batches,lengths,target,cap):
    with pytest.raises(ValueError):subdivide_batches(batches,lengths,target,cap)


class Native:
    def __init__(self,**kw):self.kw=kw;self.epoch=0
    def set_epoch(self,epoch):self.epoch=epoch
    def __iter__(self):
        return iter([[1],[0]] if self.kw['lengths'][0]==5 or self.kw['seed']==1 else [[0,1]])


def test_wrapper_matches_audit_and_seed_epoch_order():
    lengths={a:[3,4] for a in ['FS','MVD','PO-D','PO-T']};lengths['MVD']=[5,2]
    r=inspect_matched_batches(lengths,factory=Native,batch_max_length=8,seeds=[0,1],epochs=1,replicas=1)
    assert r['optimizer_steps']==2 and r['token_budget']==7
    assert set(r['native_step_counts'].values())=={1,2}
    assert len(r['subdivision_events'])==3
    for arm,values in lengths.items():
        for seed in [0,1]:
            sampler=StepMatchedSampler(factory=Native,target_steps=2,batch_max_length=8,lengths=values,num_replicas=1,rank=0,seed=seed)
            sampler.set_epoch(0);assert len(sampler)==2
            assert list(sampler)==[b['sample_indices'] for b in r['batches'] if b['arm']==arm and b['seed']==seed]


def test_unsupported_multi_epoch_or_distributed_policy_fails():
    lengths={a:[3,4] for a in ['FS','MVD','PO-D','PO-T']}
    for epochs,replicas in [(2,1),(1,2)]:
        with pytest.raises(ValueError,match='one epoch.*one replica'):
            inspect_matched_batches(lengths,factory=Native,batch_max_length=8,seeds=[0],epochs=epochs,replicas=replicas)


def test_policy_requires_explicit_research_approval_before_finalize(tmp_path,monkeypatch):
    from followspec.tests.test_production_integration import fixture,mock_runtime,Sampler
    from followspec.production_assembly import assemble,finalize
    from followspec.production_pipeline import read,write_new
    from followspec.train_eagle3 import resolve_plan
    from atlas.run_cell import sha256
    plan=fixture(tmp_path);mock_runtime(monkeypatch)
    monkeypatch.setattr('followspec.production_assembly.native_auditor',lambda lengths,**kw:inspect_matched_batches(lengths,factory=Sampler,batch_max_length=8192,seeds=[0,1,2],epochs=1,replicas=1))
    out=assemble(plan,tmp_path/'assembled',batch_step_policy='native_split_max_v1')
    proof=tmp_path/'proof.json';write_new(proof,dict(passed=True,total_seq_len=8192,full_response=True,optimizer_steps=1))
    evidence=dict(feature_acceptance=str(proof),feature_acceptance_sha256=sha256(proof),capacity_acceptance=str(proof),capacity_acceptance_sha256=sha256(proof),mask_review_sha256={a:sha256(out/a/'decoded_masks.jsonl') for a in ['FS','MVD','PO-D','PO-T']})
    e=tmp_path/'evidence.json';write_new(e,evidence)
    missing=finalize(out,e,tmp_path/'unapproved');assert not read(missing/'results.json')['production_ready']
    assert any('owner decision' in x for x in read(missing/'results.json')['blockers'])
    approval=dict(policy='native_split_max_v1',decision_id='D-TEST',approved=True)
    evidence['batch_step_policy_approval']=approval;e2=tmp_path/'approved_evidence.json';write_new(e2,evidence)
    approved=finalize(out,e2,tmp_path/'approved');assert read(approved/'results.json')['production_ready']
    for arm in ['FS','MVD','PO-D','PO-T']:
        config=read(approved/arm/'training_config.json');manifest=read(approved/arm/'manifest.json')
        assert config['batch_step_policy']==manifest['batch_step_policy']=='native_split_max_v1'
        assert config['batch_step_policy_approval']==approval
        resolve_plan(config,manifest,0)
        manifest['batch_step_policy_approval']={}
        with pytest.raises(ValueError,match='batch.*approval'):resolve_plan(config,manifest,0)
