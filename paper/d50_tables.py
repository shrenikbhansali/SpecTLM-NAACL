"""Consolidate pilot tables from immutable, frozen-harness raw records."""
import argparse,json,hashlib,datetime,csv
from pathlib import Path
import numpy as np
from paper.d50_summary import raw_values,paired_summary,invalid_path,check_pair

FROZEN='6da2e4265c0398ec0de5affaf23b0bd1df0be445'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();ws=args.workspace;out=args.output;out.mkdir(parents=True,exist_ok=False)
 inputs={};cache={};excluded=[];pending=[]
 def read(p):
  p=Path(p);data=p.read_bytes();inputs[str(p)]=hashlib.sha256(data).hexdigest();return json.loads(data)
 def lines(p):
  p=Path(p);data=p.read_bytes();inputs[str(p)]=hashlib.sha256(data).hexdigest();return [json.loads(x) for x in data.splitlines()]
 inv=read(ws/'artifacts/FIX24_20261009_1420/invalid-runs.json');invalid=inv['training_directories']+inv['invalid_evaluation_runs']
 def load(p):
  p=Path(p)
  if invalid_path(p,invalid):raise ValueError(f'FIX24 invalid run: {p}')
  if str(p) in cache:return cache[str(p)]
  c=read(p/'config.json');res=read(p/'results.json');rr=lines(p/'per_prompt.jsonl')
  assert c['code_commit']==FROZEN and c['engine_version']=='0.31.0' and res['gpu_type']=='NVIDIA A40',p
  assert c['batch_size']==8 and c['max_new_tokens']==512 and c['temperature']==0 and c['seed']==0 and c['use_prompt_token_ids'],p
  pp=lines(c['prompts']);render={r['prompt_id']:r['rendered_token_ids'] for r in pp};vals={r['prompt_id']:raw_values(r,c['K'])[:3] for r in rr}
  assert len(vals)==len(rr)==c['n'] and set(vals)==set(render),p
  value=(c,render,vals);cache[str(p)]=value;return value
 d50=ws/'artifacts/P3_D50_20261009_0200';old=ws/'artifacts/P3_repair_20261008_0305';t1=read(ws/'artifacts/T1_cells_20261007_2350/index.json');base={};oracle={}
 for t in [0,1]:
  model=read(ws/f'artifacts/P3_D48_20261008_1455/target-{t}.json')['id']
  base[t,'speed128']=Path(next(r['run_dir'] for r in t1 if r['model_id']==model and r['method']=='eagle3' and r['cell']=='A10'))
  base[t,'math64']=old/f'controls/runs/P3-math-family-{t}-0310'
 oracle['speed128']=ws/'artifacts/T1b_cells_20261008_0145/runs/T4-phase1b-R1-dedicated';oracle['math64']=old/'controls/runs/P3-math-oracle-0-0310'
 mi=read(d50/'math500/panel-index.json')
 for r in mi:
  if r['arm']=='reused':base[0,'math500']=Path(r['run_dir'])
  if r['arm']=='oracle':oracle['math500']=Path(r['run_dir'])
 catalogs=[('D50',d50/'analysis/snapshot-20261009_052027/results.json'),('seeds16k',d50/'seed16k-analysis/snapshot-20261009_020745/results.json'),('D46',ws/'artifacts/P3_D46_20261008_0335/report/results.json'),('D48',ws/'artifacts/D48_analysis_20261008_1528/snapshot-20261008_175358/results.json')]
 entries=[]
 for campaign,p in catalogs:
  for r in read(p)['records']:
   if r.get('target',0) not in [0,1] or r.get('method','eagle3')!='eagle3' and campaign!='D50':continue
   q=Path(r.get('run_dir',r.get('run','')))
   if invalid_path(q,invalid):excluded.append(dict(run=str(q),reason='INVALID (FIX-24)'));continue
   label=r.get('label') or r.get('arm') or f"{r['method']}-K{r['K']}-L{r.get('lookup')}"
   if campaign=='D46':label='self256-'+label
   if campaign=='D48':label=r.get('data',r['kind'])+'-'+label
   if campaign=='seeds16k':label='generic16k-'+label
   entries.append(dict(campaign=campaign,label=label,target=r.get('target',0),workload=r['workload'],seed=r.get('seed',0),step=r.get('step',0),run_dir=str(q),source_record=r,source_catalog=str(p)))
 for r in mi:
  arm=r['arm'];label='generic16k-'+arm if arm in ['fc','full'] else arm
  entries.append(r|dict(campaign='math500',label=label,seed=0,step=4477 if arm in ['fc','full'] else 0,source_catalog=str(d50/'math500/panel-index.json')))
 for stage in ['FIX24_20261009_1420','P3_E5c64k_20261009_1420']:
  for p in sorted((ws/'artifacts'/stage).glob('publish-eval-*/index.json')):
   for r in read(p):entries.append(r|dict(campaign=stage,seed=0,source_catalog=str(p)))
 for (t,w),p in base.items():
  if w=='math500':continue
  entries.append(dict(campaign='control',label='reused',target=t,workload=w,seed=0,step=0,run_dir=str(p)))
 for w,p in oracle.items():
  if w=='math500':continue
  entries.append(dict(campaign='control',label='oracle',target=0,workload=w,seed=0,step=0,run_dir=str(p)))
 rows=[];seen=set()
 for e in entries:
  p=Path(e['run_dir'])
  if str(p) in seen:continue
  seen.add(str(p))
  if not (p/'results.json').exists():pending.append(e);continue
  t,w=e['target'],e['workload'];c,render,v=load(p);bc,br,bv=load(base[t,w]);check_pair(c,bc,render,br);keys=sorted(v);a=np.array([v[k] for k in keys]);b=np.array([bv[k] for k in keys]);o=None
  if t==0:
   oc,orr,ov=load(oracle[w]);check_pair(c,oc,render,orr);o=np.array([ov[k] for k in keys])
  summary=paired_summary(a[None],b,o);source=e.get('source_record',{});cost=source.get('cost')
  if cost is None and source.get('total_gpu_hours') is not None:cost={k:source[k] for k in ['data_gpu_hours','training_gpu_hours','total_gpu_hours']}
  e={k:v for k,v in e.items() if k!='source_record'}
  rows.append(e|dict(method=c['method'],K=c['K'],statistics=summary,cost_operator_verified=cost,scope='Single seed paired prompt bootstrap; other-method/K recovery descriptive; ngram conditional on proposal-bearing turns'))
 # A separate hierarchical summary of all three matched 16k training seeds.
 for arm in ['fc','full']:
  for w in ['speed128','math64']:
   rr=sorted([r for r in rows if r['campaign']=='seeds16k' and r['label']=='generic16k-'+arm and r['workload']==w],key=lambda r:r['seed']);assert [r['seed'] for r in rr]==[0,1,2]
   keys=sorted(load(base[0,w])[2]);a=np.array([[load(r['run_dir'])[2][k] for k in keys] for r in rr]);b=np.array([load(base[0,w])[2][k] for k in keys]);o=np.array([load(oracle[w])[2][k] for k in keys])
   rows.append(dict(campaign='three-seed',label='generic16k-'+arm,target=0,workload=w,seed='0/1/2',step='4477/4472/4481',run_dirs=[r['run_dir'] for r in rr],method='eagle3',K=4,statistics=paired_summary(a,b,o),cost_operator_verified=[r['cost_operator_verified'] for r in rr],scope='Hierarchical paired seed + query bootstrap, 3 seeds'))
 def fmt(v):
  if v is None:return '--'
  return f"{v['mean']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]"
 def last(rr):
  groups={}
  for r in rr:
   k=(r['campaign'],r['label'],r['target'],r['workload'],r['seed']);old=groups.get(k)
   if old is None or int(r.get('step',0))>int(old.get('step',0)):groups[k]=r
  return list(groups.values())
 final=last([r for r in rows if r['campaign']!='three-seed'])+[r for r in rows if r['campaign']=='three-seed']
 header=['Target','Workload','Arm / checkpoint','n / seeds','p1 [95% CI]','tau [95% CI]','Delta p1 [95% CI]','Oracle gap [95% CI]']
 def cells(r):
  s=r['statistics'];return ['R1' if r['target']==0 else 'Nemotron',r['workload'],f"{r['label']} / {r['step']}",f"{s['n_paired']} / {s['seeds']}",fmt(s['metrics']['p1']),fmt(s['metrics']['tau']),fmt(s['delta']['p1']),fmt(s['recovery'])]
 def table(name,rr):
  rr=sorted(rr,key=lambda r:(r['target'],r['workload'],r['label'],str(r['step'])));tab=[header]+[cells(r) for r in rr]
  (out/f'{name}.md').write_text('\n'.join(['| '+' | '.join(x)+' |' for x in [header,['---']*len(header),*tab[1:]]])+'\n')
  def esc(x):return str(x).replace('\\',r'\textbackslash{}').replace('_',r'\_').replace('%',r'\%').replace('&',r'\&').replace('#',r'\#')
  tex=['% Pilot. Paired CIs; see report for estimands, source mixture, and missing cells.',r'\begin{tabular}{llllllll}',r'\hline']+[' & '.join(map(esc,x))+r' \\' for x in tab]+[r'\hline',r'\end{tabular}'];(out/f'{name}.tex').write_text('\n'.join(tex)+'\n')
 main=[r for r in final if r['target']==0 and (r['campaign'] in ['D50','control','three-seed','math500','FIX24_20261009_1420','P3_E5c64k_20261009_1420'])]
 table('r1-main',main);table('nemotron',[r for r in final if r['target']==1 and r['campaign'] not in ['D46','D48']]);table('ablations',[r for r in final if r['campaign'] in ['D46','D48'] or r['label'].startswith('E5')]);table('all-checkpoints',rows)
 # Direct ablation contrasts, paired at the query level, seed0 only.
 contrasts=[]
 def one(label,w,campaign=None):
  rr=[r for r in final if r['target']==0 and r['label']==label and r['workload']==w and r.get('seed')==0 and (campaign is None or r['campaign']==campaign)]
  if len(rr)!=1:raise ValueError((label,w,campaign,len(rr)))
  return rr[0]
 for w in ['speed128','math64']:
  pairs=[('E5-ttt4-'+a,'generic4k-'+a,'TTT4 vs TTT3, same generic4k and epoch') for a in ['fc','full']]
  pairs += [('generic4k-'+a,'self4k-'+a,'Generic vs self4k, one epoch; source/token count/steps differ') for a in ['fc','full']]
  pairs += [('E5-second-epoch','generic16k-full','Second epoch vs seed0 first epoch; incremental continuation'),('E4-scratch16k','generic16k-full','Scratch vs warm start, matched generic16k epoch'),('self256-decoder','self256-fc','Decoder-LoRA proxy vs fc-only, 300 steps'),('self256-rms','reused','Training-free RMS vs reused')]
  for aa,bb,scope in pairs:
   ra,rb=one(aa,w),one(bb,w);ac,ar,av=load(ra['run_dir']);bc,br,bv=load(rb['run_dir']);check_pair(ac,bc,ar,br);keys=sorted(av)
   ss=paired_summary(np.array([[av[k] for k in keys]]),np.array([bv[k] for k in keys]))
   contrasts.append(dict(workload=w,arm=aa,reference=bb,scope=scope,statistics=ss,arm_path=ra['run_dir'],reference_path=rb['run_dir']))
 ch=['Workload','Arm','Reference','n','Delta p1 [95% CI]','Delta tau [95% CI]','Scope'];cr=[[r['workload'],r['arm'],r['reference'],str(r['statistics']['n_paired']),fmt(r['statistics']['delta']['p1']),fmt(r['statistics']['delta']['tau']),r['scope']] for r in contrasts]
 (out/'paired-ablations.md').write_text('\n'.join('| '+' | '.join(x)+' |' for x in [ch,['---']*len(ch),*cr])+'\n')
 (out/'paired-ablations.tex').write_text('\n'.join([r'\begin{tabular}{lllllll}']+[' & '.join(x.replace('_',r'\_') for x in r)+r' \\' for r in [ch,*cr]]+[r'\end{tabular}'])+'\n')
 with (out/'summary.csv').open('w') as f:
  wr=csv.writer(f);wr.writerow(header);wr.writerows(cells(r) for r in final)
 result=dict(status='pilot',generated=datetime.datetime.now().astimezone().isoformat(),records=rows,paired_ablations=contrasts,pending=pending,excluded_FIX24=excluded,input_sha256=inputs)
 (out/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 notice=['# D50 consolidated pilot results','',f"Raw recomputation: {len(rows)} rows; {len(excluded)} FIX-24-invalid cells excluded. All acceptance counters re-read from frozen 6da2e42 / vLLM 0.31.0 A40 outputs. Exact rendered token IDs and paired target/settings verified. 10000 paired query bootstrap draws; the 3-seed rows additionally resample training seeds. Nulls remain.",'','Tables: [R1](r1-main.md), [Nemotron](nemotron.md), [ablations/nulls](ablations.md), [direct paired contrasts](paired-ablations.md), [all checkpoints](all-checkpoints.md). Corresponding .tex files and summary.csv are included. Input hashes and raw paths are in results.json.','', 'MATH-500 has seed 0 only and contains the MATH-64 panel; it is not an independent replication. Unmeasured arm/workload combinations are absent, not zero. Main rows include all n-gram settings rather than select a winner after seeing results. N-gram tau is conditional on proposal-bearing turns and is not a wall-clock speedup. Recovery uses each workload\'s raw paired reused/oracle denominator, not rounded constants; cross-method/K recovery is descriptive. Nemotron has no dedicated oracle, so recovery is undefined.','', 'Training-free RMS calibration is evaluated by the frozen harness; full affine is an HF diagnostic and excluded from acceptance tables. Decoder-LoRA is an EDA/RFC-style proxy, not EDA. Data are training-set-free/self-elicited where labelled self; generic uses public prompts. The 64k extension adds Alpaca+Dolly to the existing16k and changes the source mixture. No data-free claim.','', 'FIX-24 official4k reruns and 64k generation/training/evaluation are still progressing; new immutable snapshots will add completed cells. Old official4k cells and official_vs_production contrasts remain INVALID on disk and are excluded. Valid official reuse is retained.','', 'These are pilot results, not owner-approved conclusions. Cost/timing supplements distinguish actual measurements, cross-target model predictions, and dedicated-training estimates. No timing measurements are used as acceptance counters.']
 (out/'report.md').write_text('\n'.join(notice)+'\n');print(out)
if __name__=='__main__':main()
