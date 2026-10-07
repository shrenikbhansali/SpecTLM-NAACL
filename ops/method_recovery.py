"""Operational retries/continuation around immutable, pinned evaluation modules.

No metrics, decoding, workload selection or training recipe is implemented here.
"""
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

SAFE_NODES=['heck-srv1','heck-srv3','heck-srv4','heck-srv5']


def read(path):return json.loads(Path(path).read_text())
def lines(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def write(path,obj):
    with Path(path).open('x') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')


def retry_plan(record,job,launcher,output,*,attempt,expected_prompt_sha,expected_source_sha):
    """Only one retry of a terminated cache-allocation failure; no sampling edits."""
    run=Path(record['run_dir']);launcher=Path(launcher)
    if attempt!=1:raise ValueError('one collision retry allowed; further failure needs inspection')
    if (run/'results.json').exists() or not (run/'failure.json').is_file():raise ValueError('retry requires failed cell without results')
    if not (launcher/'exit_code').is_file() or (launcher/'exit_code').read_text().strip()=='0':raise ValueError('failed launcher must have terminated')
    log=(launcher/'launch.log').read_text(errors='replace')
    cache_collision='No available memory for the cache blocks' in log
    startup_collision='Free memory on device cuda:' in log and 'on startup is less than desired GPU memory utilization' in log
    if not (cache_collision or startup_collision):raise ValueError('not an identified GPU-memory collision')
    cfg=read(run/'config.json')
    if cfg.get('code_dirty') is not False or cfg.get('engine_version')!='0.31.0' or cfg.get('source_sha256')!=expected_source_sha:raise ValueError('failed evaluation source/pin differs')
    argv=record['argv'];prompt=argv[argv.index('--prompts')+1]
    if sha(prompt)!=expected_prompt_sha or cfg.get('prompt_sha256')!=expected_prompt_sha:raise ValueError('prompt changed')
    args=job['args'];split=args.index('--');cmd=args[split+1:]
    if [v for i,v in enumerate(cmd) if not(i==1 and v=='-u')]!=argv:raise ValueError('launcher command differs from frozen record')
    for key in ('target','drafter','adapter'):
        flag='--'+key
        if flag not in argv:continue
        local=Path(argv[argv.index(flag)+1])
        if local.is_dir():
            actual={str(p.relative_to(local)):sha(p) for p in sorted(local.rglob('*')) if p.is_file() and '.cache' not in p.parts}
            if actual!=cfg.get(key+'_files_sha256'):raise ValueError(f'{key} files changed')
    new=copy.deepcopy(record);retry=copy.deepcopy(job);name=record['run_id']+'-retry1';dest=Path(output)/name
    if dest.exists():raise ValueError('retry output already exists')
    new.update(run_id=name,run_dir=str(dest),retry_of=record['run_id'])
    new['argv'][new['argv'].index('--output')+1]=str(dest)
    new['env']['VLLM_CACHE_ROOT']=str(dest/'vllm_cache')
    retry['name']=name;retry['args'][retry['args'].index('--tag')+1]=name
    idx=retry['args'].index('--output',split+1);retry['args'][idx+1]=str(dest);retry['allowed_nodes']=SAFE_NODES.copy()
    proof=dict(retry_of=record['run_id'],failed_run=str(run),launcher=str(launcher),reason='terminated GPU-cache allocation failure',
        expected_prompt_sha256=expected_prompt_sha,expected_source_sha256=expected_source_sha,
        failed_attempt_sha256={str(p):sha(p) for p in [run/'config.json',run/'failure.json',launcher/'exit_code',launcher/'launch.log']})
    return new,retry,proof


def apply_overlay(records,overlays):
    result=[]
    for row in records:
        overlay=overlays.get(row['run_id'])
        if overlay is None:result.append(copy.deepcopy(row));continue
        new=copy.deepcopy(overlay['record']);old=copy.deepcopy(row)
        restored=copy.deepcopy(new);restored['run_id']=old['run_id'];restored['run_dir']=old['run_dir'];restored.pop('retry_of',None)
        restored['argv'][restored['argv'].index('--output')+1]=old['argv'][old['argv'].index('--output')+1]
        restored['env']=old['env']
        if restored!=old or overlay['proof']['retry_of']!=old['run_id']:raise ValueError('retry overlay changes frozen cell controls')
        result.append(new)
    if not set(overlays)<={r['run_id'] for r in records}:raise ValueError('overlay contains unknown cell')
    return result


def append_jobs(path,jobs):
    path=Path(path);old=lines(path);known={j['name']:j for j in old};new=[]
    for job in jobs:
        if job['name'] in known:
            if known[job['name']]['args']!=job['args']:raise ValueError('dispatch identity changed')
            continue
        j=copy.deepcopy(job);j['allowed_nodes']=SAFE_NODES.copy();new.append(j);known[j['name']]=j
    if new:
        temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
        with temp.open('x') as f:
            for job in old+new:f.write(json.dumps(job)+'\n')
            f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    return len(new)


def preflight(jobs,code,output):
    output.mkdir();checks=[]
    for job in jobs:
        args=job['args'];cmd=args[args.index('--')+1:]
        checks.extend([(job['name']+'-cell',cmd+['--dry-run']),
            (job['name']+'-launcher',[sys.executable,str(code/'ops/launch.py'),'run','--dry-run','--node','heck-srv4','--gpus','0',*args])])
    def run(item):
        name,cmd=item
        with (output/(name+'.log')).open('x') as f:
            r=subprocess.run(cmd,cwd=code,env=dict(os.environ,HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2'),stdout=f,stderr=subprocess.STDOUT)
        return dict(name=name,argv=cmd,returncode=r.returncode)
    with ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(run,checks))
    write(output/'results.json',dict(passed=all(r['returncode']==0 for r in rows),checks=rows))
    if any(r['returncode'] for r in rows):raise ValueError(f'preflight failed: {output}')


def frozen_modules(code,commit):
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=code,text=True).strip()!=commit:raise ValueError('frozen commit differs')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=code,text=True).strip():raise ValueError('frozen checkout dirty')
    sys.path.insert(0,str(code))
    modules={name:importlib.import_module(name) for name in ('followspec.evaluation_jobs','followspec.pilot_watch','followspec.pilot_report','followspec.evaluate','followspec.production_pipeline','atlas.run_cell')}
    if any(not Path(m.__file__).resolve().is_relative_to(code) for m in modules.values()):raise ValueError('evaluation import did not use frozen checkout')
    return modules


def watch(a):
    code=Path(a.frozen_code).resolve();modules=frozen_modules(code,a.frozen_commit)
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    lock=Path(a.training)/'method_operator_watch.lock';handle=lock.open('a+')
    fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    handle.seek(0);handle.truncate();handle.write(str(os.getpid()));handle.flush()
    os.chdir(code)
    write(out/'config.json',vars(a)|dict(operation_source_sha256=sha(__file__),frozen_sources_sha256={name:sha(m.__file__) for name,m in modules.items()}))
    previous=Path(a.previous).resolve();signature=None;overlays={};blocked={}
    def event(**row):
        with (out/'events.jsonl').open('a') as f:f.write(json.dumps(row|dict(time=datetime.now(timezone.utc).isoformat()))+'\n')
    try:
        while True:
            current=modules['followspec.pilot_watch'].checkpoint_signature(a.training)
            if current!=signature:
                stage=out/f'stage-{time.time_ns()}'
                modules['followspec.evaluation_jobs'].evaluation_jobs(a.training,a.targets,stage,python=a.python,code_repo=code,
                    completed_only=True,previous=previous,allow_validation_pending=True,training_seeds=[0])
                ids={r['run_id'] for r in read(stage/'index_k4.json')}
                jobs=[j for j in lines(stage/'jobs.jsonl') if j['name'] in ids]
                preflight(jobs,code,out/f'preflight-{time.time_ns()}');added=append_jobs(a.dispatch_jobs,jobs)
                previous=stage;signature=current;(out/'latest_stage.txt').write_text(str(stage)+'\n')
                event(event='handoff',stage=str(stage),new_k4_jobs=added,readiness=read(stage/'results.json'))
            cfg=read(previous/'config.json');records=read(previous/'index_k4.json');jobs={j['name']:j for j in lines(previous/'effective_jobs.jsonl')}
            launches={e['name']:e for e in lines(a.queue_log) if e.get('event')=='launched'}
            for row in records:
                original=row['run_id'];active=overlays.get(original,{}).get('record',row)
                if not (Path(active['run_dir'])/'failure.json').exists() or original in blocked:continue
                launch=launches.get(active['run_id'])
                if launch is None or not (Path(launch['out_dir'])/'exit_code').is_file():continue
                try:
                    rr,jj,proof=retry_plan(active,jobs[original],launch['out_dir'],out/'retries',attempt=2 if original in overlays else 1,
                        expected_prompt_sha=cfg['prompt_sha256'][str(Path(row['prompt_file']).resolve())],expected_source_sha=sha(code/'atlas/run_cell.py'))
                    preflight([jj],code,out/f'retry-preflight-{time.time_ns()}')
                    overlay=dict(record=rr,job=jj,proof=proof);write(out/f'overlay-{original}.json',overlay)
                    append_jobs(a.dispatch_jobs,[jj]);overlays[original]=overlay;event(event='collision_retry',original=original,retry=rr['run_id'])
                except ValueError as e:
                    blocked[original]=str(e);event(event='cell_blocked',original=original,reason=str(e))
            effective=apply_overlay(records,overlays)
            missing=[r['run_id'] for r in effective if not (Path(r['run_dir'])/'results.json').is_file()]
            ready=read(previous/'results.json')
            if ready['checkpoints_ready'] and not missing:
                result=modules['followspec.pilot_report'].summarize(modules['followspec.evaluate'].load_measurements(effective))
                result['validation_pending_at_handoff']=ready.get('validation_pending',[])
                report=out/'report';report.mkdir();write(report/'index_k4.json',effective)
                proof=dict(stage='full-budget-single-seed-report',evaluation_stage=str(previous),decision_id='D-37',frozen_commit=a.frozen_commit,
                    inputs_sha256={str(Path(r['run_dir'])/n):sha(Path(r['run_dir'])/n) for r in effective for n in ('config.json','results.json','per_prompt.jsonl')},
                    overlays=overlays,training=a.training,engine_version='0.31.0',n_targets=len({r['derivative_id'] for r in records if r['pool']=='test'}))
                write(report/'config.json',proof);write(report/'results.json',result)
                write(report/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title='Full-budget seed0 four-arm held-out comparison',landed=str(datetime.now().date()),status='pilot',
                    what_why='D-37 full-budget method feasibility after D-38 short pilot',new='Frozen evaluation and statistical functions; explicit unchanged collision retries',
                    artifacts=str(report),config_results=dict(config=proof,results=result),caveats=result['uncertainty']+' No original Gate3 certification.'))
                event(event='report_ready',report=str(report));return
            if a.once:event(event='checked_once',pending_cells=len(missing),blocked=blocked);return
            if ready['checkpoints_ready'] and missing and all(r in blocked or any(o['record']['run_id']==r and key in blocked for key,o in overlays.items()) for r in missing):
                raise ValueError(f'remaining cells need inspection: {blocked}')
            time.sleep(a.poll)
    except BaseException as e:event(event='error',error_type=type(e).__name__,error=str(e));raise
    finally:handle.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('frozen-code','frozen-commit','training','targets','previous','output','dispatch-jobs','queue-log','python'):p.add_argument('--'+name,required=True)
    p.add_argument('--poll',type=float,default=60);p.add_argument('--once',action='store_true');a=p.parse_args();watch(a)


if __name__=='__main__':main()
