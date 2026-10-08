import numpy as np
import pytest
import torch
from atlas.crossover import effects, paired_summary, swap_tap, token_diagnostics


def test_factorial_effects_known_cases():
    # Rows feature parent/child; columns verifier parent/child.
    assert effects([[.8,.8],[.5,.5]])==pytest.approx(dict(feature=-.3,policy=0.,interaction=0.))
    assert effects([[.8,.5],[.8,.5]])==pytest.approx(dict(feature=0.,policy=-.3,interaction=0.))
    assert effects([[.8,.5],[.5,.8]])==pytest.approx(dict(feature=0.,policy=0.,interaction=.6))


def test_paired_summary_keeps_all_four_cells_on_same_resampled_prefixes():
    rows=np.array([[[.9,.7],[.6,.4]],[[.6,.4],[.3,.1]],[[.75,.55],[.45,.25]]])
    s=paired_summary(rows,seed=0,n_boot=100)
    assert s['n']==3
    assert s['feature']['mean']==pytest.approx(-.3)
    assert s['feature']['ci95']==pytest.approx([-.3,-.3])
    assert s['interaction']['ci95']==pytest.approx([0,0],abs=1e-12)


def test_layer_swap_changes_exactly_one_tap_and_not_inputs():
    a=torch.zeros(4,12);b=torch.ones(4,12)
    s=swap_tap(a,b,1,3)
    assert torch.equal(s[:,4:8],b[:,4:8]) and not s[:,:4].any() and not s[:,8:].any()
    assert not a.any()
    with pytest.raises(ValueError):swap_tap(a,b,3,3)


def test_full_vocab_oov_is_greedy_ceiling_not_renormalized_prediction():
    logits=torch.tensor([[1.,2.,8.,0.],[3.,1.,0.,2.]])
    d=token_diagnostics(logits,torch.tensor([0,1]))
    assert d['top1'].tolist()==[2,0]
    assert d['oov'].tolist()==[True,False]
    assert d['logit_margin'].tolist()==[6.,1.]
    assert torch.all(d['prob_margin']>0)
