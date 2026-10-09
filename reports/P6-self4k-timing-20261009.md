# P6 self4k timing follow-up

Pilot completed 2026-10-08T18:13:16.650680-04:00. All30cells: fc/fullself4k1315stepseed0, reused/oracle/no-speculationfreshcontrols; A40,vLLM0.31.0,greedy512,identicalSPEED128IDs,batch1fixed32. Threeprocessespercondition,eachfirstpanel+3warmpasses. Exact215fb44timingpathimportsfrozen6da2e42; acceptance reported separately.

| Batch/n | Arm | Warm speedup vs no speculation [95% CI] | Token throughput ratio [95% CI] | First panel + startup [95% CI] |
|---|---|---|---|---|
| 8/128 | reused | 1.070 [0.999, 1.143] | 1.066 [0.994, 1.141] | 0.955 [0.895, 1.017] |
| 8/128 | fc | 1.233 [1.096, 1.394] | 1.226 [1.088, 1.389] | 1.040 [0.954, 1.136] |
| 8/128 | full | 1.286 [1.137, 1.468] | 1.280 [1.129, 1.462] | 1.044 [0.965, 1.132] |
| 8/128 | oracle | 1.408 [1.209, 1.660] | 1.403 [1.204, 1.658] | 1.095 [0.983, 1.232] |
| 1/32 | reused | 1.277 [1.208, 1.349] | 1.292 [1.236, 1.353] | 1.111 [1.049, 1.175] |
| 1/32 | fc | 1.634 [1.535, 1.736] | 1.652 [1.565, 1.738] | 1.349 [1.286, 1.413] |
| 1/32 | full | 1.750 [1.652, 1.850] | 1.773 [1.683, 1.864] | 1.428 [1.367, 1.492] |
| 1/32 | oracle | 2.038 [1.848, 2.226] | 2.056 [1.868, 2.234] | 1.534 [1.433, 1.627] |

Intervals crossing1 remain null comparisons. First(cold)panel is after engine compilation/warmup; startupseparate. Bootstrap10000pairedprocess+promptbatchdraws,averaging3warmpasseswithinprocess. AvailableA40sare notrandomizedexclusivehosts.

| Batch | Arm | Reference | Seconds saved/query [95% CI] | Break-even queries [95% CI] | Data+train GPUh |
|---|---|---|---|---|---|
| 8 | fc | reused | 0.248 [0.164, 0.331] | 78,482 [58,654, 118,146] | 5.398 |
| 8 | fc | none | 0.379 [0.176, 0.567] | 51,318 [34,287, 110,104] | 5.398 |
| 8 | full | reused | 0.316 [0.230, 0.402] | 63,361 [49,751, 87,126] | 5.555 |
| 8 | full | none | 0.447 [0.243, 0.638] | 44,770 [31,344, 82,465] | 5.555 |
| 1 | fc | reused | 2.413 [2.037, 2.701] | 8,053 [7,195, 9,542] | 5.398 |
| 1 | fc | none | 5.464 [4.837, 6.039] | 3,557 [3,218, 4,018] | 5.398 |
| 1 | full | reused | 2.986 [2.669, 3.278] | 6,698 [6,100, 7,494] | 5.555 |
| 1 | full | none | 6.037 [5.488, 6.535] | 3,313 [3,060, 3,644] | 5.555 |

Costsinclude4.7997GPUhsourcegeneration/oversamplingplusactualtraining. Eachalternativechargedsharedgenerationonce; campaignspendmustnotduplicatethiscostacrossreplicas. Engineering/search/evaluationexcluded; oracletrainingcostunknown. Break-evenassumesthisquerymixandwarmbatchoccupancy,notdeploymentforecast;nonpositivesavingsgiveundefined/unbounded estimates.

Outputidentity audit (complete sequences):

| Comparison | Batch | Arm | Identical / compared | Identical first token / compared |
|---|---|---|---|---|
| across_process | 8 | none | 85/256 | 255/256 |
| across_process | 1 | none | 33/64 | 64/64 |
| within_process | 8 | none | 632/1152 | 1151/1152 |
| within_process | 1 | none | 288/288 | 288/288 |
| versus_no_speculation | 8 | fc | 49/1536 | 1533/1536 |
| versus_no_speculation | 8 | full | 81/1536 | 1526/1536 |
| versus_no_speculation | 1 | fc | 16/384 | 384/384 |
| versus_no_speculation | 1 | full | 12/384 | 384/384 |

Actualsame-inputgreedyworkloads maydifferinoutputtokensacrossarmsandfreshprocesses. Theseare notidentical-outputworktimings or outputequivalencecertification. Lengths/token-normalizedthroughputandallper-processvaluesremaininrawsources; noacceptancestatisticisderivedfromtimingrecords.

{
  "timing": "/home/heck2/sbhansali8/SpecTLM/artifacts/P6_D48_self4k_20261008_1707/timing/snapshot-20261008_181314/results.json",
  "economics": "/home/heck2/sbhansali8/SpecTLM/artifacts/P6_D48_self4k_20261008_1707/economics/snapshot-20261008_181315/results.json",
  "output_audit": "/home/heck2/sbhansali8/SpecTLM/artifacts/P6_D48_self4k_20261008_1707/output_audit/snapshot-20261008_181316/results.json"
}

Published 2026-10-09T02:28:13.739308-04:00; immutable original analysis at `artifacts/P6_D48_self4k_20261008_1707/final-report.md`.
