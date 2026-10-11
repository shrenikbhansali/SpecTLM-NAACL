"""D56 job adapters: immutable panels, frozen acceptance, established timing core."""
import argparse,copy,json
from pathlib import Path
from followspec.review_followup import parts,replace,publish
from followspec.rev2_panels import eval_job
from followspec.rev2_launch import NODES
from followspec.rev3_x5 import panel
from followspec.independent_kd import jsonl
from ops.track_t import WS,DISPATCH,lines,write,sha,frozen_check

def p0_specs():
 rows=[]
 for t in [0,1]:
  for w in ['speed128','math128']:
   for arm in ['none','reuse','fc','full','independent']+(['oracle'] if t==0 else []):
    for rep in range(3):rows.append(dict(experiment='Y1',kind='timing',target=t,workload=w,arm=arm,batch=1,replicate=rep,n=128))
  for b in [1,8]:
   for arm in ['none','reuse','fc','full']:
    for rep in range(3):rows.append(dict(experiment='Y2',kind='timing',target=t,workload='math128',arm=arm,batch=b,replicate=rep,n=128))
 for arm in ['reuse','fc','full']:
  for w,n in [('speed128',128),('math500',500),('math32-8192',32)]:rows.append(dict(experiment='Y3a',kind='eval',target=1,workload=w,arm=arm,seed=0,n=n))
  for w in ['speed128','math128']:
   for rep in range(3):rows.append(dict(experiment='Y3a',kind='timing',target=1,workload=w,arm=arm,batch=1,replicate=rep,n=128))
 return rows

def render_thinking(tok,text):
 rendered=tok.apply_chat_template([dict(role='system',content='detailed thinking on'),dict(role='user',content=text)],tokenize=False,add_generation_prompt=True,enable_thinking=False)
 return tok.encode(rendered,add_special_tokens=False)

def prepare_panels(stage,d):
 from followspec.repair_data import tokenizer_for
 root=stage/'panels';root.mkdir();proof={}
 for t in [0,1]:jsonl(root/f't{t}-math128.jsonl',lines(panel(t,'math500',d))[:128])
 row=json.loads((WS/'artifacts/P3_D48_20261008_1455/target-1.json').read_text());tok=tokenizer_for(row['path'])
 for w in ['speed128','math500','math32-8192']:
  source=panel(1,w,d);rows=[]
  for r in lines(source):
   ids=render_thinking(tok,r['raw_prompt']);rows.append(r|dict(prompt=tok.decode(ids,skip_special_tokens=False),rendered_token_ids=ids))
  dest=root/f't1-thinking-{w}.jsonl';jsonl(dest,rows)
  proof[w]=dict(source=str(source),source_sha256=sha(source),sha256=sha(dest),n=len(rows),system='detailed thinking on',decoded_five=[r['prompt'] for r in rows[:5]],same_raw_ids=True)
  assert [r['prompt_id'] for r in rows]==[r['prompt_id'] for r in lines(source)]
  if w=='math500':jsonl(root/'t1-thinking-math128.jsonl',rows[:128])
 write(root/'thinking-render-audit.json',proof)

def source_eagle(d,t,arm,w='speed128'):
 if arm=='reuse':return d[f'D50-E1-official-t{t}-'+('speed128' if w=='speed128' else 'math64')]
 return d[f'FIX24-official-t{t}-16k-{arm}-s{4477 if t==0 else 2625}-'+('speed128' if w=='speed128' else 'math64')]

def make_timing(src,name,out,prompts,code,batch=1,cap=512):
 j=copy.deepcopy(src);o,i=parts(j)
 for a in [o,i]:replace(a,'--prompts',prompts)
 for f,v in [('--tag',name),('--code-repo',code),('--note','D56 REV4 A40 paired timing; n128;3processesx3warm; frozen6da engine0.31; pilot')]:replace(o,f,v)
 for f,v in [('--output',out),('--batch-size',batch),('--max-new-tokens',cap),('--max-model-len',12288 if cap>512 else 4096),('--min-free-gb',350)]:replace(i,f,v)
 j.update(name=name,args=o+['--']+i,allowed_nodes=NODES);return j

def prepare_p0(stage,code,publish_now=False):
 frozen_check();stage.mkdir(exist_ok=False);d={r['name']:r for r in lines(DISPATCH)};prepare_panels(stage,d);jobs=[];records=[]
 for r in p0_specs():
  exp,t,w,arm=r['experiment'],r['target'],r['workload'],r['arm'];name=f'REV4-{exp}-t{t}-{arm}-{w}'+(f'-b{r["batch"]}-r{r["replicate"]}' if r['kind']=='timing' else '')
  out=stage/'runs'/name
  prompts=stage/'panels'/f't1-thinking-{w}.jsonl' if exp=='Y3a' else (stage/'panels'/f't{t}-math128.jsonl' if w=='math128' else panel(t,w,d))
  if r['kind']=='timing':
   b,rep=r['batch'],r['replicate']
   if exp=='Y2':src=d[f'REV3-X5-t{t}-{arm}-timing-b{b}-r{rep}']
   else:src=d[f'D52-timing-'+('r1' if t==0 else 'nemo')+'-'+dict(reuse='official-reused',fc='official-fc',full='official-full').get(arm,arm)+f'-b1-r{rep}']
   j=make_timing(src,name,out,prompts,code,b)
  else:
   j=eval_job(source_eagle(d,t,arm,w),name,out,prompts);o,i=parts(j)
   for f,v in [('--max-new-tokens',8192 if w=='math32-8192' else 512),('--max-model-len',12288 if w=='math32-8192' else 4096)]:replace(i,f,v)
   j['args']=o+['--']+i
  jobs.append(j);records.append(r|dict(name=name,run_dir=str(out),prompts=str(prompts),prompt_sha256=sha(prompts)))
 write(stage/'plan.json',records);write(stage/'jobs.json',jobs)
 if publish_now:publish(jobs,stage/'publish')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);p.add_argument('--publish',action='store_true');a=p.parse_args();prepare_p0(a.stage,a.code,a.publish)
