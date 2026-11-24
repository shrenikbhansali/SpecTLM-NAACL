"""Enforce the approved experiment GPU-hour ceiling without altering run outputs."""
import argparse
import fcntl
import inspect
import json
import os
from pathlib import Path
import subprocess
import time


def usage(runs, prefix, now=None):
    now = time.time() if now is None else now
    total = 0.
    for run in Path(runs).glob(prefix+'*'):
        if (run/'metrics.json').exists():
            total += json.loads((run/'metrics.json').read_text())['gpu_hours']
        elif (run/'cmd.txt').exists():
            total += max(0.,now-(run/'cmd.txt').stat().st_mtime)/3600
    return total


def is_target_process(args, owner, current_uid, outputs, modules=None):
    modules=modules or ['followspec.family_repair','atlas.run_cell']
    return (owner == current_uid and '-m' in args and
            any(args[args.index('-m')+1:args.index('-m')+2]==[m] for m in modules) and
            '--output' in args and args[args.index('--output')+1:args.index('--output')+2]
            and args[args.index('--output')+1] in outputs)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--control',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.workspace
    a.output.mkdir(exist_ok=True,parents=True)
    with (a.output/'guard.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stopped_at=None
        while True:
            control=json.loads(a.control.read_text())
            prefix=control['prefix'];limit=control['limit_gpu_hours']
            used=usage(root/'rebuttal/runs',prefix)
            state={'time':time.time(),'used_gpu_hours':used,'limit_gpu_hours':limit}
            with (a.output/'usage.jsonl').open('a') as f:f.write(json.dumps(state)+'\n')
            # Leave time for the 20-second dispatcher poll and process teardown.
            if used>=limit-0.2 or stopped_at is not None:
                jobs=[json.loads(x) for x in (root/'rebuttal/preflight_20261124_exactfamily/jobs.jsonl').read_text().splitlines()]
                cancel=Path(control['cancel_file'])
                names=set(json.loads(cancel.read_text())) if cancel.exists() else set()
                names.update(j['name'] for j in jobs if j['name'].startswith(prefix))
                tmp=cancel.with_suffix('.tmp');tmp.write_text(json.dumps(sorted(names)));os.replace(tmp,cancel)
                outputs={str(run/'cell') for run in (root/'rebuttal/runs').glob(prefix+'*')
                         if not (run/'metrics.json').exists()}
                if stopped_at is None:
                    stopped_at=time.time();print('BUDGET CAP: cancelling pending and active experiment runs',state,flush=True)
                signame='SIGKILL' if time.time()-stopped_at>120 else 'SIGTERM'
                script='import os,signal,json\nfrom pathlib import Path\n'+inspect.getsource(is_target_process)
                script+='\noutputs=set('+repr(sorted(outputs))+')\nactions=[]\n'
                script+='''for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  args=(proc/'cmdline').read_bytes().decode().strip('\\0').split('\\0')
  if not is_target_process(args,proc.stat().st_uid,os.getuid(),outputs,MODULES):continue
  pid=int(proc.name)
  if os.getpgid(pid)!=pid:raise RuntimeError('Expected isolated native run process group')
  os.killpg(pid,getattr(signal,SIGNAME));actions.append({'pid':pid,'signal':SIGNAME,'output':args[args.index('--output')+1]})
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
print(json.dumps(actions))
'''.replace('SIGNAME',repr(signame)).replace('MODULES',repr(control.get('modules')))
                for host in ['heck-srv1','heck-srv3','heck-srv4','heck-srv5']:
                    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','GSSAPIAuthentication=yes',host+'.ece.gatech.edu','python3 -'],input=script,text=True,capture_output=True,timeout=30)
                    record=dict(host=host,time=time.time(),returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
                    with (a.output/'actions.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
                    print('BUDGET ACTION',host,result.returncode,result.stdout,flush=True)
            time.sleep(20)


if __name__=='__main__':main()
