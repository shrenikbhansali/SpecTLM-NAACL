from pathlib import Path
import pytest

def test_p0_exact_scope():
 from followspec.rev4_jobs import p0_specs
 r=p0_specs();assert len(r)==141
 assert sum(x['experiment']=='Y1' for x in r)==66
 assert sum(x['experiment']=='Y2' for x in r)==48
 assert sum(x['experiment']=='Y3a' for x in r)==27
 assert all(x['n']==128 for x in r if x['kind']=='timing')
 assert all(x['batch']==1 for x in r if x['experiment']=='Y1')
 assert all(x['target']==1 for x in r if x['experiment']=='Y3a')

def test_thinking_render_preserves_query():
 from followspec.rev4_jobs import render_thinking
 class Tokenizer:
  def apply_chat_template(self,messages,**kw):
   assert messages==[dict(role='system',content='detailed thinking on'),dict(role='user',content='question')]
   assert kw['add_generation_prompt'] and not kw['enable_thinking'];return 'rendered'
  def encode(self,x,**kw):assert x=='rendered' and not kw['add_special_tokens'];return [1,2]
 assert render_thinking(Tokenizer(),'question')==[1,2]

def test_initial_training_order_and_scope():
 from followspec.rev4_train import initial_specs
 r=initial_specs();assert len(r)==12
 assert [x['experiment'] for x in r]==['Y4']*2+['Y6']*4+['Y7']*2+['Y5']*4
 assert all(x['seed'] in [1,2] for x in r if x['experiment']=='Y5')
 assert [x['data_label'] for x in r if x['experiment']=='Y6']==['generic520']*2+['generic64k']*2

def test_qwen_dflash_timing_native_k16_opt_in():
 from atlas.timing_panel import parser,timing_speculation
 args=['--target','t','--target-revision','r','--prompts','p','--frozen-harness','h','--output','o']
 assert parser().parse_args(args).K==4
 a=parser().parse_args(args+['--method','dflash','--K','16']);assert timing_speculation(a)['num_speculative_tokens']==16

def test_response_system_prompt_opt_in_and_long_budget():
 from followspec.repair_data import render,validate_context_budget
 class Tok:
  def apply_chat_template(self,messages,**kwargs):return str(messages)
  def encode(self,text,**kwargs):return text
 tok=Tok();default=render(tok,'q');assert 'system' not in default
 assert 'detailed thinking on' in render(tok,'q',system_prompt='detailed thinking on')
 validate_context_budget([[1]*200],4096,8192)
 with pytest.raises(ValueError):validate_context_budget([[1]*5000],4096,8192)

def test_linear_alignment_orientation_and_identity():
 import torch
 from followspec.linear_alignment import fit_maps,fold_maps
 torch.manual_seed(0);x=torch.randn(40,4,dtype=torch.float64);a=torch.linalg.qr(torch.randn(4,4,dtype=torch.float64)).Q;y=x@a
 ls,op=fit_maps(x.T@x,x.T@y)
 assert torch.allclose(ls,a,atol=1e-9) and torch.allclose(op,a,atol=1e-9)
 w=torch.randn(3,8,dtype=torch.float64);z=torch.cat([x,x],1);mapped=torch.cat([y,x],1)
 assert torch.allclose(z@fold_maps(w,[a,torch.eye(4,dtype=torch.float64)]).T,mapped@w.T,atol=1e-9)

def test_census_multistage_membership_is_explicit():
 from followspec.rev4_census import memberships
 assert memberships('SFT+teacher_distillation+offline_preference')==['preference','SFT','distillation']
 assert memberships('unknown')==[]
 assert memberships('SFT+on_policy_RL')==['on_policy_RL','SFT']
