#!/usr/bin/env python3
"""Summarize A2 filter runs: one row per derivative (latest completed run), with B1 metadata.
Usage: ops/a2_summary.py --base llama|qwen3 [--csv OUT.csv]
Reads $WS/artifacts/A2-<base>-*/ (launcher config.json + cell/results.json) and B1's final staging CSV."""
import argparse
import collections
import csv
import glob
import json
from pathlib import Path

WS = "/home/heck2/sbhansali8/SpecTLM"
csv.field_size_limit(10**9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--csv")
    a = ap.parse_args()
    staged = {r["model_id"]: r for r in csv.DictReader(open(
        f"{WS}/artifacts/atlas/B1_{a.base}_finaldraft_retry_20261005/staging_{a.base}.csv"))}
    runs = {}
    for d in sorted(glob.glob(f"{WS}/artifacts/A2-{a.base}-*")):
        d = Path(d)
        if not (d / "exit_code").exists() or (d / "OPERATOR_NOTE.txt").exists():
            continue
        cfg = json.loads((d / "config.json").read_text())
        mid = cfg["models"]["target"]["id"]
        res = d / "cell" / "results.json"
        r = json.loads(res.read_text()) if res.exists() else {}
        runs[mid] = dict(run_id=d.name, exit=(d / "exit_code").read_text().strip(), **r)  # later runs override
    rows = []
    for mid, r in runs.items():
        s = staged.get(mid, {})
        rows.append(dict(model_id=mid, pool=s.get("pool", "base" if r["run_id"].endswith("-base") else "?"),
                         type=s.get("type", ""), license=s.get("license", ""), run_id=r["run_id"], exit=r["exit"],
                         loadable=r.get("loadable"), phase=r.get("phase", ""), load_error=(r.get("load_error") or "")[:160],
                         ppl=r.get("ppl"), ppl_ratio=r.get("ppl_ratio_vs_base"), degenerate=r.get("degenerate_count"),
                         accepted=r.get("accepted")))
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(sorted(rows, key=lambda x: (x["pool"], x["type"], x["model_id"])))
    print(f"{a.base}: {len(rows)} runs summarized / {len(staged)} staged; missing: {len(set(staged) - set(runs))}")
    acc = collections.Counter((r["pool"], r["accepted"]) for r in rows)
    print("accepted by pool:", dict(sorted(acc.items(), key=str)))
    c = collections.Counter((r["pool"], r["type"]) for r in rows if r["accepted"])
    for p in sorted({k[0] for k in c}):
        print(f"  accepted {p}: " + ", ".join(f"{t} {n}" for (pp, t), n in sorted(c.items()) if pp == p))
    for r in rows:
        if not r["accepted"]:
            print(f"  REJECT {r['pool']:15s} {r['type']:14s} {r['model_id'][:58]:58s} load={r['loadable']} "
                  f"ratio={r['ppl_ratio'] if r['ppl_ratio'] is None else round(r['ppl_ratio'], 3)} degen={r['degenerate']} "
                  f"{r['phase']} {r['load_error'][:70]}")


if __name__ == "__main__":
    main()
