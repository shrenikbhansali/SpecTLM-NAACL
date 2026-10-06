#!/usr/bin/env bash
# M1 (D-27) auto-chain, claude-ops: materialize round 1 -> wait for A3 Llama training queue -> baseline -> 63 filter jobs -> admit.
set -uo pipefail
WS=/home/heck2/sbhansali8/SpecTLM; M=$WS/artifacts/M1_20261006; RUN=/home/heck2/sbhansali8/SpecTLM-runs/run-M1-20261006
PY=$WS/.venv-atlas-031-clean/bin/python; OPS=/home/heck2/sbhansali8/SpecTLM-ops
cd $RUN
$PY -m followspec.production materialize --plan $M/plan --output $M/round1 > $M/materialize.log 2>&1 || { echo "materialize failed" > $M/STATUS; exit 1; }
echo materialized > $M/STATUS
until grep -q queue_empty $WS/artifacts/A3_queue_20261006/train_queue_llama.log 2>/dev/null; do sleep 60; done
slots() { S=""; for h in heck-srv1 heck-srv2 heck-srv3 heck-srv5; do f=$(timeout 15 ssh -n -o BatchMode=yes -o ConnectTimeout=6 -o LogLevel=ERROR $h 'nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits' 2>/dev/null | awk -F', ' '$2<1000{printf "%s ",$1}'); for g in $f; do S="$S,$h:$g"; done; done; echo ${S#,}; }
cd $OPS
python3 ops/queue.py --slots heck-srv2:6 --jobs $M/round1/baseline_jobs.jsonl --log $M/baseline_queue.log --poll 20 > $M/baseline_queue.out 2>&1
B=$(python3 -c "import json;print([json.loads(l) for l in open('$M/baseline_queue.log') if '\"finished\"' in l][-1]['exit'])"); echo "baseline exit $B" >> $M/STATUS
[ "$B" = "0" ] || exit 1
S=$(slots); echo "$S" > $M/filter_slots.txt
python3 ops/queue.py --slots "$S" --jobs $M/round1/filter_jobs.jsonl --log $M/filter_queue.log --poll 20 > $M/filter_queue.out 2>&1
echo "filters done" >> $M/STATUS
cd $RUN && $PY -m followspec.production admit --round-dir $M/round1 --output $M/admission1 > $M/admit1.log 2>&1; echo "admit exit $?" >> $M/STATUS
