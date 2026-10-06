# FIX-6 — zero-step requests and paired analysis

## 2026-10-06T12:55:54-04:00 — codex-1 — Claim

Read D32 and A4 failure evidence. Record requests with no speculative steps using zero counters, zero_step=true and null undefined metrics; exclude from cell macro, report total/valid/zero counts. Pairwise analyses must intersect nonzero prompt IDs and report exclusions; never compare independent per-cell subsets. Preserve existing normal outputs and historical artifacts. Write regression tests first, then implementation, including strict malformed-counter rejection and all-zero behavior. No GPU production submission; original failed cells require operator retries with new IDs. FIX4 CPU materialization proceeds in background; no active pause marker.

## 2026-10-06T13:04:10-04:00 — codex-1 — Core D32 checks pass; broad verification in progress

Wrote tests first:9 failures in FIX6_before_20261006.log and2 Gate3 failures in FIX6_gate_before_20261006.log. Targeted33 nowPASS (FIX6_gate_after_20261006.log). Added zero-step persistence with null undefined rates, explicit aggregate n_total/n_zero_step/n-valid, strict actual pinned-engine histogram checks, shared paired-cell reader/CLI, and Gate3 pairwise exclusions for target-shift cells, arm gains, retention and parent TOST. Synthetic real-main injection proves a zero-step request is written and later requests still complete; it is not a GPU smoke. Read local vLLM0.31 RequestSpecDecodeMetrics and scheduler source: requests initialize a zero histogram and empty arrays, not missing metrics.

Real immutable legacy audit (`PYTHONPATH=. python3 artifacts/FIX6_legacy_audit_20261006/check.py` from branch):1435 successful A4/A7 cells reconstruct exactly, zero discrepancies. Evidence in artifacts/FIX6_legacy_audit_20261006/results.json, including source hashes. Existing successful cells need no numerical rerun.21 A4 +7 A7 queue failures still need new output paths after merge.

Broad collection initially failed because system Python lacks compressed_tensors; pinned engine env lacks scipy/matplotlib. Kept both failures in FIX6_integrated_20261006.log and FIX6_pinned_integrated_20261006.log. Run normal CPU suite in system Python excluding only native CT test, and run that native CT test separately in pinned environment. Do not mutate locked environments to combine test dependencies.

## 2026-10-06T13:04:56-04:00 — codex-1 — Acceptance complete

Full suite:265 distinct tests PASS across their required environments. System `python3 -m pytest atlas/tests followspec/tests paper/tests ops/tests --ignore=atlas/tests/test_native_ct.py -q` gives263pass and one environment-only failure (vLLM not installed there). Pinned `.venv-atlas-031-clean/bin/python -m pytest atlas/tests/test_environment.py -q` passes both pin and pip-check tests; native CT separately1pass. Logs FIX6_cpu_integrated_20261006.log, FIX6_engine_pin_20261006.log, FIX6_native_ct_20261006.log. No numerical/core test failure remains. Paper builds included. Actual1435-cell legacy audit passes. `git diff --check` passes.

Merge before protocol freeze under D32. Operator retries only failed21A4/7A7 cells into new paths; use paired comparison CLI, not independent macros. Golden128-valid gate remains unchanged. D32 scientific inference rule is only pairwise exclusion; seeds, uncertainty bootstrap settings, thresholds, engine and generation unchanged. Per-derivative output reports pair-specific values/excluded IDs so quotient of separately displayed A11/A00 is never mistaken for matched retention. No production GPU run launched by builder.

## 2026-10-06T13:07:43-04:00 — codex-1 — Handoff: review, operator retry packet ready

Source b52fab0 merged as f00992f and pushed; tag run-FIX6-20261006 has a clean detached checkout .worktrees/run-FIX6-20261006. Acceptance artifacts/FIX6_acceptance_20261006/acceptance.json:265 distinct tests pass in appropriate environments;1435 real successful cells reproduce exact saved means. Real matched64-prompt LoRA pair CLI also passed at artifacts/FIX6_actual_pair_20261006 (same historical retention, no exclusions). No new GPU inference claimed.

Retry packet artifacts/FIX6_retry_jobs_20261006/A4_jobs.jsonl (21) and A7_jobs.jsonl (7), with source hashes, original failures, and reproducible prepare.py. All28 launcher dry runs pass; four actual cell CLI dry runs pass (one per task/base). GPU slots in dry-run artifacts are placeholders only. Retry commands preserve exact original generation arguments and pinned engine; only new output paths/tag and code checkout change. Method packet from FIX4 remains first priority. Do not launch from old evaluation checkout or overwrite failed cells.

Operator next: re-run FIX6 checks, mark done, then queue retries on available A40s after allocating method admission. Use `python -m atlas.paired_cells --parent A00_CELL --child A10_CELL --output NEW_PAIR` and atlas/ZERO_STEP.md; old independent-macro scripts cannot handle D32. Gate3 driver now records pairwise exclusions for all comparisons and blocks undefined empty intersections. Builder has no GPU jobs running.

Method handoff remains artifacts/M1_D28_20261006/round1: baseline then60 filter jobs; fresh admission required before Magpie/response generation and Gate2. No pause marker found. No other ready Codex build row remains; B9 numerical validation and B11 public recipe/license blockers are unchanged, B10 awaits operator verification. Latest direct owner fresh-plan decision supersedes D29 and must be appended to MASTER13 by operator.

## 2026-10-06T13:08:39-04:00 — codex-1 — A6 count consumer follow-up

Operator concurrently verified FIX4, marked done, recorded D33 and launched M1_D28 baseline (13:06:50); method reserved16 slots. Their new A6 journal reports6 capture failures of the same zero-step class. Read atlas/prepare_covariates.py: source validation still compares record count against macro n, which now counts only nonzero requests. Reopen own row to update this consumer to n_total (fallback legacy n), validate zero counts, preserve all generated token sequences including immediate EOS, and report n_zero_step in provenance. No covariate estimator/mask/exclusion protocol changes; truly empty sequences still fail. Tests first. Then fresh A6 retry packet/tag; existing A4/A7 retries from f00992f remain valid.

## 2026-10-06T13:10:04-04:00 — codex-1 — A6 compatibility acceptance PASS

Test first failed on existing record-count guard (FIX6_cov_before_20261006.log). New preparation uses n_total with legacy fallback, checks boolean zero flags and n_valid+n_zero==n_total, preserves all generated token sequences/masks and reports source counts. Immediate-EOS regression retains64 rows includingEOS; corrupted count rejected.29 affected covariate/cell/pair/Gate3 tests PASS (FIX6_cov_after_20261006.log). Prior265-test coverage plus this added regression gives266 distinct tests; no other code changed. Covariate estimators and truly-empty-output rejection remain unchanged. Next merge and emit6 A6 capture retries with a new tag containing this consumer fix; old28 A4/A7 packet stays valid.

## 2026-10-06T13:11:10-04:00 — codex-1 — Final Handoff / review

Covariate follow-up source d15b5d1 merged fe87b43 and pushed/tagged run-FIX6-A6-20261006, clean .worktrees/run-FIX6-A6-20261006. Final acceptance artifacts/FIX6_final_acceptance_20261006/acceptance.json: prior265-test coverage plus new regression,29 affected tests re-run PASS, actual64-record A6 source prepares correctly. Six A6 capture retry jobs at artifacts/FIX6_A6_retry_jobs_20261006/A6_jobs.jsonl:6 launcher dry runs +1 representative Qwen cell CLI dry run PASS. Exact old generation flags, including --capture-prompt-token-ids, preserved; fresh artifacts and code only. A4/A7 previous28-job packet remains valid.

Operator: verify final change, run retries after method allocation. When preparing covariates from recovered A6 cells use main at fe87b43 or newer (or the new tag), since old prepare_covariates compares total records to valid-only n. New source counts are provenance only; no sequence/mask changes or dropped covariate examples. Historical failed artifacts retained. D33 has now been recorded and FIX4 independently marked done by operator; M1_D28 baseline launched,16 method A40 slots reserved. Next method dependency is fresh baseline/filter admission, then mixture prompts and M2. No global pause marker, no builder background/GPU job remains. No ready Codex task remains; B9/B11 blockers and B10 operator-review state unchanged.

## 2026-10-06T16:18-04:00 — claude-ops — Verified; done; retries launched

- Re-ran in clean tag run-FIX6-A6-20261006 (fe87b43): `python3 -m pytest atlas/tests followspec/tests paper/tests ops/tests --ignore=atlas/tests/test_native_ct.py -q`
  → 264 passed, 1 failed (test_engine_matches_committed_pin: vLLM not installed in system Python, expected). Pinned
  `.venv-atlas-031-clean` test_environment + test_native_ct → 3 passed. Legacy audit check.py → passed, 1,435 unchanged cells, 0 failures. **FIX-6 done.**
- Owner's atlas hold lasted until M2 started. M2 prompts are complete and responses are blocked on FIX-7, so the A40s are free. Launched all 34 retry jobs
  (codex packets A4 21 + A7 7 + A6 6, unchanged; combined at artifacts/FIX6_retry_queue_20261006/jobs.jsonl) via `ops/waves/FIX6_retry.sh`
  with live GPU checks; 10 launched in the first 90 s. Analysis will use `atlas.paired_cells` (pairwise exclusion, D-32), not independent macros.

## 2026-10-06T16:59-04:00 — claude-ops — 34/34 retries complete

Queue artifacts/FIX6_retry_queue_20261006/queue.log: 34 launched, 34 exit 0. Every cell has results.json, n_total 64. Zero-step counts
are identical across K for each model (deterministic prompts): charlesli A00 1; dinostackai 1; tibogoss 1; **mkd-hossain-keural-cortex 10**; nabin2004
narrated-merged 1; narrated-sft-merged 2; **tomg dynaguard 6** (n_valid = 64 − zero). Flag for A4/A7 analysis: mkd-hossain loses 10/64 pairwise prompts.
Pairwise analysis via `atlas.paired_cells` is next (CPU). A6 capture retries (6) feed covariates.
