"""EDA released-code one/shared one/private expert port for the native EAGLE-3 MLP.

Reference: Lyn-Lucy/Efficient-Draft-Adaptation, a29f0381479a92d0f3114fd264cd790bab3a208b,
eda/model/cnets_eda.py:393-510. The two independent one-expert softmax gates
are identically one (not a joint two-expert gate). Fresh private weights use
nn.Linear's initialization, as in the release. No serving-engine modification.
"""
import torch
from torch import nn
from torch.nn import functional as F


class SwiGLU(nn.Module):
    def __init__(self,hidden,width,device=None,dtype=None):
        super().__init__()
        self.gate_proj=nn.Linear(hidden,width,bias=False,device=device,dtype=dtype)
        self.up_proj=nn.Linear(hidden,width,bias=False,device=device,dtype=dtype)
        self.down_proj=nn.Linear(width,hidden,bias=False,device=device,dtype=dtype)
    def forward(self,x):return self.down_proj(F.silu(self.gate_proj(x))*self.up_proj(x))


class SharedPrivateMLP(nn.Module):
    def __init__(self,shared,private_width):
        super().__init__()
        if private_width<1:raise ValueError('positive private width required')
        weight=shared.gate_proj.weight;hidden=weight.shape[1]
        if any(getattr(shared,k).bias is not None for k in ['gate_proj','up_proj','down_proj']):
            raise ValueError('EDA port supports the released bias-free SwiGLU only')
        self.shared_gate=nn.Linear(hidden,1,bias=False,device=weight.device,dtype=weight.dtype)
        self.private_gate=nn.Linear(hidden,1,bias=False,device=weight.device,dtype=weight.dtype)
        self.shared=shared.requires_grad_(False)
        self.private=SwiGLU(hidden,private_width,device=weight.device,dtype=weight.dtype)

    def forward(self,x):
        # Match released-code semantics explicitly, retaining the zero-gradient routers.
        sg=F.softmax(self.shared_gate(x).float(),dim=-1).to(x.dtype)
        pg=F.softmax(self.private_gate(x).float(),dim=-1).to(x.dtype)
        return sg*self.shared(x)+pg*self.private(x)


def folded_weights(model):
    return {name:torch.cat([getattr(model.shared,name).weight,getattr(model.private,name).weight],
                          dim=1 if name=='down_proj' else 0)
            for name in ['gate_proj','up_proj','down_proj']}


def fold_mlp(model):
    weights=folded_weights(model);gate=weights['gate_proj']
    result=SwiGLU(gate.shape[1],gate.shape[0],device=gate.device,dtype=gate.dtype)
    with torch.no_grad():
        for name,weight in weights.items():getattr(result,name).weight.copy_(weight)
    return result


def install_eda(model,private_width):
    model.requires_grad_(False)
    if len(model.layers)!=1:raise ValueError('matched EDA port requires the one-layer family drafter')
    model.layers[0].mlp=SharedPrivateMLP(model.layers[0].mlp,private_width)
    names=[n for n,p in model.named_parameters() if p.requires_grad]
    count=sum(p.numel() for p in model.parameters() if p.requires_grad)
    return dict(variant='eda_private',private_width=private_width,trainable_names=names,
                trainable_parameters=count,added_parameters=count,
                frozen_parameters=sum(p.numel() for p in model.parameters() if not p.requires_grad),
                routing='released code: independent singleton softmax gates; router gradients identically zero',
                export='concatenated SwiGLU columns/rows; mathematically equivalent sum, enlarged intermediate_size')
