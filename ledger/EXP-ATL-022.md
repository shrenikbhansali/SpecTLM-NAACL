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

### 2026-10-08T16:28:57.414669-04:00 — codex-1 — CPU prefix budget curve
Script artifacts/P5_prefix_curve_20261008_1627/analyze.py runs noGPUjobs. Same16/112querysplit/21checkpoints, fixed.9threshold; budgets16/32/64/128/full allreported. AUROCedgecaseasserts and exactreproductionofpriorfull/prefix16scores/labels pass. Addedpairedquery+checkpointbootstrap, propagatinguncertainlabels: fullEAGLE1.0CI[.75,1], instead ofdegenerateconditionalcheckpoint-onlyCI. EAGLE16/32/64 weak;128 .980[.653,1] uses66.4%iterations. DFlash64 .945[.709,1] uses44.7%,128 .991[.764,1] uses77.5%. No shortwallclockclaim or newcheckpointvalidation. Figureinspected andreportappended; EXP022 addendum.

### 2026-10-08T17:02:55.003260-04:00 — codex-1 — CPU triage extended to all174 census checkpoints
reports/P5-census-triage-20261008.md; artifacts/P5_census_20261008_1702/analysis-v2/results.json. All348pairedrecords retained (163own-domain64+11fallback128 eachdrafter);16probequeries vs48/112disjointlabels,outcome-blindbatchhashrule,unchangedretention0.9threshold. Own-domainfullprobeAUROC E.908[.668,.983]/D.934[.745,.993],3000checkpoint+pairedqueryCI;fixedthresholdmisses5/14and3/17. Prefix16E.888[.608,.971]/D.929[.709,.981],morefalsepositives. Fallbackm11tooimprecise; allreported. InitialindependentquerydrawCIs supersededbyv2sharedquery-setdraws, originalsretained; allcentralestimatesexactlymatch. SyntheticAUROC+348actualpairedexclusion/batchchecksPASS. Historicalgenerationcommits423d3b6/f00992fexplicit, FIX23frozenmetriccompatibility; notnewfrozenlaunches/notmixedwithSPEEDpanel. Fullprobeobservedgenerationmedians24.7/18.8s,init306.4/315.5s; prefixcostunmeasured. Prospectivecheckpointvalidation/shorttimingremainopen. NoGPUjobs.
