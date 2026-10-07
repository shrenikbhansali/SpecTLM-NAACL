#!/usr/bin/env python3
"""Compare ICE validation cells (ops/ice/validate.sh) with the heck A40 reference (EXP-ATL-002, fresh compile, 512 tokens).

Operational criterion (not a research gate; the owner decides whether ICE and heck numbers may share a table):
  SAME_RANGE  every ICE value lies within heck's observed range widened by 0.005 (3.097709–3.116301)
  SHIFTED     otherwise; report the mean shift and keep ICE numbers in ICE-only comparisons.
Writes <validation dir>/compare.json.
"""
import json
import statistics
import sys
from pathlib import Path

HECK = dict(n=20, mean=3.105030, sd=0.002910, lo=3.102709, hi=3.111301, gpu="NVIDIA A40", source="ledger/EXP-ATL-002.md")


def main() -> int:
    import os
    ws = Path(os.environ.get("WS", "."))
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path((ws / "artifacts/ICE_validation_LATEST").read_text().strip())
    rows = []
    for ev in (json.loads(l) for l in (d / "submit.log").read_text().splitlines()):
        if ev.get("event") != "submitted":
            continue
        out = Path(ev["out_dir"])
        res = out / "cell" / "results.json"
        hw = (out / "hardware.txt").read_text().strip() if (out / "hardware.txt").exists() else "?"
        if res.exists():
            r = json.loads(res.read_text())
            rows.append(dict(run=out.name, macro_al=r["macro_acceptance_length"], n=r["n"], gpu=r.get("gpu_type"), hardware=hw,
                             engine=r.get("engine_version")))
        else:
            rows.append(dict(run=out.name, macro_al=None, status="failed" if (out / "exit_code").exists() else "pending", hardware=hw))
    done = [r["macro_al"] for r in rows if r.get("macro_al") is not None]
    out = dict(heck_reference=HECK, ice=rows)
    if done:
        lo, hi = HECK["lo"] - 0.005, HECK["hi"] + 0.005
        out.update(n=len(done), mean=statistics.mean(done), sd=statistics.stdev(done) if len(done) > 1 else None,
                   shift_vs_heck=statistics.mean(done) - HECK["mean"],
                   verdict="SAME_RANGE" if all(lo <= x <= hi for x in done) else "SHIFTED",
                   engines=sorted({r.get("engine") for r in rows if r.get("engine")}))
    (d / "compare.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "ice"}, indent=1))
    for r in rows:
        print(" ", r)
    return 0 if out.get("verdict") == "SAME_RANGE" and len(done) == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
