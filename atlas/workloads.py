"""Deterministic workload preparation with explicit train/evaluation separation."""
from collections import Counter,defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import unicodedata
import numpy as np

SPEED={'repo':'nvidia/SPEED-Bench','revision':'454f88454792dfa3ccfd7ef15fff248efde44cd1',
       'file':'qualitative/test-00000-of-00001.parquet','license':'NVIDIA Evaluation Dataset License; evaluation only; no redistribution'}
GENERAL={'repo':'tatsu-lab/alpaca','revision':'dce01c9b08f87459cf36a430d809084718273017',
         'file':'data/train-00000-of-00001-a09b74b3ef9c3b56.parquet','license':'cc-by-nc-4.0'}
MAGPIE_REV='b734a36818e4ba7ef7f0f582fc55f7e860407d26'


def normalize(text):return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())
def prompt_hash(text):return hashlib.sha256(normalize(text).encode()).hexdigest()
def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def shingles(text):
    words=normalize(text).split()
    return {' '.join(words[i:i+5]) for i in range(max(1,len(words)-4))}


class MinHashIndex:
    """64 reproducible permutations, 16 bands of 4; exact Jaccard confirms hits."""
    def __init__(self,threshold):
        if not 0<threshold<=1:raise ValueError('invalid near-duplicate threshold')
        self.threshold=threshold;self.buckets=defaultdict(set);self.sets=[]
        rng=np.random.RandomState(20261005)
        self.a=rng.randint(1,2**31-1,64,dtype=np.uint64)
        self.b=rng.randint(0,2**31-1,64,dtype=np.uint64)
    def keys(self,words):
        hashes=np.array([int.from_bytes(hashlib.sha256(w.encode()).digest()[:4],'little') for w in words],dtype=np.uint64)
        signature=((hashes[:,None]*self.a+self.b) % np.uint64(4294967311)).min(axis=0)
        return [(i,tuple(signature[i*4:(i+1)*4].tolist())) for i in range(16)]
    def query(self,text):
        words=shingles(text);keys=self.keys(words)
        candidates=set().union(*(self.buckets[k] for k in keys))
        return any(len(words & self.sets[i])/len(words | self.sets[i]) >= self.threshold for i in candidates)
    def add(self,text):
        words=shingles(text);index=len(self.sets);self.sets.append(words)
        for key in self.keys(words):self.buckets[key].add(index)


def filter_prompts(rows,forbidden=(),near_threshold=.9):
    blocked={prompt_hash(s) for s in forbidden};seen=set();near=MinHashIndex(near_threshold)
    kept=[];stats=Counter(total=len(rows),length_rejected=0,exact_duplicates=0,near_duplicates=0,forbidden=0)
    for r in rows:
        text=r['prompt'].strip()
        if not 10<=len(text)<=1000:stats['length_rejected']+=1;continue
        h=prompt_hash(text)
        if h in blocked:stats['forbidden']+=1;continue
        if h in seen:stats['exact_duplicates']+=1;continue
        seen.add(h)
        if near.query(text):stats['near_duplicates']+=1;continue
        near.add(text);kept.append(r|dict(prompt=text,prompt_sha256=h))
    stats['kept']=len(kept);stats['duplicate_rate']=(stats['exact_duplicates']+stats['near_duplicates'])/len(rows) if rows else 0
    return kept,dict(stats)


def stratified_sample(rows,count,seed):
    if any('FULL BENCHMARK DATA SHOULD BE FETCHED' in r['prompt'] for r in rows):
        raise ValueError('unresolved SPEED-Bench placeholder; reconstruct official sources first')
    if count>len(rows) or count<=0:raise ValueError('invalid sample count')
    groups=defaultdict(list)
    for r in sorted(rows,key=lambda r:r['prompt_id']):groups[r['category']].append(r)
    rng=random.Random(seed)
    for key in sorted(groups):rng.shuffle(groups[key])
    result=[]
    while len(result)<count:
        for key in sorted(groups):
            if groups[key] and len(result)<count:result.append(groups[key].pop())
    return result


def audit_disjoint(training,evaluation):
    train={prompt_hash(r['prompt']) for rows in training.values() for r in rows}
    evaluation_hashes={prompt_hash(r['prompt']) for rows in evaluation.values() for r in rows}
    overlap=train & evaluation_hashes
    if overlap:raise ValueError(f'training/evaluation overlap: {len(overlap)} hashes')
    return dict(training_unique=len(train),evaluation_unique=len(evaluation_hashes),overlap_count=0)


def magpie_prefix(tokenizer,family):
    sentinel='MAGPIE_SENTINEL_9374bff123'
    rendered=tokenizer.apply_chat_template([{'role':'user','content':sentinel}],tokenize=False,
                                         add_generation_prompt=False,enable_thinking=False)
    if rendered.count(sentinel)!=1:raise ValueError('template must preserve user content exactly once')
    return rendered.split(sentinel)[0]


def language(text):
    from langdetect import detect,DetectorFactory,LangDetectException
    DetectorFactory.seed=20261005
    try:return detect(text)
    except LangDetectException:return 'und'


def write_jsonl(path,rows):
    with Path(path).open('x') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')


def public(args):
    import pyarrow.parquet as pq
    speed_raw=pq.read_table(args.speed_parquet).to_pylist()
    speed=[dict(prompt_id='speed-'+r['question_id'],prompt=r['turns'][0],category=r['category'],
                source=r['source'],original_turns=r['turns'],split='evaluation') for r in speed_raw]
    fixed=stratified_sample(speed,128,args.seed)
    # Compare training against every turn of the full release, not just selected 128.
    all_speed=[dict(prompt=t) for r in speed_raw for t in r['turns']]
    general_raw=pq.read_table(args.general_parquet).to_pylist()
    general=[dict(prompt_id=f'alpaca-{i}',prompt=r['instruction']+('\n'+r['input'] if r['input'].strip() else ''),split='training') for i,r in enumerate(general_raw)]
    filtered,stats=filter_prompts(general,[r['prompt'] for r in all_speed],args.near_threshold)
    if len(filtered)<20000:raise ValueError('fewer than 20,000 disjoint prompts after filtering')
    general=random.Random(args.seed+1).sample(filtered,20000)
    for r in fixed+general:r['language']=language(r['prompt'])
    report=audit_disjoint({'general':general},{'all_speed':all_speed})
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    write_jsonl(out/'speed128.jsonl',fixed);write_jsonl(out/'general20000.jsonl',general)
    write_jsonl(out/'all_speed_forbidden.jsonl',all_speed)
    config=dict(speed=SPEED|dict(sha256=file_hash(args.speed_parquet)),general=GENERAL|dict(sha256=file_hash(args.general_parquet)),
                seed=args.seed,general_seed=args.seed+1,near_threshold=args.near_threshold,
                minhash=dict(permutations=64,bands=16,rows_per_band=4,word_shingle_size=5,seed=20261005),
                language_detector='langdetect==1.0.9',speed_turn_policy='first user turn, original turns retained',
                counts=dict(Counter(r['category'] for r in fixed)),filters=stats,audit=report)
    (out/'manifest.json').write_text(json.dumps(config,indent=2)+'\n')
    print(json.dumps(config,indent=2))


def audit(args):
    read=lambda p:[json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
    print(json.dumps(audit_disjoint({p:read(p) for p in args.training},{p:read(p) for p in args.evaluation}),indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build-public');b.add_argument('--speed-parquet',required=True);b.add_argument('--general-parquet',required=True)
    b.add_argument('--seed',type=int,default=20261005);b.add_argument('--near-threshold',type=float,default=.9);b.add_argument('--output',required=True)
    a=sub.add_parser('audit');a.add_argument('--training',nargs='+',required=True);a.add_argument('--evaluation',nargs='+',required=True)
    args=p.parse_args();public(args) if args.command=='build-public' else audit(args)

if __name__=='__main__':main()
