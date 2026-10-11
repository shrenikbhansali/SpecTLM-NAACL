"""D56 established training/export paths. One epoch, final shared exports only."""
import argparse,copy,json,time
from pathlib import Path
from followspec.rev4_jobs import source_eagle,make_timing
from followspec.rev3_x5 import panel,publication_complete
from followspec.rev2_launch import training_job,NODES
from followspec.rev2_panels import eval_job
from followspec.rev2_p1_jobs import remove
from followspec.review_followup import parts,replace,publish
from ops.track_t import WS,DISPATCH,lines,write
QWEN=Path('/home/heck2/sbhansali8/HFcache/hub/models--z-lab--Qwen3-8B-DFlash-b16/snapshots/9b41424b7109f9c5413454f481b09a82b85333f4')

def initial_specs():
 rows=[]
 for exp,t,labels,seeds in [('Y4',2,['generic16k'],[0]),('Y6',0,['generic520','generic64k'],[0]),('Y7',0,['parent16k'],[0]),('Y5',1,['generic16k'],[1,2])]:
  for label in labels:
   for s in seeds:
    for arm in ['fc','full']:rows.append(dict(experiment=exp,kind='train',target=t,arm=arm,data_label=label,seed=s,workloads=['speed128','math500']+(['math32-8192'] if exp=='Y5' else []),algorithm='dflash' if exp in ['Y4','Y5'] else 'eagle3'))
 return rows

def prompt_path(d,t,w,thinking=False):
 if thinking:return WS/f'artifacts/REV4_P0_20261011_0240/panels/t1-thinking-{w}.jsonl'
 if t!=2:return panel(t,w,d)
 if w=='math500':return WS/'artifacts/REV2_panels_20261010_0430_v2/math500-t2.jsonl'
 _,i=parts(d['REV2-E12-t2-full-generic16k-speed128']);return Path(i[i.index('--prompts')+1])

def replace_drafter(j,path,rev,method=None,k=None):
 o,i=parts(j)
 for a,f,g in [(o,'--drafter-model','--drafter-rev'),(i,'--drafter','--drafter-revision')]:replace(a,f,path);replace(a,g,rev)
 if method:
  replace(o,'--drafter',method);replace(i,'--method',method);replace(o,'--k',k);replace(i,'--K',k)
 j['args']=o+['--']+i;return j

def eval_for(d,stage,r,drafter,revision,w):
 from followspec.rev4_recovery import descendant_record
 r=descendant_record(r)
 t=r['target'];name=r['name']+'-'+w;out=stage/'eval'/name;src=d['REV2-E12-t2-full-generic16k-speed128'] if t==2 else source_eagle(d,t,'reuse',w)
 prompts=prompt_path(d,t,w,r.get('thinking',False));j=eval_job(src,name,out,prompts);j=replace_drafter(j,drafter,revision,r['algorithm'],16 if r['algorithm']=='dflash' and t==2 else 10 if r['algorithm']=='dflash' else 4);o,i=parts(j)
 replace(i,'--max-new-tokens',8192 if w=='math32-8192' else 512);replace(i,'--max-model-len',12288 if w=='math32-8192' else 4096);j['args']=o+['--']+i
 return j,r|dict(kind='eval',workload=w,name=name,run_dir=str(out),training_dir=r.get('run_dir'),n=32 if w.startswith('math32') else 500 if w=='math500' else 128)

def timed(d,stage,code,r,drafter,rev,arms=None,w='speed128'):
 from followspec.rev4_recovery import descendant_record
 r=descendant_record(r)
 t=r['target'];jobs=[];rows=[];arms=arms or [r['arm']]
 for arm in arms:
  for b in ([1,8] if r['experiment']=='Y4' else [1]):
   for rep in range(3):
    src=d[f'REV2-E12-t2-timing-{ "full" if arm not in ["none","reuse"] else arm}-b{b}-r{rep}'] if t==2 else d[f'D52-timing-'+('r1' if t==0 else 'nemo')+f'-'+('none' if arm=='none' else 'official-reused')+f'-b{b}-r{rep}']
    prompts=prompt_path(d,t,w,r.get('thinking',False))
    if r.get('thinking') and w=='math500':prompts=WS/'artifacts/REV4_P0_20261011_0240/panels/t1-thinking-math128.jsonl'
    name=r['name']+f'-{arm}-{w}-timing-b{b}-r{rep}';out=stage/'timing'/name;j=make_timing(src,name,out,prompts,code,b)
    if arm!='none':j=replace_drafter(j,drafter,rev,r['algorithm'],16 if t==2 and r['algorithm']=='dflash' else 10 if r['algorithm']=='dflash' else 4)
    jobs.append(j);rows.append(r|dict(kind='timing',workload=w,name=name,run_dir=str(out),arm=arm,batch=b,replicate=rep,n=128))
 return jobs,rows

def prepare(stage,code):
 stage.mkdir(exist_ok=False);d={r['name']:r for r in lines(DISPATCH)};jobs=[];records=[]
 for r in initial_specs():
  exp,t,arm,s=r['experiment'],r['target'],r['arm'],r['seed'];name=f'REV4-{exp}-t{t}-{arm}-{r["data_label"]}-seed{s}';out=stage/name
  src=d['REV3-X5-t0-'+arm+'-seed0'] if exp=='Y4' else d['REV3-X5-t1-'+arm+'-seed0'] if exp=='Y5' else d[f'FIX24-official-t{t}-16k-{arm}']
  j=training_job(src,name,out,code,arm,seed=s);o,i=parts(j);remove(i,'--schedule-steps')
  for flag in ['--one-epoch','--export-only-final']:
   if flag not in i:i.append(flag)
  if exp=='Y4':
   _,q=parts(d['REV2-E12-t2-fc-generic16k']);target=json.loads(Path(q[q.index('--target-row')+1]).read_text())
   for f,v in [('--base','qwen3'),('--target',target['path']),('--target-rev',target['revision']),('--drafter-model',QWEN),('--drafter-rev',QWEN.name)]:replace(o,f,v)
   for f in ['--target-row','--data','--audit']:replace(i,f,q[q.index(f)+1])
   replace(i,'--drafter',QWEN)
  if exp=='Y6':
   _,q=parts(d['P3-train-0-generic-fc-0325' if r['data_label']=='generic520' else 'E5c-generic64k-fc'])
   for f in ['--data','--audit']:replace(i,f,q[q.index(f)+1])
  if exp=='Y7':
   parent=stage/'parent.json'
   if not parent.exists():
    p=Path('/home/heck2/sbhansali8/HFcache/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659');write(parent,dict(id='meta-llama/Llama-3.1-8B-Instruct',revision=p.name,path=str(p)))
   replace(i,'--supervision-row',parent)
  replace(o,'--prompts',i[i.index('--data')+1]);replace(o,'--note',f'D56 {exp}; {r["data_label"]}; native objective,one epoch,final-only shared export; source-mixture Alpaca+Dolly if64k')
  j['args']=o+['--']+i;jobs.append(j);records.append(r|dict(name=name,run_dir=str(out)))
 write(stage/'plan.json',records);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish-training')
 # Explicit Qwen DFlash reference uses exactly the E12 target renders.
 r=dict(experiment='Y4',kind='eval',target=2,arm='reuse',seed=0,algorithm='dflash',name='REV4-Y4-t2-reuse');jobs=[];refs=[]
 for w in ['speed128','math500']:
  j,rr=eval_for(d,stage,r,QWEN,QWEN.name,w);jobs.append(j);refs.append(rr)
 jj,rr=timed(d,stage,code,r,QWEN,QWEN.name,arms=['none','reuse']);jobs+=jj;refs+=rr;write(stage/'control-plan.json',refs);publish(jobs,stage/'publish-controls')

def sweep(stage,code):
 d={r['name']:r for r in lines(DISPATCH)};pending=0
 for r in json.loads((stage/'plan.json').read_text()):
  if r['kind']!='train':continue
  dest=stage/('publish-final-'+r['name']);root=Path(r['run_dir'])
  if publication_complete(dest):continue
  if not (root/'results.json').exists():pending+=1;continue
  result=json.loads((root/'results.json').read_text());cfg=json.loads((root/'config.json').read_text());assert result['n']==cfg['n'] and result['steps']==cfg['steps'];export=Path(result['exports'][-1]);assert (export/'repair_provenance.json').exists();jobs=[];records=[]
  for w in r['workloads']:
   j,rr=eval_for(d,stage,r,export,cfg['code_commit'],w);jobs.append(j);records.append(rr)
  if r['experiment']=='Y4' or r['experiment']=='Y6' and r['data_label']=='generic64k':
   jj,rr=timed(d,stage,code,r,export,cfg['code_commit']);jobs+=jj;records+=rr
  if r['experiment']=='Y3b':
   for w in ['speed128','math500']:
    jj,rr=timed(d,stage,code,r,export,cfg['code_commit'],w=w);jobs+=jj;records+=rr
  plan=stage/('final-plan-'+r['name']+'.json')
  if plan.exists():
   if json.loads(plan.read_text())!=records:raise ValueError('immutable export plan changed: '+str(plan))
  else:write(plan,records)
  publish(jobs,dest)
  from followspec.rev4_priority import promote
  promote()
 return pending

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','watch']);p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);a=p.parse_args()
 if a.action=='prepare':prepare(a.stage,a.code)
 else:
  while True:
   try:n=sweep(a.stage,a.code)
   except RuntimeError as e:
    if 'free disk' not in str(e):raise
    print('P1 publication held by disk guard:',e,flush=True);time.sleep(60);continue
   print('P1 pending',n,flush=True)
   if not n:break
   time.sleep(30)
