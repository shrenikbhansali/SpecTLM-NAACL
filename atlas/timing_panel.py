"""D48 A40 timing only; acceptance statistics remain in frozen run_cell outputs."""
import argparse
import importlib.util
import importlib.metadata
import json
import subprocess
import time
from pathlib import Path
from followspec.disk_guard import require_free

FROZEN='6da2e4265c0398ec0de5affaf23b0bd1df0be445'


def timing_speculation(a):
    if a.no_speculation:return None
    result=dict(model=a.drafter,revision=a.drafter_revision,method=a.method,num_speculative_tokens=a.K)
    if a.draft_vocab_mapping:
        if a.method!='draft_model':raise ValueError('vocabulary mapping requires draft_model')
        result['use_heterogeneous_vocab']=True
    return result


def timed_passes(llm,sampling,rows,batch_size,warm_repeats,check,clock=time.perf_counter):
    results=[];reference=None
    for repeat in range(warm_repeats+1):
        batches=[];outputs_all=[];elapsed=0
        for offset in range(0,len(rows),batch_size):
            check();batch=rows[offset:offset+batch_size]
            inputs=[dict(prompt_token_ids=list(r['rendered_token_ids'])) for r in batch]
            start=clock();outputs=llm.generate(inputs,sampling,use_tqdm=False);wall=clock()-start
            if len(outputs)!=len(batch):raise ValueError('missing outputs')
            elapsed+=wall;records=[]
            for r,o in zip(batch,outputs,strict=True):
                if list(o.prompt_token_ids)!=r['rendered_token_ids'] or len(o.outputs)!=1:raise ValueError('prompt IDs changed')
                records.append(dict(prompt_id=r['prompt_id'],completion_token_ids=list(o.outputs[0].token_ids)))
            outputs_all.extend(records);batches.append(dict(batch_index=offset//batch_size,wall_s=wall,prompt_ids=[r['prompt_id'] for r in batch]))
        if reference is None:reference=outputs_all
        tokens=sum(len(r['completion_token_ids']) for r in outputs_all)
        results.append(dict(phase='cold' if repeat==0 else 'warm',repeat=repeat,n=len(rows),output_tokens=tokens,generation_wall_s=elapsed,tokens_per_s=tokens/elapsed,batches=batches,per_prompt=outputs_all,matches_first_pass=outputs_all==reference))
    return results


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['target','target-revision','prompts','frozen-harness','output']:p.add_argument('--'+k,required=True)
    p.add_argument('--drafter');p.add_argument('--drafter-revision');p.add_argument('--no-speculation',action='store_true')
    p.add_argument('--method',choices=['eagle3','draft_model','dflash'],default='eagle3');p.add_argument('--K',type=int,choices=[4,6,10],default=4)
    p.add_argument('--draft-vocab-mapping',action='store_true')
    p.add_argument('--batch-size',type=int,choices=[1,8,16,32],default=8);p.add_argument('--replicate',type=int,default=0)
    p.add_argument('--warm-repeats',type=int,default=3);p.add_argument('--min-free-gb',type=float,default=250);p.add_argument('--dry-run',action='store_true')
    p.add_argument('--max-new-tokens',type=int,default=512);p.add_argument('--max-model-len',type=int,default=4096)
    return p

def main():
    a=parser().parse_args();frozen=Path(a.frozen_harness)
    if a.max_new_tokens<1 or a.max_model_len<=a.max_new_tokens:raise ValueError('invalid timing generation/context caps')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=frozen,text=True).strip()!=FROZEN:raise ValueError('wrong frozen source')
    spec=importlib.util.spec_from_file_location('frozen_run_cell',frozen/'atlas/run_cell.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=frozen,text=True).strip():raise ValueError('dirty frozen harness')
    rows=h.load_prompts(a.prompts);h.engine_prompts(rows,True)
    if not a.no_speculation and (not a.drafter or not a.drafter_revision):raise ValueError('pinned drafter required')
    proposal=timing_speculation(a)
    cfg=vars(a)|dict(engine_version='0.31.0',harness_commit=FROZEN,harness_source_sha256=h.sha256(frozen/'atlas/run_cell.py'),code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),prompt_sha256=h.sha256(a.prompts),n=len(rows),seed=0,K=None if a.no_speculation else a.K,max_new_tokens=a.max_new_tokens,max_model_len=a.max_model_len,gpu_memory_utilization=.70,temperature=0.,enable_prefix_caching=False,scope='D48/D50 timing extension only; no acceptance numbers; frozen prompt loader/input validation and identical engine settings',cold_definition='first full panel after fresh engine compile/warmup; startup recorded separately',warm_definition='repeat same panel on the same engine; prefix cache disabled')
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    def check():h.ensure_unpaused();h.ensure_unpaused(Path.cwd());require_free(a.output,a.min_free_gb)
    check()
    if importlib.metadata.version('vllm')!='0.31.0':raise ValueError('wrong vLLM')
    import torch
    from vllm import LLM,SamplingParams
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 required')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);cfg['gpu_type']=torch.cuda.get_device_name(0);h.write_new(out/'config.json',cfg)
    start=time.perf_counter()
    kwargs=dict(model=a.target,revision=a.target_revision,tokenizer_revision=a.target_revision,dtype='bfloat16',trust_remote_code=False,seed=0,disable_log_stats=False,enable_prefix_caching=False,max_model_len=a.max_model_len,gpu_memory_utilization=.70,enable_lora=False,max_lora_rank=64)
    if proposal is not None:kwargs.update(per_request_spec_decode_metrics='detailed',speculative_config=proposal)
    llm=LLM(**kwargs);startup=time.perf_counter()-start
    results=timed_passes(llm,SamplingParams(temperature=0.,top_p=1.,max_tokens=a.max_new_tokens,seed=0),rows,a.batch_size,a.warm_repeats,check)
    h.write_new(out/'timing.json',dict(startup_s=startup,cell_wall_s=time.perf_counter()-start,passes=results))
    h.write_new(out/'results.json',dict(status='timed_pending_paired_analysis',n=len(rows),passes=len(results),startup_s=startup,all_repeats_identical=all(r['matches_first_pass'] for r in results)))

if __name__=='__main__':main()
