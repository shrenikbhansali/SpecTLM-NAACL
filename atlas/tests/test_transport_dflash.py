import pytest
import torch
from atlas.transport_dflash import capture_dflash_hidden,align_dflash_step


def test_dflash_excludes_anchor_slot_and_aligns_full_native_blocks():
    class Native:
        training=False;block_size=3
        config=type('Config',(),{'sample_from_anchor':False})()
        def _backbone_forward(self,**kw):
            assert kw['max_anchors']==3
            assert kw['loss_mask'].tolist()==[[False,False,True,True,True,True,True,True]]
            indices=torch.tensor([2,3,4,3,4,5,4,5,6])
            hidden=torch.arange(18).reshape(1,9,2).float()
            return hidden,None,None,torch.tensor([[False,True,True]*3]),indices
    ids=torch.arange(8).unsqueeze(0);features=torch.zeros(1,8,4);last=torch.zeros(1,8,2)
    captured=capture_dflash_hidden(Native(),features,ids,last,response_start=2)
    labels=torch.arange(8*5).reshape(8,5)
    p,h,anchors=align_dflash_step(labels,captured,step=0)
    assert anchors.tolist()==[2,3,4]
    assert torch.equal(p,labels[2:5])
    assert h.tolist()==[[2.,3.],[8.,9.],[14.,15.]]
    p,h,_=align_dflash_step(labels,captured,step=1)
    assert torch.equal(p,labels[3:6]) and h.tolist()==[[4.,5.],[10.,11.],[16.,17.]]
    with pytest.raises(ValueError):align_dflash_step(labels,captured,step=2)
    with pytest.raises(ValueError):capture_dflash_hidden(Native(),features,ids,last,response_start=6)


def test_dflash_rejects_native_anchor_or_mask_mismatch():
    class Native:
        training=False;block_size=3
        config=type('Config',(),{'sample_from_anchor':False})()
        def _backbone_forward(self,**kw):
            return torch.zeros(1,9,2),None,None,torch.ones(1,9,dtype=torch.bool),torch.arange(9)
    with pytest.raises(ValueError):capture_dflash_hidden(Native(),torch.zeros(1,8,4),torch.zeros(1,8,dtype=torch.long),torch.zeros(1,8,2),2)


def test_head_factor_changes_only_requested_projection_without_mutating_hidden():
    from atlas.transport_dflash import project_head
    base=torch.nn.Linear(2,3,bias=False);child=torch.nn.Linear(2,3,bias=False)
    with torch.no_grad():
        base.weight.copy_(torch.tensor([[1.,0.],[0.,1.],[0.,0.]]));child.weight.copy_(base.weight.flip(0))
    hidden=torch.tensor([[2.,1.],[1.,3.]]);saved=hidden.clone()
    b=project_head(base,hidden);c=project_head(child,hidden)
    assert b.argmax(-1).tolist()==[0,1] and c.argmax(-1).tolist()==[2,1]
    assert torch.equal(hidden,saved) and not b.requires_grad and not c.requires_grad
