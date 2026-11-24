"""Run an immutable rebuttal plan; leave the frozen acceptance command untouched."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time


def seconds_until_deadline(value, now=None):
    if value is None:return None
    end=datetime.datetime.fromisoformat(value)
    if end.tzinfo is None:raise ValueError('Deadline requires an explicit timezone')
    now=now or datetime.datetime.now(datetime.timezone.utc)
    remaining=(end-now).total_seconds()
    if remaining<=0:raise ValueError('Run deadline has already passed')
    return remaining


def check_baseline_gate(plan):
    if not plan.get('requires_baseline_pass'):return
    if not plan.get('baseline_report'):raise ValueError('Missing baseline reproduction report')
    rows=json.loads(Path(plan['baseline_report']).read_text())
    target=plan['target'];arms=('reuse','full','dedicated') if target==0 else ('reuse','full')
    selected=[r for r in rows if r['target']==target]
    expected={(arm,bench) for arm in arms for bench in ('speed128','math500')}
    if len(selected)!=len(expected) or {(r['arm'],r['benchmark']) for r in selected}!=expected:
        raise ValueError('Incomplete matching-target baseline evidence')
    if any(r['status']!='pass' for r in selected):raise ValueError('Baseline reproduction gate has not passed')


def run_command(command,cwd,log,timeout=None):
    process=subprocess.Popen(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try:return process.wait(timeout=timeout),None
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGTERM)
        try:process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait()
        return process.returncode or 124,'deadline'


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);a=p.parse_args()
    plan=json.loads(a.plan.read_text());root=Path(plan['workspace'])
    check_baseline_gate(plan)
    seconds_until_deadline(plan.get('stop_at_et'))
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
        returncode,stop_reason=run_command(command,cwd,log,seconds_until_deadline(plan.get('stop_at_et')))
    elapsed=time.monotonic()-start
    (out/'gpu_hours.txt').write_text(f'{elapsed/3600:.8f}\n')
    metrics=dict(status='deadline_stopped' if stop_reason else 'completed' if returncode==0 else 'failed',exit_code=returncode,
                 started=started,wall_s=elapsed,gpu_hours=elapsed/3600,includes_engine_startup=True,
                 hostname=os.uname().nodename,cuda_visible_devices=os.getenv('CUDA_VISIBLE_DEVICES'))
    if stop_reason:metrics['stop_reason']=stop_reason
    raw=out/'cell/results.json'
    if raw.exists():metrics['frozen_engine_results']=json.loads(raw.read_text())
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    return returncode


if __name__=='__main__':sys.exit(main())
