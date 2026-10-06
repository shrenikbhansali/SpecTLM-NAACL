"""Retry only failed M2 response sources through an immutable plan overlay."""
import argparse
import copy
from pathlib import Path
from atlas.run_cell import sha256,write_new
from followspec.production_pipeline import checked_stage,finish,jsonl,lines,new_output,read


def retry_responses(plan, failed_runs, output):
    root,cfg=checked_stage(plan)
    if cfg['stage']!='responses':raise ValueError('response stage required')
    runs=read(root/'response_runs.json')
    sources={str(Path(p).resolve()) for pair in runs.values() for p in pair.values()}
    failed=[str(Path(p).resolve()) for p in failed_runs]
    if not failed or len(failed)!=len(set(failed)) or not set(failed)<=sources:
        raise ValueError('distinct referenced response sources required')
    evidence={}
    for source in failed:
        p=Path(source)
        if not (p/'failure.json').is_file() or not (p/'config.json').is_file() or (p/'results.json').exists():
            raise ValueError('explicit failed source without completed results required')
        evidence[source]={name:sha256(p/name) for name in ('failure.json','config.json')}
    jobs=lines(root/('effective_jobs.jsonl' if (root/'effective_jobs.jsonl').exists() else 'jobs.jsonl'))
    found={};out=Path(output).resolve();effective=[];retry=[]
    for original in jobs:
        job=copy.deepcopy(original);a=job['args'];split=a.index('--');cmd=a[split+1:]
        index=split+1+cmd.index('--output')+1;source=str(Path(a[index]).resolve())
        if source in failed:
            if source in found:raise ValueError('duplicate source job')
            dest=out/'runs'/Path(source).name;found[source]=str(dest)
            job['name']=job['name']+'-'+out.name;a[a.index('--tag')+1]=job['name'];a[index]=str(dest)
            retry.append(job)
        effective.append(job)
    if set(found)!=set(failed):raise ValueError('missing original command for failed source')
    out=new_output(out)
    write_new(out/'assignment.json',read(root/'assignment.json'))
    write_new(out/'response_runs.json',{target:{role:found.get(str(Path(p).resolve()),p) for role,p in pair.items()} for target,pair in runs.items()})
    jsonl(out/'jobs.jsonl',retry);jsonl(out/'effective_jobs.jsonl',effective)
    write_new(out/'render_commands.json',[])
    finish(out,cfg|dict(retry_of=str(root),retry_plan_sha256=sha256(root/'stage_files.json'),failed_source_sha256=evidence),
        dict(n_gpu_jobs=len(retry),n_effective_gpu_jobs=len(effective),n_reused_sources=len(sources)-len(failed),
             production_ready=False,next='Preflight and run retry jobs; assemble this overlay after every referenced source completes'))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',required=True);p.add_argument('--failed-runs',nargs='+',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(retry_responses(a.plan,a.failed_runs,a.output))


if __name__=='__main__':main()
