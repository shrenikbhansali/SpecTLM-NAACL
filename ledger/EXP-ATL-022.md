### EXP-ATL-022 — P5 CPU retrospective triage

**Landed:** 2026-10-08.

**Status:** pilot; no deployment certification.

**What / why.** Assess whether a small direct measurement predicts severe acceptance loss, and compare a shorter prefix and available KL diagnostic.

**New.** Outcome-independent16-query probe /112-query disjoint label split on21 frozen post-trained checkpoints per drafter. Label p1retention<0.9 from owner plan; no fitted threshold.

**Artifacts.** [Report](../reports/P5-triage-pilot-20261008.md); `artifacts/P5_triage_20261008_1533/analysis-v2/`; raw source references, effective n and hashes retained.

**Config + results.** Frozen6da2e42/vLLM0.31.0/A40 counters. Full16-request AUROC EAGLE1.000 [1,1],DFlash.945 [.818,1]; first16iterations .602 [.204,1] / .773 [.518,.971]. 10kcheckpoint bootstrap;7/10degradedlabels. Fullprobe observedgeneration medians45.2/39.3seconds plusstartup274.7/302.4seconds forbotharms. Prefixcostunmeasured. KL/directprobe bothperfect onmatched10checkpointsubset; noKLadvantageestablished.

**Caveats.** Degenerateperfect empiricalCI is notpopulationcertainty. Relatedlineages, smallfailure-enrichedsample, fixedSPEEDdistribution, noheldoutcheckpointvalidation. Onezero-stepquery excludedpairwise. Archived174census notmixed withoutfreezeaudit. No newGPU jobs orpost-cutofftraining.

### 2026-10-08T15:48:50.558182-04:00 — KL comparator overlap correction
InitialKLscoreused8contextsfrom112labelqueries. `compare_kl_disjoint.py` nowremovesthose8; bothKL/directscorescomparedagainstsame104disjointlabelqueries,n10models,4degraded. AUROCstill1forbothfamilies/probes,degenerateempiricalCIsretained. Primarydirect16/112analysisunchanged. Source `artifacts/P5_triage_20261008_1533/KL-disjoint-results.json`; originalcomparisonpreserved,superseded.
