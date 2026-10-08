### EXP-ATL-009 — Full-budget seed-0 feasibility on the original fixed panel

**Landed:** 2026-10-07 (report 19:46 ET; independently checked 22:21 ET).

**Status:** pilot; one seed, no Gate 3 certification.

**What / why.** Test whether full-budget FollowSpec separates from matched trained controls after the short pilot.

**New.** All four arms trained for 1,294 steps / 10,320,835 tokens; unchanged original pre-training D-38 panel, base plus nine held-out targets. No outcome-based target selection.

**Artifacts:** `artifacts/M4_seed0_full_20261007/fixed_panel_watch/report/{config,index_k4,results}.json`; independent reproduction `artifacts/METHOD_feasibility_20261007_2221/{audit.py,results.json}`.

**Config + results.** Frozen harness 6da2e4265c0398ec0de5affaf23b0bd1df0be445, vLLM0.31.0, greedy K4, A40, exact rendered prompts, fresh compilation, macro acceptance length including bonus. 190 cells; n=9 target pairs per workload, seed0. Paired counter reconstruction and full summary reproduced exactly.

| Workload | FS minus comparator | Median AL difference | 95% target-bootstrap CI, conditional on seed |
| --- | --- | ---: | --- |
| general | Frozen | +0.1519 | [+0.1085, +0.1751] |
| general | MVD | -0.0010 | [-0.0207, +0.0444] |
| general | PO-D | +0.0069 | [-0.0044, +0.0354] |
| general | PO-T | +0.0018 | [-0.0084, +0.0198] |
| own | Frozen | +0.1397 | [+0.1094, +0.1955] |
| own | MVD | +0.0083 | [-0.0328, +0.0320] |
| own | PO-D | +0.0182 | [-0.0307, +0.0479] |
| own | PO-T | +0.0056 | [-0.0033, +0.0429] |

**Caveats.** All trained-control comparison intervals include zero. Gain over Frozen alone does not isolate the FollowSpec-specific contribution. Small fixed panel; no training-seed uncertainty or end-to-end speed claim. Full 50-target matrix continues. Native validation status is separate; original full artifacts and collision attempts retained.
