#!/usr/bin/env bash
# A7 prep (22:23 ET): which K settings the pinned engine accepts for DFlash (trained block size 10), and acceptance at each.
# Engineering probe for A7's design (GATE-1 decision 4), not a sweep. Golden GSM8K-128, 128 tok, fresh compile, as A1.
set -euo pipefail
DRY=${DRY:-}
EXTRA='--env VLLM_CACHE_ROOT={out_dir}/vllm_cache'
source <(sed -n '/^RUN=/,/^}/p' "$(dirname "$0")/A1_wave1.sh")
L=${L/--task A1/--task A7}
cellk() { local node=$1 gpu=$2 k=$3
  $L --drafter dflash --node $node --gpus $gpu --target $TGT --target-rev $TREV --drafter-model $DF --drafter-rev $DFREV \
     --tag kprobe --note "DFlash K probe K=$k" -- \
    "$PY" -u -m atlas.run_cell --target $TGT --target-revision $TREV --drafter $DF --drafter-revision $DFREV --method dflash \
    --K $k --prompts "$P" --seed 0 --max-new-tokens 128 --gpu-memory-utilization .70 --output "{out_dir}/cell"
}
L="${L/--k 4/}"
for spec in heck-srv3:0:8 heck-srv3:1:9 heck-srv3:2:10; do IFS=: read n g k <<<"$spec"; L2="$L --k $k"; L_SAVE=$L; L=$L2; cellk $n $g $k; L=$L_SAVE; done
