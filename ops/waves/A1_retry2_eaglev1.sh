#!/usr/bin/env bash
# A1 EAGLE-v1 retry 2 (18:10 ET). Retry 1 failed offline: HFcache holds only config.json for yuhuili/EAGLE-LLaMA3.1-Instruct-8B
# (the .bin weights are in codex-1's staged cache). Config/path fix: HF_HOME=$WS/artifacts/B2_models_20261005 (same pinned
# revision d0e4a208…, the cache B2's eagle cell used). Settings otherwise identical.
set -euo pipefail
DRY=${DRY:-}
EXTRA="--env HF_HOME=/home/heck2/sbhansali8/SpecTLM/artifacts/B2_models_20261005"
source <(sed -n '/^RUN=/,/^}/p' "$(dirname "$0")/A1_wave1.sh")
cell heck-srv4 4 eagle $TGT $TREV $E1 $E1REV eagle --note "EAGLE-v1 base (retry 2; staged cache with .bin weights)"
