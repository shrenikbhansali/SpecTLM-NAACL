import numpy as np
import pytest
from paper.d51_repair_delta import delta_comparison, check_training, choose_primary


def test_delta_not_absolute_and_pairing_cancels_noise():
    q=np.arange(9).reshape(3,3)/20
    prod=np.stack([q+2,q+3,q+4]);official=prod-1
    r=delta_comparison(official,q-2,prod,q,draws=200)
    assert r['difference']['tau']['mean']==pytest.approx(1)
    assert r['difference']['tau']['ci95']==pytest.approx([1,1])
    assert r['official']['metrics']['tau']['mean']<r['production']['metrics']['tau']['mean']


def test_shared_zero_step_mask_and_shape_guard():
    a=np.ones((3,4,3))*3;b=np.ones((4,3));a[2,0,0]=np.nan
    c=np.ones((3,4,3))*2;d=b.copy();d[1,1]=np.nan
    r=delta_comparison(a,b,c,d,draws=100)
    assert r['n_total']==4 and r['n_paired']==2
    with pytest.raises(ValueError):delta_comparison(a,b,c[:2],d)


def test_matched_training_rejects_data_steps_and_seed():
    c=dict(data_sha256='a',steps=12,seed=1,n=100,token_budget=123,variant='fc',lr=2e-5,batch_tokens=2048,ttt_steps=3,algorithm='eagle3',one_epoch=True,batch_plan=[[1],[2]],schedule_horizon=12,target={'id':'x','revision':'r'})
    check_training(c,c)
    for k,v in [('data_sha256','b'),('steps',13),('seed',2),('batch_plan',[[2],[1]])]:
        with pytest.raises(ValueError,match=k):check_training(c,c|{k:v})


def test_selection_waits_for_complete_panel_and_reports_conflict():
    def record(arm,w,d):return dict(target=0,budget=16000,arm=arm,workload=w,seeds=[0,1,2],difference={'tau':{'mean':d,'ci95':[-.1,.3]}})
    rr=[record(a,w,.1) for a in ['fc','full'] for w in ['speed128','math64']]
    assert choose_primary(rr)['status']=='selected'
    assert choose_primary(rr)['primary']=='official'
    assert choose_primary(rr[:-1])['status']=='pending'
    rr[0]['difference']['tau']['mean']=-.1
    assert choose_primary(rr)['status']=='mixed_variant_directions'
