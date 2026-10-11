"""Native packed TTT3 attention equivalence before opting into long-data SDPA."""
import os
os.environ.setdefault('TORCH_COMPILE_DISABLE','1')
import copy
import torch

def test_native_packed_ttt_sdpa_preserves_loss_and_gradients():
 from followspec.training_memory import training_attention
 from speculators import SpeculatorsConfig,VerifierConfig
 from speculators.models.eagle3 import Eagle3DraftModel,Eagle3SpeculatorConfig
 from speculators.proposals.greedy import GreedyTokenProposalConfig
 from speculators.losses import resolve_loss_config
 from transformers import LlamaConfig
 torch.manual_seed(17);torch.set_num_threads(2)
 c=Eagle3SpeculatorConfig(transformer_layer_config=LlamaConfig(vocab_size=64,hidden_size=32,intermediate_size=64,num_hidden_layers=1,num_attention_heads=4,num_key_value_heads=2,head_dim=8,max_position_embeddings=128),draft_vocab_size=64,embed_requires_grad=False,speculators_config=SpeculatorsConfig(algorithm='eagle3',proposal_methods=[GreedyTokenProposalConfig(speculative_tokens=1)],default_proposal_method='greedy',verifier=VerifierConfig(name_or_path=None,architectures=['LlamaForCausalLM'])))
 training_attention(c);assert c.transformer_layer_config._attn_implementation=='eager'
 a=Eagle3DraftModel(c).float()
 with torch.no_grad():
  for p in a.parameters():
   if not torch.isfinite(p).all():p.normal_(0,.02)
 bconf=copy.deepcopy(c);training_attention(bconf,'sdpa');b=Eagle3DraftModel(bconf).float();b.load_state_dict(a.state_dict())
 batch=dict(hidden_states=torch.randn(1,12,96),input_ids=torch.randint(1,63,(1,12)),document_ids=torch.tensor([[0]*5+[1]*5+[-1]*2]),position_ids=torch.tensor([[1,2,3,4,5,1,2,3,4,5,0,0]]),loss_mask=torch.tensor([[False,False,True,True,True,False,True,True,True,True,False,False]]),verifier_last_hidden_states=torch.randn(1,12,32),ttt_steps=3,loss_config=resolve_loss_config('kl_div','eager'))
 _,la,ma=a(**batch);_,lb,mb=b(**batch);torch.testing.assert_close(la,lb,rtol=2e-5,atol=2e-6);la.backward();lb.backward()
 for (n,p),(nn,q) in zip(a.named_parameters(),b.named_parameters()):
  assert n==nn
  if p.grad is not None:torch.testing.assert_close(p.grad,q.grad,rtol=3e-4,atol=3e-6)
 for k in ma:torch.testing.assert_close(ma[k],mb[k],rtol=2e-5,atol=2e-6)
