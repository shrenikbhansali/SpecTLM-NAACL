"""Preflight and append completed pilot checkpoint evaluations to one live queue."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from atlas.run_cell import sha256,write_new
from followspec.production_pipeline import checked_stage,lines,read
from followspec.evaluation_jobs import evaluation_jobs
from followspec.pilot_report import report


def checkpoint_signature(training):
    state=[]
    for job in lines(Path(training)/'jobs.jsonl'):
        args=job['args'];cmd=args[args.index('--')+1:];run=Path(cmd[cmd.index('--output')+1])
        if list(run.glob('failure*.json')):raise ValueError(f'pilot training failed: {run}')
        files=[]
        for p in run.glob('checkpoints/epoch*_end'):
            if p.is_symlink() and (p/'training_state.json').is_file():files.append((str(p),sha256(p/'training_state.json')))
        if (run/'results.json').is_file():files.append((str(run/'results.json'),sha256(run/'results.json')))
        state.append((job['name'],sorted(files)))
    return hashlib.sha256(json.dumps(state).encode()).hexdigest()


def append_dispatch(path,jobs):
    """Mutable dispatch list only; sealed stage files are never modified."""
    path=Path(path);old=lines(path);by_name={j['name']:j for j in old}
    if len(by_name)!=len(old):raise ValueError('duplicate dispatch identity')
    new=[]
    for job in jobs:
        if job['name'] in by_name:
            if by_name[job['name']]!=job:raise ValueError('dispatch identity changed')
        else:new.append(job);by_name[job['name']]=job
    if new:
        temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
        with temp.open('x') as f:
            for job in old+new:f.write(json.dumps(job)+'\n')
            f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    return len(new)


def preflight(stage,code,output):
    primary={r['run_id'] for r in read(stage/'index_k4.json')}
    jobs=[j for j in lines(stage/'jobs.jsonl') if j['name'] in primary]
    output.mkdir();checks=[]
    for job in jobs:
        a=job['args'];cmd=a[a.index('--')+1:]
        checks.extend([(job['name']+'-cell',cmd+['--dry-run']),
            (job['name']+'-launcher',[sys.executable,str(code/'ops/launch.py'),'run','--dry-run','--node','heck-srv4','--gpus','0',*a])])
    def run(item):
        name,cmd=item
        with (output/(name+'.log')).open('x') as f:
            result=subprocess.run(cmd,cwd=code,env=dict(os.environ,HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2'),stdout=f,stderr=subprocess.STDOUT)
        return dict(name=name,argv=cmd,returncode=result.returncode)
    with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(run,checks))
    write_new(output/'results.json',dict(passed=all(r['returncode']==0 for r in results),checks=results))
    if any(r['returncode'] for r in results):raise ValueError(f'pilot evaluation preflight failed: {output}')
    return jobs


def watch(a):
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False);code=Path(a.code_repo).resolve()
    signature=None;previous=None
    write_new(out/'config.json',vars(a)|dict(code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=code,text=True).strip()))
    def event(**row):
        with (out/'events.jsonl').open('a') as f:f.write(json.dumps(row|dict(time=datetime.now(timezone.utc).isoformat()))+'\n')
    try:
        while True:
            current=checkpoint_signature(a.training)
            if current!=signature:
                stage=out/f'stage-{time.time_ns()}'
                evaluation_jobs(a.training,a.targets,stage,python=a.python,code_repo=code,completed_only=True,
                    previous=previous,reuse_frozen=a.reference if previous is None else None,allow_validation_pending=True,
                    training_seeds=[0],job_prefix='pilot-d38')
                jobs=preflight(stage,code,out/f'preflight-{time.time_ns()}')
                added=append_dispatch(a.dispatch_jobs,jobs)
                previous=stage;signature=current
                (out/'latest_stage.txt').write_text(str(stage)+'\n')
                event(event='handoff',stage=str(stage),new_k4_jobs=added,readiness=read(stage/'results.json'))
            records=read(previous/'index_k4.json')
            failures=[r['run_dir'] for r in records if list(Path(r['run_dir']).glob('failure*.json'))]
            if failures:raise ValueError(f'pilot evaluation failures: {failures}')
            missing=[r['run_id'] for r in records if not (Path(r['run_dir'])/'results.json').is_file()]
            if read(previous/'results.json')['checkpoints_ready'] and not missing:
                result=report(previous,out/'report');event(event='report_ready',report=str(result));return
            if a.once:event(event='checked_once',pending_cells=len(missing));return
            time.sleep(a.poll)
    except BaseException as e:
        event(event='error',error_type=type(e).__name__,error=str(e));raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('training','targets','reference','output','dispatch-jobs','python','code-repo'):p.add_argument('--'+name,required=True)
    p.add_argument('--poll',type=float,default=60);p.add_argument('--once',action='store_true');a=p.parse_args();watch(a)


if __name__=='__main__':main()
