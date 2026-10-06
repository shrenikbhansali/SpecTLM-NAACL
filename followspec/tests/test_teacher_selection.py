import pytest
import torch
from followspec.teacher_selection import teacher_topk,teacher_gather


@pytest.mark.parametrize('dtype',[torch.bfloat16,torch.float16,torch.float32,torch.float64])
def test_selection_preserves_float32_reference_including_ties_and_detaches(dtype):
    torch.manual_seed(8)
    x=torch.randint(-3,4,(2,65,512)).to(dtype).requires_grad_()
    expected=x.detach().float().topk(32,dim=-1)
    values,indices=teacher_topk(x,32)
    assert torch.equal(indices,expected.indices) and torch.equal(values,expected.values)
    assert values.dtype==torch.float32 and not values.requires_grad
    gathered=teacher_gather(x,indices)
    assert torch.equal(gathered,x.detach().float().gather(-1,indices)) and not gathered.requires_grad


def test_float64_selection_preserves_previous_float32_rounding():
    x=torch.tensor([1.+1e-9,1.,1.+2e-9],dtype=torch.float64)[None]
    expected=x.float().topk(2,-1)
    actual=teacher_topk(x,2)
    assert torch.equal(actual[0],expected.values) and torch.equal(actual[1],expected.indices)
