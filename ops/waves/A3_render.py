#!/usr/bin/env python3
"""A3 final step: render every successful evaluation workload with its derivative's pinned tokenizer/template (WORKLOADS.md).
Output: $WS/artifacts/A3_rendered_20261006/<base>/<slug>/ ; index.json maps model_id -> rendered prompts.jsonl."""
import glob, json, os, re, subprocess, sys
GENERAL = len(sys.argv) > 1 and sys.argv[1] == "general"
from concurrent.futures import ThreadPoolExecutor
WS = "/home/heck2/sbhansali8/SpecTLM"; OUT = f"{WS}/artifacts/A3_rendered_20261006"; PY = f"{WS}/.venv-magpie/bin/python"
jobs = []
for d in sorted(glob.glob(f"{WS}/artifacts/A3-*-eval")):
    if not os.path.exists(d + "/cell/config.json"): continue
    if not GENERAL and not os.path.exists(d + "/cell/prompts.jsonl"): continue
    lc = json.load(open(d + "/config.json")); cc = json.load(open(d + "/cell/config.json"))
    m = re.match(r"A3 Magpie evaluation: (.+?) \(", lc["notes"]).group(1); b = lc["base"]
    slug = re.sub(r"[^a-z0-9]+", "-", m.lower())[:80]
    if GENERAL: d = "GENERAL"
    jobs.append((b, m, d, cc["tokenizer"], cc["tokenizer_revision"], f"{OUT}/{b}/{slug}" + ("-speed128" if GENERAL else "")))
if GENERAL:
    seen = {}
    for j in jobs: seen.setdefault((j[0], j[1]), j)
    jobs = list(seen.values())
def run(j):
    b, m, d, tok, rev, out = j
    if os.path.exists(out + "/prompts.jsonl"): return (b, m, out, 0, "exists")
    r = subprocess.run([PY, "-m", "atlas.workloads", "render-evaluation", "--input", (f"{WS}/artifacts/B4_public_resolved_20261005/speed128.jsonl" if d == "GENERAL" else d + "/cell/prompts.jsonl"), "--tokenizer", tok,
                        "--tokenizer-revision", rev, "--family", b, "--output", out, "--capture-rendered-token-ids"],
                       capture_output=True, text=True, cwd="/home/heck2/sbhansali8/SpecTLM-runs/run-A3b-20261006", env=dict(os.environ, HF_HUB_OFFLINE="1"))
    return (b, m, out, r.returncode, r.stderr[-300:])
with ThreadPoolExecutor(8) as ex: res = list(ex.map(run, jobs))
idx = {f"{b}:{m}": {"source": d, "rendered": out + "/prompts.jsonl"} for (b, m, d, *_), (_, _, out, rc, _) in zip(jobs, res) if rc == 0}
json.dump(idx, open(f"{OUT}/index{'_speed128' if GENERAL else ''}.json", "w"), indent=1)
fails = [(b, m, e) for b, m, out, rc, e in res if rc != 0]
print(len(jobs), "workloads;", len(idx), "rendered;", len(fails), "failed"); [print("FAIL", *f) for f in fails[:10]]
