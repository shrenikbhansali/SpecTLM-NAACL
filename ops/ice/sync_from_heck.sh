#!/usr/bin/env bash
# Copy the sealed inputs ICE work needs from heck into $WS/artifacts (rsync, read-only on heck; never deletes on either side).
# Usage (on ICE login node, after `source sites/ice.env`):  bash ops/ice/sync_from_heck.sh [--dry-run] [set ...]
# Sets (default: method):
#   method   M1 admission + selected mixture adapters, M2 sealed corpus (finalized_D36), D-38 pilot corpus, M4 targets, D-39 panel,
#            B4 public workloads, A3 rendered prompts, speculators source   (~21 GB, mostly the 60 candidate mixtures)
#   valid    the 128-prompt GSM8K file used by the ICE validation cells (also vendored in ops/ice/validation/)
# Sealed bytes are copied unchanged. Follow README relocation inventory/verification before using them.
set -euo pipefail
: "${WS:?source sites/ice.env}" "${HECK_HOST:?set HECK_HOST}" "${HECK_WS:?set HECK_WS}"
DRY=""; [[ "${1:-}" == --dry-run ]] && { DRY="--dry-run"; shift; }
sets=("$@"); [[ ${#sets[@]} -eq 0 ]] && sets=(method)
method=(
  M1_D28_20261006/admission2 M1_D28_20261006/plan M1_D28_20261006/round1/mixtures M1_D28_20261006/round2/mixtures
  M2_D28_20261006/finalized_D36 M2_D28_20261006/assembly_split_proposal M2_inputs_20261006
  M2_D28_20261006/responses/runs M2_D28_20261006/responses_parent_parallel/joined-parent
  M3_pilot_D38_20261007/finalized M3_pilot_D38_20261007/panel.json M4_inputs_20261006 D39_stress_20261007/panel
  B4_public_resolved_20261005 A3_rendered_20261006 speculators_source_20261005 FIX4_D28_final_eligibility_20261006
)
for s in "${sets[@]}"; do
  case $s in
    method) for p in "${method[@]}"; do
              mkdir -p "$WS/artifacts/$(dirname "$p")"
              echo "== $p"; rsync -a $DRY --info=stats1 "$HECK_HOST:$HECK_WS/artifacts/$p" "$WS/artifacts/$(dirname "$p")/"
            done ;;
    valid)  echo "vendored: $WS/ops/ice/validation/gsm8k128_evaluation.jsonl" ;;
    *) echo "unknown set $s"; exit 1 ;;
  esac
done
echo "SYNC DONE ($(date -Is)); record this in notes/O2.md with the set names"
