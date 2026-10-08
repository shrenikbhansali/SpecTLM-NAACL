# P3 self-elicited data scaling — 2026-10-08

**Pilot; 24/24 self-scaling cells complete.** Generic4k remains in progress. Frozen6da2e42, vLLM0.31.0, EAGLE-3 K4, A40, greedy, batch8,512tokens. Exact same derivative-rendered token IDs across all arms; SPEED n128, MATH n64. All intervals are10,000 prompt-paired bootstrap draws, conditional on training seed0. Three-seed4k replication has launched.

At4k and one epoch, fc/full recover43.8%/56.8% of the SPEED dedicated-drafter gap and28.4%/40.5% of the MATH gap. Compared directly with the256-example,300-step seed0 controls, SPEED p1 rises2.33[1.55,3.11] and3.28[2.42,4.16] percentage points. MATH rises3.38[2.62,4.13] and5.75[4.58,6.93] points. Full remains stronger thanfc; neither closes the oracle gap.

The1k result is less clear: SPEED p1 contrasts against256 include zero for both arms; MATH includes zero forfc but improves forfull. Keep these nulls. The data/step/schedule budgets change jointly, so this is a data-and-compute scaling result, not an isolated effect of data diversity. Choosing a configuration on these panels makes them development evidence; there is no untouched selection-confirmation claim.

## Final-epoch results

| Data | Arm | Workload | n | Steps | Δp1 vs reused [95% CI] | τ [95% CI] | Oracle-gap recovery [95% CI] | Data+train GPUh |
|---|---|---|---:|---:|---|---|---|---:|
| self1k | fc | math64 | 64 | 329 | 0.1476 [0.1362, 0.1588] | 2.4012 [2.3536, 2.4517] | 23.2% [21.5, 24.9] | 1.500 upper bound |
| self1k | fc | speed128 | 128 | 329 | 0.1519 [0.1401, 0.1629] | 2.1370 [2.0776, 2.1932] | 36.4% [34.0, 38.8] | 1.500 upper bound |
| self1k | full | math64 | 64 | 329 | 0.1825 [0.1676, 0.1970] | 2.5835 [2.5325, 2.6387] | 32.5% [29.7, 35.5] | 1.537 upper bound |
| self1k | full | speed128 | 128 | 329 | 0.1830 [0.1707, 0.1945] | 2.2612 [2.1975, 2.3217] | 47.5% [45.1, 50.0] | 1.537 upper bound |
| self4k | fc | math64 | 64 | 1315 | 0.1742 [0.1628, 0.1850] | 2.5039 [2.4585, 2.5491] | 28.4% [26.4, 30.5] | 5.398 |
| self4k | fc | speed128 | 128 | 1315 | 0.1766 [0.1638, 0.1886] | 2.2196 [2.1564, 2.2805] | 43.8% [41.4, 46.1] | 5.398 |
| self4k | full | math64 | 64 | 1315 | 0.2191 [0.2066, 0.2313] | 2.7396 [2.6888, 2.7962] | 40.5% [37.9, 43.4] | 5.555 |
| self4k | full | speed128 | 128 | 1315 | 0.2088 [0.1948, 0.2218] | 2.3650 [2.2954, 2.4317] | 56.8% [54.5, 59.1] | 5.555 |

## Direct paired comparisons with256 examples /300steps

| Data | Arm | Workload | Δp1 [95% CI] | Δτ [95% CI] |
|---|---|---|---|---|
| self1k | fc | speed128 | -0.0014 [-0.0085, 0.0055] | 0.0098 [-0.0091, 0.0285] |
| self1k | fc | math64 | 0.0072 [-0.0021, 0.0167] | 0.0214 [-0.0104, 0.0567] |
| self1k | full | speed128 | 0.0070 [-0.0001, 0.0145] | 0.0177 [-0.0054, 0.0420] |
| self1k | full | math64 | 0.0209 [0.0130, 0.0287] | 0.0895 [0.0556, 0.1243] |
| self4k | fc | speed128 | 0.0233 [0.0155, 0.0311] | 0.0925 [0.0703, 0.1151] |
| self4k | fc | math64 | 0.0338 [0.0262, 0.0413] | 0.1241 [0.0948, 0.1537] |
| self4k | full | speed128 | 0.0328 [0.0242, 0.0416] | 0.1215 [0.0953, 0.1497] |
| self4k | full | math64 | 0.0575 [0.0458, 0.0693] | 0.2457 [0.2084, 0.2860] |

## All requested checkpoints

| Data | Arm | Step | Workload | Δp1 [95% CI] | τ | Gap recovery [95% CI] | Mean output tokens | Data+train GPUh |
|---|---|---:|---|---|---:|---|---:|---:|
| self1k | fc | 83 | math64 | 0.1243 [0.1128, 0.1352] | 2.3127 | 18.7% [17.0, 20.3] | 504.7 | 1.386* |
| self1k | fc | 83 | speed128 | 0.1325 [0.1214, 0.1433] | 2.0725 | 30.6% [28.3, 32.9] | 502.2 | 1.386* |
| self1k | fc | 165 | math64 | 0.1329 [0.1213, 0.1444] | 2.3740 | 21.8% [19.9, 23.8] | 501.2 | 1.426* |
| self1k | fc | 165 | speed128 | 0.1512 [0.1394, 0.1625] | 2.1281 | 35.6% [33.3, 37.9] | 502.3 | 1.426* |
| self1k | fc | 329 | math64 | 0.1476 [0.1362, 0.1588] | 2.4012 | 23.2% [21.5, 24.9] | 505.8 | 1.500* |
| self1k | fc | 329 | speed128 | 0.1519 [0.1401, 0.1629] | 2.1370 | 36.4% [34.0, 38.8] | 503.2 | 1.500* |
| self1k | full | 83 | math64 | 0.1550 [0.1429, 0.1666] | 2.4574 | 26.1% [24.1, 28.1] | 504.8 | 1.398* |
| self1k | full | 83 | speed128 | 0.1647 [0.1523, 0.1766] | 2.1992 | 41.9% [39.4, 44.5] | 503.7 | 1.398* |
| self1k | full | 165 | math64 | 0.1750 [0.1614, 0.1886] | 2.5546 | 31.0% [28.4, 34.0] | 501.2 | 1.447* |
| self1k | full | 165 | speed128 | 0.1793 [0.1672, 0.1906] | 2.2448 | 46.0% [43.8, 48.2] | 499.6 | 1.447* |
| self1k | full | 329 | math64 | 0.1825 [0.1676, 0.1970] | 2.5835 | 32.5% [29.7, 35.5] | 501.2 | 1.537* |
| self1k | full | 329 | speed128 | 0.1830 [0.1707, 0.1945] | 2.2612 | 47.5% [45.1, 50.0] | 501.5 | 1.537* |
| self4k | fc | 329 | math64 | 0.1620 [0.1512, 0.1730] | 2.4506 | 25.7% [24.1, 27.3] | 505.6 | 4.955 |
| self4k | fc | 329 | speed128 | 0.1634 [0.1513, 0.1746] | 2.1733 | 39.6% [37.4, 41.9] | 501.4 | 4.955 |
| self4k | fc | 658 | math64 | 0.1710 [0.1593, 0.1824] | 2.4857 | 27.5% [25.5, 29.5] | 503.8 | 5.104 |
| self4k | fc | 658 | speed128 | 0.1747 [0.1635, 0.1853] | 2.2129 | 43.2% [41.0, 45.4] | 497.7 | 5.104 |
| self4k | fc | 1315 | math64 | 0.1742 [0.1628, 0.1850] | 2.5039 | 28.4% [26.4, 30.5] | 505.9 | 5.398 |
| self4k | fc | 1315 | speed128 | 0.1766 [0.1638, 0.1886] | 2.2196 | 43.8% [41.4, 46.1] | 502.8 | 5.398 |
| self4k | full | 329 | math64 | 0.2039 [0.1917, 0.2156] | 2.6570 | 36.3% [34.0, 38.8] | 501.2 | 4.997 |
| self4k | full | 329 | speed128 | 0.1892 [0.1767, 0.2010] | 2.2863 | 49.7% [47.5, 52.1] | 498.9 | 4.997 |
| self4k | full | 658 | math64 | 0.2113 [0.2004, 0.2221] | 2.6751 | 37.2% [35.1, 39.5] | 501.2 | 5.186 |
| self4k | full | 658 | speed128 | 0.2029 [0.1895, 0.2152] | 2.3366 | 54.2% [51.8, 56.8] | 501.0 | 5.186 |
| self4k | full | 1315 | math64 | 0.2191 [0.2066, 0.2313] | 2.7396 | 40.5% [37.9, 43.4] | 501.2 | 5.555 |
| self4k | full | 1315 | speed128 | 0.2088 [0.1948, 0.2218] | 2.3650 | 56.8% [54.5, 59.1] | 500.9 | 5.555 |

## Provenance and limitations

- Family-drafter warm start; native TTT3 objective unchanged. Exactly one epoch:1k329steps/556,908tokens;4k1,315steps/2,228,270tokens. Fc/full match data/order/token budget/optimizer/scheduler within each scale. Actual2048-token packing gives about85steps/epoch at256, correcting the earlier informal19-step estimate in plan§7.
- Training data are nested: old256 then deterministic globally deduplicated source order. Self4k4656candidates→4652unique→4000; first1000 exactly equals self1k. All evaluation queries including full MATH500 excluded. Firstfive decoded strings/masks reviewed for every source; allselected rows have contiguous answer-only masks. No outcome filtering or answer-quality filtering.
- Self4k generation cost4.7997GPUh includes old256 and all four1100shards, including oversampling; charge this once per independently costed repair. Do not sum that shared source cost again across replicas when quoting actual campaign spend. Fc/full training cost about0.598/0.755GPUh. Evaluation, engineering and failed-path costs are excluded from per-repair numbers.
- *Self1k generation cost is a conservative elapsed-time upper bound through the early prefix snapshot, including unused work; scope is recorded in assembly.json. It is not a measured minimal1k generation cost.
- Generation is capped at512tokens:247/256,965/1000,3861/4000 answers hit the cap. Most capped reasoning traces lack a final answer; factual and query errors are retained. No quality/accuracy conclusion follows from acceptance gains.
- Recovery uses the raw paired workload-specific (repairedτ−reusedτ)/(oracleτ−reusedτ), resampling all three jointly. The fixed D46 SPEED normalization(τ−1.73)/1.12 is also retained in rawresults. MATH uses its ownoracle baseline.
- Per-depth conditional acceptance, absolute p1, paired lengths and hashes are in the raw result snapshot; no pooling across query lengths. Final4k meanlengths and length contrasts are reported, including capped-output sensitivity.
- Generic4k is pending. Larger self4k seeds and transfer runs are parallel provisional replication of this self-elicited recipe, not a declaration that it beats the generic alternative.

Acceptance source: [artifacts/D48_analysis_20261008_1528/snapshot-20261008_165630/results.json](../artifacts/D48_analysis_20261008_1528/snapshot-20261008_165630/results.json); independent256/full-fc contrasts and data audits: [artifacts/P3_D48_scaling_report_20261008_1615/snapshot-20261008_165611/results.json](../artifacts/P3_D48_scaling_report_20261008_1615/snapshot-20261008_165611/results.json). Scripts analyze_v3.py and contrasts.py rederive metrics from raw counters; all frozen-engine/hardware/prompt hashes and matched-training checks pass. Artifacts are immutable.

[Self-elicited scaling figure](figures/P3-self-scaling-D48-20261008.pdf). Serving-time results for these4k exports are pending in the separate P6 follow-up; completed256-export timing must not be presented as measured4k speed.
