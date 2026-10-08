import math
import pytest
import torch
from atlas.context_kl import compare_distributions


def test_identical_logits_zero_kl():
    logits=torch.tensor([[2.,-1.,.5],[1.,.2,-3.]])
    r=compare_distributions(logits,logits,torch.ones(3,dtype=torch.bool))
    assert r['kl_child_base']==pytest.approx(0.,abs=1e-7)
    assert r['child_extra_vocab_mass']==0 and r['support']=='identical'


def test_direction_child_to_base_and_additive_invariance():
    b=torch.tensor([[.6,.3,.1]]).log();c=torch.tensor([[.1,.2,.7]]).log()
    expected=sum(p*math.log(p/q) for p,q in zip([.1,.2,.7],[.6,.3,.1]))
    r=compare_distributions(b+23,c-7,torch.ones(3,dtype=torch.bool))
    assert r['kl_child_base']==pytest.approx(expected,abs=1e-6)


def test_added_child_vocab_not_silently_renormalized():
    b=torch.tensor([[.5,.5]]).log();c=torch.tensor([[.25,.25,.5]]).log()
    r=compare_distributions(b,c,torch.ones(2,dtype=torch.bool))
    assert r['kl_child_base'] is None
    assert r['full_kl_infinite_under_zero_extension'] is True
    assert r['conditional_common_vocab_kl']==pytest.approx(0,abs=1e-7)
    assert r['child_extra_vocab_mass']==pytest.approx(.5)


def test_smaller_child_vocab_requires_separate_policy():
    with pytest.raises(ValueError):compare_distributions(torch.ones(1,3),torch.ones(1,2),torch.ones(3,dtype=torch.bool))
