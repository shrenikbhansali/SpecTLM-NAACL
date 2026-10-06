#!/usr/bin/env bash
# M1: run codex's 2-job retry overlay (FIX-4) then admit; claude-ops.
set -uo pipefail
R=/home/heck2/sbhansali8/SpecTLM/artifacts; O=$R/FIX4_M1_retry_overlay_20261006; M=$R/M1_20261006
cd /home/heck2/sbhansali8/SpecTLM-ops && python3 ops/queue.py --slots heck-srv2:6,heck-srv2:7 --jobs $O/filter_jobs.jsonl --log $M/filter_retry_queue.log --poll 20 > $M/filter_retry_queue.out 2>&1
echo "retry filters done" >> $M/STATUS
cd /home/heck2/sbhansali8/SpecTLM-runs/run-M1-20261006 && /home/heck2/sbhansali8/SpecTLM/.venv-atlas-031-clean/bin/python -m followspec.production admit --round-dir $O --output $M/admission1_after_retry > $M/admit1_retry.log 2>&1; echo "admit-after-retry exit $?" >> $M/STATUS
