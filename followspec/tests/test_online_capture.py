from contextlib import contextmanager
from types import SimpleNamespace
import pytest
import torch
from followspec.online_capture import OnlinePairCapture, route_arm


class Core(torch.nn.Module):
    def __init__(self, owner):
        super().__init__(); self.embed=torch.nn.Embedding(20,4)
        self.norm=torch.nn.LayerNorm(4)
        # No parent-module reference: this is a tiny target, not a recursive tree.
        object.__setattr__(self,'owner',owner)
    def forward(self,input_ids,output_hidden_states,use_cache):
        assert output_hidden_states and not use_cache
        x=self.embed(input_ids); y=x+self.owner.active*self.owner.delta
        z=y*torch.tensor([1.,2.,3.,4.]); last=self.norm(z)
        return SimpleNamespace(last_hidden_state=last,hidden_states=(x,y,last))


class Target(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.active=True; self.delta=.25
        self.model=Core(self); self.lm_head=torch.nn.Linear(4,20,bias=False)
        self.config=SimpleNamespace(num_hidden_layers=2,hidden_size=4,vocab_size=20)
    def get_base_model(self):return self
    @contextmanager
    def disable_adapter(self):
        old=self.active;self.active=False
        try:yield
        finally:self.active=old


def sample():return torch.tensor([1,2,3,4,5]),torch.tensor([False,False,True,True,True])


def test_online_pair_uses_identical_ids_pre_norm_labels_and_no_teacher_gradients():
    torch.manual_seed(1);model=Target();before={k:id(v) for k,v in model.named_parameters()}
    capture=OnlinePairCapture(model,[1],torch.tensor([2,5,8]),pause_check=lambda:None)
    ids,mask=sample();raw=capture(ids,mask)
    assert before=={k:id(v) for k,v in model.named_parameters()}
    assert all(not p.requires_grad for p in model.parameters()) and not model.training
    assert torch.equal(raw['input_ids'],ids) and torch.equal(raw['loss_mask'],mask)
    assert not torch.equal(raw['hidden_states'],raw['base_hidden_states'])
    assert raw['child_target_logits'].shape==(5,3)
    with torch.no_grad():
        expected=model.lm_head(model.model.norm(raw['verifier_last_hidden_states']))[:,[2,5,8]]
    torch.testing.assert_close(raw['child_target_logits'],expected,rtol=0,atol=0)
    # Normal tensors must support drafter backward; inference_mode tensors don't.
    head=torch.nn.Linear(4,1);head(raw['hidden_states']).sum().backward()
    assert head.weight.grad is not None
    assert all(p.grad is None for p in model.parameters())
    assert model.active and not model.model.norm._forward_pre_hooks


def test_zero_adapter_exact_base_and_base_route_is_exact():
    model=Target();model.delta=0
    capture=OnlinePairCapture(model,[1],torch.tensor([2,5,8]),pause_check=lambda:None)
    ids,mask=sample();raw=capture(ids,mask)
    for key in ['hidden_states','verifier_last_hidden_states']:
        assert torch.equal(raw[key],raw['base_'+key])
    assert torch.equal(raw['child_target_logits'],raw['base_target_logits'])
    model.delta=.25;base=capture(ids,mask,feature_target='base')
    assert torch.equal(base['hidden_states'],base['base_hidden_states'])
    assert model.active


def test_masks_pauses_and_cleanup_fail_closed():
    model=Target();calls=[]
    def pause():
        calls.append(1)
        if len(calls)==2:raise RuntimeError('paused')
    capture=OnlinePairCapture(model,[1],torch.tensor([2,5,8]),pause_check=pause)
    ids,mask=sample()
    with pytest.raises(RuntimeError,match='paused'):capture(ids,mask)
    assert model.active and not model.model.norm._forward_pre_hooks
    capture.pause_check=lambda:None
    with pytest.raises(ValueError,match='assistant'):capture(ids,torch.tensor([False,True,False,True,True]))
    with pytest.raises(ValueError):capture(ids,mask.float())
    with pytest.raises(ValueError):OnlinePairCapture(model,[2],torch.tensor([1]),pause_check=lambda:None)
    def fail(*args,**kwargs):raise RuntimeError('forward failed')
    model.model.forward=fail
    with pytest.raises(RuntimeError,match='forward failed'):capture(ids,mask)
    assert model.active and not model.model.norm._forward_pre_hooks


def test_arm_routing_never_substitutes_generated_response_source():
    assert route_arm('FS','child','child')=='child'
    assert route_arm('MVD','child','child')=='child'
    assert route_arm('PO-T','child','child')=='base'
    assert route_arm('PO-D','base','child')=='base'
    assert route_arm('FS','base','base')=='base'
    with pytest.raises(ValueError):route_arm('PO-D','child','child')
    with pytest.raises(ValueError):route_arm('FS','base','child')
    with pytest.raises(ValueError):route_arm('FS','test-child','child')
