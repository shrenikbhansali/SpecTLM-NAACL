"""D56 mode/math response training: explicit manual audit before publication."""
import argparse,json
from pathlib import Path
from followspec.review_followup import parts,replace,publish
from followspec.rev2_launch import training_job
from followspec.rev2_p1_jobs import remove
from followspec.rev4_priority import promote
from ops.track_t import WS,DISPATCH,lines,write,sha

def checked_audit(a,digest):
 if not a.get('passed') or a.get('data_sha256')!=digest:raise ValueError('five decoded samples and masks require matching manual audit')
 return True

def specs(exp,t):
 if exp not in ['Y3b','Y10'] or exp=='Y3b' and t!=1:raise ValueError('unexpected data experiment')
 return [dict(experiment=exp,kind='train',target=t,arm=arm,data_label=label,seed=0,algorithm='eagle3',thinking=exp=='Y3b',workloads=['speed128','math500','math32-8192']) for label in (['thinking16k'] if exp=='Y3b' else ['math4k','mixed20k']) for arm in ['fc','full']]

def prepare(stage,code,sealed,t,experiment):
 # Validate all data paths BEFORE creating the immutable job stage.
 records=specs(experiment,t);metadata={}
 for label in {r['data_label'] for r in records}:
  root=sealed/label;data=root/'per_prompt.jsonl';audit=root/'manual-audit.json';checked_audit(json.loads(audit.read_text()),sha(data));metadata[label]=(data,audit,json.loads((root/'seal.json').read_text()))
 stage.mkdir(exist_ok=False);d={j['name']:j for j in lines(DISPATCH)};jobs=[];plan=[]
 for r in records:
  name=f'REV4-{experiment}-t{t}-{r["arm"]}-{r["data_label"]}-seed0';out=stage/name;data,audit,seal=metadata[r['data_label']]
  j=training_job(d[f'FIX24-official-t{t}-16k-{r["arm"]}'],name,out,code,r['arm']);o,i=parts(j)
  # Preserve whole sequences. Math data use the smallest 128-token multiple
  # admitting the longest sequence, avoiding unnecessary fixed padding.
  budget=2048 if experiment=='Y3b' else ((seal['max_sequence']-1+127)//128)*128
  for f,v in [('--data',data),('--audit',audit),('--batch-tokens',budget)]:replace(i,f,v)
  if experiment=='Y10':replace(i,'--training-attention','sdpa')
  remove(i,'--schedule-steps')
  for flag in ['--one-epoch','--export-only-final']:
   if flag not in i:i.append(flag)
  replace(o,'--prompts',data);replace(o,'--note',f'D56 {experiment}; {r["data_label"]}; nativeTTT3 oneepoch; complete sequences; audited data; final-only shared export')
  j['args']=o+['--']+i;jobs.append(j);plan.append(r|dict(name=name,run_dir=str(out)))
 write(stage/'plan.json',plan);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish-training');promote()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);p.add_argument('--sealed',type=Path,required=True);p.add_argument('--target',type=int,required=True);p.add_argument('--experiment',choices=['Y3b','Y10'],required=True);a=p.parse_args();prepare(a.stage,a.code,a.sealed,a.target,a.experiment)
