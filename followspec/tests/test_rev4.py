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
