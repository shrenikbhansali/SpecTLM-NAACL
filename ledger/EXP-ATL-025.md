### EXP-ATL-025 — FIX-24 embedding parity diagnostics and corrected official repair

**Landed:** 2026-10-09T14:53:39.454090-04:00.

**Status:** pilot; core bug acceptance passes, corrected training/evaluation in progress.

**What / why.** Official checkpoint omits embed_tokens; native loading had randomized a frozen embedding, invalidating old official repair. Restore target weights only on omission, preserve production checkpoint embedding.

**New.** Exact omission detection and selective copy, regression tests, bounded no-update probe. GPU loaded-state comparison for both targets and production vLLM inspection.

**Artifacts.** artifacts/FIX24_20261009_1420/{acceptance.json,core-acceptance.json,production-serving-embedding.json}; tests-pinned.log, invalid-runs.json, matched-served and corrected training/eval directories. Code7997072, pushed run-FIX24-20261009 before worktree creation.

**Config + results.** 19 CPU tests pass. Official embedding exactly equals target after bf16→fp32 conversion with exact roundtrip, both targets. Eight teacher-forced batches: R1 5854/13718=.426739; Nemo5974/12915=.462563. Frozen served diagnostics on same training queries: R1 n30 p1=.395608; Nemo n57 p1=.440140; differences3.113/2.242 percentage points. Production entire loaded-state hash and all first-batch metrics equal historical E1-production-t1-4k-fc (803/1685=.476558). Actual vLLM production embedding equals its checkpoint, differs from target on both. Four corrected4k one-epochfc/full training jobs published with compact/shared checkpoints and350GB guard; fresh frozenSPEED/MATH64 evaluation each export.

**Caveats.** Diagnostic data are training queries, not held-out paper results. Teacher-forced token-weighted positions and served macro proposal starts are different estimands even with identical queries. The within5pp check verifies requested coarse parity, not exact framework output equivalence. Historical official4k and derived contrasts INVALID(FIX24), not evidence against official repair. Production path unchanged. Corrected paper cells remain pending; conditionalofficial16k uses only corrected comparisons.
