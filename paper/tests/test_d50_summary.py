import numpy as np,pytest
from paper.d50_summary import raw_values,paired_summary,invalid_path

def test_counter_reconstruction_and_zero_step():
 r=dict(per_step_accepted=[0,2,1],per_step_drafted=[4,4,2],completion_token_ids=[1]*6,num_drafts=3,num_accepted_tokens=3,num_draft_tokens=10,acceptance_length=2.)
 v=raw_values(r,4);assert v[:3]==[2/3,2.,6]
 with pytest.raises(ValueError):raw_values(r|dict(per_step_accepted=[5,2,1]),4)
 z=r|dict(per_step_accepted=[],per_step_drafted=[],num_drafts=0,num_accepted_tokens=0,num_draft_tokens=0,acceptance_length=None)
 assert np.isnan(raw_values(z,4)[0])

def test_paired_seed_bootstrap_shared_noise_cancels():
 x=np.arange(12,dtype=float).reshape(1,4,3)+2;b=x[0]-1;o=b+4
 a=paired_summary(np.concatenate([x,x],axis=0),b,o,draws=200)
 assert a['delta']['p1']['ci95']==[1.,1.] and a['recovery']['ci95']==[.25,.25]
 assert a['seeds']==2 and a['n_paired']==4

def test_invalid_manifest_excludes_only_exact_affected_tree():
 bad=['/a/E1-official-t0-4k-fc']
 assert invalid_path('/a/E1-official-t0-4k-fc/export-1',bad)
 assert not invalid_path('/b/FIX24-official-t0-4k-fc',bad)
 assert not invalid_path('/a/E1-official-t0-4k-fc2',bad)

def test_pair_validation_rejects_render_and_target_mismatch():
    from paper.d50_summary import check_pair
    c=dict(engine_version='0.31.0',target='x',target_revision='a',batch_size=8,max_new_tokens=512,seed=0,temperature=0,dtype='bfloat16',max_model_len=4096,enable_prefix_caching=False)
    check_pair(c,c,{'a':[1,2]},{'a':[1,2]})
    import pytest
    with pytest.raises(ValueError,match='rendered'):
        check_pair(c,c,{'a':[1,2]},{'a':[1,3]})
    with pytest.raises(ValueError,match='target_revision'):
        check_pair(c,c|dict(target_revision='b'),{'a':[1,2]},{'a':[1,2]})
