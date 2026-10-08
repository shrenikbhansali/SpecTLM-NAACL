### EXP-ATL-010 — D-39 lambda and matched K8 feasibility follow-ups

**Landed:** 2026-10-07; all automatic reports complete by21:44ET.

**Status:** pilot; discovery results, not confirmation or Gate 3.

**What / why.** Test whether loss weighting or a larger speculative block exposes a method-specific advantage.

**New.** Approved lambda0/.03/.1/.3 at250matched steps /1,991,138tokens, seed0. K4 public fixed panel (9targets) and six code/math stress conditions; K8 all four trained arms plus Frozen on the same six conditions. Identical controls reused within K, never between K4/K8.

**Artifacts:** `artifacts/M5_D39_20261007/watch_fix20/{000,003,030}/report/`; `artifacts/D39_stress_20261007/prepared/lambda_watch/{000,003,030}/report/`; `artifacts/D39_K8_20261007/report_{000,003,010,030}/`. Lambda.1 K4 references in EXP-ATL-006/008. All input hashes and result/statistic reconstruction verified in `artifacts/METHOD_feasibility_20261007_2221/results.json` (11 reports including EXP-ATL-009,1,884unique input files).

**Config + results.** Frozen evaluation6da2e42/vLLM0.31.0, greedy, same exact prompts and A40 controls. Public K4: all trained-control median-difference intervals include zero at every tested lambda; lambda0 retains roughly+0.10–.12 AL gain over Frozen. Stress K8 results below count positive FS-minus-control differences across all6conditions; each has32paired prompts. Full paired prompt intervals remain in reports.

| Lambda | Wins vs Frozen /6 | Wins vs MVD /6 | Wins vs PO-D /6 | Wins vs PO-T /6 |
| --- | ---: | ---: | ---: | ---: |
| 0.0 | 6 | 6 | 4 | 2 |
| 0.03 | 6 | 5 | 4 | 1 |
| 0.1 | 5 | 5 | 3 | 2 |
| 0.3 | 5 | 5 | 3 | 2 |

K4 stress: math generally gains over Frozen/MVD even atlambda0, while code outcomes are mixed. Publiclambda0,.03,.3 gains and uncertainty, all individual stress contrasts, regressions and parent-retention results are retained in the linked reports. No across-condition independence or best-lambda selection is inferred.

**Caveats.** Six stress conditions share only two target-training trajectories and reused prompts. Public CIs condition on one drafter seed; stress CIs bootstrap prompts, omit seed/compilation uncertainty, and are not multiple-comparison adjusted. Best-case wins cannot establish general advantage. Loss-weight ablation does not establish a useful delta-specific contribution here. No unseen confirmation set was evaluated; task-quality diagnostic remains K4.
