#!/usr/bin/env bash
# A3 phase 2 auto-start (claude-ops): wait for the phase-1 queue (codex-resumed) to empty, then build training-prompt jobs that
# forbid every successful phase-1 evaluation set, and run them on the same 12 atlas slots.
set -uo pipefail
WS=/home/heck2/sbhansali8/SpecTLM; Q=$WS/artifacts/A3_queue_20261006; P1=$WS/artifacts/METHOD_priority_20261006/atlas_resumed.log
until grep -q queue_empty "$P1" 2>/dev/null; do sleep 60; done
ls $WS/artifacts/A3-*-eval/cell/prompts.jsonl > $Q/eval_prompt_files.txt
cd /home/heck2/sbhansali8/SpecTLM-ops && python3 ops/waves/A3_magpie.py train $Q/train_jobs.jsonl $Q/eval_prompt_files.txt > $Q/train_build.log 2>&1
SLOTS=$(python3 -c "import json;print(json.load(open('$WS/artifacts/METHOD_priority_20261006/scheduler.json')).get('slots','') if isinstance(json.load(open('$WS/artifacts/METHOD_priority_20261006/scheduler.json')).get('slots',''),str) else ','.join(json.load(open('$WS/artifacts/METHOD_priority_20261006/scheduler.json'))['slots']))" 2>/dev/null)
[ -z "$SLOTS" ] && SLOTS=heck-srv1:6,heck-srv1:7,heck-srv2:0,heck-srv2:1,heck-srv2:2,heck-srv2:3,heck-srv2:4,heck-srv2:5,heck-srv3:2,heck-srv3:3,heck-srv5:5,heck-srv5:7
echo "$SLOTS" > $Q/train_slots.txt
python3 ops/queue.py --slots "$SLOTS" --jobs $Q/train_jobs.jsonl --log $Q/train_queue.log --poll 20 > $Q/train_queue.out 2>&1
