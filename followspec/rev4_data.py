"""D56 mode-specific/public-math response generation and reviewed-data sealing."""
import argparse,copy,json
from pathlib import Path
from followspec.review_followup import parts,replace,publish
from followspec.independent_kd import jsonl
from followspec.rev2_launch import NODES
from followspec.repair_data import tokenizer_for
from followspec.family_repair import validate_rows
from atlas.workloads import prompt_hash
from ops.track_t import WS,DISPATCH,lines,write,sha
FORBIDDEN=WS/'artifacts/P3_repair_20261008_0305/eval/forbidden.jsonl'

def prepare(stage,code,experiment='Y3b',queries=None):
 stage.mkdir(exist_ok=False);d={r['name']:r for r in lines(DISPATCH)};jobs=[];records=[]
 for t in ([1] if experiment=='Y3b' else [0,1]):
  source=WS/'artifacts/P3_D50_20261009_0200/E7-sealed16000/per_prompt.jsonl' if experiment=='Y3b' else queries
  original=lines(source)
  queries_all=[dict(prompt=r['raw_prompt'],prompt_id=r['prompt_id'],split='training',source='existing approved Alpaca16k') for r in original] if experiment=='Y3b' else original
  size=2000 if experiment=='Y3b' else 500;cap=512 if experiment=='Y3b' else 4096
  assert len(queries_all)==(16000 if experiment=='Y3b' else 4000)
  for shard,offset in enumerate(range(0,len(queries_all),size)):
   q=stage/f't{t}-queries-{shard}.jsonl';jsonl(q,queries_all[offset:offset+size]);name=f'REV4-{experiment}-t{t}-data-{shard}';out=stage/name
   j=copy.deepcopy(d['P3-D48-data-self-target-2-1455']);o,i=parts(j);row=WS/f'artifacts/P3_D48_20261008_1455/target-{t}.json';target=json.loads(row.read_text())
   for f,v in [('--tag',name),('--code-repo',code),('--base','llama'),('--prompts',q),('--target',target['path']),('--target-rev',target['revision']),('--seed',7001),('--note',f'D56 {experiment}; exact training-query pool; manual five-sample gate; cap{cap}')]:replace(o,f,v)
   for f,v in [('--target-row',row),('--public-queries',q),('--count',size),('--output',out),('--seed',7001),('--max-new-tokens',cap),('--training-context-budget',2048 if experiment=='Y3b' else 8192),('--min-free-gb',350)]:replace(i,f,v)
   if experiment=='Y3b':replace(i,'--system-prompt','detailed thinking on')
   oo,_=parts(d[f'FIX24-official-t{t}-16k-fc'])
   for f in ['--drafter-model','--drafter-rev']:replace(o,f,oo[oo.index(f)+1])
   j.update(name=name,args=o+['--']+i,allowed_nodes=NODES);jobs.append(j);records.append(dict(experiment=experiment,kind='data',target=t,shard=shard,n=size,cap=cap,name=name,run_dir=str(out),source=str(source),source_sha256=sha(source),prompts=str(q)))
 write(stage/'plan.json',records);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish')

def seal(stage,out,t):
 plan=[r for r in json.loads((stage/'plan.json').read_text()) if r['target']==t];exp=plan[0]['experiment'];expected=16000 if exp=='Y3b' else 4000;byhash={}
 for r in plan:
  root=Path(r['run_dir']);res=json.loads((root/'results.json').read_text());assert res['n']==r['n'] and res['per_prompt_sha256']==sha(root/'per_prompt.jsonl')
  for row in lines(root/'per_prompt.jsonl'):
   assert row['prompt_sha256'] not in byhash;byhash[row['prompt_sha256']]=row
 original=lines(Path(plan[0]['source']));order=[r.get('prompt_sha256',prompt_hash(r.get('prompt',r.get('raw_prompt')))) for r in original];assert len(byhash)==expected and set(order)==set(byhash);rows=[byhash[k] for k in order]
 forbidden={prompt_hash(r.get('raw_prompt',r.get('prompt'))) for r in lines(FORBIDDEN)};validate_rows(rows,forbidden,8193 if exp=='Y10' else 2049)
 out.mkdir(exist_ok=False);data=out/'per_prompt.jsonl';jsonl(data,rows);target=json.loads((WS/f'artifacts/P3_D48_20261008_1455/target-{t}.json').read_text());tok=tokenizer_for(target['path'])
 decoded=[dict(sample_id=r['sample_id'],prompt=tok.decode(r['prompt_token_ids']),answer=tok.decode(r['completion_token_ids']),input_ids=r['input_ids'],loss_mask=r['loss_mask'],response_start=r['response_start'],mask_valid=r['loss_mask']==[False]*r['response_start']+[True]*len(r['completion_token_ids'])) for r in rows[:5]]
 write(out/'five_decoded_masks.json',decoded);write(out/'seal.json',dict(n=len(rows),data_sha256=sha(data),sample_sha256=sha(out/'five_decoded_masks.json'),max_sequence=max(len(r['input_ids']) for r in rows),sequence_tokens=sum(len(r['input_ids']) for r in rows),status='pending_manual_decoded_mask_review',sources=plan))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','seal']);p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path);p.add_argument('--experiment',choices=['Y3b','Y10'],default='Y3b');p.add_argument('--queries',type=Path);p.add_argument('--output',type=Path);p.add_argument('--target',type=int);a=p.parse_args()
 if a.action=='prepare':prepare(a.stage,a.code,a.experiment,a.queries)
 else:seal(a.stage,a.output,a.target)
