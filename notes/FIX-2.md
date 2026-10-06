# FIX-2 — Exact rendered inputs and matched LoRA settings

## 2026-10-05T23:34:24-04:00 — codex-1 — Claim and acceptance spec

Builder discovered B4→B2 integration bug during B8 acceptance: B4 rendered token_ids start with oneBOS, while feeding the rendered string into vLLM adds a secondBOS. Evidence artifacts/B8_capture_gptq_retry_20261005/cell/per_prompt.jsonl versus artifacts/B8_native_backends_20261005/prompts.jsonl. B2 also lacks an explicit way to enableLoRA on A00 when A10 uses an adapter (operator erratum, MASTER §1(L)); existing matching-settings rule already requires that capability. Add opt-in flags, never change historical default behavior, numbers, gates or thresholds. Owner still chooses protocol decisions; implementing a missing control does not choose a new criterion.

Acceptance tests, written before implementation:
1. Existing default text input remains byte-for-byte the supplied text. Default LoRA behavior remains adapter-dependent.
2. Explicit token-input flag requires validated nonempty integer token_ids and forwards exactly thoseIDs to the engine; missing/badIDs fail before launch.
3. Explicit enable-LoRA flag resolves true even without an adapter and is recorded in config/resolved config; an adapter always enablesLoRA.
4. Paired bounded A40 smoke,5 B4 rendered prompts, pinnedvLLM0.31.0/Eagle3K4/freshcompile: base and ledger-child bothenableLoRA true, same maxrank/prompts/settings, capturedengineIDs exactlyequalrenderedIDs (singleBOS), raw per-request metrics re-derive. No numeric improvement threshold.
5. Pause/dry-run/B2 existing tests pass. Tests and command logs retained; no rerun of historical campaign. Operator later reruns affected production cells if any exist (A4 not launched currently).

Work on codex/FIX-2. No remote available for pull/rebase. B9 P1 pauses while this fix proceeds.
