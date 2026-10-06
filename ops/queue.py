#!/usr/bin/env python3
"""Run a list of launcher jobs over a fixed set of GPU slots (one job per slot at a time).

Usage: ops/queue.py --slots heck-srv2:0,heck-srv2:1,... --jobs jobs.jsonl --log queue.log [--poll 20]

Each line of jobs.jsonl is {"name": ..., "args": [... ops/launch.py run arguments WITHOUT --node/--gpus ...]}.
A slot is free when the run it last started has an exit_code file. Jobs already listed as launched in the
log are skipped, so the queue can be restarted. Never launches two jobs on one slot.
"""
import argparse
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


def reserved():
    try:
        d = json.loads(RESERVATIONS.read_text())
        return set(d["slots"] if isinstance(d, dict) else d)
    except Exception:
        return set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slots", required=True)
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--poll", type=float, default=20)
    a = ap.parse_args()
    slots = a.slots.split(",")
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    log = Path(a.log)
    done_names = set()
    busy = {}  # slot -> out_dir
    if log.exists():
        for l in log.read_text().splitlines():
            e = json.loads(l)
            if e.get("event") == "launched":
                done_names.add(e["name"])
                busy[e["slot"]] = e["out_dir"]
    pending = [j for j in jobs if j["name"] not in done_names]

    def emit(**e):
        e["t"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with log.open("a") as f:
            f.write(json.dumps(e) + "\n")

    while pending or busy:
        for slot in slots:
            od = busy.get(slot)
            if od and not (Path(od) / "exit_code").exists():
                continue
            if od:
                emit(event="finished", slot=slot, out_dir=od, exit=(Path(od) / "exit_code").read_text().strip())
                busy.pop(slot)
            if not pending or slot in reserved():
                continue
            job = pending.pop(0)
            node, gpu = slot.split(":")
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
