"""D50 opt-in proposal adapters; execute the unmodified frozen cell loop.

Only parser choices and vLLM speculative_config are extended. All prompt loading,
request counters, generation, aggregation and artifact writes run through 6da2e42.
"""
import argparse,importlib.util,json,subprocess,sys
from pathlib import Path
FROZEN='6da2e4265c0398ec0de5affaf23b0bd1df0be445'


def speculative_options(a):
 if a.method=='ngram':
  if not 1<=a.prompt_lookup_min<=a.prompt_lookup_max:raise ValueError('invalid prompt lookup range')
  return dict(method='ngram',num_speculative_tokens=a.K,prompt_lookup_min=a.prompt_lookup_min,prompt_lookup_max=a.prompt_lookup_max)
 if a.method=='suffix':
  # Avoid order-dependent contamination from previously completed evaluation requests.
  return dict(method='suffix',num_speculative_tokens=a.K,suffix_decoding_max_cached_requests=0)
 out=dict(model=a.drafter,revision=a.drafter_revision,method=a.method,num_speculative_tokens=a.K)
 if a.draft_vocab_mapping:
  if a.method!='draft_model':raise ValueError('vocabulary mapping requires draft_model')
  out['use_heterogeneous_vocab']=True
 return out


def run_frozen(h,argv,provenance):
 original_parser=h.parser;original_write=h.write_new;original_config=h.read_drafter_config;old_argv=sys.argv
 def parser():
  p=original_parser()
  next(a for a in p._actions if a.dest=='method').choices+=['draft_model','ngram','suffix']
  p.add_argument('--prompt-lookup-min',type=int,default=1);p.add_argument('--prompt-lookup-max',type=int,default=5)
  p.add_argument('--draft-vocab-mapping',action='store_true')
  return p
 a=parser().parse_args(argv);options=speculative_options(a)
 def write(path,value):
  if path.name in ['config.json','resolved_config.json']:value=value|provenance|dict(resolved_speculative_options=options)
  return original_write(path,value)
 h.parser=parser;h.write_new=write
 if a.method in ['ngram','suffix']:h.read_drafter_config=lambda *_:dict(method=a.method,trainable_parameters=0,model_weights_loaded=False)
 sys.argv=[old_argv[0],*argv]
 engine=None;original_llm=None
 try:
  if not a.dry_run:
   import vllm as engine
   original_llm=engine.LLM
   def llm(**kwargs):
    kwargs['speculative_config']=options
    return original_llm(**kwargs)
   engine.LLM=llm
  h.main()
 finally:
  if engine is not None:engine.LLM=original_llm
  h.parser=original_parser;h.write_new=original_write;h.read_drafter_config=original_config;sys.argv=old_argv


def main():
 p=argparse.ArgumentParser(add_help=False);p.add_argument('--frozen-harness',required=True);a,argv=p.parse_known_args();root=Path(a.frozen_harness)
 if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!=FROZEN:raise ValueError('wrong frozen harness')
 spec=importlib.util.spec_from_file_location('d50_frozen_cell',root/'atlas/run_cell.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
 if '--dry-run' not in argv and subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit extension source before running')
 run_frozen(h,argv,dict(extension_commit=commit,extension_source_sha256=h.sha256(__file__),frozen_harness_commit=FROZEN,frozen_harness_source_sha256=h.sha256(root/'atlas/run_cell.py'),authorization='D50 opt-in methods; unchanged frozen generation/counters/aggregation'))

if __name__=='__main__':main()
