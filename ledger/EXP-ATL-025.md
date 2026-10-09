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

### 2026-10-09T15:14:50.842117-04:00 — codex-1 — corrected official final Nemotron4k pilot

[Raw paired report](../artifacts/FIX24_check_20261009_1515/report.md),32 comparisons from16 completed cells at analysis start; frozen6da/vLLM0.31/A40, identical rendered IDs, seed0,10000 paired-query draws. Nemotron final4k SPEED n128: fc versus production Delta p1 .01483[.00403,.02542],Delta tau .08396[.05022,.11821]; full Delta p1 .00949[-.00194,.02094] (null),Delta tau .07581[.04404,.10925]. Full finalMATH pending at check. Owner-authorized conditional official16k fc/full now published, based on higher point means; no claim of significance for the full p1 difference. R1 quarter-epoch full SPEED Delta p1 .023[.014,.032],Delta tau .110[.084,.137]; final R1 still pending. Old invalid official repairs remain excluded.

E5c: 23/48 new-data shards complete, 32360/48000 responses written plus existing16000; source audits pass, automatic assembly/train/eval awaits all-row checks. Nemo timing 4/30. Collision caused one intermediate evaluation failure; unchanged retry active, preserved partial excluded. Disk 700.4GiB above350GB floor.

### 2026-10-09T16:24:34.674099-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_162434/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_162434/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_162434/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_162434/README.md).

| Target | Examples | Arm | Panel | n / seeds | Official repair Delta tau | Production repair Delta tau | Difference [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | 4000 | fc | speed128 | 128 / 1 | 0.563 [0.525, 0.599] | 0.494 [0.460, 0.525] | 0.069 [0.035, 0.104] |
| R1 | 4000 | fc | math64 | 64 / 1 | 0.765 [0.726, 0.804] | 0.584 [0.544, 0.627] | 0.181 [0.120, 0.237] |
| R1 | 4000 | full | speed128 | 128 / 1 | 0.698 [0.654, 0.742] | 0.644 [0.601, 0.683] | 0.054 [0.017, 0.093] |
| R1 | 4000 | full | math64 | 64 / 1 | 0.963 [0.921, 1.006] | 0.837 [0.783, 0.895] | 0.126 [0.074, 0.176] |
| Nemotron | 4000 | fc | speed128 | 128 / 1 | 0.573 [0.524, 0.621] | 0.429 [0.398, 0.459] | 0.144 [0.102, 0.187] |
| Nemotron | 4000 | fc | math64 | 64 / 1 | 0.898 [0.863, 0.930] | 0.523 [0.496, 0.549] | 0.375 [0.347, 0.402] |
| Nemotron | 4000 | full | speed128 | 128 / 1 | 0.673 [0.623, 0.724] | 0.537 [0.500, 0.574] | 0.136 [0.100, 0.173] |
| Nemotron | 4000 | full | math64 | 64 / 1 | 1.084 [1.041, 1.125] | 0.736 [0.701, 0.770] | 0.348 [0.308, 0.389] |


### 2026-10-09T16:25:47.187818-04:00 — D-51 validation

Eight raw 4k difference-of-differences comparisons verified; all favour official with paired95% intervals abovezero. Final16k selection remains pending, existing operatorseeds not duplicated. Six paired16k training configurations audited, all match data/steps/seed/order. Tests8PASS and LaTeXcompilationPASS. CPUwatch943172 will publish the3seed decision with SPEEDprimary/MATHsecondary, retain otherdrafter as robustness. Sourcecode c70f71d, stage artifacts/D51_reports_20261009_1627; estimand and full uncertainty in the preceding table.
