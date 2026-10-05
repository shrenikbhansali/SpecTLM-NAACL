#!/usr/bin/env python3
"""A1 / Gate 1 analysis: validate every cell (MASTER §8.4) and compute the noise floor,
child drift, LoRA-vs-merged parity and per-cell timings. Prints JSON and a Markdown summary.

Usage: ops/a1_analyze.py [--golden FILE] [--out JSON] RUN_DIR...
Each RUN_DIR is $WS/artifacts/<run_id>/ containing config.json (launcher) and cell/ (harness).
Runs with OPERATOR_NOTE.txt (aborted) or non-zero exit codes are reported and excluded.
"""
import argparse
import hashlib
import itertools
import json
import statistics as st
from pathlib import Path

LEDGER = {"base": 3.0559, "noise_floor": 0.0138, "eagle_v1": 2.5951,
          "child_drift_seed": {0: -0.1998, 1: -0.2470, 2: -0.2961}, "child_drift_mean": -0.2476}


def validate(cell: Path, gold_ids, gold_sha):
    cfg = json.load(open(cell / "config.json"))
    res = json.load(open(cell / "results.json"))
    recs = [json.loads(l) for l in open(cell / "per_prompt.jsonl")]
    K, probs, als = cfg["K"], [], []
    ids = [r["prompt_id"] for r in recs]
    if sorted(ids) != sorted(gold_ids) or len(set(ids)) != len(ids):
        probs.append("prompt ids differ from golden or duplicated")
    if cfg.get("prompt_sha256") != gold_sha:
        probs.append("prompt sha mismatch")
    for k in ("target", "target_revision", "drafter", "drafter_revision", "engine_version", "code_commit", "seed", "K"):
        if cfg.get(k) in (None, ""):
            probs.append(f"config missing {k}")
    if cfg.get("code_dirty"):
        probs.append("dirty code")
    for r in recs:
        s, a = r["num_drafts"], r["num_accepted_tokens"]
        if s <= 0 or sum(r["per_step_accepted"]) != a or len(r["per_step_accepted"]) != s:
            probs.append(f"{r['prompt_id']}: counter mismatch")
            continue
        al = 1 + a / s
        if not 1 <= al <= K + 1:
            probs.append(f"{r['prompt_id']}: AL {al} outside [1, K+1]")
        als.append(al)
    macro = st.mean(als)
    res = dict(res, completion_tokens_total=sum(len(r["completion_token_ids"]) for r in recs),
               max_new_tokens=cfg.get("max_new_tokens"))
    if abs(macro - res["macro_acceptance_length"]) > 1e-9:
        probs.append("macro recompute mismatch")
    return cfg, res, macro, probs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default="/home/heck2/sbhansali8/cache_big/spectlm_a40_iclr_20260809/artifacts/"
                                        "l31-math-s0-splits-full-a1/splits/evaluation.jsonl")
    ap.add_argument("--out")
    ap.add_argument("runs", nargs="+")
    a = ap.parse_args()
    gold_ids = [json.loads(l)["prompt_id"] for l in open(a.golden)]
    gold_sha = hashlib.sha256(open(a.golden, "rb").read()).hexdigest()
    cells, excluded = {}, {}
    for r in map(Path, a.runs):
        if (r / "OPERATOR_NOTE.txt").exists():
            excluded[r.name] = "aborted (OPERATOR_NOTE.txt)"
            continue
        code = (r / "exit_code").read_text().strip() if (r / "exit_code").exists() else None
        if code != "0":
            excluded[r.name] = f"exit {code}"
            continue
        lcfg = json.load(open(r / "config.json"))
        cfg, res, macro, probs = validate(r / "cell", gold_ids, gold_sha)
        cells[r.name] = dict(macro=macro, problems=probs, tag=lcfg.get("tag"), rep=lcfg.get("replicate"),
                             method=cfg["method"], node=lcfg["launch"]["node"], gpu=lcfg["launch"]["gpus"],
                             gen_s=res["generation_wall_s"], startup_s=res["startup_s"], cell_s=res["cell_wall_s"],
                             ci=res.get("prompt_bootstrap_95_ci"), dflash_block=res.get("dflash_block_size"),
                             gpu_type=res.get("gpu_type"), engine=res.get("engine_version"),
                             tok=res["completion_tokens_total"], tok_s=res["completion_tokens_total"] / res["generation_wall_s"],
                             mnt=res["max_new_tokens"])
    out = {"n_cells": len(cells), "excluded": excluded, "cells": cells}
    groups = {"shared_compile": None, "fresh_compile": "freshcompile", "fresh_compile_mnt512": "freshcompile-mnt512"}
    for gname, gtag in groups.items():
        g = {k: v for k, v in cells.items() if v["rep"] is not None and v["method"] == "eagle3" and v["tag"] == gtag}
        if gname == "fresh_compile":
            out["noise_dflash_fresh_compile_values"] = sorted(round(v["macro"], 6) for v in cells.values()
                                                              if v["method"] == "dflash" and v["tag"] == "freshcompile")
        gv = [v["macro"] for v in g.values()]
        if len(gv) < 2:
            continue
        pair = sorted(abs(x - y) for x, y in itertools.combinations(gv, 2))
        out[f"noise_{gname}"] = dict(n=len(gv), mean=st.mean(gv), sd=st.stdev(gv), min=min(gv), max=max(gv),
                                     range=max(gv) - min(gv), distinct_values=len(set(round(x, 12) for x in gv)),
                                     pairwise_abs_diff_median=st.median(pair),
                                     pairwise_abs_diff_p95=pair[int(0.95 * (len(pair) - 1))],
                                     values=sorted(round(x, 6) for x in gv))
    reps = {k: v for k, v in cells.items() if v["rep"] is not None and v["method"] == "eagle3" and not v["tag"]}
    rv = [v["macro"] for v in reps.values()]
    if len(rv) >= 2:
        pair = sorted(abs(x - y) for x, y in itertools.combinations(rv, 2))
        out["noise"] = dict(n=len(rv), mean=st.mean(rv), sd=st.stdev(rv), min=min(rv), max=max(rv), range=max(rv) - min(rv),
                            distinct_values=len(set(round(x, 12) for x in rv)),
                            pairwise_abs_diff_median=st.median(pair), pairwise_abs_diff_p95=pair[int(0.95 * (len(pair) - 1))],
                            by_node={n: sorted(round(v["macro"], 6) for v in reps.values() if v["node"] == n)
                                     for n in sorted({v["node"] for v in reps.values()})})
        a00 = st.mean(rv)
        drift = {}
        for k, v in cells.items():
            if v["tag"] and v["tag"].startswith("mth018d-lora-s"):
                s = int(v["tag"][-1])
                drift[s] = dict(a10=v["macro"], drift=v["macro"] - a00, ledger=LEDGER["child_drift_seed"][s])
        if drift:
            ds = [d["drift"] for d in drift.values()]
            out["child"] = dict(a00_mean=a00, per_seed=drift, mean_drift=st.mean(ds),
                                sd=st.stdev(ds) if len(ds) > 1 else None, ledger_mean=LEDGER["child_drift_mean"])
        lora0 = [v["macro"] for v in cells.values() if v["tag"] == "mth018d-lora-s0"]
        merged0 = [v["macro"] for v in cells.values() if v["tag"] == "mth018d-merged-s0"]
        if lora0 and merged0:
            out["lora_vs_merged_s0"] = dict(lora=lora0[0], merged=merged0[0], diff=lora0[0] - merged0[0])
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "cells"}, indent=1))
    print("\n| run | method | tag/rep | node:gpu | max tok | macro AL | gen s | out tok/s | startup s | cell s | problems |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for k, v in sorted(cells.items()):
        print(f"| {k} | {v['method']} | {v['tag'] or ''}{('-r' + str(v['rep'])) if v['rep'] else ''} | {v['node']}:{v['gpu']} | {v['mnt']} | {v['macro']:.4f} | "
              f"{v['gen_s']:.0f} | {v['tok_s']:.1f} | {v['startup_s']:.0f} | {v['cell_s']:.0f} | {'; '.join(v['problems'][:3]) or 'none'} |")


if __name__ == "__main__":
    main()
