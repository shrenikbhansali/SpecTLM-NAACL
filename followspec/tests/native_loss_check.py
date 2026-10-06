"""Fixed CPU tensor batch through real pinned native loss, not a training run."""
import unittest
import torch
from speculators.models.eagle3.metrics import compute_metrics
from speculators.losses import resolve_loss_config
from speculators.version import git_commit
from followspec.eagle3_extension import install_follow_spec


class LossFixture(torch.nn.Module):
    def __init__(self):
        super().__init__();self.lm_head=torch.nn.Identity();self.verifier_lm_head=torch.nn.Identity()
    def forward(self,hidden_states,input_ids,document_ids,loss_mask,verifier_last_hidden_states,ttt_steps=3,ttt_step_loss_decay=1.,**kwargs):
        targets=self.verifier_lm_head(verifier_last_hidden_states)
        loss=hidden_states.new_zeros(());prev=loss_mask.clone();metrics={};tokens=[]
        for step in range(ttt_steps):
            q=self.lm_head(hidden_states+.01*step)
            term,values=compute_metrics(q,targets,loss_mask,prev,step,ttt_step_loss_decay,loss_config=resolve_loss_config('kl_div','eager'))
            loss=loss+term;metrics.update(values);tokens.append(q.argmax(-1))
        return tokens,loss,metrics


class NativeLossCheck(unittest.TestCase):
    def test_lambda_zero_matches_real_native_loss_on_fixed_batch(self):
        self.assertEqual(git_commit,'261a82dd44ca05ff73006938c0614111bb2dd2b7')
        torch.manual_seed(41);m=LossFixture()
        b=dict(hidden_states=torch.randn(1,8,16),verifier_last_hidden_states=torch.randn(1,8,16),
            input_ids=torch.arange(8).reshape(1,8),document_ids=torch.zeros(1,8,dtype=torch.long),loss_mask=torch.tensor([[False,False,True,True,True,True,False,True]]))
        base_h=torch.randn(1,8,16);base_last=torch.randn(1,8,16)
        _,child,_=m(**b);_,base,_=m(**(b|dict(hidden_states=base_h,verifier_last_hidden_states=base_last)))
        install_follow_spec(m,beta=1.,delta_lambda=0.,top_k=4,shared_verifier_head=True)
        _,actual,_=m(**b,base_hidden_states=base_h,base_verifier_last_hidden_states=base_last,target_id=['unit-fixture'])
        self.assertLessEqual(abs(float(actual-(child+base))),1e-6)
        print('native paired loss absolute difference:',abs(float(actual-(child+base))))

if __name__=='__main__':unittest.main()
