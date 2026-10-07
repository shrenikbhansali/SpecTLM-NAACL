"""D-39 stress cells and task-quality reports around the frozen evaluation engine."""
import argparse
from datetime import datetime,timezone
import fcntl
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
import time
from ops.method_recovery import (read,lines,sha,write,frozen_modules,preflight,append_jobs,retry_plan,apply_overlay)


def filter_commands(spec,targets,out,reference,baseline):
    jobs=[]
    for t in targets:
        if t['model_id']=='base':continue
        name='d39-filter-'+t['model_id'].split('/')[-1]
        cmd=['-m','atlas.filter_pool','--base-snapshot',spec['base_snapshot'],'--base-id',spec['base_id'],
             '--base-revision',spec['base_revision'],'--reference',str(reference),'--baseline',str(baseline),
             '--derivative-id',t['model_id'],'--adapter',t['adapter'],'--adapter-revision',t['revision'],
             '--drafter','RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3','--drafter-revision',spec['drafter_revision'],
             '--K','4','--max-lora-rank','128','--seed','0','--repetition-threshold','0.5','--output',str(out/name)]
        jobs.append((name,cmd))
    return jobs


def prepare(a,m):
    checked=m['followspec.production_pipeline'].checked_stage
    panel,pcfg=checked(a.panel);source,scfg=checked(a.training)
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    code=Path(a.frozen_code).resolve();stage=out/'evaluation'
    m['followspec.evaluation_jobs'].evaluation_jobs(source,panel/'targets.json',stage,python=a.python,code_repo=code,
        completed_only=True,allow_validation_pending=True,training_seeds=[0],job_prefix='d39-stress')
    if not read(stage/'results.json')['checkpoints_ready']:raise ValueError('all four pilot checkpoints required')
    records=read(stage/'index_k4.json');ids={r['run_id'] for r in records}
    celljobs=[j for j in lines(stage/'jobs.jsonl') if j['name'] in ids]
    from followspec.production import launcher_job
    spec=read(stage/'config.json')['spec'];filters=[]
    for name,cmd in filter_commands(spec,read(panel/'targets.json')['targets'],out/'filters',Path(a.reference),Path(a.baseline)):
        j=launcher_job(spec|dict(seed=0),name,'M4',a.reference,cmd,python=a.python)
        j['args'][j['args'].index('--drafter')+1]='eagle3';j['args'][j['args'].index('--k')+1]='4';filters.append(j)
    jobs=filters+celljobs
    preflight(jobs,code,out/'preflight')
    write(out/'jobs.json',jobs);write(out/'filters.json',filters)
    config=vars(a)|dict(operation_source_sha256=sha(__file__),evaluation_stage=str(stage),panel_sha256=sha(panel/'stage_files.json'),
        input_sha256={str(Path(a.reference)):sha(a.reference),str(Path(a.baseline)/'config.json'):sha(Path(a.baseline)/'config.json'),
            str(Path(a.baseline)/'results.json'):sha(Path(a.baseline)/'results.json')},n_jobs=len(jobs))
    write(out/'config.json',config)
    write(out/'prepared_sha256.json',{str(p):sha(p) for p in (out/'config.json',out/'jobs.json',out/'filters.json',out/'preflight/results.json')})
    return out


def lambda_command(out,cfg,campaign):
    command=[sys.executable,'-m','ops.lambda_watch','--campaign',str(campaign),
        '--reference',cfg['evaluation_stage'],'--reference-index',str(out/'report/index_k4.json'),
        '--targets',str(Path(cfg['panel'])/'targets.json'),'--output',str(out/'lambda_watch'),
        '--lock-name','lambda_stress_watch.lock']
    for name in ('frozen_code','frozen_commit','dispatch_jobs','queue_log','python'):
        command += ['--'+name.replace('_','-'),cfg[name]]
    return command


def watch(out,m,lambda_campaign=None):
    cfg=read(out/'config.json');code=Path(cfg['frozen_code']).resolve()
    for p,h in read(out/'prepared_sha256.json').items():
        if sha(p)!=h:raise ValueError('prepared plan changed')
    for p,h in cfg['input_sha256'].items():
        if sha(p)!=h:raise ValueError('filter reference changed')
    panel,_=m['followspec.production_pipeline'].checked_stage(cfg['panel'])
    if sha(panel/'stage_files.json')!=cfg['panel_sha256']:raise ValueError('panel changed')
    stage,_=m['followspec.production_pipeline'].checked_stage(cfg['evaluation_stage'])
    handle=(out/'watch.lock').open('a+');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    quality_path=Path(__file__).resolve().parents[1]/'followspec/stress_quality.py'
    spec=importlib.util.spec_from_file_location('d39_quality',quality_path);quality=importlib.util.module_from_spec(spec);spec.loader.exec_module(quality)
    runtime=out/('watch-runtime-'+str(time.time_ns())+'.json')
    write(runtime,dict(operation_source_sha256=sha(__file__),quality_source_sha256=sha(quality_path),lambda_campaign=lambda_campaign,pid=os.getpid(),frozen_commit=cfg['frozen_commit']))
    jobs=read(out/'jobs.json');byname={j['name']:j for j in jobs};records=read(stage/'index_k4.json')
    filters=read(out/'filters.json');overlays={p.stem[len('overlay-'):]:read(p) for p in out.glob('overlay-*.json')};blocked=set()
    def event(**row):
        with (out/'events.jsonl').open('a') as f:f.write(json.dumps(row|dict(time=datetime.now(timezone.utc).isoformat()))+'\n')
    event(event='dispatch',n_added=append_jobs(cfg['dispatch_jobs'],jobs))
    while True:
        launches={e['name']:e for e in lines(cfg['queue_log']) if e.get('event')=='launched'}
        for r in records:
            original=r['run_id'];active=overlays.get(original,{}).get('record',r)
            if not (Path(active['run_dir'])/'failure.json').exists() or original in blocked:continue
            launch=launches.get(active['run_id'])
            if not launch or not (Path(launch['out_dir'])/'exit_code').is_file():continue
            try:
                rr,jj,proof=retry_plan(active,byname[original],launch['out_dir'],out/'retries',attempt=2 if original in overlays else 1,
                    expected_prompt_sha=sha(r['prompt_file']),expected_source_sha=sha(code/'atlas/run_cell.py'))
                preflight([jj],code,out/('preflight-'+rr['run_id']))
                overlays[original]=dict(record=rr,job=jj,proof=proof);write(out/('overlay-'+original+'.json'),overlays[original])
                append_jobs(cfg['dispatch_jobs'],[jj]);event(event='collision_retry',original=original,retry=rr['run_id'])
            except ValueError as e:blocked.add(original);event(event='cell_blocked',original=original,reason=str(e))
        effective=apply_overlay(records,overlays)
        missing=[r for r in effective if not (Path(r['run_dir'])/'results.json').is_file()]
        filter_results={}
        for j in filters:
            cmd=j['args'][j['args'].index('--')+1:];p=Path(cmd[cmd.index('--output')+1])
            if (p/'results.json').is_file():filter_results[cmd[cmd.index('--derivative-id')+1]]=read(p/'results.json')
        if not missing and len(filter_results)==len(filters):
            # Reuse frozen pairing and AL aggregation without a new selected-only summary.
            loaded=m['followspec.evaluate'].load_measurements(effective)
            paired=m['followspec.pilot_report'].paired_values
            bykey={(r['derivative_id'],r['workload'],r['arm'],r['cell']):r for r in loaded}
            rows=[]
            for t in read(panel/'targets.json')['targets']:
                if t['model_id']=='base':continue
                domain=t['domain'];key=t['model_id'];parent=bykey[key,domain,'Frozen','A00'];child=bykey[key,domain,'Frozen','A10']
                pair=paired(parent,child);per_arm={}
                for arm in ('FS','MVD','PO-D','PO-T'):
                    r=bykey[key,domain,arm,'A11'];ap=paired(r,child)
                    per_arm[arm]=dict(gain_over_frozen=ap['values'][0]-ap['values'][1],paired=ap,uncertainty=quality.acceptance_interval(r,child))
                comparisons={arm:paired(bykey[key,domain,'FS','A11'],bykey[key,domain,arm,'A11'])|dict(uncertainty=quality.acceptance_interval(bykey[key,domain,'FS','A11'],bykey[key,domain,arm,'A11'])) for arm in ('MVD','PO-D','PO-T')}
                q=quality.compare(lines(t['workloads'][domain]),lines(Path(parent['run_dir'])/'per_prompt.jsonl'),lines(Path(child['run_dir'])/'per_prompt.jsonl'))
                rows.append(dict(target=key,domain=domain,target_training_steps=t['target_training_steps'],frozen_pair=pair,
                    frozen_retention=pair['values'][1]/pair['values'][0],frozen_uncertainty=quality.acceptance_interval(parent,child),quality=q,coherence_filter=filter_results[key],arms=per_arm,fs_vs_controls=comparisons))
            report=out/'report';report.mkdir(exist_ok=False)
            result=dict(status='pilot',decision_id='D-39',n_conditions=len(rows),n_independent_training_trajectories=len({r['domain'] for r in rows}),
                rows=rows,confirmation_evaluated=False,gate_certified=False,
                scope='All fixed development conditions, including regressions. Multiple update strengths share trajectories. No model-level independence or positive-method claim inferred.')
            proof=dict(frozen_commit=cfg['frozen_commit'],quality_source_sha256=sha(quality_path),panel_sha256=cfg['panel_sha256'],
                inputs_sha256={str(Path(r['run_dir'])/n):sha(Path(r['run_dir'])/n) for r in effective for n in ('config.json','results.json','per_prompt.jsonl')})
            write(report/'config.json',proof);write(report/'results.json',result);write(report/'index_k4.json',effective)
            write(report/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title='D-39 controlled target-update stress screen',landed=str(datetime.now().date()),status='pilot',
                what_why='Measure acceptance and task usefulness across fixed target SFT strengths with matched drafters',new='Fixed development panel; original frozen acceptance implementation',
                artifacts=str(report),config_results=dict(config=proof,results=result),caveats=result['scope']))
            event(event='report_ready',report=str(report))
            if lambda_campaign:
                command=lambda_command(out,cfg,lambda_campaign)
                with (out/'lambda_watch.log').open('x') as log:
                    proc=subprocess.Popen(command,cwd=Path(__file__).resolve().parents[1],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                write(out/'lambda_continuation.json',dict(pid=proc.pid,argv=command))
                event(event='lambda_continuation',pid=proc.pid)
            return
        time.sleep(60)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--resume');p.add_argument('--prepare-only',action='store_true');p.add_argument('--lambda-campaign')
    for name in ('panel','training','reference','baseline','frozen-code','frozen-commit','output','dispatch-jobs','queue-log','python'):p.add_argument('--'+name)
    a=p.parse_args()
    if a.resume:
        out=Path(a.resume).resolve();cfg=read(out/'config.json');code=Path(cfg['frozen_code']).resolve();m=frozen_modules(code,cfg['frozen_commit']);os.chdir(code);watch(out,m,lambda_campaign=a.lambda_campaign)
    else:
        if any(getattr(a,n) is None for n in ('panel','training','reference','baseline','frozen_code','frozen_commit','output','dispatch_jobs','queue_log','python')):p.error('all preparation arguments required')
        code=Path(a.frozen_code).resolve();m=frozen_modules(code,a.frozen_commit);os.chdir(code);out=prepare(a,m)
        if not a.prepare_only:watch(out,m,lambda_campaign=a.lambda_campaign)

if __name__=='__main__':main()
