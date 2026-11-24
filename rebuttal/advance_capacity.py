"""Wait for one exact reproduction, then append approved R1 work to the sole queue."""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from rebuttal.run_recorded import check_baseline_gate


def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source',type=Path,help='approved ready-plan directory; defaults to the initial capacity stage')
    a=p.parse_args();root=a.workspace
    a.output.mkdir(parents=True,exist_ok=False)
    required=root/'rebuttal/runs/BASELINE_t0_reuse_math500_s0_cachefix1/metrics.json'
    mapping=json.loads((root/'rebuttal/preflight_20261124_exactfamily/run-map.json').read_text())
    mapping.pop('BASELINE_t0_reuse_math500_s0_cachefix1')
    mapfile=a.output/'run-map.json';mapfile.write_text(json.dumps(mapping,indent=2))
    while not required.exists():
        print('Waiting for exact R1 MATH reproduction',flush=True);time.sleep(20)
    gate=a.output/'gate'
    subprocess.run([sys.executable,'-m','rebuttal.baselines','--workspace',str(root),
                    '--run-map',str(mapfile),'--output',str(gate)],check=True)
    report=gate/'results.json';check_baseline_gate(dict(requires_baseline_pass=True,target=0,baseline_report=str(report)))
    # Inspect the existing queue and new stage before appending, never start a dispatcher.
    probe=subprocess.run(['pgrep','-af','[q]ueue.py'],capture_output=True,text=True,check=True)
    print(probe.stdout,flush=True);print('Stage contents:',sorted(x.name for x in a.output.iterdir()),flush=True)
    source=a.source or root/'rebuttal/ready_20261124_1504';jobs=[]
    for line in (source/'jobs.jsonl').read_text().splitlines():
        job=json.loads(line)
        if '_t0_' not in job['name']:continue
        plan=json.loads((source/(job['name']+'.json')).read_text())
        plan['baseline_report']=str(report)
        plan['input_sha256'][str(report)]=hashlib.sha256(report.read_bytes()).hexdigest()
        check_baseline_gate(plan)
        if Path(plan['run_dir']).exists():raise FileExistsError(plan['run_dir'])
        out=a.output/(job['name']+'.json');out.write_text(json.dumps(plan,indent=2)+'\n')
        args=job['args'];args[args.index('--plan')+1]=str(out);jobs.append(job)
    q=root/'rebuttal/preflight_20261124_exactfamily/jobs.jsonl'
    with (q.parent/'append.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        old=[json.loads(x) for x in q.read_text().splitlines()];names={x['name'] for x in old}
        if any(j['name'] in names for j in jobs):raise ValueError('Already submitted job')
        tmp=q.with_name('jobs.advance.tmp');tmp.write_text(''.join(json.dumps(x)+'\n' for x in old+jobs));os.replace(tmp,q)
    (a.output/'activated.json').write_text(json.dumps(dict(jobs=[x['name'] for x in jobs],gate=str(report)),indent=2))
    print('APPENDED',len(jobs),'R1 jobs after complete exact reproduction PASS',flush=True)


if __name__=='__main__':main()
