"""Hook plumbing with a toy module, never a real model or training run."""
import torch
import pytest
from followspec.eagle3_extension import install_follow_spec


class NativeFixture(torch.nn.Module):
    def __init__(self):
        super().__init__();torch.manual_seed(7)
        self.lm_head=torch.nn.Linear(3,8,bias=False)
        self.verifier_lm_head=torch.nn.Linear(3,8,bias=False)
    def forward(self,hidden_states,input_ids,document_ids,loss_mask,verifier_last_hidden_states,
                ttt_steps=3,ttt_step_loss_decay=1.,**kwargs):
        targets=self.verifier_lm_head(verifier_last_hidden_states)
        loss=hidden_states.sum()*0;tokens=[]
        for step in range(ttt_steps):
            q=self.lm_head(hidden_states+step*.01)
            qs=q[:,:-step] if step else q
            loss=loss+ttt_step_loss_decay**step*((qs-targets[:,step:]).square().mean(-1)*loss_mask[:,step:]).mean()
            tokens.append(q.argmax(-1))
        return tokens,loss,{'loss_sum':loss.detach(),'loss_total':torch.tensor(1.)}


def batch():
    torch.manual_seed(11)
    return dict(hidden_states=torch.randn(1,5,3),base_hidden_states=torch.randn(1,5,3),
        verifier_last_hidden_states=torch.randn(1,5,3),base_verifier_last_hidden_states=torch.randn(1,5,3),
        input_ids=torch.arange(5).reshape(1,5),document_ids=torch.zeros(1,5,dtype=torch.long),
        loss_mask=torch.tensor([[False,True,True,True,True]]),target_id=['bank-a'])


def test_zero_lambda_exactly_preserves_native_paired_loss_and_state_keys():
    m=NativeFixture();b=batch();keys=set(m.state_dict());native=m.forward
    child={k:v for k,v in b.items() if not k.startswith('base_') and k!='target_id'}
    _,lc,_=native(**child)
    _,lb,_=native(**(child|dict(hidden_states=b['base_hidden_states'],verifier_last_hidden_states=b['base_verifier_last_hidden_states'])))
    install_follow_spec(m,beta=1.,delta_lambda=0.,top_k=3,shared_verifier_head=True)
    _,loss,metrics=m(**b)
    torch.testing.assert_close(loss,lc+lb,atol=1e-6,rtol=0)
    assert set(m.state_dict())==keys
    assert metrics['delta_loss_sum']==0


def test_each_unroll_step_gets_delta_and_hooks_are_removed():
    m=NativeFixture();install_follow_spec(m,beta=1.,delta_lambda=.1,top_k=3,shared_verifier_head=True)
    b=batch();_,loss,metrics=m(**b);loss.backward()
    assert all(f'delta_step_{i}_sum' in metrics for i in range(3))
    assert not m.lm_head._forward_hooks and not m.verifier_lm_head._forward_hooks
    assert m.lm_head.weight.grad.abs().sum()>0


def test_explicit_labels_override_shared_head_and_failure_cleans_hooks():
    m=NativeFixture();install_follow_spec(m,beta=1.,delta_lambda=.1,top_k=3,shared_verifier_head=True)
    b=batch();b['child_target_logits']=torch.randn(1,5,8);b['base_target_logits']=torch.randn(1,5,8)
    _,loss,_=m(**b);assert torch.isfinite(loss)
    b['child_target_logits']=torch.randn(1,5,7)
    with pytest.raises(ValueError,match='shape'):m(**b)
    assert not m.lm_head._forward_hooks and not m.verifier_lm_head._forward_hooks
