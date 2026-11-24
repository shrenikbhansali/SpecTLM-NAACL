"""Independent E4/E5 raw-counter and process/batch timing reduction."""
import argparse,csv,hashlib,json,re
from collections import defaultdict
from pathlib import Path
import numpy as np
FROZEN='6da2e4265c0398ec0de5affaf23b0bd1df0be445'


def metric(row,k):
 a=row['per_step_accepted'];d=row['per_step_drafted']
 if len(a)!=len(d) or any(type(x)!=int or type(y)!=int or not 0<=x<=y<=k or y==0 for x,y in zip(a,d)):raise ValueError('invalid counters')
 return (1+sum(a)/len(a),sum(x>0 for x in a)/len(a)) if a else None


def matched_reference_rows(raw,original_prompts,panel_prompts):
 identity=lambda rr:[(r['prompt_id'],r['rendered_token_ids']) for r in rr]
 if identity(original_prompts[:len(panel_prompts)])!=identity(panel_prompts):raise ValueError('reference panel is not the identical rendered prefix')
 mapping={r['prompt_id']:r for r in raw}
 if len(mapping)!=len(raw) or set(mapping)!={r['prompt_id'] for r in original_prompts}:raise ValueError('incomplete reference raw counters')
 return [mapping[r['prompt_id']] for r in panel_prompts]


def acceptance_contrast(reference,candidate,reference_k,candidate_k):
 seeds=sorted(reference.keys()&candidate.keys())
 if not seeds:raise ValueError('no paired seeds')
 pairs=[];ids=None
 for seed in seeds:
  pair=[]
  for records,k in [(reference[seed],reference_k),(candidate[seed],candidate_k)]:
   values={r['prompt_id']:metric(r,k) for r in records}
   if len(values)!=len(records) or ids is not None and set(values)!=ids:raise ValueError('mismatched query set')
   ids=set(values);pair.append(values)
  pairs.append(pair)
 kept=sorted(i for i in ids if all(p[j][i] is not None for p in pairs for j in [0,1]))
 if not kept:raise ValueError('no valid pairs')
 values=np.array([[[p[0][i],p[1][i]] for i in kept] for p in pairs]);rng=np.random.default_rng(0)
 si=rng.integers(len(seeds),size=(10000,len(seeds)));qi=rng.integers(len(kept),size=(10000,len(kept)))
 boot=values[si[:,:,None],qi[:,None,:]].mean((1,2));mean=values.mean((0,1))
 result={'n':len(kept),'seeds':seeds,'excluded_zero_step':len(ids)-len(kept)}
 for j,label in enumerate(['tau','p1']):
  for i,arm in enumerate(['reference','candidate']):result[arm+'_'+label]=float(mean[i,j]);result[arm+'_'+label+'_ci95']=np.quantile(boot[:,i,j],[.025,.975]).tolist()
  delta=values[:,:,1,j]-values[:,:,0,j];db=delta[si[:,:,None],qi[:,None,:]].mean((1,2));result['delta_'+label]=float(delta.mean());result['delta_'+label+'_ci95']=np.quantile(db,[.025,.975]).tolist()
 return result


def gap_recovery(reuse,dedicated,candidate):
 seeds=sorted(candidate);reference=[{r['prompt_id']:metric(r,4) for r in arm} for arm in [reuse,dedicated]]
 if any(len(m)!=len(r) for m,r in zip(reference,[reuse,dedicated])) or set(reference[0])!=set(reference[1]):raise ValueError('unpaired gap references')
 maps={s:{r['prompt_id']:metric(r,4) for r in candidate[s]} for s in seeds};ids=set(reference[0])
 if not seeds or any(len(maps[s])!=len(candidate[s]) or set(maps[s])!=ids for s in seeds):raise ValueError('unpaired recovery candidates')
 kept=sorted(i for i in ids if all(m[i] is not None for m in [*reference,*maps.values()]))
 if not kept:raise ValueError('no valid recovery queries')
 values=np.array([[[reference[0][i][0],reference[1][i][0],maps[s][i][0]] for i in kept] for s in seeds])
 rng=np.random.default_rng(0);si=rng.integers(len(seeds),size=(10000,len(seeds)));qi=rng.integers(len(kept),size=(10000,len(kept)))
 boot=values[si[:,:,None],qi[:,None,:]].mean((1,2));mean=values.mean((0,1));denom=mean[1]-mean[0];bd=boot[:,1]-boot[:,0];valid=bd!=0
 ratios=(boot[valid,2]-boot[valid,0])/bd[valid]
 return {'n':len(kept),'seeds':seeds,'K':4,'excluded_zero_step':len(ids)-len(kept),'recovery':float((mean[2]-mean[0])/denom) if denom!=0 else None,'recovery_ci95':np.quantile(ratios,[.025,.975]).tolist() if len(ratios) else None,'undefined_bootstrap_samples':int((~valid).sum()),'reuse_tau':float(mean[0]),'dedicated_tau':float(mean[1]),'candidate_tau':float(mean[2]),'definition':'(candidate tau - reuse tau)/(dedicated tau - reuse tau); ratio recomputed within each shared seed/query resample; K4 only'}


def pair_seed_records(left_name,left,right_name,right):
 # A fixed released reference has no training-seed variation. Reuse the same
 # query observations for each trained seed, never invent a learned seed.
 if left_name.startswith('reference_') and not right_name.startswith('reference_'):
  if set(left)!={0}:raise ValueError('expected one fixed reference')
  return {s:left[0] for s in right},right
 if right_name.startswith('reference_') and not left_name.startswith('reference_'):
  if set(right)!={0}:raise ValueError('expected one fixed reference')
  return left,{s:right[0] for s in left}
 shared=left.keys()&right.keys()
 return {s:left[s] for s in shared},{s:right[s] for s in shared}


def timing_contrast(candidate,reference):
 if len(candidate)!=3 or len(reference)!=3:raise ValueError('three fresh processes per arm required')
 arrays=[[],[],[],[]];startup=[[],[]];mismatch=[]
 for arm,ref in zip(candidate,reference):
  for key in ['prompt_sha256','target_revision','batch_size','max_new_tokens','seed','max_model_len','temperature','gpu_memory_utilization']:
   if arm['config'].get(key)!=ref['config'].get(key):raise ValueError('unmatched timing '+key)
  acc=[[],[],[],[]];mm=[]
  if len(arm['timing']['passes'])!=4 or len(ref['timing']['passes'])!=4:raise ValueError('one cold and three warm passes required')
  for a,b in zip(arm['timing']['passes'],ref['timing']['passes']):
   if [x['prompt_ids'] for x in a['batches']]!=[x['prompt_ids'] for x in b['batches']]:raise ValueError('unpaired timing batches')
   am={r['prompt_id']:r['completion_token_ids'] for r in a['per_prompt']};bm={r['prompt_id']:r['completion_token_ids'] for r in b['per_prompt']}
   if am.keys()!=bm.keys():raise ValueError('unpaired timing queries')
   acc[0].append([r['wall_s'] for r in a['batches']]);acc[1].append([r['wall_s'] for r in b['batches']]);acc[2].append([sum(len(am[q]) for q in r['prompt_ids']) for r in a['batches']]);acc[3].append([sum(len(bm[q]) for q in r['prompt_ids']) for r in b['batches']]);mm.append(sum(am[k]!=bm[k] for k in am))
  for dest,values in zip(arrays,acc):dest.append(values)
  startup[0].append(arm['timing']['startup_s']);startup[1].append(ref['timing']['startup_s']);mismatch.append(mm)
 arrays=list(map(np.asarray,arrays));rng=np.random.default_rng(0);pi=rng.integers(3,size=(10000,3));bi=rng.integers(arrays[0].shape[-1],size=(10000,arrays[0].shape[-1]));result={'processes':3,'warm_passes_per_process':3,'output_mismatch_by_process_pass':mismatch}
 for name,passes in [('cold',[0]),('warm',[1,2,3])]:
  a,b,at,bt=[x[:,passes,:].mean(1) for x in arrays];aa,bb,att,btt=[x[pi[:,:,None],bi[:,None,:]].sum(2).mean(1) for x in [a,b,at,bt]]
  result[name]={'panel_speedup':float(b.sum()/a.sum()),'panel_ci95':np.quantile(bb/aa,[.025,.975]).tolist(),'token_speedup':float((at.sum()/a.sum())/(bt.sum()/b.sum())),'token_ci95':np.quantile((att/aa)/(btt/bb),[.025,.975]).tolist(),'candidate_panel_s':float(a.sum(1).mean()),'reference_panel_s':float(b.sum(1).mean()),'candidate_tokens':float(at.sum(1).mean()),'reference_tokens':float(bt.sum(1).mean())}
  if name=='cold':result[name]['startup_inclusive_speedup']=float((b.sum(1)+startup[1]).mean()/(a.sum(1)+startup[0]).mean());result[name]['startup_inclusive_ci95']=np.quantile((bb+np.array(startup[1])[pi].mean(1))/(aa+np.array(startup[0])[pi].mean(1)),[.025,.975]).tolist()
 return result


def rows(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csv_write(path,records):
 fields=list(dict.fromkeys(k for r in records for k in r)) or ['status']
 with path.open('x',newline='') as f:
  writer=csv.DictWriter(f,fields);writer.writeheader();writer.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in records)


def reference_records(root):
 result=[];gate=json.loads((root/'rebuttal/advance_r1_20261124_1523/gate/results.json').read_text())
 for entry in gate:
  if entry['status']!='pass':raise ValueError('failed acceptance reference')
  run=root/'rebuttal/runs'/entry['name'];cell=run/'cell';cfg=json.loads((cell/'config.json').read_text());t=entry['target']
  bench='speed128' if entry['benchmark']=='speed128' else 'math128'
  if cfg['code_commit']!=FROZEN or cfg['engine_version']!='0.31.0' or cfg['seed']!=0 or cfg['max_new_tokens']!=512 or cfg['batch_size']!=8 or cfg['temperature']!=0:raise ValueError('changed reference protocol')
  if sha(cell/'per_prompt.jsonl')!=entry['raw_sha256'] or sha(cfg['prompts'])!=cfg['prompt_sha256']:raise ValueError('reference evidence changed')
  plan=json.loads((root/f'rebuttal/ready_20261124_1504/E2_t{t}_interface_{bench}_s0.json').read_text());cmd=plan['command'];panel=Path(cmd[cmd.index('--prompts')+1]);prompts=rows(panel)
  data=matched_reference_rows(rows(cell/'per_prompt.jsonl'),rows(cfg['prompts']),prompts);stat=acceptance_contrast({0:data},{0:data},4,4)
  for exp in ['E4','E5']:
   result.append({'experiment':exp,'target':t,'benchmark':bench,'run':run.name,'training_run':None,'seed':0,'K':4,'kind':'acceptance','variant':'reference_'+entry['arm'],'n':stat['n'],'tau':stat['candidate_tau'],'tau_ci95':stat['candidate_tau_ci95'],'p1':stat['candidate_p1'],'p1_ci95':stat['candidate_p1_ci95'],'prompt_sha256':sha(panel),'raw_sha256':sha(cell/'per_prompt.jsonl'),'subset_prompt_ids':[r['prompt_id'] for r in prompts],'source_n':cfg['n'],'reference_proof':'identical rendered prefix of completed current-campaign gate cell; raw/config hashes verified'})
 return result


def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=False)
 acceptance=[];timings={};sources=[];costs=defaultdict(float);run_costs=[];pending=[];failed=[];latency=[]
 for run in sorted((a.workspace/'rebuttal/runs').iterdir()):
  if not run.name.startswith(('E4','E5')) or not (run/'config.yaml').exists():continue
  cfg=json.loads((run/'config.yaml').read_text());exp=cfg['experiment'];meta=run/'metrics.json'
  if not meta.exists():pending.append(run.name);continue
  result=json.loads(meta.read_text());costs[exp]+=result['gpu_hours'];run_costs.append({'run':run.name,'experiment':exp,'target':cfg.get('target'),'kind':cfg.get('kind'),'gpu_h':result['gpu_hours'],'status':result['status']})
  if result['exit_code']!=0:failed.append({'run':run.name,'status':result['status']});continue
  cell=run/'cell'
  if cfg.get('smoke') or 'smoke' in run.name:continue
  if (cell/'per_prompt.jsonl').exists() and cfg.get('kind') in ['acceptance','selection']:
   c=json.loads((cell/'config.json').read_text())
   if c.get('frozen_harness_commit',c.get('code_commit'))!=FROZEN or c['engine_version']!='0.31.0':raise ValueError('nonfrozen acceptance')
   if c['seed']!=0 or c['max_new_tokens']!=512 or c['batch_size']!=8:raise ValueError('changed acceptance protocol')
   data=rows(cell/'per_prompt.jsonl');s=cfg.get('training_seed',0);stats=acceptance_contrast({s:data},{s:data},c['K'],c['K'])
   record={'experiment':exp,'target':cfg['target'],'benchmark':cfg.get('benchmark'),'run':run.name,'training_run':cfg.get('training_run',cfg.get('selected_training_run')),'seed':s,'K':c['K'],'kind':cfg['kind'],'n':stats['n'],'p1':stats['candidate_p1'],'p1_ci95':stats['candidate_p1_ci95'],'tau':stats['candidate_tau'],'tau_ci95':stats['candidate_tau_ci95'],'prompt_sha256':c['prompt_sha256'],'raw_sha256':sha(cell/'per_prompt.jsonl')}
   record['variant']=re.sub(r'_s[0-9]+$','',record['training_run'] or record['run']) if exp=='E4' else cfg.get('arm',cfg.get('training_run',record['run']))+'_k'+str(c['K'])
   if record['training_run']:
    t=a.workspace/'rebuttal/runs'/record['training_run'];tc=json.loads((t/'config.yaml').read_text());record.update(lr=tc.get('lr'),epochs=tc.get('epochs'),train_gpu_h=json.loads((t/'metrics.json').read_text())['gpu_hours'])
    if exp=='E5':
     teacher=a.workspace/f"rebuttal/runs/E5_t{cfg['target']}_teacher_full16k_s0/metrics.json"
     record['teacher_gpu_h']=json.loads(teacher.read_text())['gpu_hours']
    if (t/'cell/parameters.json').exists():pr=json.loads((t/'cell/parameters.json').read_text());record.update(trainable_params=pr['trainable_parameters'],added_params=pr.get('added_parameters',0))
   acceptance.append(record);sources.append({'run':run.name,'raw_sha256':record['raw_sha256']})
  if (cell/'timing.json').exists() and cfg.get('kind')=='timing':
   c=json.loads((cell/'config.json').read_text());v=json.loads((cell/'timing.json').read_text())
   if c['harness_commit']!=FROZEN or c['engine_version']!='0.31.0' or c['gpu_type']!='NVIDIA A40':raise ValueError('nonfrozen timing')
   arm=run.name.split('_timing_',1)[1].split('_',1)[0];key=(cfg['target'],cfg['benchmark'],cfg['batch_size'])
   timings.setdefault(key,{})[arm,cfg['replicate']]={'config':c,'timing':v,'path':str(cell),'sha256':sha(cell/'timing.json')}
  if cfg.get('kind')=='latency':latency+=json.loads((cell/'results.json').read_text())['records']
 acceptance+=reference_records(a.workspace)
 paired=[];recoveries=[]
 # Every reported comparison has matching rendered prompt-file hashes and query IDs.
 groups=defaultdict(dict)
 for r in acceptance:
  if r['kind']!='acceptance':continue
  groups[r['experiment'],r['target'],r['benchmark']].setdefault(r['variant'],{})[r['seed']]=r
 for group,arms in groups.items():
  keys=sorted(arms)
  for ai,left in enumerate(keys):
   for right in keys[ai+1:]:
    lr,rr=pair_seed_records(left,arms[left],right,arms[right]);ss=sorted(lr)
    if not ss:continue
    if any(lr[s]['prompt_sha256']!=rr[s]['prompt_sha256'] for s in ss):raise ValueError('unpaired prompt render')
    def load(records):
     result={}
     for seed,r in records.items():
      data=rows(a.workspace/'rebuttal/runs'/r['run']/'cell/per_prompt.jsonl')
      if 'subset_prompt_ids' in r:
       byid={x['prompt_id']:x for x in data};data=[byid[x] for x in r['subset_prompt_ids']]
      result[seed]=data
     return result
    result=acceptance_contrast(load(lr),load(rr),lr[ss[0]]['K'],rr[ss[0]]['K']);paired.append({'experiment':group[0],'target':group[1],'benchmark':group[2],'reference':left,'candidate':right,**result})
  if group[1]==0 and 'reference_reuse' in arms and 'reference_dedicated' in arms:
   for name,records in arms.items():
    if name.startswith('reference_') or any(r['K']!=4 for r in records.values()):continue
    hashes={r['prompt_sha256'] for rr in [records,arms['reference_reuse'],arms['reference_dedicated']] for r in rr.values()}
    if len(hashes)!=1:raise ValueError('unmatched recovery prompt IDs')
    rec=gap_recovery(load(arms['reference_reuse'])[0],load(arms['reference_dedicated'])[0],load(records))
    recoveries.append({'experiment':group[0],'target':0,'benchmark':group[2],'variant':name,**rec})
 timed=[]
 for key,cells in timings.items():
  for arm in sorted({x[0] for x in cells}-{'none'}):
   for ref in ['none','reuse','full']:
    if arm==ref or any((x,i) not in cells for x in [arm,ref] for i in range(3)):continue
    result=timing_contrast([cells[arm,i] for i in range(3)],[cells[ref,i] for i in range(3)])
    timed.append({'target':key[0],'benchmark':key[1],'batch':key[2],'arm':arm,'reference':ref,**result})
 for exp in ['E4','E5']:
  dest=out/exp;dest.mkdir();csv_write(dest/('results.csv' if exp=='E4' else 'sweep.csv'),[r for r in acceptance if r['experiment']==exp]);csv_write(dest/('latency.csv' if exp=='E4' else 'timing.csv'),latency if exp=='E4' else timed)
 (out/'results.json').write_text(json.dumps({'status':'pilot','acceptance':acceptance,'paired':paired,'recoveries':recoveries,'timing':timed,'latency':latency,'gpu_hours_completed_including_failures':dict(costs),'completed_run_costs':run_costs,'pending':pending,'failed':failed,'sources':sources,'uncertainty':'10000 paired query/seed or process/prompt-batch resamples; repeats averaged within process'},indent=2)+'\n')
 print(json.dumps({'acceptance_cells':len(acceptance),'timing_contrasts':len(timed),'pending':pending,'failed':failed}))
if __name__=='__main__':main()
