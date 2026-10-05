#!/usr/bin/env bash
# A1 wave 1 (Gate 1): 20 base A00 replicates + EAGLE-v1 + DFlash + MTH-018 cell-D child (LoRA s0/s1/s2, merged s0).
# Settings identical to B2's golden cells: K=4, greedy seed 0, max_new_tokens 128, batch 1, gpu-mem 0.70.
set -euo pipefail
DRY=${DRY:-}            # DRY=--dry-run for a dry run
RUN=/home/heck2/sbhansali8/SpecTLM-runs/run-A1-20261005
PY=/home/heck2/sbhansali8/SpecTLM/.venv-atlas-031-clean/bin/python
P=/home/heck2/sbhansali8/cache_big/spectlm_a40_iclr_20260809/artifacts/l31-math-s0-splits-full-a1/splits/evaluation.jsonl
CH=/home/heck2/sbhansali8/cache_big/spectlm_a40_iclr_20260809/artifacts
TGT=meta-llama/Llama-3.1-8B-Instruct; TREV=0e9e39f249a16976918f6564b8830bc894c89659
E3=RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3; E3REV=f4fa34a8f803a0ba75d048d6b3dbc1ad5149e9ac
E1=yuhuili/EAGLE-LLaMA3.1-Instruct-8B; E1REV=d0e4a2087339ece9fc619b7773846e329e995768
DF=z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat; DFREV=d3af30def9601abdd10810aba220d692f0e803f0
MERGED=/home/heck2/sbhansali8/SpecTLM/artifacts/B2_merge_20261005/model
L="python3 $(dirname "$0")/../launch.py run $DRY --task A1 --base llama --k 4 --seed 0 --no-resolve --prompts $P --engine-lock $RUN/atlas/env/requirements.lock --python $PY --code-repo $RUN --env HF_HUB_OFFLINE=1 ${EXTRA:-}"
cell() { # node gpu drafter-label tgt trev dmodel drev method [extra launcher args] -- [extra run_cell args]
  local node=$1 gpu=$2 dl=$3 tgt=$4 trev=$5 dm=$6 dr=$7 meth=$8; shift 8
  local la=() ra=(); while [[ $# -gt 0 && $1 != -- ]]; do la+=("$1"); shift; done; [[ ${1:-} == -- ]] && shift; ra=("$@")
  $L --drafter "$dl" --node "$node" --gpus "$gpu" --target "$tgt" --target-rev "$trev" --drafter-model "$dm" --drafter-rev "$dr" "${la[@]}" -- \
    "$PY" -u -m atlas.run_cell --target "$tgt" --target-revision "$trev" --drafter "$dm" --drafter-revision "$dr" --method "$meth" \
    --K 4 --prompts "$P" --seed 0 --max-new-tokens 128 --gpu-memory-utilization .70 --output "{out_dir}/cell" "${ra[@]}"
}
# r01/r02 were started at 17:56/17:58 by the first (hanging-ssh) attempt and are registered by hand; start at r03.
r=2
for spec in heck-srv2:2 heck-srv2:3 heck-srv2:4 heck-srv2:5 heck-srv2:6 heck-srv2:7 \
            heck-srv5:0 heck-srv5:1 heck-srv5:2 heck-srv5:3 heck-srv5:4 heck-srv5:5 heck-srv5:6 heck-srv5:7 \
            heck-srv4:0 heck-srv4:1 heck-srv4:2 heck-srv4:3; do
  r=$((r+1)); cell ${spec%:*} ${spec#*:} eagle3 $TGT $TREV $E3 $E3REV eagle3 --rep $r --note "A00 noise-floor replicate $r/20"
done
cell heck-srv4 4 eagle $TGT $TREV $E1 $E1REV eagle --note "EAGLE-v1 base"
cell heck-srv4 5 dflash $TGT $TREV $DF $DFREV dflash --note "DFlash base, K=4 (trained block size 10)"
for s in 0 1 2; do
  node=heck-srv4; gpu=6; [[ $s == 1 ]] && { node=heck-srv1; gpu=6; }; [[ $s == 2 ]] && { node=heck-srv1; gpu=7; }
  cell $node $gpu eagle3 $TGT $TREV $E3 $E3REV eagle3 --tag mth018d-lora-s$s --adapter $CH/l31-math-s$s-drift-full-a1/adapters/window_003 \
    --adapter-rev EXP-MTH-018-cell-D-seed$s-window003 --note "A10: EXP-MTH-018 cell D child seed $s (LoRA, w3)" -- \
    --adapter $CH/l31-math-s$s-drift-full-a1/adapters/window_003 --adapter-revision EXP-MTH-018-cell-D-seed$s-window003
done
cell heck-srv3 0 eagle3 $MERGED $TREV $E3 $E3REV eagle3 --tag mth018d-merged-s0 --note "A10: same child seed 0, merged (B2_merge_20261005)"
