"""D-45 target-own Magpie or public-query greedy responses, with evaluation exclusion."""
import argparse,json,hashlib,importlib.metadata,subprocess,time
from pathlib import Path
from followspec.independent_kd import read,write,jsonl,filter_training_queries
from followspec.generate_responses import make_sample
from atlas.generate_magpie import unpaused,managed_engine,request_seeds
from atlas.workloads import file_hash,magpie_prefix


def tokenizer_for(path):
    # Read the exact pinned tokenizer.json; avoid AutoTokenizer's DeepSeek BPE/SP misclassification.
    from transformers import PreTrainedTokenizerFast
    return PreTrainedTokenizerFast.from_pretrained(path,local_files_only=True)


def render(tok,text):
    text=tok.apply_chat_template([dict(role='user',content=text)],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    return tok.encode(text,add_special_tokens=False)


def query_stops(tok):
    # DeepSeek ends the user turn with Assistant, rather than an eot token.
    tokens=['<|eot_id|>','<|im_end|>','<｜end▁of▁sentence｜>','<｜Assistant｜>']
    return sorted(set([tok.convert_tokens_to_ids(t) for t in tokens if t in tok.get_vocab()]+([tok.eos_token_id] if tok.eos_token_id is not None else [])))


def usable_query(text):
    return bool(text.strip()) and not any(t in text for t in ['<think>','</think>','<｜Assistant｜>','<|start_header_id|>assistant'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['target-row','forbidden','output']:p.add_argument('--'+key,required=True)
    p.add_argument('--public-queries');p.add_argument('--count',type=int,default=520)
    p.add_argument('--seed',type=int,default=7001);p.add_argument('--max-new-tokens',type=int,default=512)
    p.add_argument('--query-rounds',type=int,default=64);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    row=json.loads(Path(a.target_row).read_text());target=Path(row['path'])
    if target.name!=row['revision'] or not row['license']:raise ValueError('pinned licensed target required')
    if a.count<5 or a.max_new_tokens<4:raise ValueError('five examples and nonempty answers required')
    cfg=vars(a)|dict(target=row,engine_version='0.31.0',code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),forbidden_sha256=file_hash(a.forbidden),public_sha256=file_hash(a.public_queries) if a.public_queries else None,query_temperature=.8,response_temperature=0.,batch_size=8,max_model_len=4096,enable_thinking=False)
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    unpaused()
    if importlib.metadata.version('vllm')!='0.31.0':raise ValueError('wrong engine')
    import torch
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 required')
    from vllm import LLM,SamplingParams
    tok=tokenizer_for(target);out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write(out/'config.json',cfg)
    forbidden=[r.get('raw_prompt',r.get('prompt')) for r in read(a.forbidden)]
    start=time.monotonic();queries=[]
    with managed_engine(lambda:LLM(model=str(target),tokenizer=str(target),dtype='bfloat16',seed=a.seed,max_model_len=4096,gpu_memory_utilization=.7,enable_prefix_caching=False)) as llm:
        if a.public_queries:
            candidates=read(a.public_queries)
            candidates=sorted(candidates,key=lambda r:hashlib.sha256((str(a.seed)+r['prompt']).encode()).hexdigest())
            queries,report=filter_training_queries(candidates,forbidden)
            queries=queries[:a.count];write(out/'query_filter.json',report)
        else:
            prefix_ids=tok.encode(magpie_prefix(tok,row['base']),add_special_tokens=False)
            # Native user-turn terminator from the template, not a family-token assumption.
            stop=query_stops(tok)
            candidates=[]
            with (out/'raw_queries.jsonl').open('x') as raw:
                for iteration in range(a.query_rounds):
                    unpaused();seeds=request_seeds(a.seed,iteration,32)
                    outputs=llm.generate([dict(prompt_token_ids=prefix_ids)]*32,[SamplingParams(temperature=.8,top_p=1.,max_tokens=256,stop_token_ids=stop,seed=s) for s in seeds],use_tqdm=False)
                    for j,o in enumerate(outputs):
                        c=o.outputs[0];text=tok.decode(list(c.token_ids),skip_special_tokens=True).strip()
                        r=dict(prompt=text,prompt_id=f'P3-magpie-{a.seed}-{iteration}-{j}',split='training',derivative_id=row['id'],seed=a.seed)
                        raw.write(json.dumps(r|dict(finish_reason=c.finish_reason,token_ids=list(c.token_ids)))+'\n');raw.flush()
                        if c.finish_reason!='length' and usable_query(text):candidates.append(r)
                    queries,report=filter_training_queries(candidates,forbidden)
                    if len(queries)>=a.count:break
            write(out/'query_filter.json',report);queries=queries[:a.count]
        if len(queries)!=a.count:
            jsonl(out/'partial_queries.jsonl',queries);raise ValueError(f'query shortfall {len(queries)}/{a.count}')
        queries=[r|dict(rendered_token_ids=render(tok,r['prompt']),split='training') for r in queries]
        if any(len(r['rendered_token_ids'])+a.max_new_tokens>2048 for r in queries):raise ValueError('pilot context exceeds 2048; no silent truncation')
        jsonl(out/'queries.jsonl',queries);samples=[]
        with (out/'per_prompt.jsonl').open('x') as f:
            for offset in range(0,len(queries),8):
                unpaused();batch=queries[offset:offset+8]
                outputs=llm.generate([dict(prompt_token_ids=r['rendered_token_ids']) for r in batch],SamplingParams(temperature=0.,top_p=1.,max_tokens=a.max_new_tokens,seed=a.seed),use_tqdm=False)
                for r,o in zip(batch,outputs,strict=True):
                    if list(o.prompt_token_ids)!=r['rendered_token_ids']:raise ValueError('prompt IDs changed')
                    c=o.outputs[0];sample=make_sample(r,r['rendered_token_ids'],list(c.token_ids),target_id=row['id'],revision=row['revision'],acceptance_only=False)
                    sample.update(finish_reason=c.finish_reason,data_kind='generic' if a.public_queries else 'magpie')
                    f.write(json.dumps(sample)+'\n');f.flush();samples.append(sample)
        write(out/'five_decoded_masks.json',[dict(prompt=tok.decode(r['prompt_token_ids']),answer=tok.decode(r['completion_token_ids']),input_ids=r['input_ids'],loss_mask=r['loss_mask'],response_start=r['response_start']) for r in samples[:5]])
    write(out/'results.json',dict(status='pending_manual_five_sample_audit',n=len(samples),answer_tokens=sum(sum(r['loss_mask']) for r in samples),wall_s=time.monotonic()-start,capped=sum(r['finish_reason']=='length' for r in samples),per_prompt_sha256=file_hash(out/'per_prompt.jsonl')))

if __name__=='__main__':main()
