"""Activation offload that retains compiled backward's exact view layout.

The pinned torch save_on_cpu(pin_memory=True) packs into a contiguous tensor.
That changes padded/transposed strides expected by compiled backward kernels.
Store the view's storage span instead; no loss or optimizer arithmetic changes.
"""
import math
import torch


def pack_tensor(tensor):
    if tensor.layout!=torch.strided:raise ValueError('Only dense strided activations are supported')
    shape=tuple(tensor.shape);stride=tuple(tensor.stride());offset=tensor.storage_offset()
    span=offset+1+sum((n-1)*s for n,s in zip(shape,stride)) if tensor.numel() else offset
    storage=torch.zeros(span,dtype=tensor.dtype,device='cpu',pin_memory=tensor.device.type=='cuda')
    # Collapse broadcast axes so copy_ has no zero-stride write aliases.
    reduced=tuple(1 if s==0 and n>1 else n for n,s in zip(shape,stride))
    source=tensor.detach()
    for axis,(n,s) in enumerate(zip(shape,stride)):
        if s==0 and n>1:source=source.narrow(axis,0,1)
    view=storage.as_strided(reduced,stride,offset)
    view.copy_(source,non_blocking=False)
    return tensor.device,shape,stride,offset,storage


def unpack_tensor(packed):
    device,shape,stride,offset,storage=packed
    return storage.to(device=device,non_blocking=True).as_strided(shape,stride,offset)


def stride_preserving_offload():
    return torch.autograd.graph.saved_tensors_hooks(pack_tensor,unpack_tensor)
