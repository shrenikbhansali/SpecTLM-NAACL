#!/usr/bin/env python3
"""Operator job launcher (MASTER §8.2, AGENTS rule 5).

Assigns a run ID, creates $WS/artifacts/<run_id>/ (never overwrites), writes
config.json, then starts the command on a node via ssh under nohup. The command
may use the placeholders {run_id} and {out_dir}.

Usage:
  ops/launch.py run --task A1 --base llama --drafter eagle3 --k 4 --seed 0 \
      --node heck-srv3 --gpus 0 --target meta-llama/Llama-3.1-8B-Instruct \
      --drafter-model RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3 \
      --prompts path/to/prompts.jsonl --engine-lock path/to/lock \
      --python /path/to/env/bin/python -- python atlas/run_cell.py ... --out {out_dir}
  ops/launch.py list [--n 20] [--no-poll]   # registry with live state per run

Guards: refuses real launches while EXPERIMENTS_PAUSED.json exists (use
--dry-run); refuses heck-srv6 (dedicated H200s) for anything but A9; refuses an
existing artifact directory; refuses a dirty or non-main checkout for real runs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
REPO = Path(__file__).resolve().parents[1]
WS = Path(os.environ.get("WS", "/home/heck2/sbhansali8/SpecTLM"))
PAUSE_MARKER = Path(os.environ.get(
    "PAUSE_MARKER", "/home/heck2/sbhansali8/SpecTLM/tlm-spec-maintenance/EXPERIMENTS_PAUSED.json"))
DEDICATED_H200 = {"heck-srv6"}
REGISTRY = WS / "ops" / "runs.jsonl"


class LaunchError(RuntimeError):
    pass


def now_et() -> dt.datetime:
    return dt.datetime.now(ET)


def make_run_id(task, base, drafter, k, seed, when=None, rep=None) -> str:
    when = when or now_et()
    rid = f"{task}-{base}-{drafter}-k{k}-s{seed}-{when.strftime('%Y%m%d%H%M')}"
    # Replicates of one cell launched in the same minute: suffix -r<NN>.
    return rid if rep is None else f"{rid}-r{int(rep):02d}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args, cwd=REPO) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout.strip()


def code_state(repo: Path) -> dict:
    return {
        "repo": str(repo),
        "commit": git("rev-parse", "HEAD", cwd=repo),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD", cwd=repo),
        "dirty": bool(git("status", "--porcelain", "--untracked-files=no", cwd=repo)),
        "tags": git("tag", "--points-at", "HEAD", cwd=repo).split(),
    }


def resolve_revision(model_id: str, revision: str | None) -> str:
    """Return a commit hash; resolve via the Hub if a branch/None was given."""
    if revision and len(revision) == 40 and all(c in "0123456789abcdef" for c in revision):
        return revision
    if model_id.startswith("/") or Path(model_id).exists():
        raise LaunchError(f"local path {model_id}: pass --*-rev with the source commit hash")
    from huggingface_hub import HfApi  # deferred: network only when needed
    return HfApi().model_info(model_id, revision=revision).sha


def engine_info(lock: Path | None) -> dict:
    if lock is None:
        return {"lock_file": None, "lock_sha256": None, "vllm": None}
    text = lock.read_text()
    vllm = None
    for line in text.splitlines():
        s = line.strip().lower()
        if s.startswith("vllm==") or s.startswith("vllm ") or s.startswith("- vllm=="):
            vllm = line.strip().split("==")[-1].split()[-1]
            break
    return {"lock_file": str(lock.resolve()), "lock_sha256": sha256_file(lock), "vllm": vllm}


def build_config(a, run_id: str, out_dir: Path) -> dict:
    models = {}
    for role, mid, rev in (("target", a.target, a.target_rev), ("drafter", a.drafter_model, a.drafter_rev),
                           ("adapter", a.adapter, a.adapter_rev)):
        if mid:
            models[role] = {"id": mid, "revision": resolve_revision(mid, rev) if a.resolve else rev}
    prompts = None
    if a.prompts:
        p = Path(a.prompts)
        prompts = {"path": str(p.resolve()), "sha256": sha256_file(p)}
    cmd = [c.format(run_id=run_id, out_dir=str(out_dir)) for c in a.command]
    return {
        "run_id": run_id,
        "task": a.task, "base": a.base, "drafter_method": a.drafter, "K": a.k, "seed": a.seed,
        "replicate": a.rep,
        "models": models,
        "prompts": prompts,
        "engine": engine_info(Path(a.engine_lock) if a.engine_lock else None),
        "code": code_state(Path(a.code_repo)),
        "launch": {
            "node": a.node, "gpus": a.gpus, "python": a.python, "command": cmd,
            "cwd": str(Path(a.code_repo).resolve()), "launched_at_et": now_et().isoformat(timespec="seconds"),
            "launched_by": "claude-ops", "dry_run": a.dry_run,
            "pause_marker_present": PAUSE_MARKER.exists(),
        },
        "notes": a.note,
    }


def check_guards(a):
    if a.node in DEDICATED_H200 and a.task != "A9":
        raise LaunchError(f"{a.node} is the dedicated H200 box: A9 timing only (MASTER §8.2)")
    if not a.dry_run:
        if PAUSE_MARKER.exists():
            raise LaunchError(f"pause marker present at {PAUSE_MARKER}; only --dry-run allowed (AGENTS §4)")
        st = code_state(Path(a.code_repo))
        if st["dirty"]:
            raise LaunchError("code checkout is dirty; real runs need a clean main commit")
        on_tag = st["branch"] == "HEAD" and any(t.startswith("run-") for t in st["tags"]) and subprocess.run(
            ["git", "merge-base", "--is-ancestor", "HEAD", "main"], cwd=a.code_repo).returncode == 0
        if st["branch"] != "main" and not on_tag and not a.allow_branch:
            raise LaunchError(f"checkout is on {st['branch']}; real runs run from main or a run-* tag on main (MASTER §2.2)")
        if not a.engine_lock:
            raise LaunchError("--engine-lock is required for real runs (AGENTS rule 2)")
        if not a.prompts:
            raise LaunchError("--prompts is required for real runs (prompt-file hash, AGENTS rule 5)")


def append_registry(rec: dict):
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY, "a") as f:
        f.write(json.dumps(rec) + "\n")


def cmd_run(a) -> int:
    check_guards(a)
    run_id = make_run_id(a.task, a.base, a.drafter, a.k, a.seed, rep=a.rep)
    root = WS / "artifacts" / ("_dryrun" if a.dry_run else "")
    out_dir = root / run_id
    if out_dir.exists():
        raise LaunchError(f"{out_dir} exists; never overwrite (use --rep for replicates or wait a minute)")
    cfg = build_config(a, run_id, out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    (out_dir / a.config_name).write_text(json.dumps(cfg, indent=2) + "\n")
    inner = " ".join(shlex.quote(c) for c in cfg["launch"]["command"])
    env = f"CUDA_VISIBLE_DEVICES={shlex.quote(a.gpus)} HF_HOME={shlex.quote(os.environ.get('HF_HOME', ''))} "
    if a.python:
        env += f"PATH={shlex.quote(str(Path(a.python).parent))}:$PATH "
    script = (f"cd {shlex.quote(cfg['launch']['cwd'])} && {env} nohup bash -c "
              f"{shlex.quote(inner + '; echo $? > ' + str(out_dir / 'exit_code'))} "
              f"> {shlex.quote(str(out_dir / 'launch.log'))} 2>&1 < /dev/null & echo $!")
    rec = {"run_id": run_id, "task": a.task, "node": a.node, "gpus": a.gpus, "out_dir": str(out_dir),
           "launched_at_et": cfg["launch"]["launched_at_et"], "dry_run": a.dry_run, "pid": None}
    if a.dry_run:
        (out_dir / "launch_script.sh").write_text(script + "\n")
        print(f"[dry-run] {run_id}\n  config: {out_dir / a.config_name}\n  would run on {a.node}: {script}")
    else:
        res = subprocess.run(["ssh", "-o", "BatchMode=yes", a.node, script], capture_output=True, text=True,
                             timeout=60)
        if res.returncode != 0:
            raise LaunchError(f"ssh launch failed: {res.stderr.strip()}")
        rec["pid"] = int(res.stdout.strip().splitlines()[-1])
        print(f"launched {run_id} on {a.node} gpus={a.gpus} pid={rec['pid']}\n  {out_dir}")
    append_registry(rec)
    return 0


def read_registry() -> list[dict]:
    if not REGISTRY.exists():
        return []
    return [json.loads(l) for l in REGISTRY.read_text().splitlines() if l.strip()]


def run_state(rec: dict) -> str:
    out = Path(rec["out_dir"])
    if (out / "exit_code").exists():
        code = (out / "exit_code").read_text().strip()
        return "done" if code == "0" else f"failed(exit {code})"
    if rec.get("dry_run"):
        return "dry-run"
    try:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", rec["node"], f"kill -0 {rec['pid']} 2>/dev/null && echo up"],
                           capture_output=True, text=True, timeout=20)
        return "running" if "up" in r.stdout else "vanished(no exit_code)"
    except subprocess.TimeoutExpired:
        return "unknown(ssh timeout)"


def cmd_list(a) -> int:
    recs = read_registry()[-a.n:]
    for r in recs:
        print(f"{r['launched_at_et'][:16]}  {run_state(r) if a.poll else '':<22} {r['node']}:{r['gpus']:<6} {r['run_id']}")
    if not recs:
        print("(no runs in registry)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--task", required=True)
    r.add_argument("--base", required=True, choices=["llama", "qwen3"])
    r.add_argument("--drafter", required=True, help="eagle3 | eagle | dflash | fs-<arm> ...")
    r.add_argument("--k", type=int, required=True)
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--rep", type=int, default=None, help="replicate index (adds -rNN to the run ID)")
    r.add_argument("--node", required=True)
    r.add_argument("--gpus", required=True, help="CUDA_VISIBLE_DEVICES on the node")
    r.add_argument("--target"), r.add_argument("--target-rev")
    r.add_argument("--drafter-model"), r.add_argument("--drafter-rev")
    r.add_argument("--adapter"), r.add_argument("--adapter-rev")
    r.add_argument("--no-resolve", dest="resolve", action="store_false",
                   help="do not resolve revisions on the Hub (tests / offline)")
    r.add_argument("--prompts")
    r.add_argument("--engine-lock")
    r.add_argument("--python", help="interpreter of the pinned env (its bin/ is prepended to PATH)")
    r.add_argument("--code-repo", default=str(REPO), help="checkout the job runs from (default: this repo)")
    r.add_argument("--allow-branch", action="store_true", help="permit a non-main checkout (verification only)")
    r.add_argument("--config-name", default="config.json")
    r.add_argument("--note", default="")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("command", nargs=argparse.REMAINDER)
    l = sub.add_parser("list")
    l.add_argument("--n", type=int, default=20)
    l.add_argument("--no-poll", dest="poll", action="store_false")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "run":
            if a.command and a.command[0] == "--":
                a.command = a.command[1:]
            if not a.command:
                raise LaunchError("no command given after --")
            return cmd_run(a)
        return cmd_list(a)
    except LaunchError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
