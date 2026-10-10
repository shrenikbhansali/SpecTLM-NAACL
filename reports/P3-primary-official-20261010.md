# Primary official-drafter results — pilot, 2026-10-10

D-51 selects the official yuhuili family drafter from matched 16k repair gains, confirmed on three R1 seeds. Production RedHat remains the robustness comparison. This report collects completed D-52 acceptance and measured timing; it supersedes the provisional production choice, not the historical measurements.

Acceptance: frozen6da2e42/vLLM0.31.0, A40, greedy512, b8,K4, identical derivative-rendered prompt IDs. Raw counters rechecked; paired10000 query draws and paired training-seed resampling for R1 SPEED/MATH64. Three seeds remain a small replication sample; CIs are not adjusted for selecting the drafter. MATH500 is seed0 only, overlaps MATH64, and is not an independent benchmark replication. All repair deltas and oracle denominators use the same drafter's own reuse. Nemotron has no oracle.

## Acceptance

| Target | Panel | Arm | n / seeds | p1 [95% CI] | tau [95% CI] | Own-reuse Delta tau [95% CI] | Oracle gap [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | speed128 | fc | 128 / 3 | 0.626 [0.600, 0.650] | 2.414 [2.339, 2.487] | 0.650 [0.607, 0.692] | 0.599 [0.576, 0.624] |
| R1 | math64 | fc | 64 / 3 | 0.733 [0.723, 0.744] | 2.817 [2.764, 2.871] | 0.894 [0.854, 0.934] | 0.451 [0.431, 0.471] |
| R1 | speed128 | full | 128 / 3 | 0.650 [0.623, 0.674] | 2.542 [2.462, 2.618] | 0.778 [0.731, 0.823] | 0.717 [0.692, 0.743] |
| R1 | math64 | full | 64 / 3 | 0.760 [0.748, 0.771] | 2.998 [2.941, 3.057] | 1.074 [1.027, 1.123] | 0.542 [0.519, 0.566] |
| R1 | math500 | reused | 500 / 1 | 0.495 [0.490, 0.499] | 1.928 [1.914, 1.942] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| R1 | math500 | fc | 500 / 1 | 0.723 [0.718, 0.727] | 2.773 [2.753, 2.794] | 0.845 [0.830, 0.861] | 0.442 [0.435, 0.449] |
| R1 | math500 | full | 500 / 1 | 0.756 [0.752, 0.760] | 2.969 [2.947, 2.991] | 1.041 [1.023, 1.059] | 0.544 [0.535, 0.552] |
| Nemotron | speed128 | fc | 128 / 1 | 0.614 [0.585, 0.640] | 2.418 [2.332, 2.502] | 0.655 [0.604, 0.707] | -- |
| Nemotron | math64 | fc | 64 / 1 | 0.711 [0.698, 0.723] | 2.715 [2.661, 2.767] | 1.012 [0.967, 1.055] | -- |
| Nemotron | speed128 | full | 128 / 1 | 0.629 [0.597, 0.658] | 2.487 [2.394, 2.577] | 0.724 [0.662, 0.787] | -- |
| Nemotron | math64 | full | 64 / 1 | 0.749 [0.736, 0.762] | 2.910 [2.854, 2.966] | 1.207 [1.157, 1.258] | -- |

Official vs production repair-delta contrasts and full robustness rows: [D51](../artifacts/D51_reports_20261009_1627/snapshot-20261009_192136/report.md). MATH500 independent1B has tau2.966 versus officialfull2.969; no superiority claim from these nearly equal means. Full [MATH500 controls and raw CIs](../artifacts/D52_analysis_20261010_0020/math500/table.md).

## Real speed

Fresh D52 controls in the same wave; three processes each, three warm repeats averaged within process. CIs jointly resample paired processes and prompt batches. Timing uses seed0 repair exports, not three independently trained checkpoints. Startup separate; output lengths and token throughput retained. A40 placement was available-host, not randomized exclusive-host scheduling. These timings do not produce acceptance numbers.

| Target | Batch | Arm | n / processes | Warm panel speedup | Warm token speedup | First panel + startup |
| --- | --- | --- | --- | --- | --- | --- |
| r1 | 8 | reused | 128 / 3 | 1.075 [0.989, 1.168] | 1.072 [0.988, 1.165] | 0.955 [0.898, 1.013] |
| r1 | 8 | fc | 128 / 3 | 1.268 [1.104, 1.473] | 1.266 [1.104, 1.470] | 1.073 [0.975, 1.187] |
| r1 | 8 | full | 128 / 3 | 1.287 [1.117, 1.505] | 1.280 [1.110, 1.497] | 1.089 [0.988, 1.208] |
| r1 | 8 | independent | 128 / 3 | 1.111 [1.090, 1.136] | 1.111 [1.089, 1.134] | 0.988 [0.951, 1.028] |
| r1 | 8 | oracle | 128 / 3 | 1.406 [1.203, 1.665] | 1.402 [1.198, 1.665] | 1.106 [1.002, 1.225] |
| r1 | 1 | reused | 32 / 3 | 1.312 [1.230, 1.393] | 1.319 [1.246, 1.393] | 1.147 [1.096, 1.198] |
| r1 | 1 | fc | 32 / 3 | 1.738 [1.577, 1.894] | 1.747 [1.586, 1.899] | 1.399 [1.306, 1.486] |
| r1 | 1 | full | 32 / 3 | 1.828 [1.652, 1.992] | 1.840 [1.667, 1.997] | 1.460 [1.360, 1.550] |
| r1 | 1 | independent | 32 / 3 | 1.264 [1.201, 1.331] | 1.263 [1.214, 1.321] | 1.139 [1.098, 1.185] |
| r1 | 1 | oracle | 32 / 3 | 2.054 [1.855, 2.249] | 2.068 [1.878, 2.248] | 1.579 [1.469, 1.686] |
| nemo | 8 | reused | 128 / 3 | 1.129 [1.055, 1.204] | 1.130 [1.052, 1.208] | 0.966 [0.920, 1.009] |
| nemo | 8 | fc | 128 / 3 | 1.393 [1.218, 1.600] | 1.384 [1.212, 1.589] | 1.115 [1.017, 1.220] |
| nemo | 8 | full | 128 / 3 | 1.424 [1.228, 1.670] | 1.425 [1.233, 1.663] | 1.163 [1.049, 1.288] |
| nemo | 8 | independent | 128 / 3 | 1.238 [1.204, 1.273] | 1.227 [1.188, 1.270] | 1.086 [1.049, 1.127] |
| nemo | 1 | reused | 32 / 3 | 1.291 [1.204, 1.376] | 1.306 [1.235, 1.375] | 1.172 [1.066, 1.309] |
| nemo | 1 | fc | 32 / 3 | 1.694 [1.483, 1.887] | 1.737 [1.588, 1.883] | 1.418 [1.265, 1.586] |
| nemo | 1 | full | 32 / 3 | 1.803 [1.629, 1.977] | 1.822 [1.654, 1.986] | 1.481 [1.347, 1.645] |
| nemo | 1 | independent | 32 / 3 | 1.370 [1.285, 1.466] | 1.384 [1.310, 1.465] | 1.225 [1.124, 1.357] |

## Measured repair cost

Seed0, data generation plus training; shared data charged once per alternative. Excludes search, engineering and evaluation. These are measured costs, not the dedicated oracle's unknown training bill.

| Target | Arm | Seed | Data GPUh | Train GPUh | Total GPUh |
| --- | --- | --- | --- | --- | --- |
| R1 | fc | 0 | 8.916 | 2.206 | 11.122 |
| R1 | full | 0 | 8.916 | 2.211 | 11.127 |
| Nemotron | fc | 0 | 8.588 | 1.240 | 9.828 |
| Nemotron | full | 0 | 8.588 | 1.398 | 9.986 |

## Remaining

Production64k fc/full continues; intermediate exports are labelled by step and not treated as the final scaling point. The additional48k prompts change the source mixture to Alpaca+Dolly. The owner's D52 list includes no official64k; no such run was launched. Production ablations/nulls, DFlash, mechanism and triage findings keep their original model/source labels in the [D50 report](P3-D50-consolidated-20261009.md). Prospective triage validation is not completed and is outside the frozen remaining experiment list.

Sources: artifacts/D52_analysis_20261010_0020 contains independent timing reducers, input hashes, raw checked MATH500 and generated tables. All69D52cells complete (66timing+3acceptance). FIX24-invalid historical repairs excluded.
