"""Pure tensor acceptance checks; no model generation or optimizer steps."""
import pytest
import torch
from followspec.delta import centered_delta, objective


def values():
    g=torch.Generator().manual_seed(42)
    return [torch.randn(2,5,4,generator=g,dtype=torch.float64,requires_grad=True) for _ in range(4)]


def test_exact_tracking_has_zero_delta():
    qc,q0,pc,p0=values();qc=q0+(pc-p0)
    assert centered_delta(qc,q0,pc,p0).item()<1e-28


@pytest.mark.parametrize('which',range(4))
def test_invariant_to_independent_per_prefix_constants(which):
    v=values();original=centered_delta(*v)
    constant=torch.arange(10,dtype=torch.float64).reshape(2,5,1)/3
    v[which]=v[which]+constant
    torch.testing.assert_close(centered_delta(*v),original,atol=1e-12,rtol=1e-12)


def test_detached_base_and_teachers_but_nonzero_child_gradient():
    qc,q0,pc,p0=values();loss=centered_delta(qc,q0,pc,p0);loss.backward()
    assert qc.grad.abs().sum()>0
    assert q0.grad is None and pc.grad is None and p0.grad is None


def test_selected_child_weights_are_normalized_and_masked():
    qc,q0,pc,p0=values();mask=torch.tensor([[True,False,True,False,True],[False]*5])
    w=pc.detach().softmax(-1);d=qc-q0.detach()-pc.detach()+p0.detach()
    variance=(w*(d-(w*d).sum(-1,keepdim=True)).square()).sum(-1)
    torch.testing.assert_close(centered_delta(qc,q0,pc,p0,mask),variance[mask].mean())
    empty=centered_delta(qc,q0,pc,p0,torch.zeros_like(mask));empty.backward()
    assert empty==0 and qc.grad.abs().sum()==0


def test_lambda_zero_keeps_stock_losses_exactly_and_anchor_gradient():
    child=torch.tensor(.317,requires_grad=True);base=torch.tensor(.823,requires_grad=True)
    loss=objective(child,base,torch.tensor(float('nan')),beta=1.,delta_lambda=0.)
    torch.testing.assert_close(loss,child+base,atol=1e-6,rtol=0)
    loss.backward();assert child.grad==1 and base.grad==1
    torch.testing.assert_close(objective(child,base,None,beta=0.,delta_lambda=0.),child,atol=1e-6,rtol=0)
