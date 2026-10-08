# FIX-22 — Dispatcher overhead and process identity

## 2026-10-08T00:16:47-04:00 — codex-1 — Claim

Observed repeated12–13s launcherhandoffs while GPUs idle. ops/runs.jsonl records pid:null for4oflast5launches although remotePIDfiles nowexist: launcher waits50×0.2s on shared-filesystemvisibility. Add opt-in no-waitPIDmetadata collection; keep defaultbehavior andactualjobPID/exitfiles unchanged. Also actualqueue processvalidation mustignorediagnostic bashwrappers whoseargumenttext mentions queue.py. Testsfirst; no research/evaluation change. T1/I1 continue runningthroughsolequeue3518506; reports3518508/3518990, hourlyhealth3508524.
