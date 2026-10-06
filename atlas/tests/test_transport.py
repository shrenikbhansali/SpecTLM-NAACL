import numpy as np
import pytest
from atlas.transport import score_distribution, score_grid, validate_diagonals


def test_top1_overlap_forward_kl_and_mask_are_exact():
    p=np.array([[.8,.2],[.3,.7],[.5,.5]]);q=np.array([[.6,.4],[.8,.2],[.5,.5]])
    r=score_distribution(np.log(p),np.log(q),[True,True,False])
    assert r['n']==2 and r['top1_agreement']==.5
    assert r['overlap']==pytest.approx((.8+.5)/2)
    assert r['forward_kl']==pytest.approx(np.sum(p[:2]*np.log(p[:2]/q[:2]),axis=1).mean())


def test_zero_draft_support_yields_explicit_infinite_kl_without_epsilon():
    r=score_distribution(np.log([[.5,.5]]),np.array([[0.,-np.inf]]),[True])
    assert r['overlap']==.5 and r['forward_kl'] is None and r['forward_kl_infinite']
    assert r['infinite_kl_positions']==1


def test_identical_and_masked_cells_carry_diagnostic_labels_at_every_depth_and_head():
    lp=np.log(np.array([[[.5,.5],[.75,.25]],[[.5,.5],[.75,.25]]]))
    cells=score_grid({'base':lp,'child':lp},{'base':{'base':lp,'child':lp},'child':{'base':lp,'child':lp}},np.ones((2,2),dtype=bool))
    assert len(cells)==16 and all(r['diagnostic'] and r['overlap']==1 and r['forward_kl']==0 for r in cells)
    assert {r['head'] for r in cells}=={'base','child'}


def test_validation_requires_ten_derivatives_and_detects_sign_failure():
    records=[dict(derivative_id=str(i),offline_A00=.5+i/100,offline_A10=.4+i/100,A00=3+i/10,A10=2+i/10) for i in range(10)]
    r=validate_diagonals(records)
    assert r['passed'] and r['n_derivatives']==10 and r['sign_agreement']==1
    with pytest.raises(ValueError):validate_diagonals(records[:9])
    bad=[r|dict(offline_A10=r['offline_A00']+.1) for r in records]
    assert not validate_diagonals(bad)['passed']
    with pytest.raises(ValueError):validate_diagonals(records+[records[0]])


def test_owner_decomposition_exact_identity_and_zero_denominator():
    from atlas.transport import decompose
    r=decompose(.8,.6,.5)
    assert r['label_shift']==pytest.approx(-.2)
    assert r['transport']==pytest.approx(-.1)
    assert r['R']==pytest.approx(-.5)
    assert r['total_shift']==pytest.approx(r['label_shift']+r['transport'])
    assert r['diagnostic'] and r['R_defined']
    zero=decompose(.5,.5,.4)
    assert zero['R'] is None and not zero['R_defined']
    assert zero['undefined_reason']=='zero denominator'
    infinite=decompose(None,None,None)
    assert infinite['R'] is None and infinite['undefined_reason']=='nonfinite cell'
    with pytest.raises(ValueError):decompose(float('nan'),.4,.5)


def test_prompt_cells_pool_by_scored_tokens_and_keep_infinite_kl_explicit():
    from atlas.capture_transport import aggregate_cells
    row=dict(feature_source='base',label_source='child',head='frozen_drafter',unroll_position=0,n=1,top1_agreement=1.,overlap=.8,forward_kl=.1,forward_kl_infinite=False,infinite_kl_positions=0,diagnostic=True)
    r=aggregate_cells([row,row|dict(n=3,top1_agreement=0.,overlap=.4,forward_kl=None,forward_kl_infinite=True,infinite_kl_positions=1)])[0]
    assert r['n']==4 and r['n_prompts']==2
    assert r['top1_agreement']==.25 and r['overlap']==pytest.approx(.5)
    assert r['forward_kl'] is None and r['forward_kl_infinite'] and r['infinite_kl_positions']==1
    with pytest.raises(ValueError):aggregate_cells([row|dict(diagnostic=False)])
