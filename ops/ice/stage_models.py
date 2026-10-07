#!/usr/bin/env python3
"""Stage pinned models into $HF_HOME/hub on ICE (read/download only; never uploads). Tiers in ops/ice/models.json.

  python ops/ice/stage_models.py --tier core            # bases + drafters (~50 GB); needed for validation and training
  python ops/ice/stage_models.py --tier core bank       # + 30 D-28-eligible Llama bank adapters (small)
  python ops/ice/stage_models.py --tier atlas           # both atlas pools (174 models, multi-TB; only if atlas work moves)
  python ops/ice/stage_models.py --check --tier core     # offline: report which pinned snapshots are present

Run on a login node with internet. Needs HF_TOKEN (or `huggingface-cli login`) with access to gated repos
(meta-llama). Every download is pinned to the exact revision in models.json; a missing revision is an error, not a fallback.
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def snapshot_dir(hub: Path, repo: str, rev: str) -> Path:
    return hub / ("models--" + repo.replace("/", "--")) / "snapshots" / rev


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tier", nargs="+", default=["core"], choices=["core", "bank", "atlas"])
    ap.add_argument("--check", action="store_true", help="offline presence check only")
    ap.add_argument("--only", nargs="*", default=None, help="restrict to these repo ids")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    home = os.environ.get("HF_HOME", "")
    if not home or home.startswith("TODO"):
        sys.exit("set HF_HOME (source sites/ice.env)")
    hub = Path(home) / "hub"
    spec = json.loads((HERE / "models.json").read_text())["tiers"]
    todo, seen = [], set()
    for t in a.tier:
        for m in spec[t]:
            if (m["id"], m["revision"]) in seen or (a.only and m["id"] not in a.only):
                continue
            seen.add((m["id"], m["revision"]))
            todo.append(m)
    present = [m for m in todo if snapshot_dir(hub, m["id"], m["revision"]).is_dir()]
    missing = [m for m in todo if m not in present]
    print(f"tiers {a.tier}: {len(todo)} pinned, {len(present)} present, {len(missing)} missing  (hub {hub})")
    if a.check:
        for m in missing:
            print(f"  missing {m['id']}@{m['revision'][:12]}")
        return 0 if not missing else 1
    os.environ.pop("HF_HUB_OFFLINE", None)
    from huggingface_hub import snapshot_download
    failures = []
    for i, m in enumerate(missing, 1):
        print(f"[{i}/{len(missing)}] {m['id']}@{m['revision'][:12]} ({m.get('role')})", flush=True)
        try:
            p = snapshot_download(m["id"], revision=m["revision"], cache_dir=str(hub), max_workers=a.workers)
            assert Path(p).name == m["revision"], f"resolved {p}, expected revision {m['revision']}"
        except Exception as e:  # keep going; report every failure at the end
            failures.append((m["id"], repr(e)[:300]))
            print(f"  FAILED: {failures[-1][1]}", flush=True)
    print(f"done: {len(missing) - len(failures)} downloaded, {len(failures)} failed")
    for f in failures:
        print("  ", *f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
