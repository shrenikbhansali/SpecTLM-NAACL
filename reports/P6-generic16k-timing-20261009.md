# P6 generic16k timing follow-up

Pilot completed 2026-10-09T02:50:34.277931-04:00. All30cells: fc/fullgeneric16k4477stepseed0, reused/oracle/no-speculationfreshcontrols; A40,vLLM0.31.0,greedy512,identicalSPEED128IDs,batch1fixed32. Threeprocessespercondition,eachfirstpanel+3warmpasses. Exact215fb44timingpathimportsfrozen6da2e42; acceptance reported separately.

| Batch/n | Arm | Warm speedup vs no speculation [95% CI] | Token throughput ratio [95% CI] | First panel + startup [95% CI] |
|---|---|---|---|---|
| 8/128 | reused | 1.072 [1.000, 1.148] | 1.074 [1.002, 1.151] | 0.947 [0.902, 0.993] |
| 8/128 | fc | 1.274 [1.125, 1.447] | 1.274 [1.124, 1.449] | 1.061 [0.979, 1.147] |
| 8/128 | full | 1.306 [1.140, 1.515] | 1.317 [1.151, 1.531] | 1.081 [0.989, 1.185] |
| 8/128 | oracle | 1.438 [1.239, 1.693] | 1.445 [1.242, 1.702] | 1.151 [1.052, 1.265] |
| 1/32 | reused | 1.291 [1.228, 1.363] | 1.296 [1.240, 1.358] | 1.136 [1.094, 1.182] |
| 1/32 | fc | 1.724 [1.626, 1.821] | 1.743 [1.651, 1.831] | 1.392 [1.338, 1.447] |
| 1/32 | full | 1.807 [1.683, 1.929] | 1.820 [1.705, 1.930] | 1.446 [1.382, 1.509] |
| 1/32 | oracle | 2.048 [1.865, 2.230] | 2.057 [1.881, 2.221] | 1.575 [1.475, 1.675] |

Intervals crossing1 remain null comparisons. First(cold)panel is after engine compilation/warmup; startupseparate. Bootstrap10000pairedprocess+promptbatchdraws,averaging3warmpasseswithinprocess. AvailableA40sare notrandomizedexclusivehosts.

| Batch | Arm | Reference | Seconds saved/query [95% CI] | Break-even queries [95% CI] | Data+train GPUh |
|---|---|---|---|---|---|
| 8 | fc | reused | 0.296 [0.207, 0.378] | 132,869 [103,823, 189,275] | 10.907 |
| 8 | fc | none | 0.431 [0.223, 0.617] | 91,159 [63,683, 176,094] | 10.907 |
| 8 | full | reused | 0.335 [0.226, 0.440] | 120,229 [91,502, 178,283] | 11.175 |
| 8 | full | none | 0.470 [0.247, 0.679] | 85,628 [59,239, 162,730] | 11.175 |
| 1 | fc | reused | 2.749 [2.383, 3.057] | 14,285 [12,843, 16,477] | 10.907 |
| 1 | fc | none | 5.939 [5.391, 6.438] | 6,611 [6,099, 7,284] | 10.907 |
| 1 | full | reused | 3.126 [2.776, 3.450] | 12,868 [11,661, 14,495] | 11.175 |
| 1 | full | none | 6.317 [5.678, 6.862] | 6,369 [5,863, 7,085] | 11.175 |

Costsincludeactual16kgeneration(includingreused4kprefix)plusactualtraining. Eachalternativechargedsharedgenerationonce; campaignspendmustnotduplicatethiscostacrossreplicas. Engineering/search/evaluationexcluded; oracletrainingcostunknown. Break-evenassumesthisquerymixandwarmbatchoccupancy,notdeploymentforecast;nonpositivesavingsgiveundefined/unbounded estimates.

Outputidentity audit (complete sequences):

| Comparison | Batch | Arm | Identical / compared | Identical first token / compared |
|---|---|---|---|---|
| across_process | 8 | none | 21/256 | 254/256 |
| across_process | 1 | none | 3/64 | 64/64 |
| within_process | 8 | none | 750/1152 | 1146/1152 |
| within_process | 1 | none | 288/288 | 288/288 |
| versus_no_speculation | 8 | fc | 100/1536 | 1518/1536 |
| versus_no_speculation | 8 | full | 68/1536 | 1518/1536 |
| versus_no_speculation | 1 | fc | 12/384 | 384/384 |
| versus_no_speculation | 1 | full | 8/384 | 384/384 |

Actualsame-inputgreedyworkloads maydifferinoutputtokensacrossarmsandfreshprocesses. Theseare notidentical-outputworktimings or outputequivalencecertification. Lengths/token-normalizedthroughputandallper-processvaluesremaininrawsources; noacceptancestatisticisderivedfromtimingrecords.

{
  "timing": "/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/E6-timing/timing/snapshot-20261009_025031/results.json",
  "economics": "/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/E6-timing/economics/snapshot-20261009_025032/results.json",
  "output_audit": "/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/E6-timing/output_audit/snapshot-20261009_025033/results.json"
}
