#!/usr/bin/env bash
# ICE engine validation: re-run the Gate 1 reference cell (Llama-3.1-8B-Instruct + RedHatAI EAGLE-3, K=4, 128 GSM8K prompts,
# 512 new tokens, greedy, seed 0, fresh compile per cell) N times on ICE GPUs and compare with heck (EXP-ATL-002:
# n=20 fresh compiles, mean 3.105030, SD 0.002910, range 3.102709–3.111301, A40).
# Usage: source sites/ice.env && bash ops/ice/validate.sh [N=5]        then: python3 ops/ice/validate_compare.py
# Needs: .venv-atlas-031-clean built (build_envs.sh), core models staged, clean checkout at main or a run-* tag.
set -euo pipefail
: "${WS:?source sites/ice.env}" "${ATLAS_PY:?}"
N=${1:-5}
P=$WS/ops/ice/validation/gsm8k128_evaluation.jsonl
echo "e365702983e4e1c5d640c6100a9b3ca46e16bc285520a237101137d0bab99ea7  $P" | sha256sum -c -
TGT=meta-llama/Llama-3.1-8B-Instruct; TREV=0e9e39f249a16976918f6564b8830bc894c89659
E3=RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3; E3REV=f4fa34a8f803a0ba75d048d6b3dbc1ad5149e9ac
OUT=$WS/artifacts/ICE_validation_$(date +%Y%m%d%H%M); mkdir -p "$OUT"; : > "$OUT/jobs.jsonl"
for r in $(seq 1 "$N"); do
  python3 - "$r" >> "$OUT/jobs.jsonl" <<PY
import json,sys
r=int(sys.argv[1])
args=["--task","ICEV","--base","llama","--drafter","eagle3","--k","4","--seed","0","--no-resolve","--tag","freshcompile-mnt512","--rep",str(r),
 "--target","$TGT","--target-rev","$TREV","--drafter-model","$E3","--drafter-rev","$E3REV",
 "--prompts","$P","--engine-lock","$WS/atlas/env/requirements.lock","--python","$ATLAS_PY","--code-repo","$WS",
 "--env","HF_HUB_OFFLINE=1","--env","VLLM_CACHE_ROOT={out_dir}/vllm_cache","--note",f"ICE validation replicate {r}",
 "--","$ATLAS_PY","-u","-m","atlas.run_cell","--target","$TGT","--target-revision","$TREV","--drafter","$E3","--drafter-revision","$E3REV",
 "--method","eagle3","--K","4","--prompts","$P","--seed","0","--max-new-tokens","512","--gpu-memory-utilization",".70","--output","{out_dir}/cell"]
print(json.dumps(dict(name=f"icev-r{r:02d}",args=args)))
PY
done
python3 "$WS/ops/ice/submit.py" --jobs "$OUT/jobs.jsonl" --log "$OUT/submit.log" --time 01:00:00
echo "$OUT" > "$WS/artifacts/ICE_validation_LATEST"
echo "submitted $N validation cells -> $OUT ; when done: python3 ops/ice/validate_compare.py"
