#!/usr/bin/env bash
# A1 wave 2: 20 base A00 replicates (EAGLE-3), each with a FRESH vLLM compile cache (VLLM_CACHE_ROOT=<run>/vllm_cache).
# Why: wave-1 replicates all loaded one shared AOT-compiled graph from ~/.cache/vllm and are bit-identical, while B2's
# base/repeat (separate per-cell caches) differ by 0.0083. Between-compile variation is the noise relevant when cells
# compile separately. Settings otherwise identical to wave 1.
set -euo pipefail
DRY=${DRY:-}
EXTRA='--env VLLM_CACHE_ROOT={out_dir}/vllm_cache'
source <(sed -n '/^RUN=/,/^}/p' "$(dirname "$0")/A1_wave1.sh")
r=0
for spec in ${SPECS:?set SPECS="node:gpu ..." (20 entries)}; do
  r=$((r+1)); cell ${spec%:*} ${spec#*:} eagle3 $TGT $TREV $E3 $E3REV eagle3 --tag freshcompile --rep $r --note "A00 fresh-compile replicate $r/20"
done
