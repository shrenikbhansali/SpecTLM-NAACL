"""Tiny CPU native EAGLE3 hook/teacher-forcing contract; synthetic, no training."""
import json
import torch
from transformers import LlamaConfig
from speculators.models.eagle3.config import Eagle3SpeculatorConfig
from speculators.models.eagle3.core import Eagle3DraftModel
from speculators.version import git_commit
from atlas.transport_native import capture_eagle_unroll

assert git_commit=='261a82dd44ca05ff73006938c0614111bb2dd2b7'
torch.manual_seed(9)
tl=LlamaConfig(hidden_size=32,intermediate_size=64,num_hidden_layers=1,num_attention_heads=4,num_key_value_heads=2,vocab_size=16,max_position_embeddings=128)
tl._attn_implementation='eager'
cfg=Eagle3SpeculatorConfig(transformer_layer_config=tl,draft_vocab_size=8,eagle_aux_hidden_state_layer_ids=[2,4,6])
model=Eagle3DraftModel(cfg).eval()
with torch.no_grad():
 for p in model.parameters():
  if not torch.isfinite(p).all():p.uniform_(-.1,.1)
features=torch.randn(1,8,96);ids=torch.arange(8).unsqueeze(0)
a=capture_eagle_unroll(model,features,ids,3);b=capture_eagle_unroll(model,features,ids,3)
assert len(a)==3 and all(x.shape==(7,8) and torch.isfinite(x).all() for x in a)
assert all(torch.equal(x,y) for x,y in zip(a,b,strict=True))
assert not model.lm_head._forward_hooks
print(json.dumps(dict(passed=True,synthetic=True,device='cpu',native_commit=git_commit,steps=3,positions=7,draft_vocab=8)))
