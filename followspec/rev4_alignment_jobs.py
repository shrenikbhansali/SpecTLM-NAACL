"""D56 Y8 paired training-only feature fits and frozen exported-map evaluations."""
import argparse,copy,json,time
from pathlib import Path
from followspec.review_followup import parts,replace,publish
from followspec.rev2_launch import NODES
from followspec.rev4_train import eval_for
from ops.track_t import WS,DISPATCH,lines,write

def prepare(stage,code):
 stage.mkdir(exist_ok=False);d={r['name']:r for r in lines(DISPATCH)};jobs=[];records=[]
 for t in [0,1]:
  name=f'REV4-Y8-t{t}-linearfit';out=stage/name;j=copy.deepcopy(d['P3-D46-calibration-self-0355']);o,i=parts(j);i[i.index('followspec.calibration')]='followspec.linear_alignment';oo,ii=parts(d[f'FIX24-official-t{t}-16k-fc']);target=json.loads(Path(ii[ii.index('--target-row')+1]).read_text())
  for f in ['--data','--audit','--drafter']:replace(i,f,ii[ii.index(f)+1])
  for f,v in [('--child',target['path']),('--output',out),('--count',4000),('--min-free-gb',350)]:replace(i,f,v)
  for f,v in [('--tag',name),('--code-repo',code),('--target',target['path']),('--target-rev',target['revision']),('--prompts',ii[ii.index('--data')+1]),('--drafter-model',ii[ii.index('--drafter')+1]),('--drafter-rev',Path(ii[ii.index('--drafter')+1]).name),('--note','D56 Y8 fp64 paired per-tap LS/orthogonal Procrustes; first4k training responses; FIX24 init; no optimizer')]:replace(o,f,v)
  j.update(name=name,args=o+['--']+i,allowed_nodes=NODES);jobs.append(j);records.append(dict(experiment='Y8',kind='fit',target=t,seed=0,algorithm='eagle3',name=name,run_dir=str(out)))
 write(stage/'plan.json',records);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish')

def sweep(stage):
 d={r['name']:r for r in lines(DISPATCH)};pending=0
 for r in json.loads((stage/'plan.json').read_text()):
  root=Path(r['run_dir']);dest=stage/('publish-eval-'+r['name'])
  if (dest/'published.json').exists():continue
  if not (root/'results.json').exists():pending+=1;continue
  res=json.loads((root/'results.json').read_text());cfg=json.loads((root/'config.json').read_text());jobs=[];records=[]
  for arm,export in res['exports'].items():
   for w in ['speed128','math500']:
    j,rr=eval_for(d,stage,r|dict(arm=arm,name=r['name']+'-'+arm),export,cfg['code_commit'],w);jobs.append(j);records.append(rr)
  write(stage/('final-plan-'+r['name']+'.json'),records);publish(jobs,dest)
 return pending
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','watch']);p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path);a=p.parse_args()
 if a.action=='prepare':prepare(a.stage,a.code)
 else:
  while True:
   n=sweep(a.stage);print('Y8 fits pending',n,flush=True)
   if not n:break
   time.sleep(30)
