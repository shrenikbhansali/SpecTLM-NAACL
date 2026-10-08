#!/usr/bin/env python3
"""T1 (D-40): render the shared SPEED-128 general workload with each T1 model's own chat template (D-30: template-less pretrained
Llama-3.1-8B uses the Instruct template). Frozen harness code (run-FIX15 6da2e42). Output: artifacts/T1_rendered_20261007/<base>/<slug>/prompts.jsonl + index.json"""
import json, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor
WS = "/home/heck2/sbhansali8/SpecTLM"; CODE = f"{WS}/.worktrees/run-FIX15-pilot-eval-20261007"; PY = f"{WS}/.venv-magpie/bin/python"
OUT = f"{WS}/artifacts/T1_rendered_20261007"; SPEED = f"{WS}/artifacts/B4_public_resolved_20261005/speed128.jsonl"
INSTRUCT = {"llama": ("/home/heck2/sbhansali8/SpecTLM/artifacts/B2_models_20261005/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659", "0e9e39f249a16976918f6564b8830bc894c89659")}
man = [json.loads(l) for l in open(f"{WS}/artifacts/T1_models_20261007/manifest.jsonl") if '"ok"' in l]
def run(r):
    slug = re.sub(r"[^a-z0-9]+", "-", r["id"].lower())[:80]; out = f"{OUT}/{r['base']}/{slug}"
    tok, rev, note = r["path"], r["revision"], "own template"
    if "chat_template" not in json.load(open(r["path"] + "/tokenizer_config.json")) and not os.path.exists(r["path"] + "/chat_template.jinja"):
        tok, rev = INSTRUCT[r["base"]]; note = "D-30: Instruct template (model has none)"
    if os.path.exists(out + "/prompts.jsonl"): return r["id"], out, 0, "exists", note
    p = subprocess.run([PY, "-m", "atlas.workloads", "render-evaluation", "--input", SPEED, "--tokenizer", tok, "--tokenizer-revision", rev,
                        "--family", r["base"], "--output", out, "--capture-rendered-token-ids"], capture_output=True, text=True, cwd=CODE,
                       env=dict(os.environ, HF_HUB_OFFLINE="1"))
    return r["id"], out, p.returncode, p.stderr[-300:], note
with ThreadPoolExecutor(6) as ex: res = list(ex.map(run, man))
idx = {m: {"rendered": out + "/prompts.jsonl", "template": note} for m, out, rc, _, note in res if rc == 0}
json.dump(idx, open(f"{OUT}/index.json", "w"), indent=1)
print(len(man), "models;", len(idx), "rendered"); [print("FAIL", m, e) for m, out, rc, e, _ in res if rc]
