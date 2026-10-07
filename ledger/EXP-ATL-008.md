### EXP-ATL-008 — D-39 controlled target-update stress screen (K4, reduced-budget seed 0)

**Landed:** 2026-10-07.

**Status:** pilot; fixed discovery panel, not confirmation or Gate 3.

**What / why.** Measure how useful target fine-tuning changes speculative acceptance, and compare the released Frozen drafter with four matched trained arms.

**New.** Six local code/math SFT checkpoints at 50/100/200 updates, from two shared trajectories; all six included. Four drafter arms use the D-38 250-step, 1,991,138-token corpus, seed 0, FS lambda 0.1. Targets excluded from the training bank; discovery prompts disjoint from 43,478 training hashes. Reserved confirmation prompts remain unused.

**Artifacts.** `artifacts/D39_stress_20261007/{panel,prepared/report}`; independent reproduction `artifacts/D39_stress_20261007/audit_1919/{recheck.py,results.json}` verified all 70 K4 cells, 210 input hashes, paired statistics and task-quality scores.

**Config + results.** Frozen evaluation commit 6da2e4265c0398ec0de5affaf23b0bd1df0be445; vLLM 0.31.0, greedy K4, fresh compile, batch 8, 512 new tokens, exact rendered prompts, paired LoRA controls. Macro acceptance length includes the bonus token. Each condition has 32 paired prompts, zero exclusions. Confidence intervals below bootstrap paired prompts, conditional on these checkpoints and one drafter-training seed.

| Condition | Frozen retention [95% CI] | Target quality parent → child | FS−MVD AL [95% CI] | FS−PO-D AL | FS−PO-T AL |
| --- | --- | --- | --- | --- | --- |
| code 50 | 0.901 [0.847, 0.957] | 0.500 → 0.562 | +0.0834 [+0.0196, +0.1567] | +0.0337 | +0.0188 |
| code 100 | 0.913 [0.866, 0.962] | 0.531 → 0.562 | +0.0003 [-0.0649, +0.0682] | -0.0062 | +0.0087 |
| code 200 | 0.928 [0.868, 0.993] | 0.531 → 0.531 | -0.0103 [-0.0947, +0.0743] | +0.0626 | -0.0235 |
| math 50 | 0.897 [0.866, 0.929] | 0.781 → 0.719 | +0.0603 [-0.0151, +0.1300] | +0.0226 | +0.0076 |
| math 100 | 0.896 [0.857, 0.933] | 0.781 → 0.719 | +0.0060 [-0.0417, +0.0539] | -0.0209 | +0.0062 |
| math 200 | 0.902 [0.854, 0.953] | 0.812 → 0.812 | +0.0686 [+0.0214, +0.1191] | +0.0135 | -0.0241 |

All six coherence checks passed. Acceptance decreases by 7.2–10.4% across this panel. FS−MVD is positive in five conditions; FS−PO-D and FS−PO-T have mixed signs, with all their prompt-level intervals crossing zero (full intervals in results.json). No across-condition significance claim: checkpoints share trajectories and prompts. No conclusion that more target updates monotonically worsen acceptance.

**Caveats.** Quality uses GSM8K answer exact match and MBPP visible-tests pass@1; the historical MBPP prompt contains those tests. All target-quality delta intervals include zero, so useful-quality preservation/improvement is not established statistically. Parent scores differ slightly between fresh cells; each reported result uses its actual matched parent. Prompt intervals omit training-seed and compilation uncertainty and are not corrected for multiple comparisons. Lambda and K8 follow-ups are exploratory, and all outcomes must remain available. No paper conclusion or gate promotion is inferred.
