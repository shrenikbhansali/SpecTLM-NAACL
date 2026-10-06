#!/usr/bin/env bash
# A6 chain (claude-ops): wait capture queue -> prepare + covariate job list -> run covariate queue on free GPUs.
WS=/home/heck2/sbhansali8/SpecTLM; Q=$WS/artifacts/A6_queue_20261006
until grep -q queue_empty $Q/capture_queue.log 2>/dev/null; do sleep 60; done
cd /home/heck2/sbhansali8/SpecTLM-ops && python3 ops/waves/A6_stage2.py $Q/cov_jobs.jsonl > $Q/stage2.log 2>&1
S=""; for h in heck-srv1 heck-srv2 heck-srv3 heck-srv4 heck-srv5; do f=$(timeout 15 ssh -n -o BatchMode=yes -o ConnectTimeout=6 -o LogLevel=ERROR $h 'nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits' 2>/dev/null | awk -F', ' '$2<1000{printf "%s ",$1}'); for g in $f; do S="$S,$h:$g"; done; done; S=${S#,}
echo "$S" > $Q/cov_slots.txt
python3 ops/queue.py --slots "$S" --jobs $Q/cov_jobs.jsonl --log $Q/cov_queue.log --poll 20 > $Q/cov_queue.out 2>&1
