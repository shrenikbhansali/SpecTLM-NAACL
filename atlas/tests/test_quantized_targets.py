import torch
import pytest
from atlas.quantized_targets import unpack_awq, unpack_gptq_symmetric


def pack_last(values,order):
    result=torch.zeros(values.shape[:-1],dtype=torch.int64)
    for i,shift in enumerate(order):result|=values[...,i].long()<<(shift*4)
    return result.to(torch.int32)


def test_awq_inverse_permutation_group_scales_and_asymmetric_zero_points():
    # Independent known unsigned nibbles; native AWQ permutation differs from GPTQ.
    order=[0,4,1,5,2,6,3,7]
    values=torch.arange(32).reshape(4,8)%16
    zeros=torch.tensor([[1,2,3,4,5,6,7,8],[8,7,6,5,4,3,2,1]])
    scales=torch.arange(1,17).reshape(2,8).float()/16
    got=unpack_awq(pack_last(values,order)[:,None],pack_last(zeros,order)[:,None],scales,2)
    want=((values-zeros.repeat_interleave(2,0))*scales.repeat_interleave(2,0)).T
    assert torch.equal(got,want)


def test_gptq_pinned_engine_symmetric_static_groups():
    values=torch.arange(32).reshape(8,4)%16
    qweight=pack_last(values.T,list(range(8)))[None,:]
    scales=torch.tensor([[.25,.5,.75,1.],[1.,.75,.5,.25]])
    got=unpack_gptq_symmetric(qweight,scales,bits=4,group_size=4)
    assert torch.equal(got,((values-8)*scales.repeat_interleave(4,0)).T)
    with pytest.raises(ValueError):unpack_gptq_symmetric(qweight,scales,bits=3,group_size=4)
