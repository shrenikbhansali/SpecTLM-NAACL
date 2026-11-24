"""Run an immutable rebuttal plan; leave the frozen acceptance command untouched."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);a=p.parse_args()
    plan=json.loads(a.plan.read_text());root=Path(plan['workspace'])
    for rel in ['EXPERIMENTS_PAUSED.json','tlm-spec-maintenance/EXPERIMENTS_PAUSED.json']:
        if (root/rel).exists():raise RuntimeError('Experiments paused')
    command=plan['command'];out=Path(plan['run_dir'])
    if Path(command[command.index('--output')+1])!=out/'cell':raise ValueError('cell output is not inside run dir')
    for path,expected in plan['input_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError('Changed input '+path)
    cwd=Path(plan['cwd'])
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=cwd,text=True).strip()
    if commit!=plan['harness_commit']:raise ValueError('Wrong harness commit')
    out.mkdir(parents=True,exist_ok=False)
    (out/'config.yaml').write_text(json.dumps(plan,indent=2)+'\n')  # JSON is a YAML subset.
    (out/'cmd.txt').write_text(shlex.join(command)+'\n')
    (out/'git_commit.txt').write_text(commit+'\n')
    start=time.monotonic();started=datetime.datetime.now().astimezone().isoformat()
    with (out/'log.txt').open('x') as log:
        result=subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
    elapsed=time.monotonic()-start
    (out/'gpu_hours.txt').write_text(f'{elapsed/3600:.8f}\n')
    metrics=dict(status='completed' if result.returncode==0 else 'failed',exit_code=result.returncode,
                 started=started,wall_s=elapsed,gpu_hours=elapsed/3600,includes_engine_startup=True,
                 hostname=os.uname().nodename,cuda_visible_devices=os.getenv('CUDA_VISIBLE_DEVICES'))
    raw=out/'cell/results.json'
    if raw.exists():metrics['frozen_engine_results']=json.loads(raw.read_text())
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    return result.returncode


if __name__=='__main__':sys.exit(main())
