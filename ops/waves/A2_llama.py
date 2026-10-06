#!/usr/bin/env python3
"""A2 (Llama) loadability + coherence filter over B1's final staged list (132 = 100 sampled + all bank adapters).
Usage: A2_llama.py base            -> launch the base reference run (must finish first)
       A2_llama.py jobs BASE_RUN    -> write jobs.jsonl for ops/queue.py (one job per staged derivative)
Settings: atlas/POOL_FILTER.md; EAGLE-3 K=4; max LoRA rank 128 (max staged r = 128); repetition threshold 0.5 (D-16);
fresh compile per cell (D-14); HF_HUB_OFFLINE=1."""
import csv, json, re, subprocess, sys
from pathlib import Path
csv.field_size_limit(10**9)
WS = "/home/heck2/sbhansali8/SpecTLM"
RUN = "/home/heck2/sbhansali8/SpecTLM-runs/run-A2-20261005"
PY = f"{WS}/.venv-atlas-031-clean/bin/python"
FD = f"{WS}/artifacts/atlas/B1_llama_finaldraft_retry_20261005"
BASE_SNAP = f"{WS}/artifacts/B2_models_20261005/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659"
BID, BREV = "meta-llama/Llama-3.1-8B-Instruct", "0e9e39f249a16976918f6564b8830bc894c89659"
DR, DRREV = "RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3", "f4fa34a8f803a0ba75d048d6b3dbc1ad5149e9ac"
REF = f"{WS}/artifacts/FIX-1_reference_retry_20261005/reference.jsonl"

def common(tag, target, trev, note):
    return ["--task", "A2", "--base", "llama", "--drafter", "eagle3", "--k", "4", "--seed", "0", "--no-resolve", "--tag", tag,
            "--prompts", REF, "--engine-lock", f"{RUN}/atlas/env/requirements.lock", "--python", PY, "--code-repo", RUN,
            "--env", "HF_HUB_OFFLINE=1", "--env", "VLLM_CACHE_ROOT={out_dir}/vllm_cache",
            "--target", target, "--target-rev", trev, "--drafter-model", DR, "--drafter-rev", DRREV, "--note", note, "--"]

def fp(extra):
    return [PY, "-u", "-m", "atlas.filter_pool", "--base-snapshot", BASE_SNAP, "--base-id", BID, "--base-revision", BREV,
            "--reference", REF, "--drafter", DR, "--drafter-revision", DRREV, "--K", "4", "--max-lora-rank", "128",
            "--repetition-threshold", "0.5", "--seed", "0", *extra, "--output", "{out_dir}/cell"]

if sys.argv[1] == "base":
    args = common("base", BID, BREV, "A2 Llama base reference run") + fp(["--derivative-id", "base"])
    sys.exit(subprocess.call([sys.executable, str(Path(__file__).parents[1] / "launch.py"), "run", "--node", sys.argv[2], "--gpus", sys.argv[3], *args]))
base_run = sys.argv[2]
rows = list(csv.DictReader(open(f"{FD}/staging_llama.csv")))
with open(sys.argv[3], "w") as f:
    for r in rows:
        slug = re.sub(r"[^a-z0-9]+", "-", r["model_id"].lower()).strip("-")[:60]
        args = common(slug, r["model_id"], r["revision"], f"A2 Llama filter: {r['model_id']} ({r['type']}, {r['pool']})") + fp(
            ["--pool", f"{FD}/staging_llama.csv", "--downloads", f"{FD}/downloads.jsonl", "--derivative-id", r["model_id"],
             "--baseline", f"{base_run}/cell"])
        f.write(json.dumps({"name": r["model_id"], "args": args}) + "\n")
print(len(rows), "jobs")
