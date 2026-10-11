"""D56 P1/P2 raw-counter reduction, with explicit existing matched references."""
import argparse,json,time,fcntl
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from followspec.rev2_analysis import load_raw
from followspec.rev2_training_analysis import combine,matched_training
from followspec.rev2_timing_analysis import analyze as timing
from followspec.review_followup import parts
from ops.track_t import WS,DISPATCH,lines,write

def reference_name(r,kind='reuse'):
 exp,t,w,arm=r['experiment'],r['target'],r['workload'],r['arm']
 if exp=='Y4':return 'REV4-Y4-t2-reuse-'+w
 if exp=='Y5':return f'REV3-X5-t1-reuse-seed0-{w}'
 if exp=='Y3b':return 'REV4-Y3a-t1-reuse-'+w
 a=arm if kind=='child16k' else 'reuse'
 if w=='math32-8192':return f'REV1-long-t{t}-{a}-8192'
 if w=='math500':return 'D52-MATH500-official-'+('reused' if a=='reuse' else a) if t==0 else f'REV2-E14-t1-{a}-seed0-math500'
 return f'D50-E1-official-t{t}-speed128' if a=='reuse' else f'FIX24-official-t{t}-16k-{a}-s{4477 if t==0 else 2625}-speed128'

def timing_group(r):
 # Y4 has one declared16k repair budget; its untrained controls have no data label.
 label=r.get('data_label','') or ('generic16k' if r['experiment']=='Y4' else '')
 return r['experiment']+'-'+label+'-'+r['workload']

def jobpath(d,name):
 _,i=parts(d[name]);return Path(i[i.index('--output')+1])

def is_dispatched(r,d):return r['name'] in d and Path(r['run_dir'])==jobpath(d,r['name'])

def inventory():
 records={};dispatch={j['name']:j for j in lines(DISPATCH)}
 for stage in sorted((WS/'artifacts').glob('REV4_*')):
  if not stage.is_dir() or stage.name.startswith('REV4_P0'):continue
  for p in sorted(stage.glob('*plan*.json')):
   obj=json.loads(p.read_text())
   if not isinstance(obj,list):continue
   for r in obj:
    if not isinstance(r,dict) or not {'name','run_dir','experiment','kind'}<=r.keys():continue
    if not is_dispatched(r,dispatch):continue
    if r['name'] in records and records[r['name']]!=r:raise ValueError('conflicting plan '+r['name'])
    records[r['name']]=r
 from followspec.rev4_recovery import active_attempts,finished
 return active_attempts(list(records.values()),finished()[0])

def reduce(out):
 out.mkdir(exist_ok=False);rows=inventory();d={j['name']:j for j in lines(DISPATCH)};groups=defaultdict(list);timings=[];costs=[];pending=[];results=[];train_pairs=defaultdict(dict);audits=[]
 for r in rows:
  root=Path(r['run_dir'])
  if r['kind']=='timing':timings.append(r|dict(experiment=timing_group(r)));continue
  if r['kind']=='eval' and r['arm']!='reuse':groups[r['experiment'],r['target'],r.get('data_label',''),r['arm'],r['workload']].append(r);continue
  if r['kind'] in ['train','fit','data']:
   if not (root/'results.json').exists():pending.append(r['name']);continue
   res=json.loads((root/'results.json').read_text());cfg=json.loads((root/'config.json').read_text());costs.append(r|dict(measured_gpu_hours=res['wall_s']/3600,n=res.get('n'),steps=res.get('steps'),gpu_memory_gb=res.get('max_gpu_allocated_gb'),data_sha256=cfg.get('data_sha256'),config=str(root/'config.json'),results=str(root/'results.json')))
   if r['kind']=='train':train_pairs[r['experiment'],r['target'],r['data_label'],r['seed']][r['arm']]=(cfg,root)
 for key,pair in sorted(train_pairs.items()):
  if 'fc' not in pair or 'full' not in pair:continue
  a,b=pair['fc'][0],pair['full'][0];matched_training(a,b)
  for field in ['algorithm','supervision','supervision_row','training_attention','max_anchors']:
   if a.get(field)!=b.get(field):raise ValueError('unmatched intended controls: '+str(key)+' '+field)
  audits.append(dict(experiment=key,passed=True,configs=[str(pair[x][1]/'config.json') for x in ['fc','full']]))
 write(out/'matched-training.json',audits)
 for key,group in sorted(groups.items()):
  exp,t,label,arm,w=key;r=group[0];group=sorted(group,key=lambda r:r['seed'])
  if exp=='Y5':
   group=[dict(name=f'REV3-X5-t1-{arm}-seed0-{w}',run_dir=str(jobpath(d,f'REV3-X5-t1-{arm}-seed0-{w}')),seed=0)]+group
   if len(group)!=3 or [x['seed'] for x in group]!=[0,1,2]:pending.append(str(key)+' needs seeds0/1/2');continue
  names=[reference_name(r)]+([reference_name(r,'child16k')] if exp=='Y7' else [])
  missing=[x['name'] for x in group if not (Path(x['run_dir'])/'results.json').exists()]+[n for n in names if n not in d or not (jobpath(d,n)/'results.json').exists()]
  if missing:pending+=missing;continue
  cells=[load_raw(x['run_dir']) for x in group]
  for name in names:results.append(dict(experiment=exp,target=t,data_label=label,arm=arm,workload=w,reference='child16k' if name!=names[0] else 'reuse',result=combine(load_raw(jobpath(d,name)),cells)))
 # Timing references reuse exactly the same panels/modes and n=128 processes.
 p0=json.loads((WS/'artifacts/REV4_P0_20261011_0240/plan.json').read_text());extra={}
 for r in timings:
  exp=r['experiment'].split('-')[0]
  if exp not in ['Y6','Y3b']:continue
  for q in p0:
   wanted='Y1' if exp=='Y6' else 'Y3a';ww='math128' if r['workload']=='math500' else r['workload']
   if q['kind']=='timing' and q['experiment']==wanted and q['target']==r['target'] and q['workload']==ww and q['arm'] in ['none','reuse']:
    z=q|dict(experiment=r['experiment']);extra[r['experiment'],q['name']]=z
 timings+=list(extra.values());write(out/'timing-plan.json',timings);timing([out/'timing-plan.json'],out/'timing');write(out/'acceptance.json',results);write(out/'costs.json',costs)
 # A missing future plan is not completion: compare all mandatory contrast counts.
 counts=defaultdict(int)
 for r in results:counts[r['experiment']]+=1
 wanted={'Y3b':6,'Y4':4,'Y5':6,'Y6':8,'Y7':8,'Y8':8,'Y10':24}
 status=dict(acceptance_counts=dict(counts),expected=wanted,declared_jobs=len(rows),pending=sorted(set(pending)),y9_complete=(WS/'artifacts/REV4_Y9_20261011_0300/focused21.csv').exists());write(out/'progress.json',status)
 def f(x):return f"{x['mean']:.3f} [{x['ci95'][0]:.3f},{x['ci95'][1]:.3f}]"
 text=[f'Updated {datetime.now(ZoneInfo("America/New_York")).isoformat()}; pilot. Independent raw counters;10,000 paired seed/query draws. Training seeds and query counts explicit.','','| Experiment | Target | Data | Arm / reference | Workload | n/seeds | τ [95% CI] | Δτ [95% CI] | Δp1 [95% CI] |','|---|---|---|---|---|---:|---|---|---|']
 for r in results:
  m=r['result']['metrics'];q=m['tau'];text.append(f"| {r['experiment']} | {r['target']} | {r['data_label']} | {r['arm']} / {r['reference']} | {r['workload']} | {q['n']}/{q['seeds']} | {f(q['arm'])} | {f(q['delta'])} | {f(m['p1']['delta'])} |")
 text+=['','Timing: paired process/query-batch intervals; workloads, data budgets and thinking mode separate.']
 text.extend(x for x in (out/'timing/report.md').read_text().splitlines() if x.startswith('|'))
 text+=['','Measured per-run costs exclude unmeasured dedicated-drafter estimates. Data generation is listed separately and shared across repair arms; no zero cost is imputed for incomplete data.', '| Experiment | Target | Kind | Arm | n | GPU-h |','|---|---|---|---|---:|---:|']
 for r in costs:text.append(f"| {r['experiment']} | {r['target']} | {r['kind']} | {r.get('arm','')} | {r['n']} | {r['measured_gpu_hours']:.3f} |")
 text+=['',f'[Raw acceptance, lengths and per-depth evidence](../{(out/"acceptance.json").relative_to(WS)}); [costs/configs](../{(out/"costs.json").relative_to(WS)}); [completion counts](../{(out/"progress.json").relative_to(WS)}).'];(out/'report.md').write_text('\n'.join(text)+'\n');return '\n'.join(text)

def integrate(text):
 with (WS/'artifacts/REV4-report.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  p=WS/'reports/REV4-results-20261011.md';s=p.read_text();a='<!-- REV4 FOLLOWUP BEGIN -->';b='<!-- REV4 FOLLOWUP END -->';block=a+'\n'+text+'\n'+b
  if a in s:s=s[:s.index(a)]+block+s[s.index(b)+len(b):]
  else:s+='\n'+block+'\n'
  tmp=p.with_suffix('.md.followup-tmp');tmp.write_text(s);tmp.replace(p)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--watch',action='store_true');a=p.parse_args();a.output.mkdir(exist_ok=False);last=None
 while True:
  rows=inventory();key=tuple(sorted((r['name'],(Path(r['run_dir'])/'results.json').exists()) for r in rows))
  # New reference cells can land even without a new repair result.
  key+=(('dispatch_size',DISPATCH.stat().st_size),)
  key+=(('queue_events',(WS/'artifacts/M2_D28_20261006/response_queue.log').stat().st_size),)
  if key!=last:
   out=a.output/datetime.now().strftime('%Y%m%d_%H%M%S_%f');integrate(reduce(out));print('REDUCED',out,flush=True);last=key
  if not a.watch:break
  time.sleep(60)
