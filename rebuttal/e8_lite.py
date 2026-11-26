"""D61 E8-lite CPU preparation; fixed multilingual strata, no outcome selection."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np


def apportioned_counts(weights,n):
    total=sum(weights.values());counts={k:int(n*v/total) for k,v in weights.items()}
    order=sorted(weights,key=lambda k:(-(n*weights[k]/total-counts[k]),k))
    for k in order[:n-sum(counts.values())]:counts[k]+=1
    return counts


def replaced_indices(n,k):return sorted(np.random.default_rng(0).choice(n,k,replace=False).tolist())


def main():
    import pyarrow.parquet as pq
    from followspec.independent_kd import filter_training_queries,read
    from followspec.repair_data import tokenizer_for,render
    from rebuttal.e3a_data import jsonl_line,write
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.workspace
    a.output.mkdir(parents=True,exist_ok=False)
    src=json.loads((root/'rebuttal/source_stage_20261125_2020/aya-complete.json').read_text());target=json.loads((root/'rebuttal/inputs/target-0.json').read_text());tok=tokenizer_for(target['path'])
    original=root/'artifacts/P3_D49_20261008_1800/sealed-generic16k/per_prompt.jsonl';english=read(original)
    if len(english)!=16000:raise ValueError('expected unchanged16k original data')
    forbidden=root/'artifacts/P3_repair_20261008_0305/eval/forbidden.jsonl';evaluation=read(forbidden)
    public=read(root/'artifacts/B4_public_resolved_20261005/speed128.jsonl');domain=[r for r in public if r['category']=='multilingual'];labels=Counter(r['language'] for r in domain)
    mapping={'ar':'arb','en':'eng','es':'spa','fr':'fra','th':'tha','vi':'vie'}
    if set(labels)-set(mapping):raise ValueError('new SPEED language requires explicit mapping')
    weights={mapping[k]:v for k,v in labels.items()};train_quota=apportioned_counts(weights,4000);eval_quota=apportioned_counts(weights,128)
    pools={k:[] for k in weights};key=lambda r:hashlib.sha256(('E8-lite-seed0\0'+r['prompt']).encode()).hexdigest()
    for f in sorted((Path(src['path'])/'data').glob('*.parquet')):
        for b in pq.ParquetFile(f).iter_batches(columns=['inputs','language','language_code'],batch_size=2048):
            for i,r in enumerate(b.to_pylist()):
                if r['language_code'] not in pools or not r['inputs'].strip():continue
                text=r['inputs'];pools[r['language_code']].append({'prompt':text,'prompt_id':'aya-'+hashlib.sha256(text.encode()).hexdigest(),'language':r['language_code'],'language_name':r['language'],'source':'Aya pinned train/test union; split by seed0 hash below'})
    candidates=[]
    for lang,pool in sorted(pools.items()):
        candidates.extend(r for r in sorted(pool,key=key) if len(render(tok,r['prompt']))<=1536)
    # Held-out evaluation is also disjoint from the English-only baseline's full16k.
    base_forbidden=[r.get('raw_prompt',r.get('prompt')) for r in evaluation+english]
    filtered,initial_report=filter_training_queries(candidates,base_forbidden);heldout=[];training=[]
    for lang in weights:
        rr=[r for r in filtered if r['language']==lang]
        if len(rr)<train_quota[lang]+eval_quota[lang]:raise ValueError('Aya language quota shortfall '+lang)
        heldout+=rr[:eval_quota[lang]]
    # Fresh approximate check against newly held-out Aya, not just exact IDs.
    selected,second_report=filter_training_queries(filtered,base_forbidden+[r['prompt'] for r in heldout])
    for lang in weights:
        rr=[r for r in selected if r['language']==lang][:train_quota[lang]]
        if len(rr)!=train_quota[lang]:raise ValueError('dedup quota shortfall '+lang)
        training+=rr
    heldout.sort(key=key);training.sort(key=key)
    for name,rr in [('queries4000',training),('aya128',[r|{'rendered_token_ids':render(tok,r['prompt'])} for r in heldout]),('forbidden',evaluation+[{'prompt':r['prompt'],'prompt_id':r['prompt_id']} for r in heldout])]:
        with (a.output/(name+'.jsonl')).open('x') as f:
            for r in rr:f.write(jsonl_line(r))
    # Subset the exact main-table target renders; do not independently re-render SPEED.
    plan=json.loads((root/'rebuttal/ready_20261124_1504/E2_t0_interface_speed128_s0.json').read_text());cmd=plan['command'];speed=Path(cmd[cmd.index('--prompts')+1]);ids={r['prompt_id'] for r in domain}
    speedrows=read(speed)
    with (a.output/'speed-multilingual12.jsonl').open('x') as f:
        for r in speedrows:
            if r['prompt_id'] in ids:f.write(jsonl_line(r))
    write(a.output/'manifest.json',{'dataset':{k:src[k] for k in ['repo','revision','license']},'seed':0,'original_data':str(original),'original_data_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
        'replace_indices':replaced_indices(16000,4000),'replacement_n':4000,'keep_n':12000,'target':target,
        'language_source':'observed language labels of the exact12-query SPEED multilingual domain, including English translation instructions; proportional integer allocation',
        'SPEED_language_counts':dict(labels),'train_quotas':train_quota,'eval_quotas':eval_quota,'initial_dedup':initial_report,'new_heldout_dedup':second_report,
        'split':'fixed seed0 prompt hash over pinned Aya train/test union;128 reserved first within strata, then4000 disjoint training; source answers unused',
        'generation':'R1-Distill greedy512 cap; new responses only for4000 Aya instructions; retain original12k Alpaca responses',
        'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.output.glob('*.jsonl')}})
    write(a.output/'five_rendered_queries.json',[r|{'decoded':tok.decode(render(tok,r['prompt']))} for r in training[:5]])
    print(json.dumps({'n_train':len(training),'n_eval':len(heldout),'train_quotas':train_quota,'eval_quotas':eval_quota,'output':str(a.output)}))


if __name__=='__main__':main()
