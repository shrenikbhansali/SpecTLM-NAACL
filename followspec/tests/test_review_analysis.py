import pytest
from followspec.review_analysis import counter_metrics, repeated_coverage, paired


def test_raw_macro_and_conditional_counts():
    r=dict(per_step_accepted=[0,1,4],per_step_drafted=[4,4,4],completion_token_ids=list(range(9)))
    m=counter_metrics(r)
    assert m['p1']==2/3 and m['tau']==pytest.approx(8/3)
    assert m['conditional']==[2/3,1/2,1.,1.]
    assert counter_metrics(dict(per_step_accepted=[],per_step_drafted=[],completion_token_ids=[1]))['p1'] is None
    with pytest.raises(ValueError):counter_metrics(r|dict(per_step_drafted=[1,1,1]))


def test_repeat_coverage_and_pairwise_exclusion():
    assert repeated_coverage(list(range(20)))==0
    assert repeated_coverage([1,2,3,4]*8)==1
    a={'a':1.,'b':None,'c':3.};b={'a':2.,'b':2.,'c':4.}
    assert paired(a,b)['mean']==1.
    assert paired(a,b)['n']==2
    assert paired(a,b)['ci95']==[1.,1.]
