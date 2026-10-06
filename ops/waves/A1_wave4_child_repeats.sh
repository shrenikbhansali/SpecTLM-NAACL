#!/usr/bin/env bash
# A1 wave 4 (22:05 ET): fresh-compile repeats of the EXP-MTH-018 cell-D child s0, as LoRA (×5) and merged (×5).
# Why: B2's s0 LoRA cell (2.8747) and A1's (2.8554) differ by 0.0193, more than the base A00 fresh-compile range (0.0123);
# the Gate 1 report attributed child-cell uncertainty to base compile noise without child repeats (codex-1 audit,
# notes/BUILD-AUDIT-20261005.md items 4-5). Settings identical to wave 1 child cells; fresh compile per run.
set -euo pipefail
DRY=${DRY:-}
EXTRA='--env VLLM_CACHE_ROOT={out_dir}/vllm_cache'
source <(sed -n '/^RUN=/,/^}/p' "$(dirname "$0")/A1_wave1.sh")
CH=/home/heck2/sbhansali8/cache_big/spectlm_a40_iclr_20260809/artifacts
A=$CH/l31-math-s0-drift-full-a1/adapters/window_003
r=0
for spec in heck-srv2:0 heck-srv2:1 heck-srv2:2 heck-srv2:3 heck-srv2:4; do
  r=$((r+1)); cell ${spec%:*} ${spec#*:} eagle3 $TGT $TREV $E3 $E3REV eagle3 --tag mth018d-lora-s0-fresh --rep $r --adapter $A \
    --adapter-rev EXP-MTH-018-cell-D-seed0-window003 --note "child s0 LoRA fresh-compile repeat $r/5" -- \
    --adapter $A --adapter-revision EXP-MTH-018-cell-D-seed0-window003
done
r=0
for spec in heck-srv5:0 heck-srv5:1 heck-srv5:2 heck-srv5:3 heck-srv5:4; do
  r=$((r+1)); cell ${spec%:*} ${spec#*:} eagle3 $MERGED $TREV $E3 $E3REV eagle3 --tag mth018d-merged-s0-fresh --rep $r \
    --note "child s0 merged fresh-compile repeat $r/5"
done
