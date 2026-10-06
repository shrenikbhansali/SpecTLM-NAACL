#!/usr/bin/env bash
# A1 wave 3 (18:22 ET): (a) 20 fresh-compile EAGLE-3 base A00 replicates at max_new_tokens 512 (atlas protocol setting;
# noise floor at the length the atlas will use); (b) 5 fresh-compile DFlash base replicates at 128 (B2 and A1 DFlash cells
# differ by 0.018; no DFlash noise estimate exists). Settings otherwise as wave 1.
set -euo pipefail
DRY=${DRY:-}
EXTRA='--env VLLM_CACHE_ROOT={out_dir}/vllm_cache'
source <(sed -n '/^RUN=/,/^}/p' "$(dirname "$0")/A1_wave1.sh")
r=0
for spec in heck-srv2:0 heck-srv2:1 heck-srv2:2 heck-srv2:3 heck-srv2:4 heck-srv2:5 heck-srv2:6 heck-srv2:7 \
            heck-srv5:0 heck-srv5:1 heck-srv5:2 heck-srv5:3 heck-srv5:4 heck-srv5:5 heck-srv5:6 heck-srv5:7 \
            heck-srv4:0 heck-srv4:1 heck-srv4:2 heck-srv4:3; do
  r=$((r+1)); MAXTOK=512 cell ${spec%:*} ${spec#*:} eagle3 $TGT $TREV $E3 $E3REV eagle3 --tag freshcompile-mnt512 --rep $r \
    --note "A00 fresh-compile replicate $r/20 at max_new_tokens 512"
done
r=0
for spec in heck-srv4:4 heck-srv4:5 heck-srv4:6 heck-srv1:6 heck-srv1:7; do
  r=$((r+1)); cell ${spec%:*} ${spec#*:} dflash $TGT $TREV $DF $DFREV dflash --tag freshcompile --rep $r --note "DFlash fresh-compile replicate $r/5"
done
