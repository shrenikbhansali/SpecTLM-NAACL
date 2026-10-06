#!/usr/bin/env python3
"""A3: Magpie workloads for the frozen pools (D-04, D-19 A40 production, D-23).
Usage: A3_magpie.py eval  OUT_JOBS          -> 64 evaluation queries per atlas derivative (both bases)
       A3_magpie.py train OUT_JOBS EVALDIRS  -> 500 training queries per bank child; forbids every eval set (file of paths)
Seeds: evaluation 2026100600+i, training 2026100700+i (distinct per derivative and split)."""
import csv, json, sys
from pathlib import Path
csv.field_size_limit(10**9)
WS = "/home/heck2/sbhansali8/SpecTLM"; import os
RUN = os.environ.get("A3_RUN","/home/heck2/sbhansali8/SpecTLM-runs/run-A3-20261006")
PY = f"{WS}/.venv-magpie/bin/python"
FORB = [f"{WS}/artifacts/B4_public_resolved_20261005/all_speed_forbidden.jsonl"]
GEN = f"{WS}/artifacts/B4_public_resolved_20261005/general20000.jsonl"
BASES = {"llama": dict(id="meta-llama/Llama-3.1-8B-Instruct", rev="0e9e39f249a16976918f6564b8830bc894c89659",
                       snap="/home/heck2/sbhansali8/HFcache/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659"),
         "qwen3": dict(id="Qwen/Qwen3-8B", rev="b968826d9c46dd6066d109eabc6255188de91218",
                       snap="/home/heck2/sbhansali8/HFcache/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218")}

def job(b, r, i, split, seed, forbidden):
    B = BASES[b]; staging = f"{WS}/artifacts/atlas/B1_{b}_finaldraft_retry_20261005/staging_{b}.csv"
    snap = r["staged_path"]; is_ad = r["type"] == "lora_adapter"
    srow = next(x for x in csv.DictReader(open(staging)) if x["model_id"] == r["model_id"])
    inherited = srow["tokenizer_source"] == "inherited_base"
    tok, tokrev = (B["snap"], B["rev"]) if inherited else (snap, r["revision"])
    hub = "/home/heck2/sbhansali8/HFcache/hub" if is_ad else str(Path(snap).parents[2])
    target, rev = (B["id"], B["rev"]) if is_ad else (r["model_id"], r["revision"])
    slug = "".join(c if c.isalnum() else "-" for c in r["model_id"].lower())[:50] + f"-{split[:4]}"
    cmd = [PY, "-u", "-m", "atlas.generate_magpie", "--derivative-id", r["model_id"], "--pool-manifest", staging,
           "--target", target, "--revision", rev, "--tokenizer", tok, "--tokenizer-revision", tokrev, "--family", b,
           "--split", split, "--seed", str(seed), "--allow-a40-production", *(["--d23-oversampling"] if os.environ.get("A3_D23") else []), "--forbidden-files", *forbidden, "--output", "{out_dir}/cell"]
    if is_ad: cmd[cmd.index("--tokenizer"):cmd.index("--tokenizer")] = ["--adapter", snap]
    args = ["--task", "A3", "--base", b, "--drafter", "magpie", "--k", "0", "--seed", str(seed), "--no-resolve", "--tag", slug,
            "--prompts", FORB[0], "--engine-lock", f"{RUN}/atlas/env/requirements.lock", "--python", PY, "--code-repo", RUN,
            "--env", "HF_HUB_OFFLINE=1", "--env", "PATH=/home/heck2/sbhansali8/SpecTLM/.venv-magpie/bin:/home/heck2/sbhansali8/SpecTLM/.venv-atlas-031-clean/bin:/usr/local/bin:/usr/bin:/bin", "--env", f"HF_HUB_CACHE={hub}", "--env", "VLLM_CACHE_ROOT={out_dir}/vllm_cache",
            "--target", target, "--target-rev", rev, "--note", f"A3 Magpie {split}: {r['model_id']} ({r['type']}, {r['pool']})", "--", *cmd]
    if is_ad: args[args.index("--note"):args.index("--note")] = ["--adapter", snap, "--adapter-rev", r["revision"]]
    return {"name": f"{b}:{split}:{r['model_id']}", "args": args}

mode, outp = sys.argv[1], sys.argv[2]; jobs = []
for b in BASES:
    rows = list(csv.DictReader(open(f"{WS}/artifacts/atlas/pool_manifest_{b}.csv")))
    if mode == "eval":
        sel = [r for r in rows if r["in_atlas"] == "True"]
        jobs += [job(b, r, i, "evaluation", 2026100600 + i, FORB + [GEN]) for i, r in enumerate(sel)]
    else:
        evals = [p for p in Path(sys.argv[3]).read_text().split() if p]
        sel = [r for r in rows if r["in_bank"] == "True"]
        jobs += [job(b, r, i, "training", 2026100700 + i, FORB + evals) for i, r in enumerate(sel)]
Path(outp).write_text("".join(json.dumps(j) + "\n" for j in jobs)); print(len(jobs), "jobs")
