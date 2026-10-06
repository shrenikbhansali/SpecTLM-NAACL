#!/usr/bin/env bash
# M1 fresh plan: retry 34 failed filters (other-user GPU collision on srv3) then admit. claude-ops.
WS=/home/heck2/sbhansali8/SpecTLM; M=$WS/artifacts/M1_D28_20261006
cd /home/heck2/sbhansali8/SpecTLM-ops && python3 ops/queue.py --owner method-M1 --slots "heck-srv1:0,heck-srv1:1,heck-srv1:2,heck-srv1:3,heck-srv1:4,heck-srv1:5,heck-srv1:6,heck-srv1:7,heck-srv2:0,heck-srv2:1,heck-srv2:2,heck-srv2:3,heck-srv2:4,heck-srv2:5,heck-srv2:6,heck-srv2:7,heck-srv3:0,heck-srv3:1,heck-srv3:2,heck-srv3:3,heck-srv3:4,heck-srv3:5,heck-srv3:6,heck-srv3:7,heck-srv4:0,heck-srv4:1,heck-srv4:2,heck-srv4:3,heck-srv4:4,heck-srv4:5,heck-srv4:6,heck-srv4:7,heck-srv5:0,heck-srv5:1,heck-srv5:2,heck-srv5:3,heck-srv5:4,heck-srv5:5,heck-srv5:6,heck-srv5:7" --jobs $M/round1_retry1/filter_jobs.jsonl --log $M/retry1_queue.log --poll 15 > $M/retry1_queue.out 2>&1
echo "retry1 filters done" >> $M/STATUS
cd $WS/.worktrees/run-method-D28-20261006 && $WS/.venv-atlas-031-clean/bin/python -m followspec.production admit --round-dir $M/round1_retry1 --output $M/admission1_retry1 > $M/admit1_retry1.log 2>&1; echo "admit-after-retry1 exit $?" >> $M/STATUS
