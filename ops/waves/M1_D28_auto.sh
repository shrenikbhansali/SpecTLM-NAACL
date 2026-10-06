#!/usr/bin/env bash
# M1 (fresh D-28 plan, owner D-33): baseline -> 60 filters -> admit, on method-reserved slots (claude-ops).
set -uo pipefail
WS=/home/heck2/sbhansali8/SpecTLM; M=$WS/artifacts/M1_D28_20261006; RUN=$WS/.worktrees/run-method-D28-20261006; PY=$WS/.venv-atlas-031-clean/bin/python
SL=$(python3 -c "import json;print(','.join(json.load(open('$WS/ops/gpu_reservations.json'))['slots']))")
cd /home/heck2/sbhansali8/SpecTLM-ops
python3 ops/queue.py --owner method-M1 --slots heck-srv2:0 --jobs $M/round1/baseline_jobs.jsonl --log $M/baseline_queue.log --poll 15 > $M/baseline_queue.out 2>&1
B=$(python3 -c "import json;print([json.loads(l) for l in open('$M/baseline_queue.log') if '\"finished\"' in l][-1]['exit'])"); echo "baseline exit $B" >> $M/STATUS; [ "$B" = "0" ] || exit 1
python3 ops/queue.py --owner method-M1 --slots "$SL" --jobs $M/round1/filter_jobs.jsonl --log $M/filter_queue.log --poll 15 > $M/filter_queue.out 2>&1
echo "filters done" >> $M/STATUS
cd $RUN && $PY -m followspec.production admit --round-dir $M/round1 --output $M/admission1 > $M/admit1.log 2>&1; echo "admit exit $?" >> $M/STATUS
