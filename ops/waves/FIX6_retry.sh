#!/bin/bash
# FIX-6 (D-32) zero-step retries: 21 A4 + 7 A7 + 6 A6-capture cells from codex packets, new output paths. Run while M2 waits on FIX-7.
set -u
WS=/home/heck2/sbhansali8/SpecTLM; Q=$WS/artifacts/FIX6_retry_queue_20261006
SLOTS=$(for n in 1 2 3 4 5; do for g in 0 1 2 3 4 5 6 7; do printf "heck-srv$n:$g,"; done; done | sed 's/,$//')
cd $WS
python3 ops/queue.py --owner method-M1 --slots "$SLOTS" --jobs $Q/jobs.jsonl --log $Q/queue.log --poll 15 > $Q/queue.out 2>&1
echo "FIX6 retry queue exit $? $(date +%FT%T)" >> $Q/STATUS
