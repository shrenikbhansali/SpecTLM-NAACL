# EXP-ATL-012 — Full-budget 50-target FollowSpec matrix

**Landed:** 2026-10-07, D-37 / M4.

**Status:** pilot.

**What / why:** Complete the full-budget single-seed feasibility comparison against Frozen, MVD, parent-only data-matched and text-matched controls. Report every held-out target and the owner-requested degraded tail separately.

**New in this experiment:** 50 targets per workload, 1,010 cells; independent raw-counter re-derivation without followspec imports.

**Artifacts:** `artifacts/M4_seed0_full_20261007/watch_fix16/report`; independent audit `artifacts/M4_independent_20261007_2347`; [report](../reports/M4-full-seed0-20261007.md).

**Config + results:** vLLM0.31.0, A40, EAGLE-3 K4, greedy seed0, batch8, 512 output tokens, 10,320,835 training tokens /1,294 steps per arm. Same rendered prompts within each pair; pairwise shared nonzero-step IDs. Median acceptance-length differences and 95% target-bootstrap intervals (10,000 draws):

| Workload | Subset | n targets | FS − Frozen | FS − MVD | FS − PO-D | FS − PO-T |
| --- | --- | ---: | --- | --- | --- | --- |
| general | all | 50 | +0.1308 [+0.1187, +0.1433] | +0.0014 [-0.0068, +0.0092] | +0.0090 [-0.0010, +0.0187] | +0.0033 [-0.0001, +0.0128] |
| general | degraded_tail | 15 | +0.1467 [+0.1062, +0.1683] | -0.0016 [-0.0207, +0.0089] | +0.0097 [+0.0007, +0.0319] | +0.0028 [-0.0084, +0.0198] |
| own | all | 50 | +0.1598 [+0.1384, +0.1866] | +0.0067 [-0.0003, +0.0176] | +0.0060 [-0.0066, +0.0228] | +0.0076 [-0.0005, +0.0246] |
| own | degraded_tail | 9 | +0.1663 [+0.0682, +0.2203] | +0.0040 [-0.0180, +0.0288] | +0.0008 [-0.0353, +0.0264] | -0.0076 [-0.0384, +0.0490] |

**Caveats:** One training seed; exploratory workload-specific tail (<.95 Frozen first-position retention), no multiplicity correction, no parent equivalence certification. Earlier Frozen repository commits have identical cell-source hashes and the same pinned engine. Native validation pending at checkpoint handoff for FS/PO-D/PO-T, recorded in the frozen report. All full-pool trained-control intervals include zero. No owner framing/gate decision.
