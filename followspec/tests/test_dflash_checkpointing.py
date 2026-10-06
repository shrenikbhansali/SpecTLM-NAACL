import copy
from functools import partial
from types import SimpleNamespace as NS
import pytest
import torch
from torch.utils.checkpoint import checkpoint
from followspec.training_memory import checkpoint_dflash_layers


class KeywordModel(torch.nn.Module):
    supports_gradient_checkpointing=True
    def __init__(self):
        super().__init__();self.weight=torch.nn.Parameter(torch.randn(4,4))
        self.config=NS(speculators_config=NS(algorithm='dflash'));self.options=None
    def gradient_checkpointing_enable(self,gradient_checkpointing_kwargs=None):
        self.options=gradient_checkpointing_kwargs or {'use_reentrant':True}
    def forward(self,*,hidden_states,target_hidden):
        operation=lambda: ((hidden_states@self.weight).sin()+target_hidden@self.weight).square()
        return operation() if self.options is None else checkpoint(operation,**self.options)


def test_keyword_only_inputs_and_parameters_keep_exact_gradients():
    torch.manual_seed(22);a=KeywordModel();b=copy.deepcopy(a);checkpoint_dflash_layers(b)
    x=torch.randn(3,4,requires_grad=True);y=torch.randn(3,4,requires_grad=True)
    xx=x.detach().clone().requires_grad_();yy=y.detach().clone().requires_grad_()
    first=a(hidden_states=x,target_hidden=y).sum();second=b(hidden_states=xx,target_hidden=yy).sum()
    first.backward();second.backward()
    assert torch.equal(first,second) and torch.equal(x.grad,xx.grad) and torch.equal(y.grad,yy.grad)
    assert torch.equal(a.weight.grad,b.weight.grad)


def test_checkpointing_refuses_eagle_cache_and_unsupported_backend():
    a=KeywordModel();a.config.speculators_config.algorithm='eagle3'
    with pytest.raises(ValueError,match='DFlash'):checkpoint_dflash_layers(a)
    a.config.speculators_config.algorithm='dflash';a.supports_gradient_checkpointing=False
    with pytest.raises(ValueError,match='support'):checkpoint_dflash_layers(a)
