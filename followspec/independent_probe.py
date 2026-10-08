"""D-43 exploratory teacher-forced next-token agreement; cached counts, no selection gates."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time
from followspec.independent_kd import read,write,jsonl,answer_labels
from atlas.generate_magpie import unpaused
from atlas.workloads import file_hash


def agreement_counts(predicted_next,row):
    answer_labels(row,len(row['input_ids']))
    if len(predicted_next)!=len(row['input_ids'])-1:raise ValueError('one prediction per causal next-token position required')
    pairs=[(p,y) for p,y,m in zip(predicted_next,row['input_ids'][1:],row['loss_mask'][1:],strict=True) if m]
    return sum(p==y for p,y in pairs),len(pairs)


def validate_probe(rows,training):
    if not rows or any(r.get('source_pool') not in {'bank','precutoff_atlas'} for r in rows):raise ValueError('pre-cutoff probe required')
    hashes=[r['prompt_sha256'] for r in rows]
    if len(set(hashes))!=len(hashes):raise ValueError('duplicate probe prompt')
    if set(hashes)&{r['prompt_sha256'] for r in training}:raise ValueError('probe overlaps training')


def transfer_candidates(donors,target):return [d for d in donors if d['source_model']!=target]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['data','candidates','output']:p.add_argument('--'+key,required=True)
    p.add_argument('--training-files',nargs='+',required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    rows=read(a.data);training=[r for path in a.training_files for r in read(path)];validate_probe(rows,training)
    if not 5<=len(rows)<=32:raise ValueError('small fixed probe requires5–32 sequences')
    candidates=json.loads(Path(a.candidates).read_text())
    if len({c['id'] for c in candidates})!=len(candidates):raise ValueError('duplicate candidate identity')
    cfg=vars(a)|dict(n=len(rows),data_sha256=file_hash(a.data),candidate_sha256=file_hash(a.candidates),
        training_sha256={path:file_hash(path) for path in a.training_files},code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        definition='macro answer-token top1 agreement with cached child greedy trajectory; next-token causal shift; exploratory',status='pilot')
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    unpaused();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write(out/'config.json',cfg)
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    torch.manual_seed(0);results=[]
    for j,c in enumerate(candidates):
        unpaused();start=time.monotonic();path=Path(c['path'])
        tok=AutoTokenizer.from_pretrained(path,local_files_only=True)
        vh=hashlib.sha256(json.dumps(tok.get_vocab(),sort_keys=True).encode()).hexdigest()
        if any(r['vocab_sha256']!=vh for r in rows):raise ValueError('probe vocabulary mismatch')
        model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda').eval()
        counts=[]
        with torch.inference_mode():
            for r in rows:
                ids=torch.tensor([r['input_ids']],device='cuda');pred=model(ids).logits[0,:-1].argmax(-1).cpu().tolist()
                matches,n=agreement_counts(pred,r);counts.append(dict(prompt_id=r['prompt_id'],matches=matches,n=n,agreement=matches/n))
        jsonl(out/f'candidate-{j}-per_prompt.jsonl',counts)
        result=dict(candidate=c,n_sequences=len(rows),macro_agreement=statistics.mean(r['agreement'] for r in counts),
            micro_agreement=sum(r['matches'] for r in counts)/sum(r['n'] for r in counts),
            sequence_std=statistics.stdev(r['agreement'] for r in counts),wall_s=time.monotonic()-start,
            model_files_sha256={p.name:file_hash(p) for p in path.iterdir() if p.is_file() and p.suffix in {'.json','.safetensors'}})
        write(out/f'candidate-{j}-results.json',result);results.append(result)
        del model;gc.collect();torch.cuda.empty_cache()
    write(out/'results.json',dict(status='pilot',rows=results,n=len(rows),caveat='Proxy ranking only; native acceptance measured separately on disjoint prompts.'))

if __name__=='__main__':main()
