#!/usr/bin/env python3
"""A6 stage 2: prepare_covariates for every successful A6 capture cell, then covariate jobs (child + one base/self per base).
Usage: A6_stage2.py OUT_JOBS  (runs prepare on CPU first; writes queue jobs for the GPU passes)."""
import csv, glob, json, os, re, subprocess, sys
csv.field_size_limit(10**9)
WS = "/home/heck2/sbhansali8/SpecTLM"; RUN = "/home/heck2/sbhansali8/SpecTLM-runs/run-A4-20261006"; PY = f"{WS}/.venv-covariates/bin/python"
SEQ = f"{WS}/artifacts/A6_sequences_20261006"
B = {"llama": dict(snap=f"{WS}/artifacts/B2_models_20261005/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659",
                   rev="0e9e39f249a16976918f6564b8830bc894c89659",
                   dr=f"{WS}/artifacts/B2_models_20261005/hub/models--RedHatAI--Llama-3.1-8B-Instruct-speculator.eagle3/snapshots/f4fa34a8f803a0ba75d048d6b3dbc1ad5149e9ac",
                   drrev="f4fa34a8f803a0ba75d048d6b3dbc1ad5149e9ac"),
     "qwen3": dict(snap="/home/heck2/sbhansali8/HFcache/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218",
                   rev="b968826d9c46dd6066d109eabc6255188de91218",
                   dr="/home/heck2/sbhansali8/HFcache/hub/models--RedHatAI--Qwen3-8B-speculator.eagle3/snapshots/08610ffa01dd9f16731fe8f627b85905b6aa51c4",
                   drrev="08610ffa01dd9f16731fe8f627b85905b6aa51c4")}
man = {}
for b in B:
    for r in csv.DictReader(open(f"{WS}/artifacts/atlas/pool_manifest_{b}.csv")): man[(b, r["model_id"])] = r
jobs = []; first_seq = {}
for d in sorted(glob.glob(f"{WS}/artifacts/A6-*-A6cap-*") + glob.glob(f"{WS}/artifacts/A6-*-A10-*")):
    if not os.path.exists(d + "/exit_code") or open(d + "/exit_code").read().strip() != "0": continue
    lc = json.load(open(d + "/config.json")); b = lc["base"]
    m = re.search(r"workload=\w+ (.+?) \(", lc["notes"]).group(1); r = man[(b, m)]
    out = f"{SEQ}/{b}/{re.sub(r'[^a-z0-9]+', '-', m.lower())[:70]}"
    if not os.path.exists(out + "/sequences.jsonl"):
        p = subprocess.run(["python3", "-m", "atlas.prepare_covariates", "--cell", d + "/cell", "--output", out], cwd=RUN, capture_output=True, text=True)
        if p.returncode: print("PREPARE FAIL", m, p.stderr[-200:]); continue
    first_seq.setdefault(b, out + "/sequences.jsonl"); x = B[b]
    tgt = ["--adapter", r["staged_path"]] if r["type"] == "lora_adapter" else ["--child", r["staged_path"]]
    cmd = [PY, "-u", "-m", "atlas.covariates", "--base", x["snap"], "--base-revision", x["rev"], "--drafter", x["dr"], "--drafter-revision", x["drrev"],
           *tgt, "--derivative-id", m, "--derivative-revision", r["revision"], "--sequences", out + "/sequences.jsonl", "--output", "{out_dir}/cell"]
    slug = re.sub(r"[^a-z0-9]+", "-", m.lower())[:50]
    jobs.append({"name": f"{b}:cov:{m}", "args": ["--task", "A6", "--base", b, "--drafter", "cov", "--k", "0", "--seed", "0", "--no-resolve", "--tag", slug,
        "--prompts", out + "/sequences.jsonl", "--engine-lock", f"{RUN}/atlas/env/covariates-requirements.lock", "--python", PY, "--code-repo", RUN,
        "--env", "HF_HUB_OFFLINE=1", "--env", "OMP_NUM_THREADS=4", "--target", m, "--target-rev", r["revision"], "--note", f"A6 covariates {b} {m} ({r['type']})", "--", *cmd]})
for b, x in B.items():
    cmd = [PY, "-u", "-m", "atlas.covariates", "--base", x["snap"], "--base-revision", x["rev"], "--drafter", x["dr"], "--drafter-revision", x["drrev"],
           "--derivative-id", "base", "--derivative-revision", x["rev"], "--sequences", first_seq[b], "--output", "{out_dir}/cell"]
    jobs.insert(0, {"name": f"{b}:cov:base-self", "args": ["--task", "A6", "--base", b, "--drafter", "cov", "--k", "0", "--seed", "0", "--no-resolve", "--tag", "base-self",
        "--prompts", first_seq[b], "--engine-lock", f"{RUN}/atlas/env/covariates-requirements.lock", "--python", PY, "--code-repo", RUN,
        "--env", "HF_HUB_OFFLINE=1", "--env", "OMP_NUM_THREADS=4", "--target", "base", "--target-rev", x["rev"], "--note", f"A6 covariates base/self {b} (zero control)", "--", *cmd]})
open(sys.argv[1], "w").write("".join(json.dumps(j) + "\n" for j in jobs)); print(len(jobs), "covariate jobs")
