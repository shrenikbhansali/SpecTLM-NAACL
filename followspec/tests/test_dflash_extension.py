from types import SimpleNamespace
import pytest
import torch
from followspec.dflash_extension import install_follow_spec_dflash, align_targets, prepare_block_sample


class BlockFixture(torch.nn.Module):
    def __init__(self):
        super().__init__();torch.manual_seed(9)
        self.head=torch.nn.Linear(3,8,bias=False)
        self.block_size=3;self.config=SimpleNamespace(sample_from_anchor=False)
        self.observed=[]
    def _backbone_forward(self,hidden_states,input_ids,loss_mask,verifier_last_hidden_states,document_ids,**kw):
        anchor=int(torch.randint(1,4,()).item())
        indices=torch.arange(anchor,anchor+3)
        q=self.head(hidden_states[:,indices]);q.retain_grad();self.observed.append((indices.clone(),q))
        targets=align_targets(verifier_last_hidden_states,indices,sample_from_anchor=False)
        mask=loss_mask[:,indices].clone();mask[:,::3]=False
        return hidden_states[:,indices],q,targets,mask,indices
    def forward(self,**kw):
        _,q,p,mask,_=self._backbone_forward(**kw)
        loss=((q-p.detach()).square().mean(-1)*mask).sum()/mask.sum()
        return None,loss,{'loss_sum':loss.detach(),'loss_total':torch.tensor(1.)}


def batch():
    torch.manual_seed(11)
    return dict(hidden_states=torch.randn(1,8,3),base_hidden_states=torch.randn(1,8,3),
        verifier_last_hidden_states=torch.randn(1,8,8),base_verifier_last_hidden_states=torch.randn(1,8,8),
        input_ids=torch.arange(8)[None],document_ids=torch.zeros(1,8,dtype=torch.long),
        loss_mask=torch.tensor([[False,True,True,True,True,True,True,True]]),target_id=['bank'])


def native_args(b,base=False):
    return {k:(b['base_'+k] if base and k in ['hidden_states','verifier_last_hidden_states'] else v)
            for k,v in b.items() if not k.startswith('base_') and k!='target_id'}


def test_lambda_zero_preserves_native_paired_loss_rng_and_state_keys():
    m=BlockFixture();b=batch();rng=torch.get_rng_state();keys=set(m.state_dict())
    _,child,_=m(**native_args(b));after=torch.get_rng_state()
    torch.set_rng_state(rng);_,base,_=m(**native_args(b,True))
    torch.set_rng_state(rng);install_follow_spec_dflash(m,delta_lambda=0,top_k=3,shared_verifier_head=True)
    _,loss,metrics=m(**b)
    torch.testing.assert_close(loss,child+base,atol=1e-6,rtol=0)
    assert torch.equal(torch.get_rng_state(),after)
    assert torch.equal(m.observed[-2][0],m.observed[-1][0])
    assert set(m.state_dict())==keys and metrics['delta_loss_sum']==0


def test_every_masked_position_has_delta_and_base_delta_has_no_gradient():
    m=BlockFixture();b=batch();install_follow_spec_dflash(m,beta=0,delta_lambda=1,top_k=3,shared_verifier_head=True)
    _,loss,metrics=m(**b);loss.backward()
    assert metrics['delta_position_1_total']==metrics['delta_position_2_total']==1
    assert metrics['delta_position_0_total']==0
    assert m.observed[-2][1].grad is not None and m.observed[-1][1].grad is None


def test_identical_shifts_are_zero_and_teacher_constants_cancel():
    m=BlockFixture();b=batch();b['base_hidden_states']=b['hidden_states'].clone()
    b['base_verifier_last_hidden_states']=b['verifier_last_hidden_states'].clone()
    install_follow_spec_dflash(m,top_k=3,shared_verifier_head=True)
    _,_,first=m(**b);assert float(first['delta_loss_sum'])==0
    b['base_verifier_last_hidden_states']+=7
    _,_,second=m(**b);assert float(second['delta_loss_sum'])<1e-10


def test_explicit_projection_alignment_and_failure_restore_native_backbone():
    m=BlockFixture();b=batch();native=m._backbone_forward
    labels=torch.arange(64).reshape(1,8,8).float()
    idx=torch.tensor([1,2,3]);assert torch.equal(align_targets(labels,idx,sample_from_anchor=False),labels[:,:3])
    assert torch.equal(align_targets(labels,idx,sample_from_anchor=True),labels[:,1:4])
    install_follow_spec_dflash(m,top_k=3)
    with pytest.raises(ValueError,match='projected target'):m(**b)
    assert m._backbone_forward==native
    b['child_target_logits']=labels;b['base_target_logits']=labels+1
    _,loss,_=m(**b);assert torch.isfinite(loss)
    b['base_target_logits']=torch.zeros(1,7,8)
    with pytest.raises(ValueError,match='shape'):m(**b)
    assert m._backbone_forward==native


def test_dflash_uses_unshifted_samples_with_next_token_teacher_alignment():
    raw=dict(input_ids=torch.arange(6),loss_mask=torch.tensor([False,False,True,True,True,True]))
    for key in ['hidden_states','base_hidden_states','verifier_last_hidden_states','base_verifier_last_hidden_states']:
        raw[key]=torch.arange(18).reshape(6,3).float()
    got=prepare_block_sample(raw)
    for key in raw:assert torch.equal(got[key],raw[key])
    assert got['lengths'].tolist()==[6] and got['position_ids'].tolist()==list(range(6))
