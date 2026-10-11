"""D56 math-data prerequisite gate and immutable disjoint-domain mixture."""
import argparse,json,time
from pathlib import Path
from collections import Counter
from followspec.rev4_results import inventory
from followspec.rev4_data import prepare,FORBIDDEN
from followspec.independent_kd import jsonl
from followspec.repair_data import tokenizer_for
from followspec.family_repair import validate_rows
from followspec.rev4_priority import promote
from atlas.workloads import prompt_hash
from ops.track_t import WS,lines,write,sha

def mixed_rows(short,long):
 rows=short+long
 if len({r['prompt_sha256'] for r in rows})!=len(rows) or len({r['sample_id'] for r in rows})!=len(rows):raise ValueError('mixture contains duplicate prompt or sample ID')
 return rows

def prerequisites(rows):
 expected={('Y4','train'):2,('Y4','eval'):6,('Y4','timing'):24,('Y6','train'):4,('Y6','eval'):8,('Y6','timing'):6,('Y7','train'):2,('Y7','eval'):4,('Y5','train'):4,('Y5','eval'):12,('Y3b','data'):8,('Y3b','train'):2,('Y3b','eval'):6,('Y3b','timing'):12,('Y8','fit'):2,('Y8','eval'):8}
 counts=Counter((r['experiment'],r['kind']) for r in rows);missing={str(k):v-counts[k] for k,v in expected.items() if counts[k]<v}
 return dict(ready=not missing,missing=missing,expected_total=sum(expected.values()))

def mixture(sealed,t):
 data=sealed/'math4k/per_prompt.jsonl';long=lines(data);assert len(long)==4000
 source=WS/('artifacts/P3_D49_20261008_1800/sealed-generic16k/per_prompt.jsonl' if t==0 else 'artifacts/P3_D50_20261009_0200/E7-sealed16000/per_prompt.jsonl');short=lines(source);assert len(short)==16000;rows=mixed_rows(short,long)
 validate_rows(rows,{prompt_hash(r.get('raw_prompt',r.get('prompt'))) for r in lines(FORBIDDEN)},8193)
 dest=sealed/'mixed20k';dest.mkdir(exist_ok=False);jsonl(dest/'per_prompt.jsonl',rows);target=json.loads((WS/f'artifacts/P3_D48_20261008_1455/target-{t}.json').read_text());tok=tokenizer_for(target['path'])
 samples=[dict(prompt=tok.decode(r['prompt_token_ids']),answer=tok.decode(r['completion_token_ids']),input_ids=r['input_ids'],loss_mask=r['loss_mask'],response_start=r['response_start'],mask_valid=r['loss_mask']==[False]*r['response_start']+[True]*len(r['completion_token_ids'])) for r in short[:5]+long[:5]];write(dest/'five_decoded_masks.json',samples)
 write(dest/'seal.json',dict(n=len(rows),data_sha256=sha(dest/'per_prompt.jsonl'),sample_sha256=sha(dest/'five_decoded_masks.json'),max_sequence=max(len(r['input_ids']) for r in rows),sequence_tokens=sum(len(r['input_ids']) for r in rows),status='pending_manual_decoded_mask_review',sources=[dict(path=str(p),sha256=sha(p)) for p in [source,data]],order='unchanged Alpaca16k followed by unchanged distinct MATH/GSM8K4k; one epoch shuffled by native sampler'))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['wait-dispatch','mixture']);p.add_argument('--stage',type=Path);p.add_argument('--code',type=Path);p.add_argument('--queries',type=Path);p.add_argument('--sealed',type=Path);p.add_argument('--target',type=int);a=p.parse_args()
 if a.action=='mixture':mixture(a.sealed,a.target)
 else:
  while True:
   state=prerequisites(inventory());print(json.dumps(state),flush=True)
   if state['ready']:
    # P0 publication is independently verified; all its jobs retain exact IDs.
    from followspec.rev3_x5 import publication_complete
    if not publication_complete(WS/'artifacts/REV4_P0_20261011_0240/publish'):raise ValueError('P0 not fully published')
    prepare(a.stage,a.code,'Y10',a.queries);promote();break
   time.sleep(60)
