"""REV4 independent raw reduction; timing strata never mix workloads/modes."""
import argparse,json,time,subprocess,fcntl
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from followspec.rev2_timing_analysis import analyze as timing
from followspec.rev2_analysis import load_raw
from followspec.rev2_training_analysis import combine
from ops.track_t import WS,lines,write
BEGIN='<!-- REV4 LIVE BEGIN -->';END='<!-- REV4 LIVE END -->'

def reduce_p0(stage,out):
 out.mkdir(exist_ok=False);rows=json.loads((stage/'plan.json').read_text());time_rows=[];cells={};records=[]
 for r in rows:
  if r['kind']=='timing':time_rows.append(r|dict(experiment=r['experiment']+'-'+r['workload']))
  elif (Path(r['run_dir'])/'results.json').exists():cells[r['arm'],r['workload']]=load_raw(r['run_dir'])
 write(out/'timing-plan.json',time_rows);timing([out/'timing-plan.json'],out/'timing')
 for (arm,w),cell in sorted(cells.items()):
  if arm!='reuse' and ('reuse',w) in cells:records.append(dict(experiment='Y3a',arm=arm,workload=w,result=combine(cells['reuse',w],[cell])))
 write(out/'acceptance.json',records)
 started={};done={};failed=[]
 for e in lines(WS/'artifacts/M2_D28_20261006/response_queue.log'):
  if e['event']=='launched':started[e['out_dir']]=e['name']
  elif e['event']=='finished':done[started[e['out_dir']]]=str(e['exit'])
  elif e['event']=='launch_failed' and e.get('name','').startswith('REV4-'):failed.append(e)
 success=sum(done.get(r['name'])=='0' and (Path(r['run_dir'])/'results.json').exists() for r in rows)
 bad=[r['name'] for r in rows if done.get(r['name']) not in [None,'0']]
 tr=json.loads((out/'timing/results.json').read_text())['records'];ready=success==141 and len(tr)==56 and len(records)==6 and not bad
 progress=dict(expected=141,successful=success,acceptance_contrasts=len(records),timing_contrasts=len(tr),failed=bad,launch_failed=failed,ready=ready);write(out/'progress.json',progress)
 def f(x):return f"{x['mean']:.3f} [{x['ci95'][0]:.3f},{x['ci95'][1]:.3f}]"
 text=[f'Updated {datetime.now(ZoneInfo("America/New_York")).isoformat()}. P0 {success}/141 successful; pilot.','', '| Experiment | Arm | Workload | n | Reuse τ | Repair τ [95% CI] | Δτ [95% CI] | Δp1 [95% CI] |','|---|---|---|---:|---:|---|---|---|']
 for r in records:
  m=r['result']['metrics'];q=m['tau'];text.append(f"| Y3a | {r['arm']} | {r['workload']} | {q['n']} | {q['reference']['mean']:.3f} | {f(q['arm'])} | {f(q['delta'])} | {f(m['p1']['delta'])} |")
 text+=['','All timing uses n=128, three fresh processes × three warm passes. Workloads and template modes are separate strata.']
 for exp in ['Y1','Y2']:
  selected=[r for r in tr if r['experiment'].startswith(exp+'-') and r['arm']=='full' and r['reference']=='none']
  if selected:
   text+=['',f'**{exp}: measured full-repair speedups so far.** '+ '; '.join(f"target{r['target']} {r['experiment'].split('-',1)[1]} batch{r['batch']}: {f(r['metrics']['warm']['panel_speedup'])}×" for r in selected)+'. These quantify panel completion time on the specified A40 workloads; cold/startup and output-length effects are retained below.']
 if records:
  selected=[r for r in records if r['arm']=='full'];text+=['','**Y3a: same-mode repair contrasts so far.** '+'; '.join(f"{r['workload']} Δp1 {f(r['result']['metrics']['p1']['delta'])}, Δτ {f(r['result']['metrics']['tau']['delta'])}" for r in selected)+'. The thinking-on renders are shared across reuse and repairs.']
 text.extend(x for x in (out/'timing/report.md').read_text().splitlines() if x.startswith('|'))
 text+=['',f'[Raw acceptance and per-depth/length/source evidence](../{(out/"acceptance.json").relative_to(WS)}); [timing evidence](../{(out/"timing/results.json").relative_to(WS)}); [completion](../{(out/"progress.json").relative_to(WS)}).'];return '\n'.join(text),progress

def integrate(text,progress=None):
 with (WS/'artifacts/REV4-report.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  p=WS/'reports/REV4-results-20261011.md';s=p.read_text();block=BEGIN+'\n'+text+'\n'+END
  if BEGIN in s:s=s[:s.index(BEGIN)]+block+s[s.index(END)+len(END):]
  else:s+='\n'+block+'\n'
  if progress and progress['ready']:
   for heading in ['## Y1 —','## Y2 —','## Y3a —']:
    start=s.index(heading);stop=s.index('\n## ',start+1);part=s[start:stop];part=part.replace('Outcomes pending.','Complete; independently reduced estimates and what they establish are in the live P0 summary below.').replace('outcomes pending.','complete; see the independently reduced P0 summary below.');s=s[:start]+part+s[stop:]
  tmp=p.with_suffix('.md.rev4-tmp');tmp.write_text(s);tmp.replace(p)

def ping(out,progress):
 if not progress['ready']:return
 subprocess.run(['git','pull','--ff-only'],cwd=WS,check=True)
 p=WS/'MASTER.md';rows=p.read_text().splitlines();stamp=datetime.now(ZoneInfo('America/New_York')).isoformat()
 for k,r in enumerate(rows):
  if r.startswith('| REV4-P0 |'):
   c=r.split('|')
   if c[7].strip() in ['review','done']:return
   assert c[7].strip()=='in progress' and 'codex-1' in c[8]
   c[7]=' review ';c[8]=' codex-1 / '+stamp+' ';c[9]=' [results](reports/REV4-results-20261011.md); [all141jobs and raw analyses]('+str((out/'progress.json').relative_to(WS))+'); pilot ';rows[k]='|'.join(c)
 p.write_text('\n'.join(rows)+'\n')
 for name in ['notes/REV4.md','ledger/EXP-ATL-029.md']:
  with (WS/name).open('a') as f:f.write(f'\n## {stamp} — codex-1 — P0 completion ping\n\nAll141P0 jobs successful, six acceptance and56timing contrasts independently reduced. P0 moved to review; P1/P2 remain separate. Evidence {out}. No scientific promotion.\n')
 subprocess.run(['git','add','MASTER.md','notes/REV4.md','ledger/EXP-ATL-029.md','reports/REV4-results-20261011.md'],cwd=WS,check=True);subprocess.run(['git','commit','-m','board: REV4 P0 review with independent raw evidence'],cwd=WS,check=True);subprocess.run(['git','push','origin','main'],cwd=WS,check=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--watch',action='store_true');a=p.parse_args();a.output.mkdir(exist_ok=False);last=None
 while True:
  rows=json.loads((a.stage/'plan.json').read_text());key=tuple((r['name'],(Path(r['run_dir'])/'results.json').exists()) for r in rows)
  if key!=last or all(x[1] for x in key):
   out=a.output/datetime.now().strftime('%Y%m%d_%H%M%S_%f');text,progress=reduce_p0(a.stage,out);integrate(text,progress);print('REDUCED',out,progress,flush=True);last=key
   if progress['ready']:ping(out,progress);break
  if not a.watch:break
  time.sleep(60)
