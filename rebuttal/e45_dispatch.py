"""E4/E5 dependency planning and held-out-only selection; no second GPU queue."""
import argparse,copy,fcntl,json,time,os
from pathlib import Path
import numpy as np
from rebuttal.jobs import ROOT,FROZEN,CANONICAL,job,submit
from rebuttal.dispatch_exports import write_immutable


def raw_scores(row,k=4):
 a=row['per_step_accepted'];d=row['per_step_drafted']
 if len(a)!=len(d) or any(type(x)!=int or type(y)!=int or not 0<=x<=y<=k or not y for x,y in zip(a,d)):raise ValueError('invalid raw counters')
 if not a:return None
 return 1+sum(a)/len(a),sum(x>0 for x in a)/len(a)


def choose_model(grid,records,heldout_ids):
 if len(grid)!=4 or len(records)!=4 or {x['name'] for x in grid}!=set(records):raise ValueError('incomplete LR/epoch grid')
 matrices={}
 for key,rows in records.items():
  mapping={r['prompt_id']:raw_scores(r) for r in rows}
  if len(mapping)!=len(rows) or set(mapping)!=heldout_ids:raise ValueError('selection must use exact held-out repair prompts')
  matrices[key]=mapping
 kept=sorted(k for k in heldout_ids if all(v[k] is not None for v in matrices.values()))
 if not kept:raise ValueError('no paired selection queries')
 scored=[r|{'validation_tau':float(np.mean([matrices[r['name']][k][0] for k in kept])),'validation_n':len(kept)} for r in grid]
 return sorted(scored,key=lambda r:(-r['validation_tau'],r['epochs'],r['lr']))[0]


def choose_k(records,heldout_ids):
 if set(records)!={2,3,4,5}:raise ValueError('incomplete K timing sweep')
 scores={}
 for k,data in records.items():
  if len(data['passes'])!=4:raise ValueError('expected one cold and three warm passes')
  for p in data['passes']:
   if len(p['per_prompt'])!=len(heldout_ids) or {r['prompt_id'] for r in p['per_prompt']}!=heldout_ids:raise ValueError('K selection requires the fixed held-out repair panel')
  warm=data['passes'][1:];tokens=sum(p['output_tokens'] for p in warm);seconds=sum(p['generation_wall_s'] for p in warm)
  if seconds<=0 or tokens<=0:raise ValueError('invalid timing sweep')
  scores[k]=tokens/seconds
 return {'best_k':min(scores,key=lambda k:(-scores[k],k)),'criterion':'highest aggregate warm tokens/s on fixed32 held-out repair queries; selected separately per batch; never selected on SPEED/MATH','tokens_per_s':{str(k):v for k,v in scores.items()},'n':len(heldout_ids),'processes_per_K':1,'warm_passes':3}


def read_rows(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]


def dispatch_rank(name):
 if name in ['E4_t0_reference_cache_s0','E4_t0_selection_s0']:return 0
 if name.startswith('E4') and ('selected8k' in name or 'random8k' in name):return 1
 if name.startswith('E5') and ('_student_' in name or '_validation256' in name):return 2
 return 3


def prioritize_ready(stage):
 # Only order changes. Every job identity and argument remains byte-for-byte.
 with (CANONICAL.parent/'append.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);jobs=read_rows(CANONICAL);ordered=sorted(jobs,key=lambda j:dispatch_rank(j['name']))
  if jobs==ordered:return
  stamp=str(time.time_ns());write_immutable(stage/('order-'+stamp+'.json'),{'before':[j['name'] for j in jobs],'after':[j['name'] for j in ordered],'reason':'ready E4 selection/training and E5 training before acceptance/timing sweeps; no running job interrupted'})
  temp=CANONICAL.with_name('jobs.priority-'+stamp+'.tmp');temp.write_text(''.join(json.dumps(j)+'\n' for j in ordered));os.replace(temp,CANONICAL)


def advance_offtheshelf(stage,code,student):
 jobs=[]
 for t in [0,1]:
  for k in [2,3,4,5]:
   for bench in ['speed128','math128']:
    jobs.append(eval_job(stage,code,f'E5_t{t}_offtheshelf_k{k}_{bench}_s0',t,student,'9213176726f574b556790deb65791e0c5aa438b6','draft_model',bench,k,metadata={'arm':'offtheshelf'}))
 return jobs

def completed(name):
 p=ROOT/'rebuttal/runs'/name/'metrics.json'
 return p.exists() and json.loads(p.read_text()).get('exit_code')==0


def eval_job(stage,code,name,t,export,revision,method,bench,k=4,experiment='E5',metadata=None):
 templates=ROOT/'rebuttal/ready_20261124_1504'
 template=json.loads((templates/f'E2_t{t}_interface_speed128_s0.json').read_text())
 cmd=template['command'];args=cmd[cmd.index('--target'):];args=args[:]
 def replace(key,val):args[args.index(key)+1]=str(val)
 ix=args.index('--output');del args[ix:ix+2]
 replace('--drafter',export);replace('--drafter-revision',revision);replace('--method',method);replace('--K',k)
 if isinstance(bench,Path):prompts=bench;benchmark='validation256'
 else:
  benchmark=bench
  source=json.loads((templates/f'E2_t{t}_interface_{bench}_s0.json').read_text())['command'];prompts=Path(source[source.index('--prompts')+1])
 replace('--prompts',prompts)
 if method=='draft_model':args+=['--draft-vocab-mapping']
 command=[ROOT/'.venv-atlas-031-clean/bin/python','-u','-m','atlas.frozen_baselines','--frozen-harness',FROZEN,*args]
 return job(stage,code,name,experiment,t,command,[prompts,Path(export)/'config.json'],metadata={'K':k,'benchmark':benchmark,'drafter_path':str(export),'method':method,'kind':'acceptance',**(metadata or {})})


def timing_job(stage,code,name,t,drafter,revision,method,bench,batch,rep,k=4):
 if isinstance(bench,Path):prompts=bench;benchmark='validation32'
 else:
  source=json.loads((ROOT/f'rebuttal/ready_20261124_1504/E2_t{t}_interface_{bench}_s0.json').read_text());base=source['command'];prompts=Path(base[base.index('--prompts')+1]);benchmark=bench
 target=json.loads((ROOT/f'rebuttal/inputs/target-{t}.json').read_text())
 command=[ROOT/'.venv-atlas-031-clean/bin/python','-u','-m','rebuttal.timing','--rebuttal-draft-k','--target',target['path'],'--target-revision',target['revision'],'--prompts',prompts,'--frozen-harness',FROZEN,'--batch-size',str(batch),'--replicate',str(rep),'--K',str(k),'--min-free-gb','350']
 if drafter is None:command+=['--no-speculation']
 else:command+=['--drafter',str(drafter),'--drafter-revision',revision,'--method',method]
 if method=='draft_model':command+=['--draft-vocab-mapping']
 return job(stage,code,name,'E5',t,command,[prompts]+([Path(drafter)/'config.json'] if drafter else []),metadata={'K':k,'benchmark':benchmark,'batch_size':batch,'replicate':rep,'kind':'k_selection' if isinstance(bench,Path) else 'timing','method':method})


def next_student(stage,code,t,student,lr=2e-5,epochs=1,smoke=False):
 cache=ROOT/f'rebuttal/runs/E5_t{t}_teacher_{"smoke16" if smoke else "full16k"}_s0/cell'
 name=f'E5_t{t}_student_'+('smoke2' if smoke else f'lr{lr:g}_ep{epochs}')+'_s0'
 command=[ROOT/'.venv-transport/bin/python','-u','-m','rebuttal.train_student','--cache',cache,'--model',student,'--lr',str(lr),'--epochs',str(epochs)]
 if smoke:command+=['--smoke-steps','2','--heldout','2']
 return job(stage,code,name,'E5',t,command,[cache/'manifest.json',cache/'index.jsonl',Path(student)/'config.json'],metadata={'kind':'train','lr':lr,'epochs':epochs,'smoke':smoke})


def native_training(stage,code,name,variant,data,audit,seed=0,width=None):
 source=json.loads((ROOT/'rebuttal/advance_r1_20261124_1523/E2_t0_decoder_head_lora_s0.json').read_text())
 command=source['command'].copy();ix=command.index('--output');del command[ix:ix+2]
 for key,value in [('--variant',variant),('--data',data),('--audit',audit),('--seed',seed)]:command[command.index(key)+1]=str(value)
 if width:command+=['--eda-private-width',str(width)]
 return job(stage,code,name,'E4',0,command,[data,audit,Path(command[command.index('--forbidden')+1])],seed=seed,metadata={'kind':'train','variant':variant,'private_width':width,'training_seed':seed})


def advance_eda(stage,code):
 jobs=[];reference=ROOT/'rebuttal/runs/E4_t0_reference2000_s0/cell';cache=ROOT/'rebuttal/runs/E4_t0_reference_cache_s0/cell';selection=ROOT/'rebuttal/runs/E4_t0_selection_s0/cell'
 if (reference/'manual-audit.json').exists():
  inputs=ROOT/'rebuttal/E45_inputs_20261124_1600';command=[ROOT/'.venv-transport/bin/python','-u','-m','rebuttal.teacher_cache','--target-row',ROOT/'rebuttal/inputs/target-0.json','--data',reference/'per_prompt.jsonl','--audit',reference/'manual-audit.json','--forbidden',inputs/'reference-forbidden.jsonl']
  jobs.append(job(stage,code,'E4_t0_reference_cache_s0','E4',0,command,[reference/'per_prompt.jsonl',reference/'manual-audit.json',inputs/'reference-forbidden.jsonl'],metadata={'kind':'reference_capture'}))
 candidate=ROOT/'rebuttal/runs/E5_t0_teacher_full16k_s0/cell'
 if (cache/'manifest.json').exists() and (candidate/'manifest.json').exists():
  command=[ROOT/'.venv-transport/bin/python','-u','-m','rebuttal.eda_selection','--reference-cache',cache,'--candidate-cache',candidate]
  jobs.append(job(stage,code,'E4_t0_selection_s0','E4',0,command,[cache/'manifest.json',candidate/'manifest.json'],metadata={'kind':'selection'}))
 if (selection/'results.json').exists():
  for subset in ['selected','random']:
   audit=selection/subset/'manual-audit.json';data=selection/subset/'per_prompt.jsonl'
   if not audit.exists():continue
   for seed in [0,1]:jobs.append(native_training(stage,code,f'E4b_t0_full_{subset}8k_s{seed}','full',data,audit,seed))
   if subset=='selected':
    for width in [4096,14336]:
     if not completed(f'E4_t0_train_smoke_w{width}_s0'):continue
     jobs.append(native_training(stage,code,f'E4_t0_eda_w{width}_selected8k_s0','eda_private',data,audit,width=width))
 # Evaluate all matched/E4b runs once their immutable final export is committed.
 for run in sorted((ROOT/'rebuttal/runs').glob('E4*_t0_*')):
  if 'smoke' in run.name or not completed(run.name) or not (run/'cell/parameters.json').exists():continue
  exports=sorted((run/'cell').glob('export-*'))
  for export in exports:
   if not (export/'repair_provenance.json').exists():continue
   provenance=json.loads((run/'config.yaml').read_text());variant=provenance.get('variant','unknown')
   for bench in ['speed128','math128']:
    jobs.append(eval_job(stage,code,run.name+'_'+bench,0,export,provenance['harness_commit'],'eagle3',bench,experiment='E4',metadata={'training_run':run.name,'training_seed':provenance['seed'],'variant':variant}))
 return jobs


def advance_student(stage,code,student):
 jobs=[];inputs=ROOT/'rebuttal/E45_inputs_20261124_1600'
 for t in [0,1]:
  smoke=ROOT/f'rebuttal/runs/E5_t{t}_teacher_smoke16_s0/cell'
  if (smoke/'manifest.json').exists():jobs.append(next_student(stage,code,t,student,smoke=True))
  if not completed(f'E5_t{t}_student_smoke2_s0'):continue
  cache=ROOT/f'rebuttal/runs/E5_t{t}_teacher_full16k_s0/cell'
  if not (cache/'manifest.json').exists() or not (inputs/f't{t}/training-audit.json').exists():continue
  grid=[];records={};validation=inputs/f't{t}/validation256.jsonl'
  for lr in [1e-5,2e-5]:
   for epochs in [1,3]:
    train=next_student(stage,code,t,student,lr,epochs);jobs.append(train);name=train['name'];run=ROOT/'rebuttal/runs'/name
    grid.append({'name':name,'lr':lr,'epochs':epochs})
    if not completed(name):continue
    export=run/'cell/export';provenance=json.loads((run/'config.yaml').read_text())
    valname=name+'_validation256'
    jobs.append(eval_job(stage,code,valname,t,export,provenance['harness_commit'],'draft_model',validation,metadata={'kind':'selection','training_run':name,'lr':lr,'epochs':epochs}))
    if completed(valname):records[name]=read_rows(ROOT/'rebuttal/runs'/valname/'cell/per_prompt.jsonl')
  if len(records)!=4:continue
  selected=choose_model(grid,records,{r['prompt_id'] for r in read_rows(validation)})
  selection_file=stage/f'E5_t{t}_selected.json';write_immutable(selection_file,selected|{'criterion':'paired tau on256 held-out repair prompts atK4; no SPEED/MATH selection'})
  selected_run=ROOT/'rebuttal/runs'/selected['name'];trained=selected_run/'cell/export';revision=json.loads((selected_run/'config.yaml').read_text())['harness_commit']
  panel=stage/f'E5_t{t}_K_validation32.jsonl';panel_rows=read_rows(validation)[:32]
  panel_text=''.join(json.dumps(r)+'\n' for r in panel_rows)
  if panel.exists():
   if panel.read_text()!=panel_text:raise ValueError('changed K selection panel')
  else:
   with panel.open('x') as f:f.write(panel_text)
  for arm,export,rev in [('distilled',trained,revision),('offtheshelf',student,'9213176726f574b556790deb65791e0c5aa438b6')]:
   ready={}
   for k in [2,3,4,5]:
    for bench in ['speed128','math128']:
     name=f'E5_t{t}_{arm}_k{k}_{bench}_s0'
     jobs.append(eval_job(stage,code,name,t,export,rev,'draft_model',bench,k,metadata={'arm':arm,**({'selected_training_run':selected['name']} if arm=='distilled' else {})}))
     if completed(name):ready[k,bench]=read_rows(ROOT/'rebuttal/runs'/name/'cell/per_prompt.jsonl')
   for batch in [1,8]:
    ktimes={}
    for k in [2,3,4,5]:
     name=f'E5_t{t}_Ktune_{arm}_k{k}_b{batch}'
     jobs.append(timing_job(stage,code,name,t,export,rev,'draft_model',panel,batch,0,k))
     if completed(name):ktimes[k]=json.loads((ROOT/'rebuttal/runs'/name/'cell/timing.json').read_text())
    if len(ktimes)!=4 or len(ready)!=8:continue
    choice=choose_k(ktimes,{r['prompt_id'] for r in panel_rows});write_immutable(stage/f'E5_t{t}_{arm}_b{batch}_K.json',choice)
    for bench in ['speed128','math128']:
     for rep in range(3):jobs.append(timing_job(stage,code,f'E5_t{t}_timing_{arm}_{bench}_b{batch}_r{rep}',t,export,rev,'draft_model',bench,batch,rep,choice['best_k']))
  # Retimed references live in the identical pinned environment and campaign.
  templates=ROOT/'rebuttal/preflight_20261124_exactfamily'
  gate=json.loads((ROOT/'rebuttal/advance_r1_20261124_1523/gate/results.json').read_text())
  for arm in ['none','reuse','full']:
   ref=next(x for x in gate if x['target']==t and x['arm']==('reuse' if arm=='none' else arm) and x['benchmark']=='speed128')
   cfg=json.loads((ROOT/'rebuttal/runs'/ref['name']/'cell/config.json').read_text())
   for bench in ['speed128','math128']:
    for batch in [1,8]:
     for rep in range(3):jobs.append(timing_job(stage,code,f'E5_t{t}_timing_{arm}_{bench}_b{batch}_r{rep}',t,None if arm=='none' else Path(cfg['drafter']),cfg['drafter_revision'],'eagle3',bench,batch,rep))
 return jobs


def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--code',type=Path,required=True);p.add_argument('--student',type=Path,required=True);p.add_argument('--once',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 with (a.output/'controller.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while True:
   jobs=advance_eda(a.output,a.code)+advance_student(a.output,a.code,a.student)+advance_offtheshelf(a.output,a.code,a.student)
   if jobs:submit(a.output,jobs);prioritize_ready(a.output)
   if a.once:return
   time.sleep(40)
if __name__=='__main__':main()
