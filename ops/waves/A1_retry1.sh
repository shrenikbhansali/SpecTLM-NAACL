#!/usr/bin/env bash
# A1 retry 1 (18:08 ET): EAGLE-v1 base and MTH-018 child s0 LoRA failed on HF 429 during engine init.
# Same settings; HF_HUB_OFFLINE=1 (all models cached at pinned revisions). §8.3 infrastructure retry 1 of 2.
set -euo pipefail
DRY=${DRY:-}
source <(sed -n '/^RUN=/,/^}/p' "$(dirname "$0")/A1_wave1.sh")
CH=/home/heck2/sbhansali8/cache_big/spectlm_a40_iclr_20260809/artifacts
cell heck-srv4 4 eagle $TGT $TREV $E1 $E1REV eagle --note "EAGLE-v1 base (retry 1 of A1-llama-eagle-k4-s0-202610051805, HF 429)"
cell heck-srv4 6 eagle3 $TGT $TREV $E3 $E3REV eagle3 --tag mth018d-lora-s0 --adapter $CH/l31-math-s0-drift-full-a1/adapters/window_003 \
  --adapter-rev EXP-MTH-018-cell-D-seed0-window003 --note "A10: MTH-018 cell D child seed 0 (retry 1, HF 429)" -- \
  --adapter $CH/l31-math-s0-drift-full-a1/adapters/window_003 --adapter-revision EXP-MTH-018-cell-D-seed0-window003
