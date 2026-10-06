#!/bin/bash
# M2 mixture Magpie prompts retry 1: original jobs ran in .venv-atlas-031-clean (no langdetect) and failed at post-filtering.
# Same args, .venv-magpie interpreter + PATH (A3 precedent, vLLM 0.31.0), new output dirs under mixture_prompts_retry1/runs.
set -u
WS=/home/heck2/sbhansali8/SpecTLM; M=$WS/artifacts/M2_D28_20261006
SLOTS=$(for n in 1 2 3 4 5; do for g in 0 1 2 3 4 5 6 7; do printf "heck-srv$n:$g,"; done; done | sed 's/,$//')
cd $WS
python3 ops/queue.py --owner method-M1 --slots "$SLOTS" --jobs $M/mixture_prompts_retry1/jobs.jsonl --log $M/mixture_retry1_queue.log --poll 15 > $M/mixture_retry1_queue.out 2>&1
echo "mixture prompts retry1 queue exit $? $(date +%FT%T)" >> $M/STATUS
