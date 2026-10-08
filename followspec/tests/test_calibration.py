import pytest
import torch
from followspec.calibration import TapMoments, calibration_parameters, transform, fold_rms


def test_streaming_moments_and_affine_recover_known_layer_shift():
    torch.manual_seed(7)
    parent=torch.randn(20,12,dtype=torch.float64)
    scale=torch.tensor([2.,3.,4.]).repeat_interleave(4)
    offset=torch.tensor([1.,-2.,.5]).repeat_interleave(4)
    child=(parent-offset)/scale
    p,c=TapMoments(3),TapMoments(3)
    for a,b in zip(parent.split(3),child.split(3)):p.add(a);c.add(b)
    fitted=calibration_parameters(p,c)
    torch.testing.assert_close(transform(child,fitted,'affine'),parent)
    assert p.n==80 # scalar observations per layer
    assert fitted['n_tokens']==20


def test_rms_folding_is_exact_and_has_no_bias_or_offset():
    torch.manual_seed(2);x=torch.randn(8,12,dtype=torch.float64);w=torch.randn(3,12,dtype=torch.float64)
    p,c=TapMoments(3),TapMoments(3);p.add(x*2+1);c.add(x)
    fitted=calibration_parameters(p,c)
    torch.testing.assert_close(transform(x,fitted,'rms')@w.T,x@fold_rms(w,fitted).T)
    assert torch.equal(transform(torch.zeros_like(x),fitted,'rms'),torch.zeros_like(x))
    with pytest.raises(ValueError):fold_rms(torch.randn(3,11),fitted)


def test_zero_rms_fails_instead_of_silent_clipping():
    p,c=TapMoments(2),TapMoments(2);p.add(torch.ones(4,6));c.add(torch.zeros(4,6))
    with pytest.raises(ValueError):calibration_parameters(p,c)
