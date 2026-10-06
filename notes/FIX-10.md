# FIX-10 — Immutable M2 response recovery

## 2026-10-06T17:47:50-04:00 — codex-1 — Claim

M2 parent response job target-019-base failed before generating records: engine reports availableKVcache -5.48GiB, CUDA graph memory delta -16.63GiB. Only this job failed; other same-engine/settings jobs succeed. Preserve original failure and first try identical controls in a new directory on a free slot. Need an immutable response-plan overlay so completed120other sources remain usable and assembly references the successful retry. Tests first; no data/seed/recipe changes, no overwrite, no waiver. Failed path artifacts/M2_D28_20261006/responses/runs/target-019-base; launcher M2-llama-method-data-k0-s20261006-202610061743-responses-response-019-base. Prior CPU assembly watcher correctly stopped on the failure. Original GPUqueuePID2187668 continues; do not duplicate it.
