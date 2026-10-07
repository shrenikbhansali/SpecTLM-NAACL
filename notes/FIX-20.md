# FIX-20: shared inference export planning race

## 2026-10-07T19:12:22.729445-04:00 — codex-1 — Claim and acceptance specification

Public lambda watcher3028651 stopped with inference export changed or incomplete; simultaneous stress watcher3067243 shares the same per-variant training/evaluation_exports path and completed all three plans. All three training checkpoints prove exactly250 steps. No model weights failed. Verify exact export bytes against source, preserve original failure/logs, serialize all future planners using a shared training-stage lock outside frozen evaluation code, restart public evaluation into fresh directory.

Tests first: concurrent planners for same stage cannot enter export section together; different stage locks remain independent; lock released after exceptions; existing changed-export rejection remains; actual3exports validate and public evaluator passes planning/preflight. Existing evaluation code6da2e42 unchanged. Check and avoid duplicate run identities before dispatch. Full-budget controller continues; move new queue placements off contested heck5, retain launched jobs.

## 2026-10-07T19:17:56.149668-04:00 — codex-1 — Repair verification

Tests were written before implementation: missing-module failure preserved in `artifacts/FIX20_recovery_20261007/first.log`. Added a training-directory flock around shared export planning in all three operations controllers. `python -m pytest ops/tests followspec/tests -q`: 317 passed in 29.90s (`tests.log`). Frozen evaluator unchanged. Called frozen `immutable_export` on all 12 existing exports, comparing complete hashes against source: all passed (`export_audit.json`). New planner lock does not alter export validation. Queue restart excludes contested heck5 and prioritizes matched full-budget pilot-panel cells, then stress lambda cells; existing jobs retained. Evidence: `queue_restart.json`, `dispatch_before.jsonl`. Public watcher will restart into a new output directory; failed original retained.
