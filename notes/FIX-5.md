# FIX-5 — Magpie oversampling and cleanup

## 2026-10-06T03:51:21-04:00 — codex-1 — Claim

Read MASTER§0–4/7/13, D-23 and notes/A3.md. Fixed production loop20×64 requests is insufficient for Qwen3; shortfall raises before engine shutdown, retaining GPUs. Scope: D-23 explicit bounded oversampling up to5× requested prompt budget, preserve filters/settings/seeds and originals; shortfall result marks own_domain unavailable, never publishes partial prompts as full workload. Engine shutdown in finally on success/error/shortfall. Tests first: multiple rounds,5× cap including length-terminated completions, duplicate/forbidden filtering across rounds, clean shortfall and cleanup on all exit paths. Build codex/FIX-5. B6 capacity retry runs on reservedGPU7;GPU6 available for bounded FIX-5 smoke. No production sweep launches by builder.
