"""Small D-43 exploratory hard-label KD. Existing training paths are unchanged."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import subprocess
import time
from atlas.generate_magpie import unpaused
from atlas.workloads import filter_prompts, MinHashIndex, prompt_hash, file_hash


def read(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
def write(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def jsonl(path,rows):
    with Path(path).open('x') as f:
        for r in rows:f.write(json.dumps(r)+'\n')


def validate_target(row):
    if row.get('pool') not in {'precutoff_atlas','bank'} or row.get('exclusion'):
        raise ValueError('repairs require an admitted pre-cutoff target')
    if row.get('base')!='llama':raise ValueError('pilot is Llama only')


def filter_training_queries(rows,forbidden,threshold=.9):
    kept,report=filter_prompts(rows,forbidden,threshold)
    near=MinHashIndex(threshold)
    for text in forbidden:near.add(text)
    result=[r for r in kept if not near.query(r['prompt'])]
    return result,report|dict(near_evaluation_rejected=len(kept)-len(result),kept=len(result))


def answer_labels(row,max_length):
    ids=row['input_ids'];start=row['response_start']
    if not 0<start<len(ids)<=max_length:raise ValueError('empty answer or sequence exceeds limit; no truncation')
    if row['loss_mask']!=[False]*start+[True]*(len(ids)-start):raise ValueError('incorrect answer mask')
    if any(type(i)!=int or i<0 for i in ids):raise ValueError('invalid tokens')
    return [-100]*start+ids[start:]


def balanced_pool(donors,n):
    if not donors or n%len(donors):raise ValueError('equal donor counts required')
    count=n//len(donors)
    if any(len(v)<count for v in donors.values()):raise ValueError('donor shortfall')
    rows=[donors[k][i] for i in range(count) for k in sorted(donors)]
    if len({r['prompt_sha256'] for r in rows})!=n:raise ValueError('pooled duplicate prompts')
    return rows


def paired_training(child,base,n):
    if min(len(child),len(base))<n:raise ValueError('paired data shortfall')
    aa=[];bb=[];log=[]
    for a,b in zip(child[:n],base[:n],strict=True):
        for key in ['sample_id','prompt_sha256','prompt_token_ids','response_start']:
            if a[key]!=b[key]:raise ValueError('paired prompt mismatch: '+key)
        length=min(len(a['completion_token_ids']),len(b['completion_token_ids']))
        if not length:raise ValueError('empty paired answer')
        for row,dest in [(a,aa),(b,bb)]:
            context=row['prompt_token_ids'];answer=row['completion_token_ids'][:length]
            dest.append(row|dict(input_ids=context+answer,completion_token_ids=answer,
                loss_mask=[False]*len(context)+[True]*length))
        log.append(dict(sample_id=a['sample_id'],child_trim=len(a['completion_token_ids'])-length,
            base_trim=len(b['completion_token_ids'])-length,kept=length))
    return aa,bb,log


def head_only(model):
    import torch
    for p in model.parameters():p.requires_grad_(False)
    old=model.get_output_embeddings()
    head=torch.nn.Linear(old.in_features,old.out_features,bias=old.bias is not None,
        device=old.weight.device,dtype=old.weight.dtype)
    with torch.no_grad():
        head.weight.copy_(old.weight)
        if old.bias is not None:head.bias.copy_(old.bias)
    model.set_output_embeddings(head);model.config.tie_word_embeddings=False
    return model


def train(a):
    import importlib.metadata
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from peft import LoraConfig,get_peft_model
    cfg=vars(a).copy();rows=read(a.data)
    if len(rows)!=a.n:raise ValueError('explicit n must match sealed data')
    if not rows or any(r.get('source_pool') not in {'bank','precutoff_atlas'} for r in rows):raise ValueError('pre-cutoff provenance missing')
    if len({r['prompt_sha256'] for r in rows})!=len(rows):raise ValueError('duplicate training prompts')
    labels=[answer_labels(r,a.max_length) for r in rows]
    cfg.update(data_sha256=file_hash(a.data),code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256=file_hash(__file__),versions={k:importlib.metadata.version(k) for k in ['torch','transformers','peft']},
        supervised_tokens=sum(sum(v!=-100 for v in y) for y in labels)*a.epochs,
        scope='D-43 exploratory; answer-only hard labels; not a confirmatory result')
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    unpaused();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write(out/'config.json',cfg)
    random.seed(a.seed);torch.manual_seed(a.seed);torch.cuda.manual_seed_all(a.seed)
    tokenizer=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
    # Direct token reuse is permitted only after generation checked exact vocabulary identity.
    vocab_hash=hashlib.sha256(json.dumps(tokenizer.get_vocab(),sort_keys=True).encode()).hexdigest()
    if any(r.get('vocab_sha256')!=vocab_hash for r in rows):raise ValueError('training tokenizer vocabulary mismatch')
    samples=[]
    for r,y in list(zip(rows,labels))[:5]:
        s=r['response_start'];samples.append(dict(sample_id=r['sample_id'],prompt=tokenizer.decode(r['input_ids'][:s]),
            answer=tokenizer.decode(r['input_ids'][s:]),input_ids=r['input_ids'],labels=y,response_start=s))
    write(out/'five_decoded_masks.json',samples)
    model=AutoModelForCausalLM.from_pretrained(a.model,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda')
    model.config.use_cache=False
    if a.mode=='head':model=head_only(model)
    else:
        model=get_peft_model(model,LoraConfig(r=a.rank,lora_alpha=2*a.rank,lora_dropout=0.,bias='none',task_type='CAUSAL_LM',
        target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']))
        model.enable_input_require_grads();model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    model.train();params=[p for p in model.parameters() if p.requires_grad]
    optimizer=torch.optim.AdamW(params,lr=a.lr,weight_decay=0.)
    start=time.monotonic();step=0;losses=[];order=list(range(len(rows)));rng=random.Random(a.seed)
    with (out/'steps.jsonl').open('x') as log:
        for epoch in range(a.epochs):
            rng.shuffle(order)
            for offset in range(0,len(order),a.accumulate):
                unpaused();batch=order[offset:offset+a.accumulate];optimizer.zero_grad(set_to_none=True)
                tokens=sum(sum(x!=-100 for x in labels[i]) for i in batch);total=0.
                for i in batch:
                    ids=torch.tensor([rows[i]['input_ids']],device='cuda');ys=torch.tensor([labels[i]],device='cuda')
                    loss=model(input_ids=ids,labels=ys).loss
                    if not torch.isfinite(loss):raise ValueError('nonfinite KD loss')
                    weight=sum(x!=-100 for x in labels[i])/tokens
                    (loss*weight).backward();total+=float(loss.detach())*weight
                torch.nn.utils.clip_grad_norm_(params,1.);optimizer.step();step+=1;losses.append(total)
                log.write(json.dumps(dict(step=step,epoch=epoch,loss=total,answer_tokens=tokens,elapsed_s=time.monotonic()-start))+'\n');log.flush()
    model.eval()
    if a.mode=='lora':
        model.save_pretrained(out/'adapter');merged=model.merge_and_unload()
    else:merged=model
    merged.config.use_cache=True
    merged.save_pretrained(out/'merged',safe_serialization=True);tokenizer.save_pretrained(out/'merged')
    write(out/'results.json',dict(status='pilot',n=len(rows),steps=step,wall_s=time.monotonic()-start,
        initial_loss=losses[0],final_loss=losses[-1],trainable_parameters=sum(p.numel() for p in params),
        merged=str((out/'merged').resolve()),files_sha256={p.name:file_hash(p) for p in (out/'merged').iterdir() if p.is_file()}))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['data','model','output']:p.add_argument('--'+key,required=True)
    p.add_argument('--mode',choices=['lora','head'],default='lora')
    p.add_argument('--n',type=int,required=True);p.add_argument('--epochs',type=int,default=2)
    p.add_argument('--rank',type=int,default=8);p.add_argument('--lr',type=float,default=2e-4)
    p.add_argument('--accumulate',type=int,default=8);p.add_argument('--max-length',type=int,default=2048)
    p.add_argument('--seed',type=int,default=0);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    if min(a.n,a.epochs,a.rank,a.accumulate,a.max_length)<=0:raise ValueError('positive budgets required')
    train(a)

if __name__=='__main__':main()
