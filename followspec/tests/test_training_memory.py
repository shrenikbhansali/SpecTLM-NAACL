import copy
import torch
from followspec.training_memory import release_grad_before_forward


def test_native_step_order_matches_losses_gradients_weights_and_optimizer_state():
    torch.manual_seed(3)
    reference=torch.nn.Linear(7,3)
    early=copy.deepcopy(reference)
    optimizers=[torch.optim.AdamW(m.parameters(),lr=.01) for m in (reference,early)]
    class Trainer:
        model=early
        def _optimizers_zero_grad(self): optimizers[1].zero_grad()
    handle=release_grad_before_forward(Trainer())
    observed=[]
    early.register_forward_pre_hook(lambda m,_:observed.append(all(p.grad is None for p in m.parameters())))
    for _ in range(3):
        x=torch.randn(5,7);y=torch.randn(5,3)
        losses=[]
        for m,o in zip((reference,early),optimizers):
            loss=(m(x)-y).square().mean();losses.append(loss.detach())
            o.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1.);o.step()
        assert torch.equal(*losses)
        for p,q in zip(reference.parameters(),early.parameters()):
            assert torch.equal(p,q) and torch.equal(p.grad,q.grad)
        for p,q in zip(optimizers[0].state.values(),optimizers[1].state.values()):
            for key in p: assert torch.equal(p[key],q[key])
    assert observed==[True]*3
    handle.remove()


def test_eval_or_no_grad_probe_keeps_last_training_gradients():
    model=torch.nn.Linear(2,1);model(torch.ones(1,2)).sum().backward()
    saved=[p.grad.clone() for p in model.parameters()]
    class Trainer:
        def __init__(self): self.model=model
        def _optimizers_zero_grad(self): model.zero_grad(set_to_none=True)
    handle=release_grad_before_forward(Trainer())
    model.eval();model(torch.ones(1,2))
    model.train()
    with torch.no_grad(): model(torch.ones(1,2))
    assert all(torch.equal(p.grad,g) for p,g in zip(model.parameters(),saved))
    handle.remove()


def test_saved_tensor_offload_preserves_multistep_loss_gradients_and_adam_state():
    from followspec.training_memory import saved_tensor_context
    torch.manual_seed(7)
    original=torch.nn.Sequential(torch.nn.Linear(4,8),torch.nn.GELU(),torch.nn.Linear(8,2))
    copy_model=copy.deepcopy(original)
    opts=[torch.optim.AdamW(m.parameters(),lr=.001) for m in (original,copy_model)]
    for _ in range(3):
        x=torch.randn(7,4);losses=[]
        for flag,model,opt in zip((False,True),(original,copy_model),opts):
            opt.zero_grad()
            with saved_tensor_context(flag):loss=model(x).square().sum()
            loss.backward();losses.append(loss.detach());opt.step()
        assert torch.equal(*losses)
        for p,q in zip(original.parameters(),copy_model.parameters()):
            assert torch.equal(p,q) and torch.equal(p.grad,q.grad)
        for p,q in zip(opts[0].state.values(),opts[1].state.values()):
            for key in p:assert torch.equal(p[key],q[key])


def test_serial_adamw_matches_batched_updates_and_states():
    from followspec.training_memory import serial_adamw
    from types import SimpleNamespace
    torch.manual_seed(33)
    params=[torch.nn.Parameter(torch.randn(n,n)) for n in (5,9,17)]
    others=[torch.nn.Parameter(p.detach().clone()) for p in params]
    a=torch.optim.AdamW(params,lr=.003,weight_decay=.02,foreach=True)
    b=torch.optim.AdamW(others,lr=.003,weight_decay=.02,foreach=True)
    serial_adamw(SimpleNamespace(optimizers=[b]))
    for _ in range(3):
        for p,q in zip(params,others):p.grad=torch.randn_like(p);q.grad=p.grad.clone()
        a.step();b.step()
        for p,q in zip(params,others):
            assert torch.equal(p,q)
            for k in a.state[p]:assert torch.equal(a.state[p][k],b.state[q][k])
