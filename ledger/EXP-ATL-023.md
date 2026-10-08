### EXP-ATL-023 — Historical census pairing and typed reanalysis

**Landed:** 2026-10-08T16:47:21.871205-04:00.

**Status:** pilot; historical raw-counter reconstruction, not new frozen launches.

**What / why.** Apply existing D-32 paired zero-step exclusion to historical p1 summaries, distinguish prompt-macro from pooled-step p1, and tabulate all174 checkpoint labels.

**New.** Fourteen corrected pooled-p1 comparisons; both estimands retained; typed lineage/history × drafter × workload table with hierarchical intervals. No new generation or research threshold.

**Artifacts.** `artifacts/FIX23_census_20261008_1640/`; [audit](../reports/P1-census-pairing-audit-20261008.md), [all classes](../reports/P1-census-typed-table-20261008.md).

**Config + results.** 348pairs/174checkpoints; EAGLEK4 and DFlashLlamaK10/QwenK16; source682cells423d3b6 and14f00992f, vLLM0.31.0/A40/greedyseed0/batch8/512tokens; own64 or general128prompts, sameIDsperpair. Frozen6da2e42 metricfunction reconstructs all rawrecords; generationcallcompatibility checked. All348legacyunpairedpooledp1 and pairedτ values reproduce. Fourteenp1pairs receiveD32exclusion; existingτunchanged. Helper48ed12a;11testsPASS. 5000checkpointthenpairedpromptbootstrapseed20261008; n/CI/rawhashes/unknownlabels inresults. EXP000predictions notadjudicated.

**Caveats.** Historicalcommitsnotrenamedasfrozen; own-domainworkloadsdifferbycheckpoint,42unknownhistories,relatedlineages,short/degenerateoutputsallretained. NotpooledwithnewSPEED128/MATH64panel. OriginalEXP005andATLAS_lencontrolledfiles remainunchanged; thisentrydocumentslaterderivedcorrections. Noframing/gate/promotiondecision.
