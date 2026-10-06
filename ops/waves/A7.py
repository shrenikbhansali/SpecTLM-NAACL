#!/usr/bin/env python3
"""A7 atlas DFlash sweep (D-22, D-24, D-31), derived from A4.py. Usage: A7.py OUT_JOBS
Cells per atlas derivative and K in (4, 2, 8) [K=4 first]: A10 (derivative target) and A00 (base target), both on the derivative's
rendered own-domain workload (or the general set if own-domain is unavailable, D-23/D-30), exact token input, fresh compile,
max_new_tokens 512, batch 8, greedy seed 0. LoRA derivatives: A00 also --enable-lora with the same --max-lora-rank (D-22).
Plus per base and K: base on its base-template general set, and 5 batch-8 replicates at K=4 (D-31 noise check)."""
import csv, json, re, sys
from pathlib import Path
csv.field_size_limit(10**9)
WS = "/home/heck2/sbhansali8/SpecTLM"; RUN = "/home/heck2/sbhansali8/SpecTLM-runs/run-A4-20261006"; PY = f"{WS}/.venv-atlas-031-clean/bin/python"
R = f"{WS}/artifacts/A3_rendered_20261006"; own = json.load(open(f"{R}/index.json")); gen = json.load(open(f"{R}/index_speed128.json"))
B = {"llama": dict(id="meta-llama/Llama-3.1-8B-Instruct", rev="0e9e39f249a16976918f6564b8830bc894c89659",
                   dr="z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat", drrev="d3af30def9601abdd10810aba220d692f0e803f0", native=10,
                   general=f"{R}/llama/_base-speed128/prompts.jsonl"),
     "qwen3": dict(id="Qwen/Qwen3-8B", rev="b968826d9c46dd6066d109eabc6255188de91218",
                   dr="z-lab/Qwen3-8B-DFlash-b16", drrev="9b41424b7109f9c5413454f481b09a82b85333f4", native=16,
                   general=f"{R}/qwen3/_base-speed128/prompts.jsonl")}
CAPS = (8, 16, 32, 64, 128, 256, 320, 512)
def cell(b, cond, tag, target, trev, prompts, k, hub, adapter=None, arev=None, lora_rank=None, rep=None, note=""):
    x = B[b]
    cmd = [PY, "-u", "-m", "atlas.run_cell", "--target", target, "--target-revision", trev, "--drafter", x["dr"], "--drafter-revision", x["drrev"],
           "--method", "dflash", "--K", str(k), "--prompts", prompts, "--seed", "0", "--max-new-tokens", "512", "--batch-size", "8",
           "--max-model-len", "4096", "--gpu-memory-utilization", ".70", "--use-prompt-token-ids", "--output", "{out_dir}/cell"]
    if adapter: cmd += ["--adapter", adapter, "--adapter-revision", arev]
    if lora_rank: cmd += ["--max-lora-rank", str(lora_rank)] + ([] if adapter else ["--enable-lora"])
    args = ["--task", "A7", "--base", b, "--drafter", "dflash", "--k", str(k), "--seed", "0", "--no-resolve", "--tag", f"{cond}-{tag}"[:70],
            "--prompts", prompts, "--engine-lock", f"{RUN}/atlas/env/requirements.lock", "--python", PY, "--code-repo", RUN,
            "--env", "HF_HUB_OFFLINE=1", "--env", f"HF_HUB_CACHE={hub}", "--env", "VLLM_CACHE_ROOT={out_dir}/vllm_cache",
            "--target", target, "--target-rev", trev, "--drafter-model", x["dr"], "--drafter-rev", x["drrev"], "--note", note]
    if adapter: args += ["--adapter", adapter, "--adapter-rev", arev]
    if rep is not None: args += ["--rep", str(rep)]
    return {"name": f"{b}:K{k}:{cond}:{tag}" + (f":r{rep}" if rep is not None else ""), "args": args + ["--", *cmd]}
prelim = json.load(open(f"{WS}/artifacts/A4_prelim_K4_20261006.json"))
subset = {}
for b in B:
    rows = sorted([r for r in prelim if r["base"] == b], key=lambda r: r["retention"])
    subset[b] = {rows[round(i * (len(rows) - 1) / 9)]["model_id"] for i in range(10)}
jobs = []
for b, x in B.items():
    for k in (x["native"], 4):
        for i in range(1, 4):
            jobs.append(cell(b, "base", "general", x["id"], x["rev"], x["general"], k, "/home/heck2/sbhansali8/HFcache/hub", rep=i, note=f"A7 base general DFlash replicate {i}/3"))
        for r in csv.DictReader(open(f"{WS}/artifacts/atlas/pool_manifest_{b}.csv")):
            if r["in_atlas"] != "True": continue
            m = r["model_id"]
            if k == 4 and m not in subset[b]: continue
            key = f"{b}:{m}"; slug = re.sub(r"[^a-z0-9]+", "-", m.lower())[:50]
            prompts, wl = (own[key]["rendered"], "own") if key in own else (gen[key]["rendered"], "general")
            is_ad = r["type"] == "lora_adapter"; snap = r["staged_path"]
            rank = next(c for c in CAPS if c >= int(float(r["r"]))) if is_ad else None
            hub = "/home/heck2/sbhansali8/HFcache/hub"
            meta = f"A7 {b} K={k} workload={wl} {m} ({r['type']}, {r['pool']})"
            if is_ad: jobs.append(cell(b, "A10", slug, x["id"], x["rev"], prompts, k, hub, adapter=snap, arev=r["revision"], lora_rank=rank, note=meta))
            else: jobs.append(cell(b, "A10", slug, snap, r["revision"], prompts, k, hub, note=meta + f" [local snapshot of {m}@{r['revision']}]"))
            jobs.append(cell(b, "A00", slug, x["id"], x["rev"], prompts, k, hub, lora_rank=rank, note=meta + " [A00]"))
Path(sys.argv[1]).write_text("".join(json.dumps(j) + "\n" for j in jobs)); print(len(jobs), "jobs")
