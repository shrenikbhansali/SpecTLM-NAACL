# D50 consolidated results — pilot

Updated 2026-10-09T14:53:39.454090-04:00. 207 raw-recomputed rows; 32 invalid FIX-24 cells excluded. This snapshot contains completed D50 controls and three-seed16k results. Corrected official4k, 64k scaling, and Nemotron timing are running and will be appended as immutable updates. No owner conclusion or gate certification.

Acceptance: frozen6da2e42, vLLM0.31.0, A40, greedy512, batch8, same derivative-rendered token IDs across arms. Prompt hashes, paired target/settings, raw speculative counters and aggregate consistency checked. 10000 paired-query bootstrap draws; the16k three-seed rows additionally resample training seeds. MATH500 uses seed0 only and overlaps MATH64.

[Full raw source and input hashes](../artifacts/D50_final_20261009_1451/results.json); [compiled LaTeX preview](../artifacts/D50_final_20261009_1451/tables-preview.pdf); [LaTeX fragments](../paper/tables/D50-20261009-1451/README.md).

FIX-24: official reuse remains valid; every historical official4k repair and official_vs_production contrast is INVALID. Both corrected target embeddings equal target weights exactly after lossless dtype conversion; production state and all step0 metrics are unchanged. Four corrected fc/full runs use new directories. [Evidence](../notes/FIX-24.md).

## R1 main table

Recovery is the fraction of the raw workload-specific dedicated-oracle τ gap. Cross-drafter/K comparisons are descriptive. N-gram τ is conditional on proposal-bearing turns, not a measured speedup. Missing arm/workload combinations have not been measured, not assigned zero.

| Target | Workload | Arm / checkpoint | n / seeds | p1 [95% CI] | tau [95% CI] | Delta p1 [95% CI] | Oracle gap [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | math500 | generic16k-fc / 4477 | 500 / 1 | 0.696 [0.692, 0.701] | 2.611 [2.593, 2.630] | 0.201 [0.197, 0.205] | 0.350 [0.342, 0.357] |
| R1 | math500 | generic16k-full / 4477 | 500 / 1 | 0.738 [0.734, 0.743] | 2.858 [2.836, 2.880] | 0.243 [0.239, 0.248] | 0.480 [0.472, 0.488] |
| R1 | math500 | independent / 0 | 500 / 1 | 0.709 [0.705, 0.714] | 2.966 [2.940, 2.992] | 0.214 [0.209, 0.220] | 0.537 [0.528, 0.547] |
| R1 | math500 | oracle / 0 | 500 / 1 | 0.872 [0.868, 0.876] | 3.842 [3.815, 3.869] | 0.377 [0.372, 0.382] | 1.000 [1.000, 1.000] |
| R1 | math500 | reused / 0 | 500 / 1 | 0.495 [0.491, 0.500] | 1.949 [1.935, 1.964] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| R1 | math64 | E4-scratch16k / 4477 | 64 / 1 | 0.425 [0.408, 0.442] | 1.672 [1.638, 1.711] | -0.067 [-0.088, -0.046] | -0.141 [-0.174, -0.110] |
| R1 | math64 | E5-second-epoch / 4490 | 64 / 1 | 0.752 [0.742, 0.763] | 2.933 [2.876, 2.996] | 0.260 [0.245, 0.275] | 0.504 [0.478, 0.531] |
| R1 | math64 | E5-ttt4-fc / 1115 | 64 / 1 | 0.668 [0.657, 0.678] | 2.525 [2.478, 2.574] | 0.175 [0.163, 0.188] | 0.295 [0.274, 0.317] |
| R1 | math64 | E5-ttt4-full / 1115 | 64 / 1 | 0.716 [0.705, 0.727] | 2.765 [2.709, 2.826] | 0.224 [0.211, 0.237] | 0.418 [0.390, 0.449] |
| R1 | math64 | draft_model-K4-LNone / 0 | 64 / 1 | 0.723 [0.711, 0.736] | 3.019 [2.950, 3.091] | 0.231 [0.218, 0.245] | 0.548 [0.525, 0.571] |
| R1 | math64 | draft_model-K6-LNone / 0 | 64 / 1 | 0.697 [0.684, 0.710] | 3.420 [3.311, 3.535] | 0.205 [0.191, 0.218] | 0.752 [0.713, 0.795] |
| R1 | math64 | generic16k-fc / 4477/4472/4481 | 64 / 3 | 0.705 [0.695, 0.716] | 2.658 [2.610, 2.708] | 0.213 [0.202, 0.225] | 0.363 [0.343, 0.384] |
| R1 | math64 | generic16k-full / 4477/4472/4481 | 64 / 3 | 0.745 [0.735, 0.754] | 2.892 [2.842, 2.946] | 0.253 [0.240, 0.264] | 0.483 [0.463, 0.503] |
| R1 | math64 | ngram-K4-L3 / 0 | 64 / 1 | 0.293 [0.276, 0.310] | 1.591 [1.544, 1.642] | -0.199 [-0.217, -0.182] | -0.182 [-0.208, -0.156] |
| R1 | math64 | ngram-K4-L5 / 0 | 64 / 1 | 0.296 [0.278, 0.314] | 1.595 [1.549, 1.644] | -0.196 [-0.215, -0.178] | -0.180 [-0.208, -0.153] |
| R1 | math64 | ngram-K8-L3 / 0 | 64 / 1 | 0.280 [0.264, 0.295] | 1.652 [1.596, 1.712] | -0.212 [-0.230, -0.195] | -0.151 [-0.180, -0.121] |
| R1 | math64 | ngram-K8-L5 / 0 | 64 / 1 | 0.278 [0.264, 0.294] | 1.659 [1.604, 1.717] | -0.214 [-0.230, -0.197] | -0.147 [-0.178, -0.117] |
| R1 | math64 | official-reuse / 0 | 64 / 1 | 0.491 [0.479, 0.504] | 1.923 [1.881, 1.968] | -0.001 [-0.012, 0.011] | -0.013 [-0.030, 0.007] |
| R1 | math64 | oracle / 0 | 64 / 1 | 0.880 [0.869, 0.891] | 3.904 [3.828, 3.982] | 0.388 [0.373, 0.403] | 1.000 [1.000, 1.000] |
| R1 | math64 | reused / 0 | 64 / 1 | 0.492 [0.480, 0.505] | 1.948 [1.906, 1.994] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| R1 | speed128 | E4-scratch16k / 4477 | 128 / 1 | 0.345 [0.328, 0.360] | 1.519 [1.489, 1.549] | -0.066 [-0.080, -0.053] | -0.189 [-0.229, -0.153] |
| R1 | speed128 | E5-second-epoch / 4490 | 128 / 1 | 0.642 [0.616, 0.664] | 2.480 [2.405, 2.550] | 0.231 [0.217, 0.244] | 0.671 [0.650, 0.692] |
| R1 | speed128 | E5-ttt4-fc / 1115 | 128 / 1 | 0.586 [0.562, 0.607] | 2.220 [2.160, 2.277] | 0.175 [0.164, 0.186] | 0.438 [0.416, 0.460] |
| R1 | speed128 | E5-ttt4-full / 1115 | 128 / 1 | 0.618 [0.593, 0.641] | 2.367 [2.297, 2.432] | 0.207 [0.195, 0.219] | 0.569 [0.547, 0.593] |
| R1 | speed128 | draft_model-K4-LNone / 0 | 128 / 1 | 0.613 [0.603, 0.624] | 2.441 [2.388, 2.498] | 0.202 [0.187, 0.218] | 0.636 [0.581, 0.701] |
| R1 | speed128 | draft_model-K6-LNone / 0 | 128 / 1 | 0.608 [0.597, 0.619] | 2.665 [2.588, 2.746] | 0.197 [0.182, 0.213] | 0.836 [0.766, 0.918] |
| R1 | speed128 | generic16k-fc / 4477/4472/4481 | 128 / 3 | 0.606 [0.582, 0.628] | 2.300 [2.237, 2.360] | 0.195 [0.184, 0.206] | 0.509 [0.488, 0.530] |
| R1 | speed128 | generic16k-full / 4477/4472/4481 | 128 / 3 | 0.639 [0.614, 0.662] | 2.466 [2.394, 2.536] | 0.228 [0.215, 0.241] | 0.658 [0.634, 0.682] |
| R1 | speed128 | ngram-K4-L3 / 0 | 128 / 1 | 0.243 [0.228, 0.259] | 1.485 [1.439, 1.537] | -0.168 [-0.189, -0.143] | -0.219 [-0.260, -0.168] |
| R1 | speed128 | ngram-K4-L5 / 0 | 128 / 1 | 0.248 [0.230, 0.267] | 1.510 [1.449, 1.580] | -0.163 [-0.187, -0.135] | -0.197 [-0.248, -0.130] |
| R1 | speed128 | ngram-K8-L3 / 0 | 128 / 1 | 0.230 [0.218, 0.244] | 1.518 [1.468, 1.572] | -0.180 [-0.201, -0.158] | -0.190 [-0.235, -0.139] |
| R1 | speed128 | ngram-K8-L5 / 0 | 128 / 1 | 0.231 [0.219, 0.244] | 1.526 [1.474, 1.584] | -0.180 [-0.200, -0.157] | -0.183 [-0.229, -0.126] |
| R1 | speed128 | official-reuse / 0 | 128 / 1 | 0.430 [0.410, 0.447] | 1.764 [1.719, 1.808] | 0.019 [0.009, 0.028] | 0.030 [0.007, 0.050] |
| R1 | speed128 | oracle / 0 | 128 / 1 | 0.705 [0.676, 0.730] | 2.848 [2.751, 2.939] | 0.294 [0.277, 0.309] | 1.000 [1.000, 1.000] |
| R1 | speed128 | reused / 0 | 128 / 1 | 0.411 [0.393, 0.427] | 1.730 [1.687, 1.774] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

## Nemotron

No dedicated oracle exists for this target in this campaign; recovery is undefined.

| Target | Workload | Arm / checkpoint | n / seeds | p1 [95% CI] | tau [95% CI] | Delta p1 [95% CI] | Oracle gap [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nemotron | math64 | E1-production-t1-4k-fc / 652 | 64 / 1 | 0.668 [0.655, 0.680] | 2.483 [2.441, 2.525] | 0.168 [0.158, 0.177] | -- |
| Nemotron | math64 | E1-production-t1-4k-full / 652 | 64 / 1 | 0.710 [0.696, 0.723] | 2.696 [2.647, 2.746] | 0.209 [0.200, 0.218] | -- |
| Nemotron | math64 | E7-production-t1-16k-fc / 2625 | 64 / 1 | 0.693 [0.680, 0.707] | 2.591 [2.546, 2.635] | 0.193 [0.182, 0.204] | -- |
| Nemotron | math64 | E7-production-t1-16k-full / 2625 | 64 / 1 | 0.734 [0.722, 0.746] | 2.819 [2.770, 2.868] | 0.234 [0.223, 0.244] | -- |
| Nemotron | math64 | draft_model-K4-LNone / 0 | 64 / 1 | 0.674 [0.662, 0.686] | 2.838 [2.781, 2.893] | 0.174 [0.161, 0.187] | -- |
| Nemotron | math64 | draft_model-K6-LNone / 0 | 64 / 1 | 0.660 [0.648, 0.673] | 3.184 [3.096, 3.273] | 0.160 [0.146, 0.174] | -- |
| Nemotron | math64 | ngram-K4-L3 / 0 | 64 / 1 | 0.257 [0.245, 0.268] | 1.494 [1.463, 1.525] | -0.243 [-0.259, -0.228] | -- |
| Nemotron | math64 | ngram-K4-L5 / 0 | 64 / 1 | 0.261 [0.249, 0.272] | 1.504 [1.475, 1.535] | -0.239 [-0.255, -0.224] | -- |
| Nemotron | math64 | ngram-K8-L3 / 0 | 64 / 1 | 0.252 [0.242, 0.263] | 1.536 [1.499, 1.573] | -0.248 [-0.261, -0.234] | -- |
| Nemotron | math64 | ngram-K8-L5 / 0 | 64 / 1 | 0.254 [0.244, 0.264] | 1.547 [1.510, 1.585] | -0.246 [-0.261, -0.232] | -- |
| Nemotron | math64 | official-reuse / 0 | 64 / 1 | 0.452 [0.442, 0.461] | 1.703 [1.679, 1.727] | -0.049 [-0.058, -0.039] | -- |
| Nemotron | math64 | reused / 0 | 64 / 1 | 0.500 [0.488, 0.512] | 1.960 [1.925, 1.994] | 0.000 [0.000, 0.000] | -- |
| Nemotron | speed128 | E1-production-t1-4k-fc / 652 | 128 / 1 | 0.579 [0.554, 0.603] | 2.252 [2.184, 2.319] | 0.144 [0.133, 0.155] | -- |
| Nemotron | speed128 | E1-production-t1-4k-full / 652 | 128 / 1 | 0.605 [0.578, 0.630] | 2.361 [2.284, 2.436] | 0.170 [0.158, 0.181] | -- |
| Nemotron | speed128 | E7-production-t1-16k-fc / 2625 | 128 / 1 | 0.597 [0.569, 0.623] | 2.315 [2.239, 2.389] | 0.161 [0.149, 0.173] | -- |
| Nemotron | speed128 | E7-production-t1-16k-full / 2625 | 128 / 1 | 0.620 [0.593, 0.646] | 2.424 [2.343, 2.502] | 0.184 [0.172, 0.196] | -- |
| Nemotron | speed128 | draft_model-K4-LNone / 0 | 128 / 1 | 0.647 [0.633, 0.661] | 2.653 [2.584, 2.721] | 0.211 [0.192, 0.232] | -- |
| Nemotron | speed128 | draft_model-K6-LNone / 0 | 128 / 1 | 0.649 [0.634, 0.663] | 2.992 [2.883, 3.104] | 0.213 [0.191, 0.237] | -- |
| Nemotron | speed128 | ngram-K4-L3 / 0 | 128 / 1 | 0.260 [0.239, 0.282] | 1.563 [1.494, 1.636] | -0.176 [-0.207, -0.142] | -- |
| Nemotron | speed128 | ngram-K4-L5 / 0 | 128 / 1 | 0.259 [0.238, 0.280] | 1.557 [1.490, 1.627] | -0.177 [-0.207, -0.144] | -- |
| Nemotron | speed128 | ngram-K8-L3 / 0 | 128 / 1 | 0.253 [0.232, 0.274] | 1.703 [1.589, 1.831] | -0.183 [-0.214, -0.149] | -- |
| Nemotron | speed128 | ngram-K8-L5 / 0 | 128 / 1 | 0.246 [0.226, 0.266] | 1.653 [1.554, 1.757] | -0.190 [-0.219, -0.158] | -- |
| Nemotron | speed128 | official-reuse / 0 | 128 / 1 | 0.429 [0.408, 0.450] | 1.763 [1.711, 1.817] | -0.007 [-0.018, 0.004] | -- |
| Nemotron | speed128 | reused / 0 | 128 / 1 | 0.436 [0.415, 0.456] | 1.823 [1.769, 1.879] | 0.000 [0.000, 0.000] | -- |

## Timing and cost model

Three fresh processes × three warm passes; paired process/query-batch CIs. First-panel+startup reported separately. Identical input IDs can produce different greedy output lengths, so panel speedup and token throughput are both shown. R1 cost model is fit only to earlier256/4k timings and validated on16k. Independent-drafter coefficients are not inferred from EAGLE3. Nemotron timing remains pending; any cross-target predictions will be labelled transfer stress tests, not calibrated Nemo estimates.

| Target | Batch | Arm | n / processes | Warm panel speedup | Measured token speedup | First panel + startup | Predicted token speedup | TPS prediction error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | 8 | reused | 128 / 3 | 1.072 [1.000, 1.148] | 1.074 [1.002, 1.151] | 0.947 [0.902, 0.993] | 1.069 [0.993, 1.142] | -0.03% |
| R1 | 8 | fc | 128 / 3 | 1.274 [1.125, 1.447] | 1.274 [1.124, 1.449] | 1.061 [0.979, 1.147] | 1.260 [1.105, 1.433] | -0.61% |
| R1 | 8 | full | 128 / 3 | 1.306 [1.140, 1.515] | 1.317 [1.151, 1.531] | 1.081 [0.989, 1.185] | 1.308 [1.132, 1.510] | -0.24% |
| R1 | 8 | oracle | 128 / 3 | 1.438 [1.239, 1.693] | 1.445 [1.242, 1.702] | 1.151 [1.052, 1.265] | -- | -- |
| R1 | 1 | reused | 32 / 3 | 1.291 [1.228, 1.363] | 1.296 [1.240, 1.358] | 1.136 [1.094, 1.182] | 1.292 [1.235, 1.350] | -0.36% |
| R1 | 1 | fc | 32 / 3 | 1.724 [1.626, 1.821] | 1.743 [1.651, 1.831] | 1.392 [1.338, 1.447] | 1.719 [1.622, 1.810] | -1.48% |
| R1 | 1 | full | 32 / 3 | 1.807 [1.683, 1.929] | 1.820 [1.705, 1.930] | 1.446 [1.382, 1.509] | 1.817 [1.703, 1.929] | -0.24% |
| R1 | 1 | oracle | 32 / 3 | 2.048 [1.865, 2.230] | 2.057 [1.881, 2.221] | 1.575 [1.475, 1.675] | -- | -- |
| R1 | 8 | independent | 128 / 3 | 1.108 [1.087, 1.131] | 1.114 [1.090, 1.139] | 1.054 [1.027, 1.088] | -- | -- |
| R1 | 1 | independent | 32 / 3 | 1.267 [1.203, 1.334] | 1.269 [1.219, 1.327] | 1.172 [1.124, 1.221] | -- | -- |

## Costs

Measured repair GPUh include data generation and online-capture training; shared data charged once per alternative, not summed repeatedly as campaign spend. Second-epoch training cost includes its first epoch. Search, engineering and evaluation costs excluded.

| Target | Arm | Seed | Step | Data GPUh | Train GPUh | Total GPUh | Scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nemotron | E7-production-t1-16k-fc | 0 | 2625 | 8.588 | 1.375 | 9.963 | measured; shared data charged once per alternative |
| Nemotron | E7-production-t1-16k-full | 0 | 2625 | 8.588 | 1.625 | 10.213 | measured; shared data charged once per alternative |
| R1 | E5-second-epoch | 0 | 4490 | 8.916 | 4.898 | 13.814 | measured; shared data charged once per alternative |
| R1 | E4-scratch16k | 0 | 4477 | 8.916 | 2.728 | 11.644 | measured; shared data charged once per alternative |
| R1 | generic16k-fc | 0 | 4477/4472/4481 | 8.916 | 1.991 | 10.907 | measured; shared data charged once per alternative |
| R1 | generic16k-fc | 1 | 4477/4472/4481 | 8.916 | 2.393 | 11.309 | measured; shared data charged once per alternative |
| R1 | generic16k-fc | 2 | 4477/4472/4481 | 8.916 | 2.024 | 10.941 | measured; shared data charged once per alternative |
| R1 | generic16k-full | 0 | 4477/4472/4481 | 8.916 | 2.259 | 11.175 | measured; shared data charged once per alternative |
| R1 | generic16k-full | 1 | 4477/4472/4481 | 8.916 | 2.258 | 11.174 | measured; shared data charged once per alternative |
| R1 | generic16k-full | 2 | 4477/4472/4481 | 8.916 | 2.339 | 11.256 | measured; shared data charged once per alternative |

Dedicated-cost sensitivity estimate, NOT the oracle’s actual bill and NOT a confidence interval. Published recipe532k–646k examples, assumed557–2048 tokens, measured local A40 rate, assumed epoch counts. Published40-epoch code default is not proof of the oracle’s schedule; upstream TTT7 differs from measured TTT3. [Detailed assumptions and sources](P6-dedicated-cost-estimate-20261008.md).

| Hypothetical epochs | Estimated data + train A40 GPUh | Scope |
| --- | --- | --- |
| 1 | 397–825 | 532k–646k examples; 557–2048 tokens; actual oracle recipe unknown |
| 10 | 1348–5073 | 532k–646k examples; 557–2048 tokens; actual oracle recipe unknown |
| 40 | 4520–19232 | 532k–646k examples; 557–2048 tokens; actual oracle recipe unknown |

## Direct ablations and nulls

All contrasts retained. Source comparison changes token count/steps at matched examples/epochs. Second epoch is a resumed extension with schedule transition, not an uninterrupted two-epoch run. Decoder-LoRA is an EDA/RFC-style proxy, not EDA. RMS-only calibration uses frozen evaluation; full affine HF diagnostic is excluded from acceptance.

| Workload | Arm | Reference | n | Delta p1 [95% CI] | Delta tau [95% CI] | Scope |
| --- | --- | --- | --- | --- | --- | --- |
| speed128 | E5-ttt4-fc | generic4k-fc | 128 | -0.003 [-0.011, 0.006] | -0.004 [-0.026, 0.017] | TTT4 vs TTT3, same generic4k and epoch |
| speed128 | E5-ttt4-full | generic4k-full | 128 | -0.003 [-0.010, 0.004] | -0.007 [-0.028, 0.013] | TTT4 vs TTT3, same generic4k and epoch |
| speed128 | generic4k-fc | self4k-fc | 128 | 0.001 [-0.004, 0.007] | 0.004 [-0.012, 0.020] | Generic vs self4k, one epoch; source/token count/steps differ |
| speed128 | generic4k-full | self4k-full | 128 | 0.002 [-0.006, 0.009] | 0.009 [-0.012, 0.031] | Generic vs self4k, one epoch; source/token count/steps differ |
| speed128 | E5-second-epoch | generic16k-full | 128 | 0.005 [-0.002, 0.012] | 0.021 [0.001, 0.043] | Second epoch vs seed0 first epoch; incremental continuation |
| speed128 | E4-scratch16k | generic16k-full | 128 | -0.293 [-0.309, -0.276] | -0.940 [-0.996, -0.883] | Scratch vs warm start, matched generic16k epoch |
| speed128 | self256-decoder | self256-fc | 128 | -0.109 [-0.117, -0.100] | -0.290 [-0.312, -0.268] | Decoder-LoRA proxy vs fc-only, 300 steps |
| speed128 | self256-rms | reused | 128 | -0.005 [-0.010, -0.001] | -0.008 [-0.018, 0.002] | Training-free RMS vs reused |
| math64 | E5-ttt4-fc | generic4k-fc | 64 | -0.005 [-0.010, -0.001] | -0.007 [-0.023, 0.009] | TTT4 vs TTT3, same generic4k and epoch |
| math64 | E5-ttt4-full | generic4k-full | 64 | -0.004 [-0.009, -0.001] | -0.020 [-0.039, -0.004] | TTT4 vs TTT3, same generic4k and epoch |
| math64 | generic4k-fc | self4k-fc | 64 | 0.007 [0.000, 0.013] | 0.028 [0.007, 0.049] | Generic vs self4k, one epoch; source/token count/steps differ |
| math64 | generic4k-full | self4k-full | 64 | 0.009 [0.000, 0.019] | 0.045 [0.007, 0.083] | Generic vs self4k, one epoch; source/token count/steps differ |
| math64 | E5-second-epoch | generic16k-full | 64 | 0.006 [-0.001, 0.014] | 0.044 [0.011, 0.081] | Second epoch vs seed0 first epoch; incremental continuation |
| math64 | E4-scratch16k | generic16k-full | 64 | -0.321 [-0.335, -0.306] | -1.216 [-1.259, -1.175] | Scratch vs warm start, matched generic16k epoch |
| math64 | self256-decoder | self256-fc | 64 | -0.099 [-0.109, -0.087] | -0.308 [-0.345, -0.270] | Decoder-LoRA proxy vs fc-only, 300 steps |
| math64 | self256-rms | reused | 64 | 0.002 [-0.005, 0.010] | -0.005 [-0.027, 0.015] | Training-free RMS vs reused |

[All ablation arms and checkpoints](../artifacts/D50_final_20261009_1451/all-checkpoints.md).

## Scaling and outstanding work

![Pilot scaling](../artifacts/D50_final_20261009_1451/scaling.png)

Self256 uses300 steps; self1k/4k and generic4k/16k use one epoch, different token totals. The16k point has3seeds. The64k extension preserves the existing16k and adds35988 Alpaca +12012 Dolly queries. This is an Alpaca+Dolly source-mixture change, not pure same-source scaling. All evaluation prompts are forbidden; five decoded samples/masks from each new source plus all-row mask/dedup checks gate training. Labels remain training-set-free/self-elicited where applicable; no data-free claim.

64k fc/full one-epoch training follows complete response generation/audit, with25/50/75/100% exports, SPEED128+MATH64 each and MATH500 final. Compact checkpoints/shared shards,350GB guard. Corrected official4k results will gate conditional official16k. Nemotron30 timing cells cover none/reused/fc16k/full16k/independent1B K4.
