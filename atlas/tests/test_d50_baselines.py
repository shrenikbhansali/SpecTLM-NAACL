"""D50 opt-in methods must retain frozen generation and counter semantics."""
from argparse import Namespace
import importlib.util,json,sys,types
from pathlib import Path
import pytest
from atlas.frozen_baselines import speculative_options, run_frozen


def args(method, **kw):
 return Namespace(method=method,drafter='draft',drafter_revision='b'*40,K=4,prompt_lookup_min=1,prompt_lookup_max=3,draft_vocab_mapping=False,**kw)


def test_only_new_speculative_options_change():
 assert speculative_options(args('ngram'))==dict(method='ngram',num_speculative_tokens=4,prompt_lookup_min=1,prompt_lookup_max=3)
 assert speculative_options(args('suffix'))==dict(method='suffix',num_speculative_tokens=4,suffix_decoding_max_cached_requests=0)
 a=args('draft_model');a.draft_vocab_mapping=True
 assert speculative_options(a)['use_heterogeneous_vocab']
 for m in ['eagle3','eagle','dflash']:
  assert speculative_options(args(m))==dict(model='draft',revision='b'*40,method=m,num_speculative_tokens=4)
 a=args('ngram');a.prompt_lookup_max=0
 with pytest.raises(ValueError):speculative_options(a)

@pytest.mark.parametrize('method',['ngram','draft_model'])
def test_actual_frozen_loop_is_used(tmp_path,monkeypatch,method):
 root=Path('/home/heck2/sbhansali8/SpecTLM/.worktrees/run-FIX15-pilot-eval-20261007')
 spec=importlib.util.spec_from_file_location('baseline_frozen_test',root/'atlas/run_cell.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 original=(h.metrics,h.request_metrics,h.aggregate,h.engine_prompts)
 p=tmp_path/'p.jsonl';p.write_text(json.dumps(dict(prompt_id='p',prompt='x',rendered_token_ids=[1,2]))+'\n');out=tmp_path/'out';captured={}
 class LLM:
  def __init__(self,**kw):captured.update(kw)
  def generate(self,batch,sampling,**kw):
   assert batch==[dict(prompt_token_ids=[1,2])];assert sampling==dict(temperature=0.,top_p=1.,max_tokens=512,seed=0)
   counters=dict(per_step_accepted=[0,2,4],per_step_drafted=[4,4,4],histogram=[1,0,1,0,1],num_spec_tokens=4,num_draft_tokens=12)
   return [types.SimpleNamespace(prompt_token_ids=[1,2],outputs=[types.SimpleNamespace(text='a',token_ids=[3],spec_decode_metrics=counters)])]
 monkeypatch.setitem(sys.modules,'vllm',types.SimpleNamespace(LLM=LLM,SamplingParams=lambda **kw:kw))
 monkeypatch.setitem(sys.modules,'torch',types.SimpleNamespace(cuda=types.SimpleNamespace(get_device_name=lambda _: 'NVIDIA A40')))
 monkeypatch.setattr(h.importlib.metadata,'version',lambda _: '0.31.0')
 monkeypatch.setattr(h.subprocess,'check_output',lambda cmd,**kw:'' if 'status' in cmd else '6da2e4265c0398ec0de5affaf23b0bd1df0be445')
 monkeypatch.setattr(h,'ensure_unpaused',lambda *a:None);monkeypatch.setattr(h,'read_drafter_config',lambda *a:{})
 argv=['--target','target','--target-revision','a'*40,'--drafter','draft','--drafter-revision','b'*40,'--method',method,'--prompts',str(p),'--output',str(out),'--use-prompt-token-ids','--batch-size','8']
 run_frozen(h,argv,dict(extension_commit='c'*40))
 assert original==(h.metrics,h.request_metrics,h.aggregate,h.engine_prompts)
 assert captured['speculative_config']['method']==method
 assert captured['enable_prefix_caching'] is False and captured['per_request_spec_decode_metrics']=='detailed'
 assert json.loads((out/'results.json').read_text())['macro_acceptance_length']==3
 cfg=json.loads((out/'config.json').read_text());assert cfg['code_commit']=='6da2e4265c0398ec0de5affaf23b0bd1df0be445' and cfg['extension_commit']=='c'*40
 assert sys.modules['vllm'].LLM is LLM
