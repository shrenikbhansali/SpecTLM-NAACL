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

### 2026-10-09T16:29:40.951147-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_162940/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_162940/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_162940/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_162940/README.md).

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


### 2026-10-09T16:34:47.238670-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_163447/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_163447/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_163447/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_163447/README.md).

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
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |


### 2026-10-09T16:39:53.755111-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_163953/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_163953/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_163953/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_163953/README.md).

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
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |


### 2026-10-09T16:45:00.832641-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_164500/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_164500/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_164500/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_164500/README.md).

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
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T16:50:08.141603-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_165008/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_165008/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_165008/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_165008/README.md).

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
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T17:00:16.074442-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_170016/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_170016/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_170016/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_170016/README.md).

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
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T17:05:24.062530-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_170524/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_170524/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_170524/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_170524/README.md).

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
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T17:35:32.168940-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_173532/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_173532/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_173532/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_173532/README.md).

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
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T18:00:40.218424-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_180040/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_180040/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_180040/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_180040/README.md).

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
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T18:05:48.201788-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_180548/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_180548/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_180548/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_180548/README.md).

| Target | Examples | Arm | Panel | n / seeds | Official repair Delta tau | Production repair Delta tau | Difference [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | 4000 | fc | speed128 | 128 / 1 | 0.563 [0.525, 0.599] | 0.494 [0.460, 0.525] | 0.069 [0.035, 0.104] |
| R1 | 4000 | fc | math64 | 64 / 1 | 0.765 [0.726, 0.804] | 0.584 [0.544, 0.627] | 0.181 [0.120, 0.237] |
| R1 | 4000 | full | speed128 | 128 / 1 | 0.698 [0.654, 0.742] | 0.644 [0.601, 0.683] | 0.054 [0.017, 0.093] |
| R1 | 4000 | full | math64 | 64 / 1 | 0.963 [0.921, 1.006] | 0.837 [0.783, 0.895] | 0.126 [0.074, 0.176] |
| R1 | 16000 | full | math64 | 64 / 1 | 1.083 [1.031, 1.134] | 0.941 [0.896, 0.988] | 0.142 [0.103, 0.181] |
| Nemotron | 4000 | fc | speed128 | 128 / 1 | 0.573 [0.524, 0.621] | 0.429 [0.398, 0.459] | 0.144 [0.102, 0.187] |
| Nemotron | 4000 | fc | math64 | 64 / 1 | 0.898 [0.863, 0.930] | 0.523 [0.496, 0.549] | 0.375 [0.347, 0.402] |
| Nemotron | 4000 | full | speed128 | 128 / 1 | 0.673 [0.623, 0.724] | 0.537 [0.500, 0.574] | 0.136 [0.100, 0.173] |
| Nemotron | 4000 | full | math64 | 64 / 1 | 1.084 [1.041, 1.125] | 0.736 [0.701, 0.770] | 0.348 [0.308, 0.389] |
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T18:10:56.429991-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_181056/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_181056/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_181056/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_181056/README.md).

| Target | Examples | Arm | Panel | n / seeds | Official repair Delta tau | Production repair Delta tau | Difference [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | 4000 | fc | speed128 | 128 / 1 | 0.563 [0.525, 0.599] | 0.494 [0.460, 0.525] | 0.069 [0.035, 0.104] |
| R1 | 4000 | fc | math64 | 64 / 1 | 0.765 [0.726, 0.804] | 0.584 [0.544, 0.627] | 0.181 [0.120, 0.237] |
| R1 | 4000 | full | speed128 | 128 / 1 | 0.698 [0.654, 0.742] | 0.644 [0.601, 0.683] | 0.054 [0.017, 0.093] |
| R1 | 4000 | full | math64 | 64 / 1 | 0.963 [0.921, 1.006] | 0.837 [0.783, 0.895] | 0.126 [0.074, 0.176] |
| R1 | 16000 | fc | speed128 | 128 / 1 | 0.639 [0.597, 0.681] | 0.564 [0.526, 0.600] | 0.075 [0.038, 0.113] |
| R1 | 16000 | fc | math64 | 64 / 1 | 0.910 [0.864, 0.952] | 0.703 [0.670, 0.738] | 0.207 [0.155, 0.254] |
| R1 | 16000 | full | speed128 | 128 / 1 | 0.772 [0.725, 0.817] | 0.728 [0.684, 0.769] | 0.044 [0.016, 0.073] |
| R1 | 16000 | full | math64 | 64 / 1 | 1.083 [1.031, 1.134] | 0.941 [0.896, 0.988] | 0.142 [0.103, 0.181] |
| Nemotron | 4000 | fc | speed128 | 128 / 1 | 0.573 [0.524, 0.621] | 0.429 [0.398, 0.459] | 0.144 [0.102, 0.187] |
| Nemotron | 4000 | fc | math64 | 64 / 1 | 0.898 [0.863, 0.930] | 0.523 [0.496, 0.549] | 0.375 [0.347, 0.402] |
| Nemotron | 4000 | full | speed128 | 128 / 1 | 0.673 [0.623, 0.724] | 0.537 [0.500, 0.574] | 0.136 [0.100, 0.173] |
| Nemotron | 4000 | full | math64 | 64 / 1 | 1.084 [1.041, 1.125] | 0.736 [0.701, 0.770] | 0.348 [0.308, 0.389] |
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T18:16:06.211088-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_181606/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_181606/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_181606/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_181606/README.md).

| Target | Examples | Arm | Panel | n / seeds | Official repair Delta tau | Production repair Delta tau | Difference [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | 4000 | fc | speed128 | 128 / 1 | 0.563 [0.525, 0.599] | 0.494 [0.460, 0.525] | 0.069 [0.035, 0.104] |
| R1 | 4000 | fc | math64 | 64 / 1 | 0.765 [0.726, 0.804] | 0.584 [0.544, 0.627] | 0.181 [0.120, 0.237] |
| R1 | 4000 | full | speed128 | 128 / 1 | 0.698 [0.654, 0.742] | 0.644 [0.601, 0.683] | 0.054 [0.017, 0.093] |
| R1 | 4000 | full | math64 | 64 / 1 | 0.963 [0.921, 1.006] | 0.837 [0.783, 0.895] | 0.126 [0.074, 0.176] |
| R1 | 16000 | fc | speed128 | 128 / 1 | 0.639 [0.597, 0.681] | 0.564 [0.526, 0.600] | 0.075 [0.038, 0.113] |
| R1 | 16000 | fc | math64 | 64 / 1 | 0.910 [0.864, 0.952] | 0.703 [0.670, 0.738] | 0.207 [0.155, 0.254] |
| R1 | 16000 | full | speed128 | 128 / 1 | 0.772 [0.725, 0.817] | 0.728 [0.684, 0.769] | 0.044 [0.016, 0.073] |
| R1 | 16000 | full | math64 | 64 / 1 | 1.083 [1.031, 1.134] | 0.941 [0.896, 0.988] | 0.142 [0.103, 0.181] |
| Nemotron | 4000 | fc | speed128 | 128 / 1 | 0.573 [0.524, 0.621] | 0.429 [0.398, 0.459] | 0.144 [0.102, 0.187] |
| Nemotron | 4000 | fc | math64 | 64 / 1 | 0.898 [0.863, 0.930] | 0.523 [0.496, 0.549] | 0.375 [0.347, 0.402] |
| Nemotron | 4000 | full | speed128 | 128 / 1 | 0.673 [0.623, 0.724] | 0.537 [0.500, 0.574] | 0.136 [0.100, 0.173] |
| Nemotron | 4000 | full | math64 | 64 / 1 | 1.084 [1.041, 1.125] | 0.736 [0.701, 0.770] | 0.348 [0.308, 0.389] |
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T18:36:15.923210-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_183615/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_183615/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_183615/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_183615/README.md).

| Target | Examples | Arm | Panel | n / seeds | Official repair Delta tau | Production repair Delta tau | Difference [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | 4000 | fc | speed128 | 128 / 1 | 0.563 [0.525, 0.599] | 0.494 [0.460, 0.525] | 0.069 [0.035, 0.104] |
| R1 | 4000 | fc | math64 | 64 / 1 | 0.765 [0.726, 0.804] | 0.584 [0.544, 0.627] | 0.181 [0.120, 0.237] |
| R1 | 4000 | full | speed128 | 128 / 1 | 0.698 [0.654, 0.742] | 0.644 [0.601, 0.683] | 0.054 [0.017, 0.093] |
| R1 | 4000 | full | math64 | 64 / 1 | 0.963 [0.921, 1.006] | 0.837 [0.783, 0.895] | 0.126 [0.074, 0.176] |
| R1 | 16000 | fc | speed128 | 128 / 1 | 0.639 [0.597, 0.681] | 0.564 [0.526, 0.600] | 0.075 [0.038, 0.113] |
| R1 | 16000 | fc | math64 | 64 / 1 | 0.910 [0.864, 0.952] | 0.703 [0.670, 0.738] | 0.207 [0.155, 0.254] |
| R1 | 16000 | full | speed128 | 128 / 1 | 0.772 [0.725, 0.817] | 0.728 [0.684, 0.769] | 0.044 [0.016, 0.073] |
| R1 | 16000 | full | math64 | 64 / 1 | 1.083 [1.031, 1.134] | 0.941 [0.896, 0.988] | 0.142 [0.103, 0.181] |
| Nemotron | 4000 | fc | speed128 | 128 / 1 | 0.573 [0.524, 0.621] | 0.429 [0.398, 0.459] | 0.144 [0.102, 0.187] |
| Nemotron | 4000 | fc | math64 | 64 / 1 | 0.898 [0.863, 0.930] | 0.523 [0.496, 0.549] | 0.375 [0.347, 0.402] |
| Nemotron | 4000 | full | speed128 | 128 / 1 | 0.673 [0.623, 0.724] | 0.537 [0.500, 0.574] | 0.136 [0.100, 0.173] |
| Nemotron | 4000 | full | math64 | 64 / 1 | 1.084 [1.041, 1.125] | 0.736 [0.701, 0.770] | 0.348 [0.308, 0.389] |
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T19:16:25.899871-04:00 — codex-1 — D-51 repair-delta update

Selection: **pending**; primary=None. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_191625/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_191625/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_191625/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_191625/README.md).

| Target | Examples | Arm | Panel | n / seeds | Official repair Delta tau | Production repair Delta tau | Difference [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | 4000 | fc | speed128 | 128 / 1 | 0.563 [0.525, 0.599] | 0.494 [0.460, 0.525] | 0.069 [0.035, 0.104] |
| R1 | 4000 | fc | math64 | 64 / 1 | 0.765 [0.726, 0.804] | 0.584 [0.544, 0.627] | 0.181 [0.120, 0.237] |
| R1 | 4000 | full | speed128 | 128 / 1 | 0.698 [0.654, 0.742] | 0.644 [0.601, 0.683] | 0.054 [0.017, 0.093] |
| R1 | 4000 | full | math64 | 64 / 1 | 0.963 [0.921, 1.006] | 0.837 [0.783, 0.895] | 0.126 [0.074, 0.176] |
| R1 | 16000 | fc | speed128 | 128 / 2 | 0.642 [0.600, 0.684] | 0.569 [0.532, 0.602] | 0.073 [0.041, 0.107] |
| R1 | 16000 | fc | math64 | 64 / 3 | 0.894 [0.854, 0.934] | 0.710 [0.673, 0.752] | 0.184 [0.131, 0.231] |
| R1 | 16000 | full | speed128 | 128 / 1 | 0.772 [0.725, 0.817] | 0.728 [0.684, 0.769] | 0.044 [0.016, 0.073] |
| R1 | 16000 | full | math64 | 64 / 3 | 1.074 [1.027, 1.123] | 0.945 [0.901, 0.988] | 0.130 [0.088, 0.172] |
| Nemotron | 4000 | fc | speed128 | 128 / 1 | 0.573 [0.524, 0.621] | 0.429 [0.398, 0.459] | 0.144 [0.102, 0.187] |
| Nemotron | 4000 | fc | math64 | 64 / 1 | 0.898 [0.863, 0.930] | 0.523 [0.496, 0.549] | 0.375 [0.347, 0.402] |
| Nemotron | 4000 | full | speed128 | 128 / 1 | 0.673 [0.623, 0.724] | 0.537 [0.500, 0.574] | 0.136 [0.100, 0.173] |
| Nemotron | 4000 | full | math64 | 64 / 1 | 1.084 [1.041, 1.125] | 0.736 [0.701, 0.770] | 0.348 [0.308, 0.389] |
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |


### 2026-10-09T19:21:36.291447-04:00 — codex-1 — D-51 repair-delta update

Selection: **selected**; primary=official. Delta = repaired minus the same drafter reuse; SPEED-128 primary, MATH-64 secondary. Matched data/steps and paired seeds/queries, 95% CIs; pilot, selection not adjusted for multiple comparisons. [Immutable report](../artifacts/D51_reports_20261009_1627/snapshot-20261009_192136/report.md), [main rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_192136/r1-main.md), [robustness rows](../artifacts/D51_reports_20261009_1627/snapshot-20261009_192136/r1-robustness.md), [LaTeX](../paper/tables/D51-20261009_192136/README.md).

| Target | Examples | Arm | Panel | n / seeds | Official repair Delta tau | Production repair Delta tau | Difference [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | 4000 | fc | speed128 | 128 / 1 | 0.563 [0.525, 0.599] | 0.494 [0.460, 0.525] | 0.069 [0.035, 0.104] |
| R1 | 4000 | fc | math64 | 64 / 1 | 0.765 [0.726, 0.804] | 0.584 [0.544, 0.627] | 0.181 [0.120, 0.237] |
| R1 | 4000 | full | speed128 | 128 / 1 | 0.698 [0.654, 0.742] | 0.644 [0.601, 0.683] | 0.054 [0.017, 0.093] |
| R1 | 4000 | full | math64 | 64 / 1 | 0.963 [0.921, 1.006] | 0.837 [0.783, 0.895] | 0.126 [0.074, 0.176] |
| R1 | 16000 | fc | speed128 | 128 / 3 | 0.650 [0.607, 0.692] | 0.569 [0.534, 0.601] | 0.081 [0.048, 0.115] |
| R1 | 16000 | fc | math64 | 64 / 3 | 0.894 [0.854, 0.934] | 0.710 [0.673, 0.752] | 0.184 [0.131, 0.231] |
| R1 | 16000 | full | speed128 | 128 / 3 | 0.778 [0.731, 0.823] | 0.735 [0.693, 0.776] | 0.043 [0.014, 0.073] |
| R1 | 16000 | full | math64 | 64 / 3 | 1.074 [1.027, 1.123] | 0.945 [0.901, 0.988] | 0.130 [0.088, 0.172] |
| Nemotron | 4000 | fc | speed128 | 128 / 1 | 0.573 [0.524, 0.621] | 0.429 [0.398, 0.459] | 0.144 [0.102, 0.187] |
| Nemotron | 4000 | fc | math64 | 64 / 1 | 0.898 [0.863, 0.930] | 0.523 [0.496, 0.549] | 0.375 [0.347, 0.402] |
| Nemotron | 4000 | full | speed128 | 128 / 1 | 0.673 [0.623, 0.724] | 0.537 [0.500, 0.574] | 0.136 [0.100, 0.173] |
| Nemotron | 4000 | full | math64 | 64 / 1 | 1.084 [1.041, 1.125] | 0.736 [0.701, 0.770] | 0.348 [0.308, 0.389] |
| Nemotron | 16000 | fc | speed128 | 128 / 1 | 0.655 [0.604, 0.707] | 0.492 [0.454, 0.529] | 0.163 [0.125, 0.201] |
| Nemotron | 16000 | fc | math64 | 64 / 1 | 1.012 [0.967, 1.055] | 0.631 [0.597, 0.664] | 0.381 [0.342, 0.421] |
| Nemotron | 16000 | full | speed128 | 128 / 1 | 0.724 [0.662, 0.787] | 0.600 [0.557, 0.643] | 0.123 [0.080, 0.167] |
| Nemotron | 16000 | full | math64 | 64 / 1 | 1.207 [1.157, 1.258] | 0.859 [0.822, 0.897] | 0.348 [0.309, 0.387] |

D-51 main focal rows now use official; the other drafter remains a robustness comparison. This supersedes the earlier provisional production choice; production timing and MATH-500 measurements keep their original identity.

| Role | Drafter | Arm | Panel | n / seeds | p1 [95% CI] | tau [95% CI] | Own-reuse Delta tau [95% CI] | Oracle-gap recovery [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | official | fc | speed128 | 128 / 3 | 0.626 [0.600, 0.650] | 2.414 [2.339, 2.487] | 0.650 [0.607, 0.692] | 0.599 [0.576, 0.624] |
| main | official | fc | math64 | 64 / 3 | 0.733 [0.723, 0.744] | 2.817 [2.764, 2.871] | 0.894 [0.854, 0.934] | 0.451 [0.431, 0.471] |
| main | official | full | speed128 | 128 / 3 | 0.650 [0.623, 0.674] | 2.542 [2.462, 2.618] | 0.778 [0.731, 0.823] | 0.717 [0.692, 0.743] |
| main | official | full | math64 | 64 / 3 | 0.760 [0.748, 0.771] | 2.998 [2.941, 3.057] | 1.074 [1.027, 1.123] | 0.542 [0.519, 0.566] |
| main | official | reuse | speed128 | 128 / 1 | 0.430 [0.410, 0.447] | 1.764 [1.719, 1.808] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| main | official | reuse | math64 | 64 / 1 | 0.491 [0.479, 0.504] | 1.923 [1.881, 1.968] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

| Role | Drafter | Arm | Panel | n / seeds | p1 [95% CI] | tau [95% CI] | Own-reuse Delta tau [95% CI] | Oracle-gap recovery [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robustness | production | fc | speed128 | 128 / 3 | 0.606 [0.582, 0.628] | 2.300 [2.237, 2.360] | 0.569 [0.534, 0.601] | 0.509 [0.488, 0.530] |
| robustness | production | fc | math64 | 64 / 3 | 0.705 [0.695, 0.716] | 2.658 [2.610, 2.708] | 0.710 [0.673, 0.752] | 0.363 [0.343, 0.384] |
| robustness | production | full | speed128 | 128 / 3 | 0.639 [0.614, 0.662] | 2.466 [2.394, 2.536] | 0.735 [0.693, 0.776] | 0.658 [0.634, 0.682] |
| robustness | production | full | math64 | 64 / 3 | 0.745 [0.735, 0.754] | 2.892 [2.842, 2.946] | 0.945 [0.901, 0.988] | 0.483 [0.463, 0.503] |
| robustness | production | reuse | speed128 | 128 / 1 | 0.411 [0.393, 0.427] | 1.730 [1.687, 1.774] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| robustness | production | reuse | math64 | 64 / 1 | 0.492 [0.480, 0.505] | 1.948 [1.906, 1.994] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

### 2026-10-10T00:20:48.854355-04:00 — D52 official-primary analysis pilot

All69cells complete. Independent rawtiming aggregation and frozenMATH500counterreconstruction, n128/b8 or32/b1 ×3processes×3warm; MATH500n500seed0. Paired10000bootstrap; config/inputhashes retained. Results and caveats in [primaryreport](../reports/P3-primary-official-20261010.md), artifacts/D52_analysis_20261010_0020;3LaTeXtablescompile,8regressiontestsPASS. Only64kproduction remainsrunning; no official64k launch.
