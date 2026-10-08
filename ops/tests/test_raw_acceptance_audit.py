import pytest
from ops.raw_acceptance_audit import prompt_metrics, paired, bootstrap_median


def row(accepted, drafted, k=2):
    return dict(prompt_id='p',per_step_accepted=accepted,per_step_drafted=drafted,
                acceptance_length=1+sum(accepted)/len(accepted) if accepted else None,
                completion_token_ids=[1,2,3])


def test_raw_counters_rederive_bonus_macro_and_conditional():
    r=prompt_metrics(row([0,1,2],[1,1,2]),2)
    assert r['tau']==2 and r['conditional']==pytest.approx([2/3,1])
    broken=row([0,1,2],[1,1,2]);broken['acceptance_length']=1
    with pytest.raises(ValueError,match='acceptance'):prompt_metrics(broken,2)


def test_pairwise_zero_step_and_zero_denominator_are_explicit():
    a={'p':prompt_metrics(row([0],[2]),2),'z':prompt_metrics(row([],[]),2)}
    b={'p':prompt_metrics(row([1],[2]),2),'z':prompt_metrics(row([2],[2]),2)}
    r=paired(a,b)
    assert r['n_tau']==1 and r['tau_retention']==2 and r['position_retention'][0] is None
    assert r['n_total']==2 and r['position_n']==[1,0]


def test_bootstrap_retains_negative_gains():
    lo,hi=bootstrap_median([-3,-2,-1])
    assert lo<0 and hi<0
