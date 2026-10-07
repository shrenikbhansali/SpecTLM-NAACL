"""D-39 operational handoff; all evaluations/statistics come from frozen code."""
import argparse
import copy
import fcntl
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import time
from ops.method_recovery import (read,lines,sha,write,frozen_modules,preflight,append_jobs,
                                retry_plan,apply_overlay)


def identity(r):return tuple(r[k] for k in ('arm','seed','derivative_id','workload','K','cell'))


def reuse_controls(records,reference):
    old={identity(r):r for r in reference};result=[]
    if len(old)!=len(reference):raise ValueError('duplicate reference')
    for r in records:
        if r['arm']=='FS':result.append(r);continue
        prev=old.get(identity(r))
        if prev is None:raise ValueError('missing reference control')
        wanted=list(r['argv']);wanted[wanted.index('--output')+1]=prev['argv'][prev['argv'].index('--output')+1]
        di=wanted.index('--drafter')+1;old_drafter=prev['argv'][prev['argv'].index('--drafter')+1]
        if wanted[di]!=old_drafter:
            def files(path):
                root=Path(path)
                if not root.is_dir():raise ValueError('reused checkpoint missing')
                return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}
            if files(wanted[di])!=files(old_drafter):raise ValueError('reused checkpoint differs')
            wanted[di]=old_drafter
        if wanted!=prev['argv']:raise ValueError('reused controls differ')
        result.append(copy.deepcopy(prev))
    return result


def sealed(run,steps):
    run=Path(run)
    if list(run.glob('failure*.json')):raise ValueError(f'training failed: {run}')
    ck=run/'checkpoints/0';seal=ck.parent/'epoch0_end'
    if not (ck/'training_state.json').is_file() or not seal.is_symlink():return False
    state=read(ck/'training_state.json')
    if seal.resolve()!=ck.resolve() or (state.get('epoch'),state.get('global_step'),state.get('local_step'))!=(0,steps,0):
        raise ValueError('checkpoint budget/seal differs')
    return True


def watch(a):
    code=Path(a.frozen_code).resolve();m=frozen_modules(code,a.frozen_commit)
    checked=m['followspec.production_pipeline'].checked_stage
    campaign,cfg=checked(a.campaign)
    if cfg.get('decision_id')!='D-39':raise ValueError('D-39 campaign required')
    reference,rcfg=checked(a.reference)
    reference_records=read(a.reference_index) if a.reference_index else read(reference/'index_k4.json')
    # Frozen and three control cells must already exist and independently validate.
    controls=[r for r in reference_records if r['arm']!='FS']
    m['followspec.evaluate'].load_measurements(controls)
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    handle=(campaign/a.lock_name).open('a+');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.chdir(code)
    write(out/'config.json',vars(a)|dict(operation_source_sha256=sha(__file__),campaign_sha256=sha(campaign/'stage_files.json'),
        frozen_sources_sha256={k:sha(v.__file__) for k,v in m.items()}))
    states={};done=set()
    def event(**row):
        with (out/'events.jsonl').open('a') as f:f.write(json.dumps(row|dict(time=datetime.now(timezone.utc).isoformat()))+'\n')
    event(event='waiting',variants=cfg['variants'])
    while True:
        for v in cfg['variants']:
            label=v['label']
            if label in done:continue
            training,tcfg=checked(v['training'])
            fs=next(j for j in lines(training/'jobs.jsonl') if '--ablation-decision' in j['args'])
            cmd=fs['args'][fs['args'].index('--')+1:];run=Path(cmd[cmd.index('--output')+1])
            expected=read(Path(tcfg['finalized'])/'FS/training_config.json')
            if label not in states:
                if not sealed(run,expected['optimizer_steps']):continue
                stage=out/label/'evaluation'
                m['followspec.evaluation_jobs'].evaluation_jobs(training,a.targets,stage,python=a.python,code_repo=code,
                    completed_only=True,allow_validation_pending=True,training_seeds=[0],reuse_frozen=reference,job_prefix='m5-d39-l'+label)
                if not read(stage/'results.json')['checkpoints_ready']:raise ValueError('reused controls unexpectedly incomplete')
                records=reuse_controls(read(stage/'index_k4.json'),reference_records)
                ids={r['run_id'] for r in records if r['arm']=='FS'}
                jobs=[j for j in lines(stage/'jobs.jsonl') if j['name'] in ids]
                preflight(jobs,code,out/label/'preflight')
                states[label]=dict(records=records,jobs={j['name']:j for j in jobs},overlays={},blocked={},stage=stage)
                write(out/label/'effective_index_k4.json',records)
                event(event='handoff',label=label,n_new_jobs=append_jobs(a.dispatch_jobs,jobs),stage=str(stage))
            state=states[label];records=state['records'];overlays=state['overlays']
            # Idempotent reconciliation protects against another approved controller appending concurrently.
            append_jobs(a.dispatch_jobs,[*state['jobs'].values(),*[o['job'] for o in overlays.values()]])
            launches={e['name']:e for e in lines(a.queue_log) if e.get('event')=='launched'}
            for r in records:
                if r['arm']!='FS':continue
                original=r['run_id'];active=overlays.get(original,{}).get('record',r)
                if not (Path(active['run_dir'])/'failure.json').exists() or original in state['blocked']:continue
                launch=launches.get(active['run_id'])
                if not launch or not (Path(launch['out_dir'])/'exit_code').is_file():continue
                try:
                    rr,jj,proof=retry_plan(active,state['jobs'][original],launch['out_dir'],out/label/'retries',
                        attempt=2 if original in overlays else 1,expected_prompt_sha=sha(r['prompt_file']),expected_source_sha=sha(code/'atlas/run_cell.py'))
                    preflight([jj],code,out/label/('preflight-'+rr['run_id']))
                    overlays[original]=dict(record=rr,job=jj,proof=proof)
                    write(out/label/('overlay-'+original+'.json'),overlays[original]);append_jobs(a.dispatch_jobs,[jj])
                    event(event='collision_retry',label=label,original=original,retry=rr['run_id'])
                except ValueError as e:
                    state['blocked'][original]=str(e);event(event='cell_blocked',label=label,original=original,reason=str(e))
            effective=apply_overlay(records,overlays)
            if any(not (Path(r['run_dir'])/'results.json').is_file() for r in effective):continue
            result=m['followspec.pilot_report'].summarize(m['followspec.evaluate'].load_measurements(effective))
            result.update(decision_id='D-39',fs_delta_lambda=v['value'],scope='Exploratory lambda development comparison; all variants retained. Fresh confirmation required after selection.',
                validation_pending_at_handoff=read(state['stage']/'results.json').get('validation_pending',[]))
            target_rows=read(a.targets)['targets']
            if any('target_training_steps' in t for t in target_rows):
                result['uncertainty']='Update strengths share target training trajectories. Model-level bootstrap intervals suppressed; use per-condition paired prompt uncertainty in the stress report.'
                result['n_independent_training_trajectories']=len({t['domain'] for t in target_rows if t['model_id']!='base'})
                for workload in result['workloads']:
                    for comparison in workload['comparisons'].values():comparison['ci95_targets_conditional_on_seed']=None
            report=out/label/'report';report.mkdir();write(report/'index_k4.json',effective)
            config=dict(decision_id='D-39',fs_delta_lambda=v['value'],frozen_commit=a.frozen_commit,training=str(training),
                inputs_sha256={str(Path(r['run_dir'])/n):sha(Path(r['run_dir'])/n) for r in effective for n in ('config.json','results.json','per_prompt.jsonl')})
            write(report/'config.json',config);write(report/'results.json',result)
            write(report/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title='D-39 lambda '+str(v['value']),landed=str(datetime.now().date()),status='pilot',
                what_why='Isolate delta objective weight with matched short training and reused controls',new='Three added lambda variants; frozen evaluation functions unchanged',
                artifacts=str(report),config_results=dict(config=config,results=result),caveats=result['uncertainty']+' '+result['scope']))
            done.add(label);event(event='report_ready',label=label,report=str(report))
        if len(done)==len(cfg['variants']):event(event='complete');return
        if a.once:event(event='checked_once',pending=len(cfg['variants'])-len(done));return
        time.sleep(a.poll)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('campaign','reference','targets','frozen-code','frozen-commit','output','dispatch-jobs','queue-log','python'):p.add_argument('--'+name,required=True)
    p.add_argument('--reference-index');p.add_argument('--lock-name',choices=['lambda_watch.lock','lambda_stress_watch.lock'],default='lambda_watch.lock')
    p.add_argument('--poll',type=float,default=60);p.add_argument('--once',action='store_true');watch(p.parse_args())

if __name__=='__main__':main()
