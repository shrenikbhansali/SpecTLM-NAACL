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

## 2026-10-05T23:38:45-04:00 — codex-1 — Tests pass, paired GPU acceptance running

Tests first missing-function error saved FIX-2_before_20261005.log;21 input-control/B2 tests pass (FIX-2_after_20261005.log). Branch06022d0 records requested/effectiveLoRA separately, forwards exact validated token IDs under newflag, and checks returnedIDs for unexpected engine changes. Docs include B4/A4/A6 integration. Historical text/adapter-dependent defaults unchanged.

Started bounded paired5-prompt checks on free heck-srv3 GPUs5/6: PIDs1065578/1065586, base/child at artifacts/FIX-2_acceptance_20261005. Both enableLoRA rank128 and explicit token inputs, same prompt file/engine/drafter/K4/seed0/maxnew64; each fresh compile cache. No other process touched. Verify actual capturedIDs singleBOS and raw metric rederivation, then merge/review. Main source unchanged until checks pass.

## 2026-10-05T23:45:33-04:00 — codex-1 — Failed integration check exposes raw/rendered field distinction

First paired native runs completed, but acceptance check correctly FAILED the required singleBOS assertion. ActualIDs matched providedIDs; **B4 existing token_ids are raw-query IDs**, not rendered context IDs. Earlier entries describing them as rendered were incorrect. Preserve FIX-2_acceptance_20261005 and its failed checker; these runs are not B4-production evidence. No main code merged.

New tests written before correction: raw IDs must be rejected, explicit rendered-token capture preserves raw fields. Four failures preserved FIX-2_rendered_before_20261005.log; now34 input/B2/B4 tests pass. Branch898f0c7 adds optional B4 --capture-rendered-token-ids, storing separate rendered_token_ids with add_special_tokens=False; B2 explicitinput mode requires this field. Existing defaults/raw token fields unchanged. Five raw queries restored from saved raw_prompt into a new acceptance-only input and rendered into FIX-2_rendered_retry_20261005/rendered. InspectedIDs start exactlyone128000 then128006; full chat text includes same raw queries. Paired rerun uses new data/compile caches, same guards and settings; outputs preserved separately.

## 2026-10-05T23:51:05-04:00 — codex-1 — Acceptance / Review / Handoff

Corrected paired GPU check **passes**: artifacts/FIX-2_rendered_retry_20261005/acceptance.json. Base and child5 prompts each receive exact rendered_token_ids with oneBOS, bothenableLoRA rank128, fresh per-cell compile caches, same engine/drafter/K/seed/length/promptsettings. Raw counters independently rederive every metric and aggregate. B8 preparation accepts the actualchild source and rejects thebase source on revision mismatch. Decode/mask audit of five new childanswers saved decoded_audit.jsonl; errors/truncation retained, evaluation-only.

Code898f0c7 merged after34 CPU tests and corrected native acceptance; boardreview. Prior incorrect raw-token integration acceptance remains preserved and failed, never promoted. Operator: re-run34 tests and check.py with a new --report path; for production regenerate B4 rendered files with --capture-rendered-token-ids, run B2 --use-prompt-token-ids --capture-prompt-token-ids, and use --enable-lora with same maxrank for bothLoRA A00/A10 cells. Historical defaults/numbers unchanged. No FIX-2 GPU job remains. Return to B9 producer and realvalidation; no waiting for gate calendar dates.
