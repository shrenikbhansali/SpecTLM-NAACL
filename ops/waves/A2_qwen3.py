#!/usr/bin/env python3
"""A2 (Qwen3) loadability + coherence filter over B1's final staged list (132 = 100 sampled + all bank adapters).
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
FD = f"{WS}/artifacts/atlas/B1_qwen3_finaldraft_retry_20261005"
BASE_SNAP = "/home/heck2/sbhansali8/HFcache/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218"
BID, BREV = "Qwen/Qwen3-8B", "b968826d9c46dd6066d109eabc6255188de91218"
DR, DRREV = "RedHatAI/Qwen3-8B-speculator.eagle3", "08610ffa01dd9f16731fe8f627b85905b6aa51c4"
REF = f"{WS}/artifacts/A2_reference_qwen3_20261005/reference.jsonl"

def common(tag, target, trev, note):
    return ["--task", "A2", "--base", "qwen3", "--drafter", "eagle3", "--k", "4", "--seed", "0", "--no-resolve", "--tag", tag,
            "--prompts", REF, "--engine-lock", f"{RUN}/atlas/env/requirements.lock", "--python", PY, "--code-repo", RUN,
            "--env", "HF_HUB_OFFLINE=1", "--env", "VLLM_CACHE_ROOT={out_dir}/vllm_cache",
            "--target", target, "--target-rev", trev, "--drafter-model", DR, "--drafter-rev", DRREV, "--note", note, "--"]

def fp(extra):
    return [PY, "-u", "-m", "atlas.filter_pool", "--base-snapshot", BASE_SNAP, "--base-id", BID, "--base-revision", BREV,
            "--reference", REF, "--drafter", DR, "--drafter-revision", DRREV, "--K", "4", "--max-lora-rank", "128",
            "--repetition-threshold", "0.5", "--seed", "0", *extra, "--output", "{out_dir}/cell"]

if sys.argv[1] == "base":
    args = common("base", BID, BREV, "A2 Qwen3 base reference run") + fp(["--derivative-id", "base"])
    sys.exit(subprocess.call([sys.executable, str(Path(__file__).parents[1] / "launch.py"), "run", "--node", sys.argv[2], "--gpus", sys.argv[3], *args]))
base_run = sys.argv[2]
rows = list(csv.DictReader(open(f"{FD}/staging_qwen3.csv")))
with open(sys.argv[3], "w") as f:
    for r in rows:
        slug = re.sub(r"[^a-z0-9]+", "-", r["model_id"].lower()).strip("-")[:60]
        args = common(slug, r["model_id"], r["revision"], f"A2 Qwen3 filter: {r['model_id']} ({r['type']}, {r['pool']})") + fp(
            ["--pool", f"{FD}/staging_qwen3.csv", "--downloads", f"{FD}/downloads.jsonl", "--derivative-id", r["model_id"],
             "--baseline", f"{base_run}/cell"])
        f.write(json.dumps({"name": r["model_id"], "args": args}) + "\n")
print(len(rows), "jobs")
