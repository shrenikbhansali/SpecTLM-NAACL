# FIX-20: shared inference export planning race

## 2026-10-07T19:12:22.729445-04:00 — codex-1 — Claim and acceptance specification

Public lambda watcher3028651 stopped with inference export changed or incomplete; simultaneous stress watcher3067243 shares the same per-variant training/evaluation_exports path and completed all three plans. All three training checkpoints prove exactly250 steps. No model weights failed. Verify exact export bytes against source, preserve original failure/logs, serialize all future planners using a shared training-stage lock outside frozen evaluation code, restart public evaluation into fresh directory.

Tests first: concurrent planners for same stage cannot enter export section together; different stage locks remain independent; lock released after exceptions; existing changed-export rejection remains; actual3exports validate and public evaluator passes planning/preflight. Existing evaluation code6da2e42 unchanged. Check and avoid duplicate run identities before dispatch. Full-budget controller continues; move new queue placements off contested heck5, retain launched jobs.
