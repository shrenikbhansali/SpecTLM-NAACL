#!/usr/bin/env python3
"""Submit a jobs.jsonl (same format as ops/queue.py: {"name":..., "args":[launch.py run args WITHOUT --node/--gpus]})
to Slurm through ops/launch.py --node slurm. Idempotent: names already submitted in --log are skipped, so it can be re-run.

  python3 ops/ice/submit.py --jobs path/jobs.jsonl --log path/submit.log [--dry-run] [--time 12:00:00] [--gres gpu:H100:1]

Jobs generated on heck carry heck absolute paths (--python, --code-repo, inputs); regenerate them on ICE before submitting.
This script refuses any job whose args mention /home/heck2 (use --allow-heck-paths only for inspection with --dry-run).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

LAUNCH = Path(__file__).resolve().parents[1] / "launch.py"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--time", help="override SLURM_TIME for these jobs")
    ap.add_argument("--gres", help="override SLURM_GRES for these jobs")
    ap.add_argument("--allow-heck-paths", action="store_true")
    a = ap.parse_args()
    if os.environ.get("SITE") != "ice":
        sys.exit("source sites/ice.env first (SITE=ice)")
    env = dict(os.environ)
    if a.time:
        env["SLURM_TIME"] = a.time
    if a.gres:
        env["SLURM_GRES"] = a.gres
    log = Path(a.log)
    done = set()
    if log.exists():
        done = {json.loads(l)["name"] for l in log.read_text().splitlines() if '"submitted"' in l}
    jobs = [json.loads(l) for l in open(a.jobs) if l.strip()]
    n = 0
    for j in jobs:
        if j["name"] in done:
            continue
        if "/home/heck2" in json.dumps(j["args"]) and not (a.allow_heck_paths and a.dry_run):
            sys.exit(f"{j['name']}: args contain heck paths; regenerate the job on ICE (see ops/ice/README.md)")
        cmd = [sys.executable, str(LAUNCH), "run", "--node", "slurm", "--gpus", "slurm", *j["args"]]
        if a.dry_run and "--dry-run" not in cmd:
            cmd.insert(3, "--dry-run")
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        m = re.search(r"\n  (/\S+)", r.stdout)
        ev = dict(event="submitted" if r.returncode == 0 and not a.dry_run else ("dry_run" if r.returncode == 0 else "submit_failed"),
                  name=j["name"], out_dir=m.group(1) if m else None, stdout=r.stdout[-300:], stderr=r.stderr[-500:],
                  t=time.strftime("%Y-%m-%dT%H:%M:%S"))
        with log.open("a") as f:
            f.write(json.dumps(ev) + "\n")
        print(ev["event"], j["name"], ev["out_dir"] or ev["stderr"][-200:])
        n += ev["event"] == "submitted"
    print(f"{n} submitted; {len(done)} previously submitted; log {log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
