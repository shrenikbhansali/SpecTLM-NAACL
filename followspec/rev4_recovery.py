"""Explicit immutable retries of D56 jobs stopped by the disk guard."""
import argparse,copy,json
from pathlib import Path
from followspec.review_followup import parts,replace,publish
from ops.track_t import WS,DISPATCH,lines,write

def finished():
 launched={};done={};events={}
 for e in lines(WS/'artifacts/M2_D28_20261006/response_queue.log'):
  if e['event']=='launched':launched[e['out_dir']]=e['name']
  elif e['event']=='finished' and e['out_dir'] in launched:
   name=launched[e['out_dir']];done[name]=str(e['exit']);events[name]=e
 return done,events

def active_attempts(rows,done):
 active={r['name']:r for r in rows};original=dict(active)
 for r in rows:
  old=r.get('replaces_job')
  if not old:continue
  if old not in active or done.get(old) in [None,'0']:raise ValueError('replacement needs one recorded failed attempt: '+old)
  for field in ['experiment','kind','target','arm','seed','data_label','workload','batch','replicate']:
   if r.get(field)!=original[old].get(field):raise ValueError('replacement changes '+field)
  del active[old]
 return list(active.values())

def retry_job(source,record,stage):
 j=copy.deepcopy(source);name=record['name']+'-diskretry1';out=stage/name;o,i=parts(j)
 replace(o,'--tag',name);replace(i,'--output',out)
 j.update(name=name,args=o+['--']+i)
 return j,record|dict(name=name,run_dir=str(out),replaces_job=record['name'],recovery='D56 disk-floor interruption; exact same pinned command except tag/output; restart from original initialization')

def prepare(stage):
 from followspec.rev4_results import inventory
 done,events=finished();d={j['name']:j for j in lines(DISPATCH)};rows=inventory();jobs=[];records=[];proof=[]
 if stage.exists():raise ValueError('immutable retry stage exists')
 for r in rows:
  if done.get(r['name']) in [None,'0']:continue
  e=events[r['name']];log=Path(e['out_dir'])/'launch.log'
  if 'free disk' not in log.read_text() or 'below required 350 GB' not in log.read_text():raise ValueError('not disk-guard failure: '+r['name'])
  if (Path(r['run_dir'])/'results.json').exists():raise ValueError('completed output cannot be retried')
  j,rr=retry_job(d[r['name']],r,stage)
  if j['name'] in d:raise ValueError('retry already dispatched')
  jobs.append(j);records.append(rr);proof.append(dict(failed_job=r['name'],failed_launcher=e['out_dir'],failed_output=r['run_dir'],replacement=j['name'],scientific_settings_unchanged=True))
 if len(jobs)!=10:raise ValueError('expected exactly ten audited disk failures')
 stage.mkdir();write(stage/'plan.json',records);write(stage/'jobs.json',jobs);write(stage/'recovery-proof.json',proof);publish(jobs,stage/'publish-retries')
 from followspec.rev4_priority import promote
 promote()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);a=p.parse_args();prepare(a.stage)
