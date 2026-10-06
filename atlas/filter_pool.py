"""One-derivative A2 coherence diagnostic on the pinned B2 engine.

PPL = exp(total target NLL / scored tokens) on fixed general-prompt token IDs,
excluding each first token. Identical reference tokens/masks for base and child.
The preparer records explicit prefix truncation; no generated text enters training.
"""
import argparse
from collections import defaultdict
import csv
from datetime import date
import importlib.metadata
import json
import math
from pathlib import Path
import re
import subprocess
import time
from atlas.run_cell import ensure_unpaused, load_prompts, sha256, write_new, local_files


def score_reference(tokens, logprobs):
    if len(tokens)<2 or len(tokens)!=len(logprobs):raise ValueError('reference/logprob shape mismatch')
    values=[]
    for token, probs in zip(tokens[1:],logprobs[1:]):
        if probs is None or token not in probs:raise ValueError('missing observed-token prompt logprob')
        value=probs[token];value=float(value.logprob if hasattr(value,'logprob') else value)
        if not math.isfinite(value) or value>1e-5:raise ValueError('invalid prompt logprob')
        values.append(value)
    nll=-sum(values)
    return dict(nll_sum=nll,scored_tokens=len(values),ppl=math.exp(nll/len(values)),token_logprobs=values)


def repetition_coverage(tokens):
    occurrences=defaultdict(list)
    for i in range(len(tokens)-3):occurrences[tuple(tokens[i:i+4])].append(i)
    return max((len(set(j for i in positions for j in range(i,i+4)))/len(tokens)
                for positions in occurrences.values() if len(positions)>1),default=0.)


def validate_baseline(config, baseline_config):
    for k in ('engine_version','reference_sha256','base_revision','max_reference_tokens','ppl_definition'):
        if config.get(k)!=baseline_config.get(k):raise ValueError(f'baseline mismatch: {k}')


def summarize(rows, samples, base_ppl, threshold):
    n=sum(r['scored_tokens'] for r in rows);nll=sum(r['nll_sum'] for r in rows)
    if not n or len(samples)!=10:raise ValueError('need scored tokens and exactly ten generation samples')
    ppl=math.exp(nll/n);ratio=ppl/base_ppl
    if not math.isfinite(ratio) or base_ppl<=0:raise ValueError('invalid baseline PPL')
    degenerate=sum(s['empty'] or s['immediate_eos'] or
                   (threshold is not None and s['repetition_coverage']>threshold) for s in samples)
    return dict(n=len(rows),scored_tokens=n,nll_sum=nll,ppl=ppl,ppl_ratio_vs_base=ratio,
                degenerate_count=degenerate,degeneracy_n=10,repetition_threshold=threshold,
                accepted=None if threshold is None else ratio<=2 and degenerate==0,
                pending=[] if threshold is not None else ['owner repetition threshold'])


def prepare_reference(prompts, tokenizer, max_tokens):
    rows=[]
    for r in prompts:
        raw=tokenizer(r['prompt'],add_special_tokens=True)['input_ids'];ids=raw[:max_tokens]
        if len(ids)<2:raise ValueError('reference too short')
        rendered=tokenizer.apply_chat_template([{'role':'user','content':r['prompt']}],tokenize=True,
            add_generation_prompt=True,enable_thinking=False)
        # Keep the generation header at the end of an explicitly truncated context.
        generation=rendered[-max_tokens:]
        rows.append(dict(prompt_id=r['prompt_id'],input_ids=ids,score_mask=[0]+[1]*(len(ids)-1),
            decoded=tokenizer.decode(ids),original_tokens=len(raw),truncated=len(raw)>max_tokens,
            generation_input_ids=generation,generation_original_tokens=len(rendered),
            generation_truncated=len(rendered)>max_tokens))
    return rows


def resolve_target(a):
    if a.derivative_id=='base':return a.base_snapshot,None,dict(model_id=a.base_id,revision=a.base_revision,pool='base')
    if a.adapter:
        if not a.adapter_revision:raise ValueError('local adapter requires provenance ID')
        ac=json.loads((Path(a.adapter)/'adapter_config.json').read_text())
        if ac.get('base_model_name_or_path')!=a.base_id or ac.get('peft_type')!='LORA':raise ValueError('wrong local adapter base/type')
        return a.base_snapshot,a.adapter,dict(model_id=a.derivative_id,revision=a.adapter_revision,
            type='lora_adapter',pool='heldout_acceptance',files_sha256=local_files(a.adapter))
    csv.field_size_limit(max(csv.field_size_limit(),16*1024**2))
    with open(a.pool) as f:rows=list(csv.DictReader(f))
    matches=[r for r in rows if r['model_id']==a.derivative_id]
    if len(matches)!=1:raise ValueError('derivative must occur exactly once')
    row=matches[0]
    if row['exclusion']:raise ValueError(f"B1 exclusion: {row['exclusion']}")
    entries=[json.loads(x) for x in Path(a.downloads).read_text().splitlines()]
    entries=[e for e in entries if e.get('status')=='complete' and e['model_id']==a.derivative_id and e['revision']==row['revision']]
    if not entries:raise ValueError('no completed pinned download')
    snapshot=Path(entries[-1]['path'])
    if snapshot.name!=row['revision']:raise ValueError('snapshot revision mismatch')
    if row['base_id']!=a.base_id or row['base_revision']!=a.base_revision:raise ValueError('base provenance mismatch')
    for spec in json.loads(row['files']):
        p=snapshot/spec['path']
        if not p.is_file() or p.stat().st_size!=spec['size']:raise ValueError('staged file missing/size mismatch')
    return (a.base_snapshot,str(snapshot),row) if row['type']=='lora_adapter' else (str(snapshot),None,row)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepare-reference',action='store_true');p.add_argument('--prompts')
    p.add_argument('--base-snapshot',required=True);p.add_argument('--base-id',required=True);p.add_argument('--base-revision',required=True)
    p.add_argument('--max-reference-tokens',type=int,default=2048);p.add_argument('--reference')
    p.add_argument('--derivative-id',default='base');p.add_argument('--pool');p.add_argument('--downloads')
    p.add_argument('--adapter');p.add_argument('--adapter-revision')
    p.add_argument('--drafter');p.add_argument('--drafter-revision');p.add_argument('--baseline')
    p.add_argument('--K',type=int,default=4);p.add_argument('--max-lora-rank',type=int,default=128)
    p.add_argument('--repetition-threshold',type=float);p.add_argument('--seed',type=int,default=0)
    p.add_argument('--output',required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    if not re.fullmatch('[a-f0-9]{40}',a.base_revision):raise ValueError('pin base revision')
    if Path(a.base_snapshot).name!=a.base_revision:raise ValueError('base snapshot must match revision')
    if a.repetition_threshold is not None and not 0<a.repetition_threshold<1:raise ValueError('invalid repetition threshold')
    if not 2<=a.max_reference_tokens<=3968:raise ValueError('reference length must leave room for generation')
    out=Path(a.output)
    if a.prepare_reference:
        from transformers import AutoTokenizer
        tok=AutoTokenizer.from_pretrained(a.base_snapshot,local_files_only=True)
        prompts=load_prompts(a.prompts)
        if len(prompts)!=128:raise ValueError('A2 reference requires128 general prompts')
        rows=prepare_reference(prompts,tok,a.max_reference_tokens)
        if a.dry_run:print(json.dumps(dict(n=len(rows),truncated=sum(r['truncated'] for r in rows))));return
        out.mkdir(parents=True,exist_ok=False)
        with (out/'reference.jsonl').open('x') as f:
            for row in rows:f.write(json.dumps(row)+'\n')
        write_new(out/'config.json',dict(base_id=a.base_id,base_revision=a.base_revision,
            source_prompts=a.prompts,prompt_sha256=sha256(a.prompts),max_reference_tokens=a.max_reference_tokens,
            reference_sha256=sha256(out/'reference.jsonl'),ppl_definition='fixed_prompt_tokens',n=128,
            scoring='teacher-forced general prompt text; first token excluded; prefix truncated explicitly',
            generation='shared base chat template; context suffix retained if truncated; first10 records'))
        return
    if not re.fullmatch('[a-f0-9]{40}',a.drafter_revision or ''):raise ValueError('pin drafter revision')
    reference=Path(a.reference);ref_cfg=json.loads((reference.parent/'config.json').read_text())
    if ref_cfg['reference_sha256']!=sha256(reference) or ref_cfg['base_revision']!=a.base_revision or ref_cfg['max_reference_tokens']!=a.max_reference_tokens:raise ValueError('reference provenance mismatch')
    records=[json.loads(x) for x in reference.read_text().splitlines()]
    if len(records)!=128 or len({r['prompt_id'] for r in records})!=128:raise ValueError('reference must have128 unique prompts')
    for r in records:
        if r['score_mask']!=[0]+[1]*(len(r['input_ids'])-1):raise ValueError('invalid reference score mask')
    config=vars(a)|dict(engine_version='0.31.0',reference_sha256=sha256(reference),ppl_definition='fixed_prompt_tokens',
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256=sha256(__file__),reference_config=ref_cfg,enable_lora=True,max_model_len=4096,
        generation_max_tokens=128,gpu_memory_utilization=.70,temperature=0.,scope='A2 filter; no training data')
    if a.dry_run:print(json.dumps(config,indent=2));return
    ensure_unpaused();ensure_unpaused(Path.cwd())
    if importlib.metadata.version('vllm')!='0.31.0':raise ValueError('engine differs from pin')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit tracked code first')
    out.mkdir(parents=True,exist_ok=False);write_new(out/'config.json',config)
    start=time.perf_counter();phase='input_validation';loaded=False
    try:
        if a.baseline:
            baseline=Path(a.baseline);bc=json.loads((baseline/'config.json').read_text());br=json.loads((baseline/'results.json').read_text())
            validate_baseline(config,bc)
            if bc['derivative_id']!='base' or not br['loadable']:raise ValueError('baseline must be a successful base run')
            if any(config[k]!=bc[k] for k in ('drafter','drafter_revision','K','max_lora_rank','seed')):raise ValueError('engine settings differ from baseline')
        elif a.derivative_id!='base':raise ValueError('child requires baseline')
        target,adapter,row=resolve_target(a)
        write_new(out/'target_provenance.json',row)
        from vllm import LLM,SamplingParams
        import torch
        phase='engine_load';ensure_unpaused()
        llm=LLM(model=target,tokenizer=a.base_snapshot,dtype='bfloat16',trust_remote_code=False,seed=a.seed,
            enable_prefix_caching=False,max_model_len=4096,gpu_memory_utilization=.70,
            enable_lora=True,max_lora_rank=a.max_lora_rank,per_request_spec_decode_metrics='detailed',
            speculative_config=dict(model=a.drafter,revision=a.drafter_revision,method='eagle3',num_speculative_tokens=a.K))
        kwargs={}
        if adapter:
            from vllm.lora.request import LoRARequest
            kwargs['lora_request']=LoRARequest(a.derivative_id,1,adapter)
        loaded=True;phase='generation';samples=[]
        with (out/'samples.jsonl').open('x') as f:
            for r in records[:10]:
                ensure_unpaused()
                answer=llm.generate([{'prompt_token_ids':r['generation_input_ids']}],
                    SamplingParams(temperature=0.,top_p=1.,max_tokens=128,seed=a.seed),use_tqdm=False,**kwargs)[0].outputs[0]
                ids=list(answer.token_ids)
                sample=dict(prompt_id=r['prompt_id'],completion=answer.text,token_ids=ids,
                    empty=not answer.text.strip(),immediate_eos=len(ids)==0 and answer.finish_reason=='stop',
                    repetition_coverage=repetition_coverage(ids),finish_reason=answer.finish_reason)
                f.write(json.dumps(sample)+'\n');f.flush();samples.append(sample)
        phase='prompt_logprobs';scores=[]
        with (out/'per_prompt.jsonl').open('x') as f:
            for r in records:
                ensure_unpaused()
                result=llm.generate([{'prompt_token_ids':r['input_ids']}],
                    SamplingParams(temperature=0.,max_tokens=1,prompt_logprobs=1,seed=a.seed),use_tqdm=False,**kwargs)[0]
                score=dict(prompt_id=r['prompt_id'],**score_reference(r['input_ids'],result.prompt_logprobs))
                f.write(json.dumps(score)+'\n');f.flush();scores.append(score)
        own_ppl=math.exp(sum(r['nll_sum'] for r in scores)/sum(r['scored_tokens'] for r in scores))
        result=summarize(scores,samples,br['ppl'] if a.baseline else own_ppl,a.repetition_threshold)
        result.update(loadable=True,load_error=None,wall_s=time.perf_counter()-start,gpu_type=torch.cuda.get_device_name(0),engine_version='0.31.0')
        write_new(out/'results.json',result)
    except Exception as exc:
        result=dict(loadable=loaded,load_error=f'{type(exc).__name__}: {exc}',phase=phase,ppl=None,
                    ppl_ratio_vs_base=None,accepted=False,wall_s=time.perf_counter()-start)
        write_new(out/'results.json',result);write_new(out/'failure.json',dict(error=result['load_error'],phase=phase))
        if loaded:raise
    finally:
        if 'result' in locals():write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=str(date.today()),
            status='pilot',what_why='A2 loadability/perplexity/degeneracy diagnostic',new='Pinned per-derivative filter',
            artifacts=str(out.resolve()),config_results=dict(config=config,results=result),
            caveats='Fixed general text PPL; input truncation documented. Operator review required; no training.'))

if __name__=='__main__':main()
