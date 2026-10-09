### EXP-ATL-025 — FIX-24 embedding parity diagnostics and corrected official repair

**Landed:** 2026-10-09T14:53:39.454090-04:00.

**Status:** pilot; core bug acceptance passes, corrected training/evaluation in progress.

**What / why.** Official checkpoint omits embed_tokens; native loading had randomized a frozen embedding, invalidating old official repair. Restore target weights only on omission, preserve production checkpoint embedding.

**New.** Exact omission detection and selective copy, regression tests, bounded no-update probe. GPU loaded-state comparison for both targets and production vLLM inspection.

**Artifacts.** artifacts/FIX24_20261009_1420/{acceptance.json,core-acceptance.json,production-serving-embedding.json}; tests-pinned.log, invalid-runs.json, matched-served and corrected training/eval directories. Code7997072, pushed run-FIX24-20261009 before worktree creation.

**Config + results.** 19 CPU tests pass. Official embedding exactly equals target after bf16→fp32 conversion with exact roundtrip, both targets. Eight teacher-forced batches: R1 5854/13718=.426739; Nemo5974/12915=.462563. Frozen served diagnostics on same training queries: R1 n30 p1=.395608; Nemo n57 p1=.440140; differences3.113/2.242 percentage points. Production entire loaded-state hash and all first-batch metrics equal historical E1-production-t1-4k-fc (803/1685=.476558). Actual vLLM production embedding equals its checkpoint, differs from target on both. Four corrected4k one-epochfc/full training jobs published with compact/shared checkpoints and350GB guard; fresh frozenSPEED/MATH64 evaluation each export.

**Caveats.** Diagnostic data are training queries, not held-out paper results. Teacher-forced token-weighted positions and served macro proposal starts are different estimands even with identical queries. The within5pp check verifies requested coarse parity, not exact framework output equivalence. Historical official4k and derived contrasts INVALID(FIX24), not evidence against official repair. Production path unchanged. Corrected paper cells remain pending; conditionalofficial16k uses only corrected comparisons.

### 2026-10-09T14:59:34.934586-04:00 — codex-1 — first corrected held-out results

Corrected official Nemotron,25% of one4k epoch (step163), MATH64 n64, seed0. Pilot frozen6da/vLLM0.31/A40. Not final4k or the conditional16k decision.

| Arm | Reference | p1 [95% CI] | tau [95% CI] | Delta p1 [95% CI] | Delta tau [95% CI] |
|---|---|---|---|---|---|
| fc | official reuse | 0.666 [0.653, 0.678] | 2.524 [2.476, 2.570] | 0.214 [0.204, 0.225] | 0.821 [0.785, 0.856] |
| fc | production matched163 | 0.666 [0.653, 0.678] | 2.524 [2.476, 2.570] | 0.012 [0.001, 0.023] | 0.097 [0.063, 0.131] |
| full | official reuse | 0.699 [0.688, 0.711] | 2.675 [2.625, 2.723] | 0.248 [0.238, 0.257] | 0.971 [0.932, 1.010] |
| full | production matched163 | 0.699 [0.688, 0.711] | 2.675 [2.625, 2.723] | 0.010 [0.000, 0.020] | 0.072 [0.042, 0.103] |

10000 paired-query bootstrap; exact rendered IDs, settings and raw counters checked. Only unchanged official reuse and valid production repair controls used; old official repair excluded. Matched163 data/steps/nativeTTT3 verified from full config diff.

Source: artifacts/FIX24_20261009_1420/first-corrected-math64.json.
