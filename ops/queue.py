#!/usr/bin/env python3
"""Run a list of launcher jobs over a fixed set of GPU slots (one job per slot at a time).

Usage: ops/queue.py --slots heck-srv2:0,heck-srv2:1,... --jobs jobs.jsonl --log queue.log [--poll 20]

Each line of jobs.jsonl is {"name": ..., "args": [... ops/launch.py run arguments WITHOUT --node/--gpus ...]}.
A slot is free when the run it last started has an exit_code file. Jobs already listed as launched in the
log are skipped, so the queue can be restarted. Never launches two jobs on one slot.
"""
import argparse
import fcntl
import hashlib
import os
import socket
import json
import re
import subprocess
import sys
import time
from pathlib import Path

LAUNCH = Path(__file__).resolve().parent / "launch.py"
# Builders reserve GPUs by listing "node:gpu" strings in this file (JSON list or {"slots": [...]}); the queue never launches
# on a reserved slot. Shared-file coordination for codex-1 and claude-ops (2026-10-06 collision, notes/O1.md).
RESERVATIONS = Path("/home/heck2/sbhansali8/SpecTLM/ops/gpu_reservations.json")


def reserved(owner=""):
    try:
        d = json.loads(RESERVATIONS.read_text())
        if isinstance(d, dict) and owner and d.get("owner") == owner:
            return set()
        return set(d["slots"] if isinstance(d, dict) else d)
    except Exception:
        return set()



def eligible_job_index(jobs, node):
    """Optional per-job placement preserves FIFO among compatible jobs."""
    return next((i for i,job in enumerate(jobs) if 'allowed_nodes' not in job or node in job['allowed_nodes']),None)


def gpu_busy(node, gpu, limit_mib=1000):
    """True if the GPU already holds > limit_mib (another job, any user). Checked right before each launch."""
    try:
        r = subprocess.run(["ssh", "-n", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", node,
                            f"nvidia-smi -i {gpu} --query-gpu=memory.used --format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=20)
        return int(r.stdout.strip().splitlines()[-1]) > limit_mib
    except Exception:
        return True



def acquire_owner_lock(owner, directory=None):
    """One opted-in dispatcher per owner across shared-workspace processes."""
    if not owner:raise ValueError('--exclusive-owner requires a nonempty --owner')
    directory=Path(directory) if directory is not None else RESERVATIONS.parent/'queue_locks'
    directory.mkdir(parents=True,exist_ok=True)
    path=directory/(hashlib.sha256(owner.encode()).hexdigest()+'.lock')
    handle=path.open('a+')
    try:
        fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise RuntimeError(f'owner {owner} already has a dispatcher; use its existing log/queue') from None
    handle.seek(0);handle.truncate()
    json.dump(dict(owner=owner,pid=os.getpid(),host=socket.gethostname()),handle);handle.flush()
    return handle


def reload_pending(path, known, attempted):
    """Read an atomically replaced dispatch list; preserve every known identity."""
    jobs=[json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    names=set()
    for job in jobs:
        name=job['name']
        if name in names:raise ValueError('duplicate job name')
        names.add(name)
        if 'allowed_nodes' in job and (not isinstance(job['allowed_nodes'],list) or not job['allowed_nodes'] or any(not isinstance(n,str) for n in job['allowed_nodes'])):
            raise ValueError('allowed_nodes must be a nonempty node list')
        if name in known and known[name]!=job:raise ValueError('known job identity changed')
    if not set(known)<=names:raise ValueError('known jobs removed from reload list')
    known.update({j['name']:j for j in jobs})
    return [j for j in jobs if j['name'] not in attempted]


def cancel_pending(jobs, names):
    """Explicit operational holds never terminate a running job or alter its args."""
    names=set(names)
    return [j for j in jobs if j['name'] not in names],[j['name'] for j in jobs if j['name'] in names]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slots", required=True)
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--poll", type=float, default=20)
    ap.add_argument("--owner", default="", help="this queue may use reserved slots tagged for this owner (reservations: {\"slots\": [...], \"owner\": NAME})")
    ap.add_argument('--exclusive-owner',action='store_true',help='refuse a second dispatcher with the same owner; required for method queues')
    ap.add_argument('--reload-jobs',action='store_true',help='watch atomically updated job list; stay alive until explicitly stopped')
    ap.add_argument('--cancel-file',help='optional JSON list of pending job names to cancel; logged permanently, no running process is stopped')
    a = ap.parse_args()
    lock=acquire_owner_lock(a.owner) if a.exclusive_owner else None
    try:
        dispatch(a)
    finally:
        if lock is not None:lock.close()


def dispatch(a):
    slots = a.slots.split(",")
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    if any('allowed_nodes' in j and (not isinstance(j['allowed_nodes'],list) or not j['allowed_nodes'] or any(not isinstance(n,str) for n in j['allowed_nodes'])) for j in jobs):
        raise ValueError('allowed_nodes must be a nonempty node list')
    log = Path(a.log)
    done_names = set()
    busy = {}  # slot -> out_dir
    if log.exists():
        for l in log.read_text().splitlines():
            e = json.loads(l)
            if e.get('event')=='cancelled':done_names.add(e['name'])
            if e.get("event") == "launched":
                done_names.add(e["name"])
                busy[e["slot"]] = e["out_dir"]
    pending = [j for j in jobs if j["name"] not in done_names]

    def emit(**e):
        e["t"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with log.open("a") as f:
            f.write(json.dumps(e) + "\n")

    reload=getattr(a,'reload_jobs',False)
    known={j['name']:j for j in jobs}
    attempted=set(done_names)
    while pending or busy or reload:
        if reload:pending=reload_pending(a.jobs,known,attempted)
        cancel_file=getattr(a,'cancel_file',None)
        if cancel_file and Path(cancel_file).exists():
            names=json.loads(Path(cancel_file).read_text())
            if not isinstance(names,list) or any(not isinstance(n,str) for n in names):raise ValueError('cancel file must be a job-name list')
            pending,cancelled=cancel_pending(pending,names)
            for name in cancelled:
                attempted.add(name);emit(event='cancelled',name=name,cancel_file=cancel_file)
        for slot in slots:
            od = busy.get(slot)
            if od and not (Path(od) / "exit_code").exists():
                continue
            if od:
                emit(event="finished", slot=slot, out_dir=od, exit=(Path(od) / "exit_code").read_text().strip())
                busy.pop(slot)
            if not pending or slot in reserved(a.owner):
                continue
            node, gpu = slot.split(":")
            index=eligible_job_index(pending,node)
            if index is None or gpu_busy(node, gpu):
                continue
            job = pending.pop(index)
            attempted.add(job["name"])
            res = subprocess.run([sys.executable, str(LAUNCH), "run", "--node", node, "--gpus", gpu, *job["args"]],
                                 capture_output=True, text=True)
            m = re.search(r"\n  (/\S+)", res.stdout)
            if res.returncode != 0 or not m:
                emit(event="launch_failed", name=job["name"], slot=slot, stderr=res.stderr[-500:], stdout=res.stdout[-300:])
                continue
            busy[slot] = m.group(1)
            emit(event="launched", name=job["name"], slot=slot, out_dir=m.group(1))
        time.sleep(a.poll)
    emit(event="queue_empty")


if __name__ == "__main__":
    main()
