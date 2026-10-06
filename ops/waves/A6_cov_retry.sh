#!/bin/bash
# A6 covariate retry 1: 18 jobs that hit CUDA OOM from GPU sharing (pre live-check). Same args, tag -r1, new out dirs.
set -u
WS=/home/heck2/sbhansali8/SpecTLM; Q=$WS/artifacts/A6_queue_20261006
SLOTS=$(for n in 1 2 3 4 5; do for g in 0 1 2 3 4 5 6 7; do printf "heck-srv$n:$g,"; done; done | sed 's/,$//')
cd $WS
python3 ops/queue.py --owner method-M1 --slots "$SLOTS" --jobs $Q/cov_retry1_jobs.jsonl --log $Q/cov_retry1_queue.log --poll 15 > $Q/cov_retry1_queue.out 2>&1
echo "A6 cov retry1 queue exit $? $(date +%FT%T)" >> $Q/STATUS
