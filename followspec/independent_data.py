"""D-43 small Magpie/greedy data pilot, pre-cutoff only. No old defaults change."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
from followspec.independent_kd import read,write,jsonl,validate_target,filter_training_queries
from followspec.generate_responses import make_sample
from atlas.generate_magpie import unpaused,managed_engine,request_seeds
from atlas.workloads import magpie_prefix,file_hash


def render_query(tokenizer,text):
    rendered=tokenizer.apply_chat_template([dict(role='user',content=text)],tokenize=False,add_generation_prompt=True)
    return tokenizer.encode(rendered,add_special_tokens=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['target-row','base','drafter','forbidden','output']:p.add_argument('--'+key,required=True)
    p.add_argument('--teacher',choices=['child','base'],default='child')
    p.add_argument('--queries',help='reuse child Magpie queries and exact rendered contexts for base control')
    p.add_argument('--count',type=int,default=160);p.add_argument('--max-new-tokens',type=int,default=256)
    p.add_argument('--seed',type=int,default=7001);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args();row=json.loads(Path(a.target_row).read_text());validate_target(row)
    if a.teacher=='base' and not a.queries:raise ValueError('base control must share child queries')
    if a.count<5 or a.count>544:raise ValueError('bounded exploratory data only')
    base=Path(a.base);target=Path(row['staged_path'])
    if target.name!=row['revision'] or base.name!=row['base_revision']:raise ValueError('snapshot pins differ')
    adapter=target if row['type']=='lora_adapter' and a.teacher=='child' else None
    weights=base if a.teacher=='base' or adapter else target
    tokenizer_path=target if (target/'tokenizer.json').exists() and (target/'tokenizer_config.json').exists() else base
    cfg=vars(a)|dict(target=row,weights=str(weights),adapter=str(adapter) if adapter else None,
        tokenizer=str(tokenizer_path),enable_lora=row['type']=='lora_adapter',engine_version='0.31.0',code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        target_row_sha256=file_hash(a.target_row),forbidden_sha256=file_hash(a.forbidden),source_sha256=file_hash(__file__),
        query_temperature=.8,response_temperature=0.,response_top_p=1.,batch_size=8,max_model_len=4096,
        query_sha256=file_hash(a.queries) if a.queries else None,status='pilot')
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    unpaused()
    if importlib.metadata.version('vllm')!='0.31.0':raise ValueError('wrong generation engine')
    from transformers import AutoTokenizer
    from vllm import LLM,SamplingParams
    tok=AutoTokenizer.from_pretrained(tokenizer_path,local_files_only=True)
    draft=AutoTokenizer.from_pretrained(a.drafter,local_files_only=True)
    if tok.get_vocab()!=draft.get_vocab():raise ValueError('pilot direct token reuse requires identical target/draft vocabulary')
    vocab_hash=hashlib.sha256(json.dumps(tok.get_vocab(),sort_keys=True).encode()).hexdigest()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write(out/'config.json',cfg|dict(vocab_sha256=vocab_hash))
    forbidden=[r.get('raw_prompt',r.get('prompt')) for r in read(a.forbidden)]
    if any(not isinstance(s,str) for s in forbidden):raise ValueError('invalid forbidden prompt')
    max_rank=next(r for r in [8,16,32,64,128,256,320,512] if r>=int(row.get('r') or 1))
    kw={}
    if adapter:
        from vllm.lora.request import LoRARequest
        kw['lora_request']=LoRARequest(row['model_id'],1,str(adapter))
    start=time.monotonic()
    with managed_engine(lambda:LLM(model=str(weights),tokenizer=str(tokenizer_path),dtype='bfloat16',seed=a.seed,
        enable_lora=cfg['enable_lora'],max_lora_rank=max_rank,enable_prefix_caching=False,max_model_len=4096,gpu_memory_utilization=.7)) as llm:
        if a.queries:
            queries=read(a.queries)
            if len(queries)!=a.count:raise ValueError('query count mismatch')
            kept,_=filter_training_queries(queries,forbidden)
            if len(kept)!=len(queries):raise ValueError('query overlap/duplicates')
        else:
            candidates=[];queries=[];prefix=magpie_prefix(tok,'llama');stop=tok.convert_tokens_to_ids('<|eot_id|>')
            with (out/'raw_queries.jsonl').open('x') as raw:
                # Deliberately bounded: retain a shortfall, never loop indefinitely.
                for iteration in range(20):
                    unpaused();seeds=request_seeds(a.seed,iteration,32)
                    outputs=llm.generate([prefix]*32,[SamplingParams(temperature=.8,top_p=1.,max_tokens=512,stop_token_ids=[stop],seed=s) for s in seeds],use_tqdm=False,**kw)
                    for j,o in enumerate(outputs):
                        c=o.outputs[0];r=dict(prompt=c.text,prompt_id=f"I3-{hashlib.sha256(row['model_id'].encode()).hexdigest()[:8]}-{a.seed}-{iteration}-{j}",split='training',derivative_id=row['model_id'],seed=a.seed)
                        raw.write(json.dumps(r|dict(finish_reason=c.finish_reason,token_ids=list(c.token_ids)))+'\n');raw.flush()
                        if c.finish_reason!='length':candidates.append(r)
                    queries,report=filter_training_queries(candidates,forbidden)
                    if len(queries)>=a.count:break
            write(out/'query_filter.json',report)
            if len(queries)<a.count:
                jsonl(out/'partial_queries.jsonl',queries);raise ValueError(f'query shortfall {len(queries)}/{a.count}')
            queries=queries[:a.count]
            for r in queries:
                r['rendered_token_ids']=render_query(tok,r['prompt'])
        jsonl(out/'queries.jsonl',queries)
        samples=[]
        with (out/'per_prompt.jsonl').open('x') as f:
            for offset in range(0,len(queries),8):
                unpaused();batch=queries[offset:offset+8]
                inputs=[dict(prompt_token_ids=r['rendered_token_ids']) for r in batch]
                if any(len(x['prompt_token_ids'])+a.max_new_tokens>4096 for x in inputs):raise ValueError('context exceeds budget')
                outputs=llm.generate(inputs,SamplingParams(temperature=0.,top_p=1.,max_tokens=a.max_new_tokens,seed=a.seed),use_tqdm=False,**kw)
                for r,o in zip(batch,outputs,strict=True):
                    if list(o.prompt_token_ids)!=r['rendered_token_ids']:raise ValueError('context changed')
                    c=o.outputs[0]
                    sample=make_sample(r,r['rendered_token_ids'],list(c.token_ids),target_id=row['model_id'] if a.teacher=='child' else row['base_id'],
                        revision=row['revision'] if a.teacher=='child' else row['base_revision'],acceptance_only=False)
                    sample.update(source_pool=row['pool'],source_model=row['model_id'],vocab_sha256=vocab_hash,finish_reason=c.finish_reason,teacher=a.teacher)
                    f.write(json.dumps(sample)+'\n');f.flush();samples.append(sample)
        write(out/'five_decoded_masks.json',[dict(prompt=tok.decode(r['prompt_token_ids']),answer=tok.decode(r['completion_token_ids']),
            input_ids=r['input_ids'],loss_mask=r['loss_mask'],response_start=r['response_start']) for r in samples[:5]])
    write(out/'results.json',dict(status='pilot',n=len(samples),answer_tokens=sum(sum(r['loss_mask']) for r in samples),wall_s=time.monotonic()-start,
        capped=sum(r['finish_reason']=='length' for r in samples),per_prompt_sha256=file_hash(out/'per_prompt.jsonl')))

if __name__=='__main__':main()
