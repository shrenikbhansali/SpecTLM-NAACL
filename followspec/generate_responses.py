"""Pinned vLLM on-policy responses for one bank child or the base.

Stores token sequences and assistant masks, never dense target feature shards.
The B5 arm assembler must still enforce matched budgets and final split audits.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import time
from atlas.filter_pool import resolve_target
from atlas.generate_magpie import unpaused,validate_hardware,verify_inputs,request_seeds
from atlas.run_cell import sha256,write_new
from atlas.workloads import audit_disjoint,prompt_hash


def read(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def validate_queries(rows,forbidden,smoke,*,prompt_target=None,acceptance_limit=5):
    if not rows or len({r['prompt_id'] for r in rows})!=len(rows):raise ValueError('nonempty unique prompts required')
    if acceptance_limit not in (5,64) or (acceptance_limit!=5 and not smoke):raise ValueError('overfit64 requires explicit acceptance mode')
    if smoke and len(rows)>acceptance_limit:raise ValueError('response acceptance exceeds bounded prompt limit')
    for row in rows:
        if row.get('split')!='training':raise ValueError('training queries required; no evaluation prompts')
        if row.get('acceptance_only') and not smoke:raise ValueError('acceptance data cannot enter production training')
        if row.get('derivative_id') and row['derivative_id']!=prompt_target:raise ValueError('wrong prompt-generating derivative')
        if not isinstance(row.get('prompt'),str) or not row['prompt'].strip():raise ValueError('empty query')
        if row.get('format')=='chat_template_rendered':raise ValueError('raw training queries required')
    return audit_disjoint({'training':rows},{'forbidden':forbidden})


def response_limit(smoke, acceptance_limit, capacity_smoke):
    if capacity_smoke and (not smoke or acceptance_limit != 64):
        raise ValueError('capacity check requires --acceptance-smoke --acceptance-limit 64')
    return 512 if capacity_smoke or not smoke else 64


def make_sample(row,context,answer,*,target_id,revision,acceptance_only):
    if not context or not answer or any(type(i) is not int or i<0 for i in context+answer):raise ValueError('nonempty exact token sequence required')
    return dict(sample_id=row['prompt_id'],prompt_id=row['prompt_id'],raw_prompt=row['prompt'],
        prompt_sha256=prompt_hash(row['prompt']),split='train',generation_target=target_id,generation_revision=revision,
        input_ids=context+answer,prompt_token_ids=context,completion_token_ids=answer,response_start=len(context),
        loss_mask=[False]*len(context)+[True]*len(answer),acceptance_only=acceptance_only)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('base-snapshot','base-id','base-revision','prompts','tokenizer','tokenizer-revision','output'):
        p.add_argument('--'+key,required=True)
    p.add_argument('--target-registry',help='audited local B3 mixtures; no change to ordinary bank resolution')
    p.add_argument('--derivative-id',default='base');p.add_argument('--pool');p.add_argument('--downloads');p.add_argument('--filter-run')
    p.add_argument('--prompt-target',default='base',help='bank origin of Magpie prompts; may differ for PO-D base responses')
    p.add_argument('--rendered-inputs',help='B5 shared rendered training bundle; identical inputs for child and PO-D controls')
    p.add_argument('--prompt-filter-run',help='A2 proof for a bank prompt origin when the generation target is base')
    p.add_argument('--forbidden-files',nargs='+',required=True);p.add_argument('--seed',type=int,required=True)
    p.add_argument('--allow-a40-production',action='store_true');p.add_argument('--acceptance-smoke',action='store_true');p.add_argument('--dry-run',action='store_true')
    p.add_argument('--capacity-smoke',action='store_true',help='bounded64-query capacity inputs at production512 response limit; remain acceptance-only')
    p.add_argument('--acceptance-limit',type=int,choices=[5,64],default=5,help='64 only for B6 bounded overfit acceptance; still max64 response tokens')
    p.add_argument('--batch-size',type=int,default=32);p.add_argument('--max-model-len',type=int,default=4096)
    p.add_argument('--max-lora-rank',type=int,help='explicit matched rank capacity across response controls')
    p.add_argument('--gpu-memory-utilization',type=float,default=.7)
    a=p.parse_args();a.adapter=None;a.adapter_revision=None
    max_response_tokens=response_limit(a.acceptance_smoke,a.acceptance_limit,a.capacity_smoke)
    if not re.fullmatch('[a-f0-9]{40}',a.base_revision) or Path(a.base_snapshot).name!=a.base_revision:raise ValueError('pin local base snapshot')
    if not re.fullmatch('[a-f0-9]{40}',a.tokenizer_revision) or Path(a.tokenizer).name!=a.tokenizer_revision:raise ValueError('pin local tokenizer snapshot')
    if a.target_registry and a.derivative_id!='base':
        from followspec.mixture_targets import registry_row
        row=registry_row(a.target_registry,a.derivative_id,a.base_snapshot,a.base_id,a.base_revision,allow_acceptance=a.acceptance_smoke)
        target,adapter=a.base_snapshot,row['local_adapter']
    else:target,adapter,row=resolve_target(a)
    if a.derivative_id!='base':
        if row['pool'] not in {'bank','mixture'} or row['type']!='lora_adapter':raise ValueError('only bank or admitted mixture targets may generate training data')
        if row['pool']=='bank':
            if not a.filter_run:raise ValueError('A2 filter proof required')
            root=Path(a.filter_run);fc=json.loads((root/'config.json').read_text());ft=json.loads((root/'target_provenance.json').read_text())
            if fc['derivative_id']!=a.derivative_id or ft['revision']!=row['revision'] or not json.loads((root/'results.json').read_text()).get('accepted'):
                raise ValueError('wrong or rejected A2 target')
        hashes=verify_inputs(row,adapter,a.tokenizer,a.tokenizer_revision)
    else:
        if Path(a.tokenizer)!=Path(a.base_snapshot) or a.tokenizer_revision!=a.base_revision:raise ValueError('base tokenizer must match base')
        hashes={}
    rows=read(a.prompts);forbidden=[r for path in a.forbidden_files for r in read(path)]
    audit=validate_queries(rows,forbidden,a.acceptance_smoke,prompt_target=a.prompt_target,acceptance_limit=a.acceptance_limit)
    if a.capacity_smoke and len(rows)!=64:raise ValueError('capacity generation requires exactly64 distinct queries')
    inputs=None;rendering=None
    if a.rendered_inputs:
        from followspec.render_inputs import load_bundle
        inputs=load_bundle(a.rendered_inputs,rows,prompt_target=a.prompt_target,
            base_tokenizer_sha256=sha256(Path(a.base_snapshot)/'tokenizer.json'),prompt_sha256=sha256(a.prompts))
        rendering=json.loads((Path(a.rendered_inputs).parent/'config.json').read_text())
        if rendering.get('acceptance_only') and not a.acceptance_smoke:raise ValueError('acceptance rendering cannot enter production')
        if a.prompt_target!='base' and a.target_registry:
            from followspec.mixture_targets import registry_row
            origin=registry_row(a.target_registry,a.prompt_target,a.base_snapshot,a.base_id,a.base_revision,allow_acceptance=a.acceptance_smoke)
            if rendering['prompt_target_revision']!=origin['revision']:raise ValueError('wrong mixture prompt rendering pin')
        elif a.prompt_target!='base':
            from argparse import Namespace
            _,_,origin=resolve_target(Namespace(**(vars(a)|dict(derivative_id=a.prompt_target))))
            if origin['pool']!='bank' or origin['type']!='lora_adapter':raise ValueError('prompt origin must be a bank adapter')
            proof=a.prompt_filter_run or a.filter_run
            if not proof:raise ValueError('prompt-origin A2 proof required')
            pc=json.loads((Path(proof)/'config.json').read_text());pr=json.loads((Path(proof)/'target_provenance.json').read_text())
            if pc['derivative_id']!=a.prompt_target or pr['revision']!=origin['revision'] or rendering['prompt_target_revision']!=origin['revision'] or not json.loads((Path(proof)/'results.json').read_text()).get('accepted'):
                raise ValueError('wrong or rejected prompt-origin proof')
    rank=int(row['r']) if adapter else 1;cap=next((n for n in (8,16,32,64,128,256,320,512) if n>=rank),None)
    if a.max_lora_rank is not None:
        if a.max_lora_rank not in (8,16,32,64,128,256,320,512) or a.max_lora_rank<rank:raise ValueError('invalid matched LoRA rank capacity')
        cap=a.max_lora_rank
    if cap is None or a.batch_size<=0:raise ValueError('unsupported adapter rank or batch size')
    cfg=vars(a)|dict(schema='followspec_response_tokens_v1',engine_version='0.31.0',K=None,drafter=None,
        temperature=.6,top_p=.95,max_new_tokens=max_response_tokens,
        n=len(rows),target=target,adapter=adapter,derivative_revision=row['revision'],adapter_files_sha256=hashes,
        max_lora_rank=cap,prompt_sha256=sha256(a.prompts),forbidden_sha256={f:sha256(f) for f in a.forbidden_files},
        tokenizer_sha256=sha256(Path(a.tokenizer)/'tokenizer.json'),acceptance_only=a.acceptance_smoke,disjointness=audit,
        source_sha256=sha256(__file__),code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        engine_lock_sha256=sha256(Path(__file__).resolve().parents[1]/'atlas/env/requirements.lock'),
        rendered_input_provenance=rendering,
        hardware_policy='D-19 A40 production opt-in' if a.allow_a40_production else 'original H100/H200 production; bounded A40 smoke')
    if a.target_registry:cfg['target_registry_sha256']=sha256(a.target_registry)
    if row.get('mixture_registry'):cfg['mixture_registry']=row['mixture_registry']
    if a.filter_run:cfg['filter_results_sha256']=sha256(Path(a.filter_run)/'results.json')
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    unpaused()
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit source before generation')
    if importlib.metadata.version('vllm')!='0.31.0':raise ValueError('wrong generation engine')
    import torch
    from transformers import AutoTokenizer
    from vllm import LLM,SamplingParams
    from vllm.lora.request import LoRARequest
    cfg['gpu_type']=torch.cuda.get_device_name(0);validate_hardware(cfg['gpu_type'],a.acceptance_smoke,a.allow_a40_production)
    tokenizer=AutoTokenizer.from_pretrained(a.tokenizer,local_files_only=True,trust_remote_code=False)
    if inputs is None:
        inputs=[]
        for r in rows:
            text=tokenizer.apply_chat_template([{'role':'user','content':r['prompt']}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
            inputs.append({'prompt_token_ids':tokenizer.encode(text,add_special_tokens=False)})
    for entry in inputs:
        ids=entry['prompt_token_ids']
        if not ids or len(ids)+cfg['max_new_tokens']>a.max_model_len:raise ValueError('context exceeds limit; no silent truncation')
    cfg['rendered_tokens_sha256']=__import__('hashlib').sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write_new(out/'config.json',cfg);start=time.perf_counter()
    try:
        unpaused()
        llm=LLM(model=target,revision=a.base_revision,tokenizer=a.tokenizer,dtype='bfloat16',seed=a.seed,
            enable_lora=True,max_lora_rank=cap,enable_prefix_caching=False,max_model_len=a.max_model_len,
            gpu_memory_utilization=a.gpu_memory_utilization)
        kw={'lora_request':LoRARequest(a.derivative_id,1,adapter)} if adapter else {}
        seeds=request_seeds(a.seed,0,len(rows));counts=[]
        with (out/'per_prompt.jsonl').open('x') as f:
            for start_idx in range(0,len(rows),a.batch_size):
                unpaused();end=min(start_idx+a.batch_size,len(rows))
                params=[SamplingParams(temperature=.6,top_p=.95,max_tokens=cfg['max_new_tokens'],seed=s) for s in seeds[start_idx:end]]
                outputs=llm.generate(inputs[start_idx:end],params,use_tqdm=False,**kw)
                if len(outputs)!=end-start_idx:raise ValueError('engine response count mismatch')
                for j,o in enumerate(outputs,start_idx):
                    if list(o.prompt_token_ids)!=inputs[j]['prompt_token_ids']:raise ValueError('engine changed exact prompt tokens')
                    answer=o.outputs[0];r=make_sample(rows[j],list(o.prompt_token_ids),list(answer.token_ids),target_id=a.derivative_id,
                        revision=row['revision'],acceptance_only=a.acceptance_smoke)
                    r.update(completion=answer.text,finish_reason=answer.finish_reason,sampling_seed=seeds[j])
                    f.write(json.dumps(r)+'\n');f.flush();counts.append(sum(r['loss_mask']))
        result=dict(n=len(counts),assistant_tokens=sum(counts),per_sample_assistant_tokens=counts,wall_s=time.perf_counter()-start,
            acceptance_only=a.acceptance_smoke,training_ready=False,caveat='B5 arm assembly, budgets, decoded masks and final global split audit still required')
        write_new(out/'results.json',result)
        write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),
            status='pilot',what_why='On-policy response tokens for online paired capture',new='Pinned vLLM bank/base generation with exact masks',
            artifacts=str(out.resolve()),config_results=dict(config=cfg,results=result),caveats=result['caveat']))
    except Exception as e:write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__=='__main__':main()
