"""Top-k-normalized centered delta loss (owner decision 2026-10-05).

Inputs are log probabilities or logits on the SAME selected child top-k tokens.
Per-prefix log normalizers cancel after centering, so logits avoid full-vocabulary
log-softmax allocations. Teachers and the base-feature delta branch are detached.
The separate native base anchor loss keeps its ordinary gradient.
"""
import math
import torch


def centered_delta(q_child,q_base,p_child,p_base,mask=None):
    values=(q_child,q_base,p_child,p_base)
    if q_child.ndim<2 or q_child.shape[-1]==0 or any(v.shape!=q_child.shape for v in values):
        raise ValueError('aligned nonempty top-k tensors required')
    if not all(torch.isfinite(v).all() for v in values):raise ValueError('nonfinite delta input')
    dtype=torch.float64 if q_child.dtype==torch.float64 else torch.float32
    qc=q_child.to(dtype);q0=q_base.detach().to(dtype)
    pc=p_child.detach().to(dtype);p0=p_base.detach().to(dtype)
    weights=torch.softmax(pc,dim=-1)
    d=qc-q0-(pc-p0)
    centered=d-(weights*d).sum(-1,keepdim=True)
    variance=(weights*centered.square()).sum(-1)
    if mask is None:return variance.mean()
    if mask.shape!=variance.shape or mask.dtype!=torch.bool:raise ValueError('boolean aligned assistant mask required')
    return (variance*mask).sum()/mask.sum().clamp_min(1)


def objective(child_native,base_native,delta,*,beta,delta_lambda):
    if not all(math.isfinite(v) and v>=0 for v in (beta,delta_lambda)):
        raise ValueError('nonnegative finite loss coefficients required')
    loss=child_native+beta*base_native if beta else child_native
    if delta_lambda:
        if delta is None:raise ValueError('delta term required')
        loss=loss+delta_lambda*delta
    return loss
