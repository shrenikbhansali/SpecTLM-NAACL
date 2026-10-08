# FIX-22 — Dispatcher overhead and process identity

## 2026-10-08T00:16:47-04:00 — codex-1 — Claim

Observed repeated12–13s launcherhandoffs while GPUs idle. ops/runs.jsonl records pid:null for4oflast5launches although remotePIDfiles nowexist: launcher waits50×0.2s on shared-filesystemvisibility. Add opt-in no-waitPIDmetadata collection; keep defaultbehavior andactualjobPID/exitfiles unchanged. Also actualqueue processvalidation mustignorediagnostic bashwrappers whoseargumenttext mentions queue.py. Testsfirst; no research/evaluation change. T1/I1 continue runningthroughsolequeue3518506; reports3518508/3518990, hourlyhealth3508524.

## 2026-10-08T00:20:30-04:00 — codex-1 — Tests and implementation

Tests written first (`ops/tests/test_launch_pid.py`); initial missing-symbol failure retained in session output. `python -m pytest ops/tests -q`: **66 passed**. Added opt-in `--no-wait-launch-pid`/`--no-wait-pid`; normal launch behavior retains 50 visibility checks. Real jobs still write PID and exit files. Process guards now inspect actual Python argv, excluding diagnostic shells. No evaluation or model code changed. Next: merge, pin an operational checkout and restart the single dispatcher between launcher transactions.
