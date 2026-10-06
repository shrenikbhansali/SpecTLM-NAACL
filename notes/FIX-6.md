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
