# Rebuttal results

Updated Nov26: E2 complete; E4 both widths now have2seeds; all trained1B timing cells complete. Total E5timing119/120processes; one off-the-shelf repeat being retried. E3a generation retries running; scratch ~3.6epochs, next scheduled export5. Independent raw reduction exactly matches the automatic report. See [Nov26 landed summary](LANDED-20261126.md). Timing-output divergence remains an open diagnostic.

## E10 — Software versions
Status: final (version inventory; all10 exact acceptance reproductions passed)
Answers: u4ad engine-version question

Paper and current inference environment both use vLLM 0.31.0. The frozen acceptance harness is 6da2e4265c0398ec0de5affaf23b0bd1df0be445. Current inference: Python 3.11.5, PyTorch 2.13.0, CUDA 13.0, transformers 5.17.0, NVIDIA A40, driver 620.70.06. Trainer: transformers 5.16.1, Speculators 0.9.0a0, same Python/PyTorch/CUDA. SGLang has not been used. Full environment freezes and source timing-config evidence are saved.

Result in one sentence: the current inference engine version matches the submitted timing runs, and all10 matching acceptance references reproduce within0.03tau; fresh wall-clock references remain required before new timing comparisons.
GPU-hours: 0.0 (budget 0).
Deviations from spec: none.

## E1 — Crossover raw cells
Status: final (CPU reanalysis of existing fixed-text records)
Answers: RLU2 crossover interpretation; JAeB interaction request

First-draft teacher-forced agreement (%), n=64 sequences per row; paired 95% CIs. P/C denote parent/child. These are HF diagnostics, not online acceptance.

| Target | Text source | a: P/P | b: P/C | c: C/P | d: C/C |
|---|---|---|---|---|---|
| R1-Llama | parent | 59.5 [54.8, 64.0] | 53.7 [48.7, 58.4] | 52.6 [47.8, 57.3] | 52.0 [47.0, 56.9] |
| R1-Llama | child | 51.0 [48.5, 53.3] | 44.8 [42.4, 47.2] | 45.9 [43.5, 48.2] | 46.0 [43.5, 48.4] |
| R1-Llama | public-reference | 51.7 [49.2, 54.3] | 48.9 [46.2, 51.5] | 44.1 [41.4, 46.7] | 46.5 [44.1, 48.9] |
| Nemotron | parent | 67.5 [63.7, 71.2] | 62.6 [58.7, 66.3] | 55.8 [51.9, 59.6] | 55.8 [51.9, 59.7] |
| Nemotron | child | 59.6 [56.5, 62.4] | 52.0 [49.1, 54.8] | 48.8 [45.9, 51.5] | 48.9 [46.0, 51.6] |
| Nemotron | public-reference | 59.6 [57.2, 61.8] | 57.7 [55.3, 59.9] | 47.7 [45.1, 50.3] | 49.1 [46.5, 51.7] |
| R1-Qwen3 | parent | 64.5 [61.7, 67.3] | 60.4 [57.4, 63.5] | 59.7 [56.8, 62.6] | 59.4 [56.5, 62.5] |
| R1-Qwen3 | child | 58.1 [55.0, 60.9] | 51.3 [48.4, 54.2] | 52.9 [50.0, 55.5] | 52.4 [49.4, 55.2] |
| R1-Qwen3 | public-reference | 61.4 [59.2, 63.5] | 59.4 [57.2, 61.4] | 58.0 [55.9, 60.1] | 58.4 [56.4, 60.5] |
| GRPO-50 | parent | 65.5 [62.6, 68.2] | 65.3 [62.4, 68.1] | 65.4 [62.5, 68.1] | 65.3 [62.4, 68.0] |
| GRPO-50 | child | 65.9 [63.0, 68.7] | 65.9 [63.0, 68.7] | 65.9 [63.0, 68.7] | 65.9 [63.0, 68.7] |
| GRPO-50 | public-reference | 67.5 [65.5, 69.3] | 67.6 [65.7, 69.5] | 67.6 [65.6, 69.4] | 67.9 [65.9, 69.7] |

Child-generated text: deployment contrasts in percentage points.

| Target | c−a | d−b | d−a | Interaction |
|---|---|---|---|---|
| R1-Llama | -5.1 [-5.7, -4.5] | 1.2 [0.6, 1.8] | -5.0 [-5.8, -4.2] | 6.3 [5.7, 6.8] |
| Nemotron | -10.8 [-11.7, -9.8] | -3.1 [-3.9, -2.3] | -10.6 [-11.7, -9.5] | 7.6 [6.7, 8.6] |
| R1-Qwen3 | -5.2 [-5.8, -4.6] | 1.1 [0.6, 1.6] | -5.7 [-6.4, -5.0] | 6.3 [5.7, 6.9] |
| GRPO-50 | -0.1 [-0.2, 0.1] | 0.0 [-0.2, 0.1] | -0.0 [-0.2, 0.2] | 0.1 [0.0, 0.1] |

Result in one sentence: all published effects and CIs reproduce; the feature-source contrast depends on the verifier, with child taps improving child-verifier agreement on R1-Llama and R1-Qwen3 but reducing it on Nemotron.

Feature = ((c−a)+(d−b))/2; policy = ((b−a)+(d−c))/2; interaction = d−b−c+a. Feature + policy equals d−a in every paired resample; interaction is not an additional term in that identity. The feature-share ratio is computed within each resample and is unstable for the near-zero GRPO effect. The complete CSV includes every contrast and all three sources. Public-reference contexts are MATH64 solutions, whereas generated contexts use SPEED; comparisons across text sources also change questions.

Verification: independent NumPy reduction, 10,000 paired sequence resamples, seed 0, all 12 groups × 64 unique sequences; original main effects and interval endpoints match within 1e-14. Four unit tests passed, including orientation, pairing, additivity and undefined ratios.
GPU-hours: 0.0 (budget 2).
Deviations from spec: none.

## Exact reference acceptance reproduction

All cells use frozen6da2e42, vLLM0.31.0, A40, greedyK4, batch8,512tokens and exact original rendered IDs/model-file hashes. MATH here is full500 because these are the submitted-paper anchors; new E2 MATH uses first128. Repaired references are seed0. CIs below use10,000 paired prompt resamples. Every check passes both the paper-anchor and matched historical-run0.03tau tolerances.

| Target | Arm | Panel | n | Reproduced tau [95%CI] |
|---|---|---|---|---|
| R1 | reuse | speed128 | 128 | 1.78 [1.74, 1.83] |
| R1 | full | speed128 | 128 | 2.52 [2.44, 2.60] |
| R1 | dedicated | speed128 | 128 | 2.86 [2.76, 2.95] |
| R1 | reuse | math500 | 500 | 1.93 [1.92, 1.94] |
| R1 | full | math500 | 500 | 2.97 [2.95, 2.99] |
| R1 | dedicated | math500 | 500 | 3.84 [3.81, 3.86] |
| Nemotron | reuse | speed128 | 128 | 1.75 [1.70, 1.81] |
| Nemotron | full | speed128 | 128 | 2.50 [2.40, 2.58] |
| Nemotron | reuse | math500 | 500 | 1.69 [1.68, 1.70] |
| Nemotron | full | math500 | 500 | 2.85 [2.83, 2.88] |

Source: rebuttal/advance_r1_20261124_1523/gate/results.json; raw hashes and paired historical differences recorded per cell. This is acceptance reproduction, not a new wall-clock measurement.

## E2 — LoRA decomposition
Status: complete three-seed matrix; pilot.

All four target/panel groups below pair seeds 0, 1 and 2, with 128 queries per seed. Matched decoder/head-only training and whole-drafter LoRA both modestly exceed dense-interface repair. This supports interface-only as an effective option, but does not establish that it is the best parameter-matched adaptation location.

| Target | Panel | Variant | Tau | Paired delta versus dense interface |
|---|---|---|---:|---:|
| R1-Distill | MATH first 128 | decoder-head | 2.856 [2.819, 2.891] | 0.064 [0.045, 0.084] |
| R1-Distill | MATH first 128 | interface | 2.792 [2.757, 2.825] | 0.000 [0.000, 0.000] |
| R1-Distill | MATH first 128 | lora-all | 2.862 [2.825, 2.896] | 0.070 [0.051, 0.088] |
| R1-Distill | SPEED-128 | decoder-head | 2.444 [2.367, 2.518] | 0.024 [0.002, 0.044] |
| R1-Distill | SPEED-128 | interface | 2.420 [2.349, 2.488] | 0.000 [0.000, 0.000] |
| R1-Distill | SPEED-128 | lora-all | 2.465 [2.391, 2.537] | 0.045 [0.027, 0.065] |
| Nemotron | MATH first 128 | decoder-head | 2.731 [2.691, 2.772] | 0.045 [0.028, 0.063] |
| Nemotron | MATH first 128 | interface | 2.686 [2.644, 2.728] | 0.000 [0.000, 0.000] |
| Nemotron | MATH first 128 | lora-all | 2.743 [2.700, 2.785] | 0.057 [0.040, 0.074] |
| Nemotron | SPEED-128 | decoder-head | 2.437 [2.351, 2.522] | 0.046 [0.024, 0.067] |
| Nemotron | SPEED-128 | interface | 2.391 [2.309, 2.471] | 0.000 [0.000, 0.000] |
| Nemotron | SPEED-128 | lora-all | 2.439 [2.351, 2.523] | 0.048 [0.024, 0.070] |

The full table also retains post-training restoration ablations: restoring fc or retaining only fc from jointly trained whole-LoRA reduces acceptance. These are interventions on a jointly trained checkpoint, not separately trained component-only baselines. E2 total completed cost including failed/invalid attempts is 31.182 A40 GPU-hours, below the approved 40.


Sources: E2/reduction_20261125_2010/results.json and CSV; independent raw-counter seed/query reduction.


Derived capacity-control summary (all three paired seeds, n128 per panel): dense-interface repair retains93.4%[90.7,96.0] of whole-LoRA's improvement over reuse on R1SPEED,92.5%[90.7,94.5] on R1MATH,93.0%[89.9,96.5] on NemotronSPEED,94.6%[93.1,96.1] on NemotronMATH. Definition=(tau_interface−tau_reuse)/(tau_whole_LoRA−tau_reuse), recomputed in every paired seed/query bootstrap sample. This is a descriptive secondary ratio, not noninferiority or a claim that interface beats whole-LoRA. Absolute differences remain above. Source:review_audit_20261125/derived.json and reduce.py.

## E3b — scratch curve in progress
Status: partial; continuous scratch training running. Fixed20epoch cosine schedule, intermediate checkpoints are not separately annealed runs. n128,seed0,greedyK4,frozen0.31/A40.

| Epoch | SPEED tau [95%CI] | MATH tau [95%CI] |
|---|---|---|
| 1 | 1.75 [1.70,1.79] | 1.98 [1.94,2.02] |
| 2 | 1.93 [1.87,1.98] | 2.31 [2.26,2.35] |

Current warm-full references are2.52SPEED/2.99MATH on the same panels; both scratch points remain lower. Cumulative checkpointGPUh and later checkpoints pending. Source:landed_audit_20261125/results.json.

## E4 — EDA baseline
Status: partial; automatic raw-counter reduction, pending operator completion check.
All acceptance cells use frozen6da2e42/vLLM0.31.0/A40, greedy, batch8, cap512. MATH is first128. Intervals are paired10,000 query/seed bootstrap95%CIs. Smoke runs are excluded. Reference rows use the identical rendered prefix of current-campaign gate cells; hashes verified.

R1-Distill-Llama:

| Variant / seed / K | Panel | n | tau [95% CI] | p1 % [95% CI] | Train GPUh |
|---|---|---:|---|---|---:|
| E4_t0_eda_w14336_selected8k / s0 / K4 | math128 | 128 | 2.38 [2.34, 2.41] | 60.5 [59.5, 61.5] | 1.4 |
| E4_t0_eda_w14336_selected8k / s0 / K4 | speed128 | 128 | 2.18 [2.12, 2.23] | 55.0 [52.8, 57.1] | 1.4 |
| E4_t0_eda_w14336_selected8k / s1 / K4 | math128 | 128 | 2.37 [2.33, 2.40] | 60.2 [59.2, 61.2] | 1.7 |
| E4_t0_eda_w14336_selected8k / s1 / K4 | speed128 | 128 | 2.18 [2.12, 2.24] | 55.1 [52.7, 57.2] | 1.7 |
| E4_t0_eda_w4096_selected8k / s0 / K4 | math128 | 128 | 2.34 [2.31, 2.37] | 59.5 [58.5, 60.4] | 1.6 |
| E4_t0_eda_w4096_selected8k / s0 / K4 | speed128 | 128 | 2.15 [2.09, 2.21] | 54.1 [51.7, 56.2] | 1.6 |
| E4_t0_eda_w4096_selected8k / s1 / K4 | math128 | 128 | 2.35 [2.31, 2.38] | 60.0 [59.0, 60.9] | 1.3 |
| E4_t0_eda_w4096_selected8k / s1 / K4 | speed128 | 128 | 2.14 [2.08, 2.20] | 54.2 [51.9, 56.2] | 1.3 |
| E4b_t0_full_random8k / s0 / K4 | math128 | 128 | 2.94 [2.90, 2.98] | 74.8 [74.0, 75.6] | 1.6 |
| E4b_t0_full_random8k / s0 / K4 | speed128 | 128 | 2.49 [2.41, 2.56] | 63.9 [61.1, 66.4] | 1.6 |
| E4b_t0_full_random8k / s1 / K4 | math128 | 128 | 2.93 [2.89, 2.96] | 74.7 [74.0, 75.5] | 1.3 |
| E4b_t0_full_random8k / s1 / K4 | speed128 | 128 | 2.49 [2.41, 2.57] | 63.6 [60.8, 66.1] | 1.3 |
| E4b_t0_full_selected8k / s0 / K4 | math128 | 128 | 2.65 [2.61, 2.68] | 69.3 [68.4, 70.2] | 2.0 |
| E4b_t0_full_selected8k / s0 / K4 | speed128 | 128 | 2.45 [2.37, 2.52] | 63.0 [60.3, 65.4] | 2.0 |
| E4b_t0_full_selected8k / s1 / K4 | math128 | 128 | 2.66 [2.63, 2.70] | 69.7 [68.7, 70.6] | 1.8 |
| E4b_t0_full_selected8k / s1 / K4 | speed128 | 128 | 2.43 [2.35, 2.50] | 62.2 [59.5, 64.6] | 1.8 |
| reference_reuse / s0 / K4 | speed128 | 128 | 1.78 [1.74, 1.83] | 43.4 [41.4, 45.2] | — |
| reference_full / s0 / K4 | speed128 | 128 | 2.52 [2.44, 2.60] | 64.5 [61.7, 67.0] | — |
| reference_dedicated / s0 / K4 | speed128 | 128 | 2.86 [2.76, 2.95] | 70.7 [67.8, 73.2] | — |
| reference_reuse / s0 / K4 | math128 | 128 | 1.92 [1.89, 1.95] | 49.3 [48.4, 50.1] | — |
| reference_full / s0 / K4 | math128 | 128 | 2.99 [2.95, 3.03] | 76.0 [75.2, 76.8] | — |
| reference_dedicated / s0 / K4 | math128 | 128 | 3.82 [3.76, 3.88] | 86.8 [85.9, 87.7] | — |

Nemotron:

| Variant / seed / K | Panel | n | tau [95% CI] | p1 % [95% CI] | Train GPUh |
|---|---|---:|---|---|---:|
| reference_reuse / s0 / K4 | speed128 | 128 | 1.75 [1.70, 1.81] | 42.7 [40.5, 44.8] | — |
| reference_full / s0 / K4 | speed128 | 128 | 2.50 [2.40, 2.58] | 63.0 [60.0, 65.7] | — |
| reference_reuse / s0 / K4 | math128 | 128 | 1.69 [1.66, 1.71] | 44.4 [43.5, 45.3] | — |
| reference_full / s0 / K4 | math128 | 128 | 2.88 [2.83, 2.93] | 74.3 [73.2, 75.3] | — |

Paired differences are candidate minus reference; no sign filtering.

| Target / panel | Reference | Candidate | n / seeds | Delta tau [95% CI] | Delta p1 points [95% CI] |
|---|---|---|---|---|---|
| 0 / math128 | E4_t0_eda_w14336_selected8k | E4_t0_eda_w4096_selected8k | 128 / 2 | -0.03 [-0.05, -0.01] | -0.6 [-1.4, 0.1] |
| 0 / math128 | E4_t0_eda_w14336_selected8k | E4b_t0_full_random8k | 128 / 2 | 0.56 [0.53, 0.59] | 14.4 [13.6, 15.3] |
| 0 / math128 | E4_t0_eda_w14336_selected8k | E4b_t0_full_selected8k | 128 / 2 | 0.28 [0.26, 0.31] | 9.1 [8.3, 10.0] |
| 0 / math128 | E4_t0_eda_w14336_selected8k | reference_dedicated | 128 / 2 | 1.45 [1.39, 1.51] | 26.4 [25.3, 27.6] |
| 0 / math128 | E4_t0_eda_w14336_selected8k | reference_full | 128 / 2 | 0.62 [0.58, 0.65] | 15.6 [14.6, 16.7] |
| 0 / math128 | E4_t0_eda_w14336_selected8k | reference_reuse | 128 / 2 | -0.45 [-0.47, -0.43] | -11.1 [-11.8, -10.3] |
| 0 / math128 | E4_t0_eda_w4096_selected8k | E4b_t0_full_random8k | 128 / 2 | 0.59 [0.55, 0.62] | 15.1 [14.1, 16.0] |
| 0 / math128 | E4_t0_eda_w4096_selected8k | E4b_t0_full_selected8k | 128 / 2 | 0.31 [0.29, 0.33] | 9.8 [9.1, 10.5] |
| 0 / math128 | E4_t0_eda_w4096_selected8k | reference_dedicated | 128 / 2 | 1.48 [1.42, 1.53] | 27.1 [25.9, 28.3] |
| 0 / math128 | E4_t0_eda_w4096_selected8k | reference_full | 128 / 2 | 0.65 [0.61, 0.68] | 16.3 [15.2, 17.3] |
| 0 / math128 | E4_t0_eda_w4096_selected8k | reference_reuse | 128 / 2 | -0.42 [-0.44, -0.40] | -10.5 [-11.3, -9.6] |
| 0 / math128 | E4b_t0_full_random8k | E4b_t0_full_selected8k | 128 / 2 | -0.28 [-0.31, -0.24] | -5.3 [-6.2, -4.4] |
| 0 / math128 | E4b_t0_full_random8k | reference_dedicated | 128 / 2 | 0.89 [0.85, 0.93] | 12.0 [11.3, 12.8] |
| 0 / math128 | E4b_t0_full_random8k | reference_full | 128 / 2 | 0.06 [0.03, 0.08] | 1.2 [0.6, 1.9] |
| 0 / math128 | E4b_t0_full_random8k | reference_reuse | 128 / 2 | -1.01 [-1.04, -0.98] | -25.5 [-26.2, -24.8] |
| 0 / math128 | E4b_t0_full_selected8k | reference_dedicated | 128 / 2 | 1.17 [1.11, 1.22] | 17.3 [16.2, 18.4] |
| 0 / math128 | E4b_t0_full_selected8k | reference_full | 128 / 2 | 0.33 [0.30, 0.37] | 6.5 [5.5, 7.5] |
| 0 / math128 | E4b_t0_full_selected8k | reference_reuse | 128 / 2 | -0.73 [-0.76, -0.71] | -20.2 [-21.2, -19.3] |
| 0 / speed128 | E4_t0_eda_w14336_selected8k | E4_t0_eda_w4096_selected8k | 128 / 2 | -0.03 [-0.05, -0.01] | -0.9 [-1.5, -0.3] |
| 0 / speed128 | E4_t0_eda_w14336_selected8k | E4b_t0_full_random8k | 128 / 2 | 0.31 [0.27, 0.35] | 8.7 [7.7, 9.7] |
| 0 / speed128 | E4_t0_eda_w14336_selected8k | E4b_t0_full_selected8k | 128 / 2 | 0.26 [0.23, 0.29] | 7.6 [6.5, 8.6] |
| 0 / speed128 | E4_t0_eda_w14336_selected8k | reference_dedicated | 128 / 2 | 0.68 [0.62, 0.73] | 15.6 [14.4, 16.7] |
| 0 / speed128 | E4_t0_eda_w14336_selected8k | reference_full | 128 / 2 | 0.35 [0.31, 0.38] | 9.4 [8.4, 10.4] |
| 0 / speed128 | E4_t0_eda_w14336_selected8k | reference_reuse | 128 / 2 | -0.39 [-0.42, -0.37] | -11.7 [-12.7, -10.6] |
| 0 / speed128 | E4_t0_eda_w4096_selected8k | E4b_t0_full_random8k | 128 / 2 | 0.34 [0.31, 0.38] | 9.6 [8.6, 10.6] |
| 0 / speed128 | E4_t0_eda_w4096_selected8k | E4b_t0_full_selected8k | 128 / 2 | 0.29 [0.27, 0.32] | 8.5 [7.5, 9.5] |
| 0 / speed128 | E4_t0_eda_w4096_selected8k | reference_dedicated | 128 / 2 | 0.71 [0.66, 0.76] | 16.5 [15.4, 17.6] |
| 0 / speed128 | E4_t0_eda_w4096_selected8k | reference_full | 128 / 2 | 0.38 [0.34, 0.42] | 10.4 [9.3, 11.4] |
| 0 / speed128 | E4_t0_eda_w4096_selected8k | reference_reuse | 128 / 2 | -0.36 [-0.39, -0.33] | -10.7 [-11.7, -9.8] |
| 0 / speed128 | E4b_t0_full_random8k | E4b_t0_full_selected8k | 128 / 2 | -0.05 [-0.08, -0.02] | -1.1 [-2.0, -0.3] |
| 0 / speed128 | E4b_t0_full_random8k | reference_dedicated | 128 / 2 | 0.37 [0.34, 0.40] | 6.9 [6.1, 7.8] |
| 0 / speed128 | E4b_t0_full_random8k | reference_full | 128 / 2 | 0.04 [0.02, 0.05] | 0.7 [0.2, 1.3] |
| 0 / speed128 | E4b_t0_full_random8k | reference_reuse | 128 / 2 | -0.70 [-0.75, -0.66] | -20.3 [-21.7, -19.0] |
| 0 / speed128 | E4b_t0_full_selected8k | reference_dedicated | 128 / 2 | 0.42 [0.37, 0.47] | 8.0 [6.9, 9.2] |
| 0 / speed128 | E4b_t0_full_selected8k | reference_full | 128 / 2 | 0.09 [0.06, 0.12] | 1.8 [0.9, 2.8] |
| 0 / speed128 | E4b_t0_full_selected8k | reference_reuse | 128 / 2 | -0.65 [-0.70, -0.61] | -19.2 [-20.6, -17.8] |

Port: released additive singleton shared/private experts; shared FFN, fc, attention, norms and head frozen. Private widths4096/14336; PCA128 and90th-percentile Mahalanobis are predeclared port choices. Selected8k and random8k full-repair controls remain separate. Frozen tensor checks and FIX24 embedding proof gate production EDA evaluation.

| Standalone drafter | n | Median ms |
|---|---:|---:|
| /home/heck2/sbhansali8/ReFit/artifacts/P3_D50_20261009_0200/E1-official-native-v2-t0 | 1000 | 3.317 |
| /home/heck2/sbhansali8/ReFit/rebuttal/runs/E4_t0_train_smoke_w4096_s0/cell/export-2 | 1000 | 3.364 |
| /home/heck2/sbhansali8/ReFit/rebuttal/runs/E4_t0_train_smoke_w14336_s0/cell/export-2 | 1000 | 3.378 |
Standalone PyTorch first-draft forward:50warmup,1000measured CUDA-event steps, batch1, one-token context, no verifier. Not end-to-end speedup.

R1 dedicated-gap recovery at matched K4; the ratio is recomputed in each paired resample.

| Variant | Panel | n / seeds | Recovery % [95% CI] |
|---|---|---|---|
| E4_t0_eda_w14336_selected8k | math128 | 128 / 2 | 23.8 [22.5, 25.1] |
| E4_t0_eda_w4096_selected8k | math128 | 128 / 2 | 22.2 [21.0, 23.5] |
| E4b_t0_full_random8k | math128 | 128 / 2 | 53.2 [52.0, 54.4] |
| E4b_t0_full_selected8k | math128 | 128 / 2 | 38.6 [37.0, 40.2] |
| E4_t0_eda_w14336_selected8k | speed128 | 128 / 2 | 36.8 [34.5, 39.2] |
| E4_t0_eda_w4096_selected8k | speed128 | 128 / 2 | 33.7 [31.4, 35.8] |
| E4b_t0_full_random8k | speed128 | 128 / 2 | 65.7 [63.5, 67.9] |
| E4b_t0_full_selected8k | speed128 | 128 / 2 | 61.0 [57.9, 64.2] |

Result status: 16 completed non-reference cells in this snapshot; no unfinished outcome inferred.
GPU-hours: 16.5 completed, including failures; active runtime additional.
Sources: /home/heck2/sbhansali8/ReFit/rebuttal/E45_analysis_watch_20261124_1645/20261126_170336_932613/results.json
Failed runs retained: [{"run": "E5_t0_timing_distilled_math128_b1_r0", "status": "failed"}, {"run": "E5_t0_timing_distilled_math128_b1_r1", "status": "failed"}, {"run": "E5_t0_timing_distilled_math128_b1_r2", "status": "failed"}, {"run": "E5_t0_timing_distilled_speed128_b1_r0", "status": "failed"}, {"run": "E5_t0_timing_distilled_speed128_b1_r1", "status": "failed"}, {"run": "E5_t0_timing_distilled_speed128_b1_r2", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_math128_b1_r0", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_math128_b1_r1", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_math128_b1_r2", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_speed128_b1_r0", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_speed128_b1_r1", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_speed128_b1_r2", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_speed128_b1_r2_retry1", "status": "failed"}]

## E3 — Dedicated training cost
Status: partial (E3b continuous scratch run training; no completed epoch/evaluation yet; E3a throughput data preparation remains)
E3b uses existing audited64k Alpaca+Dolly data, one20epoch cosine horizon, exports at epochs1/2/5/10/15/20 and forced stop Nov28noon. First attempt failed before an optimizer update on GCC8; retry uses installed GCC13.3.1 and is progressing.
GPU-hours: failed attempt0.0245; active runtime recorded by the wrapper; no completed training-quality result claimed.

## E5 — Distilled independent drafter
Status: partial; automatic raw-counter reduction, pending operator completion check.
All acceptance cells use frozen6da2e42/vLLM0.31.0/A40, greedy, batch8, cap512. MATH is first128. Intervals are paired10,000 query/seed bootstrap95%CIs. Smoke runs are excluded. Reference rows use the identical rendered prefix of current-campaign gate cells; hashes verified.

R1-Distill-Llama:

| Variant / seed / K | Panel | n | tau [95% CI] | p1 % [95% CI] | Train GPUh |
|---|---|---:|---|---|---:|
| distilled_k2 / s0 / K2 | math128 | 128 | 2.47 [2.44, 2.49] | 80.3 [79.4, 81.2] | 3.5 |
| distilled_k2 / s0 / K2 | speed128 | 128 | 2.25 [2.22, 2.28] | 72.0 [70.8, 73.1] | 3.5 |
| distilled_k3 / s0 / K3 | math128 | 128 | 2.98 [2.94, 3.02] | 79.6 [78.7, 80.5] | 3.5 |
| distilled_k3 / s0 / K3 | speed128 | 128 | 2.63 [2.58, 2.67] | 71.6 [70.5, 72.7] | 3.5 |
| distilled_k4 / s0 / K4 | math128 | 128 | 3.41 [3.36, 3.47] | 79.0 [78.1, 80.0] | 3.5 |
| distilled_k4 / s0 / K4 | speed128 | 128 | 2.89 [2.83, 2.95] | 71.2 [70.0, 72.3] | 3.5 |
| distilled_k5 / s0 / K5 | math128 | 128 | 3.80 [3.73, 3.87] | 79.1 [78.1, 80.1] | 3.5 |
| distilled_k5 / s0 / K5 | speed128 | 128 | 3.10 [3.02, 3.19] | 70.6 [69.4, 71.8] | 3.5 |
| offtheshelf_k2 / s0 / K2 | math128 | 128 | 2.28 [2.26, 2.31] | 73.2 [72.3, 74.1] | — |
| offtheshelf_k2 / s0 / K2 | speed128 | 128 | 2.02 [2.00, 2.05] | 62.3 [61.0, 63.6] | — |
| offtheshelf_k3 / s0 / K3 | math128 | 128 | 2.68 [2.64, 2.72] | 72.1 [71.1, 73.0] | — |
| offtheshelf_k3 / s0 / K3 | speed128 | 128 | 2.29 [2.25, 2.34] | 62.2 [61.1, 63.4] | — |
| offtheshelf_k4 / s0 / K4 | math128 | 128 | 2.96 [2.91, 3.01] | 70.9 [70.0, 71.9] | — |
| offtheshelf_k4 / s0 / K4 | speed128 | 128 | 2.45 [2.40, 2.51] | 61.4 [60.3, 62.6] | — |
| offtheshelf_k5 / s0 / K5 | math128 | 128 | 3.19 [3.13, 3.26] | 70.1 [69.1, 71.1] | — |
| offtheshelf_k5 / s0 / K5 | speed128 | 128 | 2.55 [2.48, 2.62] | 60.6 [59.5, 61.7] | — |
| E5_t0_student_lr1e-05_ep1_s0_k4 / s0 / K4 | validation256 | 256 | 2.98 [2.93, 3.04] | 72.7 [71.9, 73.6] | 1.2 |
| E5_t0_student_lr1e-05_ep3_s0_k4 / s0 / K4 | validation256 | 256 | 3.02 [2.97, 3.08] | 73.2 [72.3, 74.1] | 3.5 |
| E5_t0_student_lr2e-05_ep1_s0_k4 / s0 / K4 | validation256 | 256 | 2.96 [2.91, 3.01] | 72.1 [71.3, 73.0] | 1.2 |
| E5_t0_student_lr2e-05_ep3_s0_k4 / s0 / K4 | validation256 | 256 | 3.00 [2.95, 3.05] | 73.1 [72.2, 74.0] | 3.5 |
| reference_reuse / s0 / K4 | speed128 | 128 | 1.78 [1.74, 1.83] | 43.4 [41.4, 45.2] | — |
| reference_full / s0 / K4 | speed128 | 128 | 2.52 [2.44, 2.60] | 64.5 [61.7, 67.0] | — |
| reference_dedicated / s0 / K4 | speed128 | 128 | 2.86 [2.76, 2.95] | 70.7 [67.8, 73.2] | — |
| reference_reuse / s0 / K4 | math128 | 128 | 1.92 [1.89, 1.95] | 49.3 [48.4, 50.1] | — |
| reference_full / s0 / K4 | math128 | 128 | 2.99 [2.95, 3.03] | 76.0 [75.2, 76.8] | — |
| reference_dedicated / s0 / K4 | math128 | 128 | 3.82 [3.76, 3.88] | 86.8 [85.9, 87.7] | — |

Nemotron:

| Variant / seed / K | Panel | n | tau [95% CI] | p1 % [95% CI] | Train GPUh |
|---|---|---:|---|---|---:|
| distilled_k2 / s0 / K2 | math128 | 128 | 2.41 [2.38, 2.43] | 78.2 [77.2, 79.1] | 2.8 |
| distilled_k2 / s0 / K2 | speed128 | 128 | 2.26 [2.22, 2.29] | 71.9 [70.6, 73.2] | 2.8 |
| distilled_k3 / s0 / K3 | math128 | 128 | 2.88 [2.84, 2.91] | 77.0 [76.1, 77.9] | 2.8 |
| distilled_k3 / s0 / K3 | speed128 | 128 | 2.62 [2.56, 2.67] | 71.1 [69.7, 72.5] | 2.8 |
| distilled_k4 / s0 / K4 | math128 | 128 | 3.27 [3.22, 3.33] | 76.5 [75.5, 77.5] | 2.8 |
| distilled_k4 / s0 / K4 | speed128 | 128 | 2.94 [2.87, 3.01] | 71.2 [70.0, 72.4] | 2.8 |
| distilled_k5 / s0 / K5 | math128 | 128 | 3.57 [3.50, 3.64] | 75.8 [74.8, 76.8] | 2.8 |
| distilled_k5 / s0 / K5 | speed128 | 128 | 3.14 [3.05, 3.23] | 70.3 [69.2, 71.5] | 2.8 |
| offtheshelf_k2 / s0 / K2 | math128 | 128 | 2.20 [2.18, 2.22] | 69.1 [68.2, 70.0] | — |
| offtheshelf_k2 / s0 / K2 | speed128 | 128 | 2.13 [2.10, 2.17] | 66.5 [65.0, 68.1] | — |
| offtheshelf_k3 / s0 / K3 | math128 | 128 | 2.55 [2.52, 2.59] | 67.9 [67.0, 68.9] | — |
| offtheshelf_k3 / s0 / K3 | speed128 | 128 | 2.45 [2.39, 2.50] | 65.5 [64.0, 67.1] | — |
| offtheshelf_k4 / s0 / K4 | math128 | 128 | 2.81 [2.77, 2.85] | 67.2 [66.3, 68.0] | — |
| offtheshelf_k4 / s0 / K4 | speed128 | 128 | 2.69 [2.62, 2.77] | 65.5 [64.1, 66.9] | — |
| offtheshelf_k5 / s0 / K5 | math128 | 128 | 3.00 [2.95, 3.06] | 66.3 [65.3, 67.3] | — |
| offtheshelf_k5 / s0 / K5 | speed128 | 128 | 2.86 [2.77, 2.95] | 64.9 [63.4, 66.3] | — |
| E5_t1_student_lr1e-05_ep1_s0_k4 / s0 / K4 | validation256 | 256 | 3.04 [2.98, 3.11] | 74.2 [72.8, 75.7] | 0.9 |
| E5_t1_student_lr1e-05_ep3_s0_k4 / s0 / K4 | validation256 | 256 | 3.10 [3.03, 3.17] | 75.1 [73.7, 76.5] | 2.8 |
| E5_t1_student_lr2e-05_ep1_s0_k4 / s0 / K4 | validation256 | 256 | 3.03 [2.97, 3.10] | 74.0 [72.5, 75.4] | 0.9 |
| E5_t1_student_lr2e-05_ep3_s0_k4 / s0 / K4 | validation256 | 256 | 3.03 [2.97, 3.10] | 73.8 [72.3, 75.2] | 2.7 |
| reference_reuse / s0 / K4 | speed128 | 128 | 1.75 [1.70, 1.81] | 42.7 [40.5, 44.8] | — |
| reference_full / s0 / K4 | speed128 | 128 | 2.50 [2.40, 2.58] | 63.0 [60.0, 65.7] | — |
| reference_reuse / s0 / K4 | math128 | 128 | 1.69 [1.66, 1.71] | 44.4 [43.5, 45.3] | — |
| reference_full / s0 / K4 | math128 | 128 | 2.88 [2.83, 2.93] | 74.3 [73.2, 75.3] | — |

Paired differences are candidate minus reference; no sign filtering.

| Target / panel | Reference | Candidate | n / seeds | Delta tau [95% CI] | Delta p1 points [95% CI] |
|---|---|---|---|---|---|
| 0 / math128 | distilled_k2 | distilled_k3 | 128 / 1 | 0.52 [0.50, 0.54] | -0.7 [-1.3, -0.1] |
| 0 / math128 | distilled_k2 | distilled_k4 | 128 / 1 | 0.95 [0.91, 0.99] | -1.2 [-1.8, -0.7] |
| 0 / math128 | distilled_k2 | distilled_k5 | 128 / 1 | 1.33 [1.28, 1.39] | -1.1 [-1.8, -0.5] |
| 0 / math128 | distilled_k2 | offtheshelf_k2 | 128 / 1 | -0.18 [-0.20, -0.17] | -7.1 [-7.8, -6.4] |
| 0 / math128 | distilled_k2 | offtheshelf_k3 | 128 / 1 | 0.21 [0.19, 0.24] | -8.2 [-8.9, -7.6] |
| 0 / math128 | distilled_k2 | offtheshelf_k4 | 128 / 1 | 0.50 [0.46, 0.53] | -9.4 [-10.1, -8.6] |
| 0 / math128 | distilled_k2 | offtheshelf_k5 | 128 / 1 | 0.73 [0.68, 0.78] | -10.2 [-10.9, -9.4] |
| 0 / math128 | distilled_k2 | reference_dedicated | 128 / 1 | 1.36 [1.31, 1.40] | 6.5 [5.8, 7.2] |
| 0 / math128 | distilled_k2 | reference_full | 128 / 1 | 0.52 [0.49, 0.55] | -4.3 [-5.2, -3.4] |
| 0 / math128 | distilled_k2 | reference_reuse | 128 / 1 | -0.54 [-0.57, -0.52] | -31.0 [-32.0, -30.0] |
| 0 / math128 | distilled_k3 | distilled_k4 | 128 / 1 | 0.43 [0.40, 0.46] | -0.6 [-1.2, 0.1] |
| 0 / math128 | distilled_k3 | distilled_k5 | 128 / 1 | 0.82 [0.78, 0.86] | -0.5 [-1.1, 0.2] |
| 0 / math128 | distilled_k3 | offtheshelf_k2 | 128 / 1 | -0.70 [-0.73, -0.67] | -6.4 [-7.2, -5.6] |
| 0 / math128 | distilled_k3 | offtheshelf_k3 | 128 / 1 | -0.30 [-0.32, -0.28] | -7.5 [-8.2, -6.9] |
| 0 / math128 | distilled_k3 | offtheshelf_k4 | 128 / 1 | -0.02 [-0.05, 0.01] | -8.7 [-9.4, -7.9] |
| 0 / math128 | distilled_k3 | offtheshelf_k5 | 128 / 1 | 0.21 [0.17, 0.25] | -9.5 [-10.3, -8.7] |
| 0 / math128 | distilled_k3 | reference_dedicated | 128 / 1 | 0.84 [0.80, 0.87] | 7.2 [6.4, 8.0] |
| 0 / math128 | distilled_k3 | reference_full | 128 / 1 | 0.01 [-0.03, 0.04] | -3.6 [-4.5, -2.7] |
| 0 / math128 | distilled_k3 | reference_reuse | 128 / 1 | -1.06 [-1.10, -1.03] | -30.3 [-31.3, -29.4] |
| 0 / math128 | distilled_k4 | distilled_k5 | 128 / 1 | 0.38 [0.35, 0.42] | 0.1 [-0.6, 0.8] |
| 0 / math128 | distilled_k4 | offtheshelf_k2 | 128 / 1 | -1.13 [-1.17, -1.09] | -5.9 [-6.6, -5.1] |
| 0 / math128 | distilled_k4 | offtheshelf_k3 | 128 / 1 | -0.73 [-0.77, -0.70] | -7.0 [-7.7, -6.3] |
| 0 / math128 | distilled_k4 | offtheshelf_k4 | 128 / 1 | -0.45 [-0.49, -0.42] | -8.1 [-8.9, -7.3] |
| 0 / math128 | distilled_k4 | offtheshelf_k5 | 128 / 1 | -0.22 [-0.26, -0.19] | -8.9 [-9.7, -8.1] |
| 0 / math128 | distilled_k4 | reference_dedicated | 128 / 1 | 0.41 [0.37, 0.44] | 7.7 [7.0, 8.5] |
| 0 / math128 | distilled_k4 | reference_full | 128 / 1 | -0.43 [-0.47, -0.38] | -3.1 [-3.9, -2.2] |
| 0 / math128 | distilled_k4 | reference_reuse | 128 / 1 | -1.49 [-1.55, -1.44] | -29.8 [-30.8, -28.7] |
| 0 / math128 | distilled_k5 | offtheshelf_k2 | 128 / 1 | -1.52 [-1.57, -1.46] | -5.9 [-6.8, -5.1] |
| 0 / math128 | distilled_k5 | offtheshelf_k3 | 128 / 1 | -1.12 [-1.16, -1.07] | -7.1 [-7.8, -6.3] |
| 0 / math128 | distilled_k5 | offtheshelf_k4 | 128 / 1 | -0.84 [-0.88, -0.79] | -8.2 [-9.1, -7.3] |
| 0 / math128 | distilled_k5 | offtheshelf_k5 | 128 / 1 | -0.61 [-0.65, -0.56] | -9.0 [-9.9, -8.1] |
| 0 / math128 | distilled_k5 | reference_dedicated | 128 / 1 | 0.02 [-0.02, 0.07] | 7.7 [6.8, 8.5] |
| 0 / math128 | distilled_k5 | reference_full | 128 / 1 | -0.81 [-0.86, -0.76] | -3.1 [-4.0, -2.2] |
| 0 / math128 | distilled_k5 | reference_reuse | 128 / 1 | -1.88 [-1.94, -1.81] | -29.9 [-31.0, -28.8] |
| 0 / math128 | offtheshelf_k2 | offtheshelf_k3 | 128 / 1 | 0.40 [0.38, 0.42] | -1.1 [-1.7, -0.6] |
| 0 / math128 | offtheshelf_k2 | offtheshelf_k4 | 128 / 1 | 0.68 [0.65, 0.71] | -2.3 [-2.8, -1.7] |
| 0 / math128 | offtheshelf_k2 | offtheshelf_k5 | 128 / 1 | 0.91 [0.86, 0.95] | -3.1 [-3.6, -2.5] |
| 0 / math128 | offtheshelf_k2 | reference_dedicated | 128 / 1 | 1.54 [1.49, 1.58] | 13.6 [12.9, 14.3] |
| 0 / math128 | offtheshelf_k2 | reference_full | 128 / 1 | 0.71 [0.67, 0.74] | 2.8 [1.9, 3.7] |
| 0 / math128 | offtheshelf_k2 | reference_reuse | 128 / 1 | -0.36 [-0.39, -0.33] | -23.9 [-24.9, -22.9] |
| 0 / math128 | offtheshelf_k3 | offtheshelf_k4 | 128 / 1 | 0.28 [0.26, 0.31] | -1.1 [-1.7, -0.6] |
| 0 / math128 | offtheshelf_k3 | offtheshelf_k5 | 128 / 1 | 0.51 [0.48, 0.54] | -1.9 [-2.5, -1.4] |
| 0 / math128 | offtheshelf_k3 | reference_dedicated | 128 / 1 | 1.14 [1.10, 1.18] | 14.7 [14.0, 15.4] |
| 0 / math128 | offtheshelf_k3 | reference_full | 128 / 1 | 0.31 [0.27, 0.34] | 3.9 [3.0, 4.8] |
| 0 / math128 | offtheshelf_k3 | reference_reuse | 128 / 1 | -0.76 [-0.79, -0.72] | -22.8 [-23.8, -21.8] |
| 0 / math128 | offtheshelf_k4 | offtheshelf_k5 | 128 / 1 | 0.23 [0.21, 0.25] | -0.8 [-1.3, -0.3] |
| 0 / math128 | offtheshelf_k4 | reference_dedicated | 128 / 1 | 0.86 [0.82, 0.90] | 15.9 [15.1, 16.6] |
| 0 / math128 | offtheshelf_k4 | reference_full | 128 / 1 | 0.03 [-0.02, 0.07] | 5.1 [4.2, 5.9] |
| 0 / math128 | offtheshelf_k4 | reference_reuse | 128 / 1 | -1.04 [-1.09, -1.00] | -21.7 [-22.7, -20.6] |
| 0 / math128 | offtheshelf_k5 | reference_dedicated | 128 / 1 | 0.63 [0.59, 0.67] | 16.7 [15.9, 17.5] |
| 0 / math128 | offtheshelf_k5 | reference_full | 128 / 1 | -0.20 [-0.25, -0.15] | 5.9 [4.9, 6.8] |
| 0 / math128 | offtheshelf_k5 | reference_reuse | 128 / 1 | -1.27 [-1.33, -1.21] | -20.9 [-22.0, -19.7] |
| 0 / speed128 | distilled_k2 | distilled_k3 | 128 / 1 | 0.38 [0.35, 0.40] | -0.4 [-1.1, 0.4] |
| 0 / speed128 | distilled_k2 | distilled_k4 | 128 / 1 | 0.64 [0.60, 0.68] | -0.8 [-1.6, -0.0] |
| 0 / speed128 | distilled_k2 | distilled_k5 | 128 / 1 | 0.86 [0.80, 0.92] | -1.4 [-2.2, -0.6] |
| 0 / speed128 | distilled_k2 | offtheshelf_k2 | 128 / 1 | -0.22 [-0.25, -0.20] | -9.7 [-10.7, -8.7] |
| 0 / speed128 | distilled_k2 | offtheshelf_k3 | 128 / 1 | 0.04 [0.01, 0.07] | -9.8 [-10.8, -8.8] |
| 0 / speed128 | distilled_k2 | offtheshelf_k4 | 128 / 1 | 0.21 [0.17, 0.25] | -10.6 [-11.6, -9.6] |
| 0 / speed128 | distilled_k2 | offtheshelf_k5 | 128 / 1 | 0.30 [0.25, 0.36] | -11.4 [-12.4, -10.3] |
| 0 / speed128 | distilled_k2 | reference_dedicated | 128 / 1 | 0.61 [0.52, 0.69] | -1.3 [-4.1, 1.1] |
| 0 / speed128 | distilled_k2 | reference_full | 128 / 1 | 0.27 [0.20, 0.34] | -7.5 [-10.2, -5.1] |
| 0 / speed128 | distilled_k2 | reference_reuse | 128 / 1 | -0.47 [-0.51, -0.43] | -28.6 [-30.4, -26.9] |
| 0 / speed128 | distilled_k3 | distilled_k4 | 128 / 1 | 0.26 [0.23, 0.29] | -0.5 [-1.2, 0.3] |
| 0 / speed128 | distilled_k3 | distilled_k5 | 128 / 1 | 0.48 [0.43, 0.53] | -1.0 [-1.8, -0.3] |
| 0 / speed128 | distilled_k3 | offtheshelf_k2 | 128 / 1 | -0.60 [-0.64, -0.57] | -9.3 [-10.3, -8.4] |
| 0 / speed128 | distilled_k3 | offtheshelf_k3 | 128 / 1 | -0.34 [-0.37, -0.31] | -9.4 [-10.3, -8.5] |
| 0 / speed128 | distilled_k3 | offtheshelf_k4 | 128 / 1 | -0.17 [-0.21, -0.14] | -10.2 [-11.1, -9.3] |
| 0 / speed128 | distilled_k3 | offtheshelf_k5 | 128 / 1 | -0.08 [-0.12, -0.03] | -11.0 [-11.9, -10.1] |
| 0 / speed128 | distilled_k3 | reference_dedicated | 128 / 1 | 0.23 [0.14, 0.31] | -1.0 [-3.7, 1.4] |
| 0 / speed128 | distilled_k3 | reference_full | 128 / 1 | -0.10 [-0.18, -0.04] | -7.1 [-9.8, -4.8] |
| 0 / speed128 | distilled_k3 | reference_reuse | 128 / 1 | -0.84 [-0.89, -0.80] | -28.2 [-30.1, -26.5] |
| 0 / speed128 | distilled_k4 | distilled_k5 | 128 / 1 | 0.21 [0.18, 0.25] | -0.6 [-1.3, 0.2] |
| 0 / speed128 | distilled_k4 | offtheshelf_k2 | 128 / 1 | -0.87 [-0.91, -0.82] | -8.9 [-9.9, -7.8] |
| 0 / speed128 | distilled_k4 | offtheshelf_k3 | 128 / 1 | -0.60 [-0.64, -0.56] | -8.9 [-9.9, -7.9] |
| 0 / speed128 | distilled_k4 | offtheshelf_k4 | 128 / 1 | -0.44 [-0.48, -0.40] | -9.8 [-10.8, -8.8] |
| 0 / speed128 | distilled_k4 | offtheshelf_k5 | 128 / 1 | -0.34 [-0.39, -0.30] | -10.5 [-11.6, -9.5] |
| 0 / speed128 | distilled_k4 | reference_dedicated | 128 / 1 | -0.04 [-0.13, 0.04] | -0.5 [-3.2, 1.9] |
| 0 / speed128 | distilled_k4 | reference_full | 128 / 1 | -0.37 [-0.45, -0.30] | -6.7 [-9.4, -4.3] |
| 0 / speed128 | distilled_k4 | reference_reuse | 128 / 1 | -1.11 [-1.17, -1.05] | -27.8 [-29.7, -26.0] |
| 0 / speed128 | distilled_k5 | offtheshelf_k2 | 128 / 1 | -1.08 [-1.15, -1.02] | -8.3 [-9.4, -7.3] |
| 0 / speed128 | distilled_k5 | offtheshelf_k3 | 128 / 1 | -0.81 [-0.88, -0.75] | -8.4 [-9.5, -7.3] |
| 0 / speed128 | distilled_k5 | offtheshelf_k4 | 128 / 1 | -0.65 [-0.70, -0.60] | -9.2 [-10.3, -8.1] |
| 0 / speed128 | distilled_k5 | offtheshelf_k5 | 128 / 1 | -0.56 [-0.61, -0.50] | -10.0 [-11.0, -9.0] |
| 0 / speed128 | distilled_k5 | reference_dedicated | 128 / 1 | -0.25 [-0.35, -0.16] | 0.1 [-2.6, 2.4] |
| 0 / speed128 | distilled_k5 | reference_full | 128 / 1 | -0.58 [-0.67, -0.50] | -6.1 [-8.8, -3.8] |
| 0 / speed128 | distilled_k5 | reference_reuse | 128 / 1 | -1.32 [-1.40, -1.25] | -27.2 [-29.0, -25.5] |
| 0 / speed128 | offtheshelf_k2 | offtheshelf_k3 | 128 / 1 | 0.27 [0.24, 0.29] | -0.0 [-0.9, 0.7] |
| 0 / speed128 | offtheshelf_k2 | offtheshelf_k4 | 128 / 1 | 0.43 [0.40, 0.47] | -0.9 [-1.6, -0.1] |
| 0 / speed128 | offtheshelf_k2 | offtheshelf_k5 | 128 / 1 | 0.53 [0.48, 0.57] | -1.7 [-2.4, -0.9] |
| 0 / speed128 | offtheshelf_k2 | reference_dedicated | 128 / 1 | 0.83 [0.74, 0.91] | 8.4 [5.4, 11.0] |
| 0 / speed128 | offtheshelf_k2 | reference_full | 128 / 1 | 0.50 [0.42, 0.57] | 2.2 [-0.8, 4.8] |
| 0 / speed128 | offtheshelf_k2 | reference_reuse | 128 / 1 | -0.24 [-0.28, -0.20] | -18.9 [-20.8, -17.1] |
| 0 / speed128 | offtheshelf_k3 | offtheshelf_k4 | 128 / 1 | 0.16 [0.14, 0.19] | -0.8 [-1.6, -0.1] |
| 0 / speed128 | offtheshelf_k3 | offtheshelf_k5 | 128 / 1 | 0.26 [0.22, 0.30] | -1.6 [-2.4, -0.8] |
| 0 / speed128 | offtheshelf_k3 | reference_dedicated | 128 / 1 | 0.56 [0.47, 0.65] | 8.4 [5.5, 11.0] |
| 0 / speed128 | offtheshelf_k3 | reference_full | 128 / 1 | 0.23 [0.15, 0.31] | 2.3 [-0.6, 4.8] |
| 0 / speed128 | offtheshelf_k3 | reference_reuse | 128 / 1 | -0.51 [-0.56, -0.46] | -18.8 [-20.8, -16.9] |
| 0 / speed128 | offtheshelf_k4 | offtheshelf_k5 | 128 / 1 | 0.09 [0.06, 0.13] | -0.8 [-1.5, -0.0] |
| 0 / speed128 | offtheshelf_k4 | reference_dedicated | 128 / 1 | 0.40 [0.31, 0.48] | 9.3 [6.4, 11.8] |
| 0 / speed128 | offtheshelf_k4 | reference_full | 128 / 1 | 0.07 [-0.02, 0.15] | 3.1 [0.2, 5.6] |
| 0 / speed128 | offtheshelf_k4 | reference_reuse | 128 / 1 | -0.67 [-0.73, -0.62] | -18.0 [-19.9, -16.2] |
| 0 / speed128 | offtheshelf_k5 | reference_dedicated | 128 / 1 | 0.31 [0.21, 0.39] | 10.0 [7.1, 12.6] |
| 0 / speed128 | offtheshelf_k5 | reference_full | 128 / 1 | -0.03 [-0.12, 0.06] | 3.9 [0.9, 6.4] |
| 0 / speed128 | offtheshelf_k5 | reference_reuse | 128 / 1 | -0.77 [-0.83, -0.70] | -17.2 [-19.2, -15.4] |
| 1 / math128 | distilled_k2 | distilled_k3 | 128 / 1 | 0.47 [0.45, 0.49] | -1.2 [-1.7, -0.7] |
| 1 / math128 | distilled_k2 | distilled_k4 | 128 / 1 | 0.87 [0.83, 0.90] | -1.7 [-2.3, -1.1] |
| 1 / math128 | distilled_k2 | distilled_k5 | 128 / 1 | 1.16 [1.11, 1.21] | -2.4 [-3.0, -1.7] |
| 1 / math128 | distilled_k2 | offtheshelf_k2 | 128 / 1 | -0.21 [-0.23, -0.19] | -9.1 [-9.9, -8.2] |
| 1 / math128 | distilled_k2 | offtheshelf_k3 | 128 / 1 | 0.15 [0.12, 0.17] | -10.3 [-11.0, -9.5] |
| 1 / math128 | distilled_k2 | offtheshelf_k4 | 128 / 1 | 0.40 [0.38, 0.43] | -11.0 [-11.8, -10.2] |
| 1 / math128 | distilled_k2 | offtheshelf_k5 | 128 / 1 | 0.60 [0.56, 0.64] | -11.9 [-12.7, -11.0] |
| 1 / math128 | distilled_k2 | reference_full | 128 / 1 | 0.47 [0.44, 0.51] | -3.9 [-4.8, -3.0] |
| 1 / math128 | distilled_k2 | reference_reuse | 128 / 1 | -0.72 [-0.75, -0.69] | -33.8 [-34.8, -32.8] |
| 1 / math128 | distilled_k3 | distilled_k4 | 128 / 1 | 0.40 [0.37, 0.43] | -0.5 [-1.1, 0.1] |
| 1 / math128 | distilled_k3 | distilled_k5 | 128 / 1 | 0.69 [0.65, 0.73] | -1.2 [-1.8, -0.5] |
| 1 / math128 | distilled_k3 | offtheshelf_k2 | 128 / 1 | -0.68 [-0.70, -0.65] | -7.9 [-8.7, -7.1] |
| 1 / math128 | distilled_k3 | offtheshelf_k3 | 128 / 1 | -0.32 [-0.35, -0.30] | -9.1 [-9.9, -8.3] |
| 1 / math128 | distilled_k3 | offtheshelf_k4 | 128 / 1 | -0.07 [-0.09, -0.04] | -9.8 [-10.6, -9.1] |
| 1 / math128 | distilled_k3 | offtheshelf_k5 | 128 / 1 | 0.13 [0.09, 0.16] | -10.7 [-11.5, -9.9] |
| 1 / math128 | distilled_k3 | reference_full | 128 / 1 | 0.00 [-0.03, 0.04] | -2.8 [-3.7, -1.8] |
| 1 / math128 | distilled_k3 | reference_reuse | 128 / 1 | -1.19 [-1.23, -1.16] | -32.7 [-33.7, -31.7] |
| 1 / math128 | distilled_k4 | distilled_k5 | 128 / 1 | 0.30 [0.26, 0.33] | -0.7 [-1.3, -0.1] |
| 1 / math128 | distilled_k4 | offtheshelf_k2 | 128 / 1 | -1.08 [-1.12, -1.04] | -7.4 [-8.2, -6.6] |
| 1 / math128 | distilled_k4 | offtheshelf_k3 | 128 / 1 | -0.72 [-0.76, -0.69] | -8.6 [-9.4, -7.8] |
| 1 / math128 | distilled_k4 | offtheshelf_k4 | 128 / 1 | -0.46 [-0.50, -0.43] | -9.3 [-10.2, -8.5] |
| 1 / math128 | distilled_k4 | offtheshelf_k5 | 128 / 1 | -0.27 [-0.31, -0.24] | -10.2 [-11.1, -9.3] |
| 1 / math128 | distilled_k4 | reference_full | 128 / 1 | -0.39 [-0.43, -0.36] | -2.3 [-3.2, -1.3] |
| 1 / math128 | distilled_k4 | reference_reuse | 128 / 1 | -1.59 [-1.64, -1.54] | -32.2 [-33.2, -31.0] |
| 1 / math128 | distilled_k5 | offtheshelf_k2 | 128 / 1 | -1.37 [-1.42, -1.32] | -6.7 [-7.5, -5.9] |
| 1 / math128 | distilled_k5 | offtheshelf_k3 | 128 / 1 | -1.02 [-1.06, -0.97] | -7.9 [-8.7, -7.0] |
| 1 / math128 | distilled_k5 | offtheshelf_k4 | 128 / 1 | -0.76 [-0.80, -0.71] | -8.7 [-9.4, -7.8] |
| 1 / math128 | distilled_k5 | offtheshelf_k5 | 128 / 1 | -0.57 [-0.61, -0.53] | -9.5 [-10.4, -8.6] |
| 1 / math128 | distilled_k5 | reference_full | 128 / 1 | -0.69 [-0.74, -0.64] | -1.6 [-2.5, -0.6] |
| 1 / math128 | distilled_k5 | reference_reuse | 128 / 1 | -1.88 [-1.95, -1.82] | -31.5 [-32.5, -30.4] |
| 1 / math128 | offtheshelf_k2 | offtheshelf_k3 | 128 / 1 | 0.35 [0.33, 0.37] | -1.2 [-1.8, -0.6] |
| 1 / math128 | offtheshelf_k2 | offtheshelf_k4 | 128 / 1 | 0.61 [0.59, 0.64] | -1.9 [-2.5, -1.3] |
| 1 / math128 | offtheshelf_k2 | offtheshelf_k5 | 128 / 1 | 0.80 [0.76, 0.84] | -2.8 [-3.4, -2.2] |
| 1 / math128 | offtheshelf_k2 | reference_full | 128 / 1 | 0.68 [0.64, 0.72] | 5.2 [4.2, 6.1] |
| 1 / math128 | offtheshelf_k2 | reference_reuse | 128 / 1 | -0.51 [-0.54, -0.49] | -24.7 [-25.8, -23.7] |
| 1 / math128 | offtheshelf_k3 | offtheshelf_k4 | 128 / 1 | 0.26 [0.24, 0.28] | -0.7 [-1.4, -0.1] |
| 1 / math128 | offtheshelf_k3 | offtheshelf_k5 | 128 / 1 | 0.45 [0.42, 0.48] | -1.6 [-2.2, -1.0] |
| 1 / math128 | offtheshelf_k3 | reference_full | 128 / 1 | 0.33 [0.29, 0.37] | 6.3 [5.3, 7.3] |
| 1 / math128 | offtheshelf_k3 | reference_reuse | 128 / 1 | -0.87 [-0.90, -0.84] | -23.6 [-24.6, -22.6] |
| 1 / math128 | offtheshelf_k4 | offtheshelf_k5 | 128 / 1 | 0.19 [0.17, 0.21] | -0.9 [-1.5, -0.3] |
| 1 / math128 | offtheshelf_k4 | reference_full | 128 / 1 | 0.07 [0.03, 0.11] | 7.1 [6.1, 8.0] |
| 1 / math128 | offtheshelf_k4 | reference_reuse | 128 / 1 | -1.13 [-1.16, -1.09] | -22.8 [-23.9, -21.8] |
| 1 / math128 | offtheshelf_k5 | reference_full | 128 / 1 | -0.12 [-0.17, -0.07] | 8.0 [7.0, 8.9] |
| 1 / math128 | offtheshelf_k5 | reference_reuse | 128 / 1 | -1.32 [-1.37, -1.27] | -21.9 [-23.0, -20.9] |
| 1 / speed128 | distilled_k2 | distilled_k3 | 128 / 1 | 0.36 [0.33, 0.40] | -0.8 [-2.0, 0.3] |
| 1 / speed128 | distilled_k2 | distilled_k4 | 128 / 1 | 0.68 [0.63, 0.73] | -0.8 [-1.7, 0.2] |
| 1 / speed128 | distilled_k2 | distilled_k5 | 128 / 1 | 0.88 [0.82, 0.94] | -1.6 [-2.5, -0.7] |
| 1 / speed128 | distilled_k2 | offtheshelf_k2 | 128 / 1 | -0.12 [-0.15, -0.10] | -5.4 [-6.5, -4.3] |
| 1 / speed128 | distilled_k2 | offtheshelf_k3 | 128 / 1 | 0.19 [0.15, 0.22] | -6.4 [-7.6, -5.3] |
| 1 / speed128 | distilled_k2 | offtheshelf_k4 | 128 / 1 | 0.44 [0.38, 0.49] | -6.4 [-7.8, -5.1] |
| 1 / speed128 | distilled_k2 | offtheshelf_k5 | 128 / 1 | 0.60 [0.53, 0.68] | -7.1 [-8.4, -5.8] |
| 1 / speed128 | distilled_k2 | reference_full | 128 / 1 | 0.24 [0.15, 0.32] | -9.0 [-12.2, -6.0] |
| 1 / speed128 | distilled_k2 | reference_reuse | 128 / 1 | -0.50 [-0.56, -0.45] | -29.3 [-31.7, -27.0] |
| 1 / speed128 | distilled_k3 | distilled_k4 | 128 / 1 | 0.32 [0.28, 0.36] | 0.1 [-0.9, 1.1] |
| 1 / speed128 | distilled_k3 | distilled_k5 | 128 / 1 | 0.52 [0.46, 0.58] | -0.8 [-1.8, 0.4] |
| 1 / speed128 | distilled_k3 | offtheshelf_k2 | 128 / 1 | -0.49 [-0.52, -0.44] | -4.6 [-6.0, -3.1] |
| 1 / speed128 | distilled_k3 | offtheshelf_k3 | 128 / 1 | -0.17 [-0.21, -0.14] | -5.6 [-6.7, -4.4] |
| 1 / speed128 | distilled_k3 | offtheshelf_k4 | 128 / 1 | 0.07 [0.02, 0.13] | -5.6 [-6.9, -4.4] |
| 1 / speed128 | distilled_k3 | offtheshelf_k5 | 128 / 1 | 0.24 [0.18, 0.30] | -6.3 [-7.5, -5.0] |
| 1 / speed128 | distilled_k3 | reference_full | 128 / 1 | -0.12 [-0.21, -0.05] | -8.1 [-11.0, -5.5] |
| 1 / speed128 | distilled_k3 | reference_reuse | 128 / 1 | -0.86 [-0.92, -0.81] | -28.4 [-30.5, -26.5] |
| 1 / speed128 | distilled_k4 | distilled_k5 | 128 / 1 | 0.20 [0.16, 0.24] | -0.8 [-1.7, 0.1] |
| 1 / speed128 | distilled_k4 | offtheshelf_k2 | 128 / 1 | -0.80 [-0.85, -0.76] | -4.6 [-5.8, -3.4] |
| 1 / speed128 | distilled_k4 | offtheshelf_k3 | 128 / 1 | -0.49 [-0.53, -0.45] | -5.6 [-6.6, -4.7] |
| 1 / speed128 | distilled_k4 | offtheshelf_k4 | 128 / 1 | -0.24 [-0.28, -0.20] | -5.7 [-6.7, -4.6] |
| 1 / speed128 | distilled_k4 | offtheshelf_k5 | 128 / 1 | -0.08 [-0.13, -0.02] | -6.3 [-7.5, -5.2] |
| 1 / speed128 | distilled_k4 | reference_full | 128 / 1 | -0.44 [-0.53, -0.35] | -8.2 [-11.2, -5.5] |
| 1 / speed128 | distilled_k4 | reference_reuse | 128 / 1 | -1.18 [-1.25, -1.12] | -28.5 [-30.6, -26.6] |
| 1 / speed128 | distilled_k5 | offtheshelf_k2 | 128 / 1 | -1.00 [-1.07, -0.94] | -3.8 [-5.0, -2.6] |
| 1 / speed128 | distilled_k5 | offtheshelf_k3 | 128 / 1 | -0.69 [-0.75, -0.64] | -4.8 [-5.9, -3.7] |
| 1 / speed128 | distilled_k5 | offtheshelf_k4 | 128 / 1 | -0.44 [-0.50, -0.39] | -4.9 [-6.0, -3.8] |
| 1 / speed128 | distilled_k5 | offtheshelf_k5 | 128 / 1 | -0.28 [-0.34, -0.22] | -5.5 [-6.7, -4.3] |
| 1 / speed128 | distilled_k5 | reference_full | 128 / 1 | -0.64 [-0.75, -0.54] | -7.4 [-10.3, -4.6] |
| 1 / speed128 | distilled_k5 | reference_reuse | 128 / 1 | -1.38 [-1.47, -1.30] | -27.7 [-29.8, -25.7] |
| 1 / speed128 | offtheshelf_k2 | offtheshelf_k3 | 128 / 1 | 0.31 [0.28, 0.34] | -1.0 [-2.0, -0.1] |
| 1 / speed128 | offtheshelf_k2 | offtheshelf_k4 | 128 / 1 | 0.56 [0.52, 0.60] | -1.0 [-2.1, 0.0] |
| 1 / speed128 | offtheshelf_k2 | offtheshelf_k5 | 128 / 1 | 0.73 [0.66, 0.79] | -1.7 [-2.7, -0.7] |
| 1 / speed128 | offtheshelf_k2 | reference_full | 128 / 1 | 0.36 [0.27, 0.45] | -3.6 [-7.0, -0.4] |
| 1 / speed128 | offtheshelf_k2 | reference_reuse | 128 / 1 | -0.38 [-0.43, -0.33] | -23.9 [-26.3, -21.5] |
| 1 / speed128 | offtheshelf_k3 | offtheshelf_k4 | 128 / 1 | 0.25 [0.21, 0.29] | -0.0 [-0.9, 0.9] |
| 1 / speed128 | offtheshelf_k3 | offtheshelf_k5 | 128 / 1 | 0.41 [0.37, 0.46] | -0.7 [-1.4, 0.1] |
| 1 / speed128 | offtheshelf_k3 | reference_full | 128 / 1 | 0.05 [-0.05, 0.14] | -2.6 [-5.8, 0.5] |
| 1 / speed128 | offtheshelf_k3 | reference_reuse | 128 / 1 | -0.69 [-0.75, -0.64] | -22.9 [-25.2, -20.7] |
| 1 / speed128 | offtheshelf_k4 | offtheshelf_k5 | 128 / 1 | 0.17 [0.12, 0.21] | -0.6 [-1.5, 0.2] |
| 1 / speed128 | offtheshelf_k4 | reference_full | 128 / 1 | -0.20 [-0.30, -0.10] | -2.5 [-5.6, 0.4] |
| 1 / speed128 | offtheshelf_k4 | reference_reuse | 128 / 1 | -0.94 [-1.01, -0.87] | -22.8 [-25.0, -20.7] |
| 1 / speed128 | offtheshelf_k5 | reference_full | 128 / 1 | -0.36 [-0.49, -0.25] | -1.9 [-5.3, 1.3] |
| 1 / speed128 | offtheshelf_k5 | reference_reuse | 128 / 1 | -1.11 [-1.20, -1.02] | -22.2 [-24.6, -19.9] |

Recipe: exact full-vocabulary forward KL,15744train/256heldout repair prompts per target, lr1e-5/2e-5 x1/3epochs. Select checkpoint by heldout tau atK4; select timing K by warm tokens/s on32heldout repair queries, separately b1/b8. Full K2–5 acceptance sweep retained. Teacher hidden-state/head factorization is exact, not top-k; lexical IDs match and export special-token aliases preserve training IDs.

| Target / panel / batch | Arm | Reference | Warm token speedup [95% CI] | Panel speedup [95% CI] | Processes / warm passes |
|---|---|---|---|---|---|
| 0 / math128 / b1 | distilled | none | 1.79 [1.77, 1.81] | 1.79 [1.77, 1.82] | 3 / 3 |
| 0 / math128 / b1 | distilled | reuse | 1.20 [1.19, 1.22] | 1.21 [1.19, 1.22] | 3 / 3 |
| 0 / math128 / b1 | distilled | full | 0.78 [0.77, 0.78] | 0.78 [0.77, 0.79] | 3 / 3 |
| 0 / math128 / b1 | full | none | 2.31 [2.28, 2.34] | 2.31 [2.28, 2.34] | 3 / 3 |
| 0 / math128 / b1 | full | reuse | 1.55 [1.54, 1.57] | 1.55 [1.53, 1.57] | 3 / 3 |
| 0 / math128 / b1 | offtheshelf | none | 1.56 [1.54, 1.57] | 1.56 [1.54, 1.58] | 3 / 3 |
| 0 / math128 / b1 | offtheshelf | reuse | 1.05 [1.03, 1.06] | 1.05 [1.03, 1.06] | 3 / 3 |
| 0 / math128 / b1 | offtheshelf | full | 0.67 [0.67, 0.68] | 0.67 [0.67, 0.68] | 3 / 3 |
| 0 / math128 / b1 | reuse | none | 1.49 [1.47, 1.50] | 1.49 [1.47, 1.51] | 3 / 3 |
| 0 / math128 / b1 | reuse | full | 0.64 [0.64, 0.65] | 0.64 [0.64, 0.65] | 3 / 3 |
| 0 / math128 / b8 | distilled | none | 1.61 [1.58, 1.64] | 1.61 [1.58, 1.64] | 3 / 3 |
| 0 / math128 / b8 | distilled | reuse | 1.21 [1.17, 1.24] | 1.21 [1.18, 1.24] | 3 / 3 |
| 0 / math128 / b8 | distilled | full | 0.78 [0.76, 0.80] | 0.78 [0.76, 0.80] | 3 / 3 |
| 0 / math128 / b8 | full | none | 2.06 [2.01, 2.10] | 2.06 [2.01, 2.10] | 3 / 3 |
| 0 / math128 / b8 | full | reuse | 1.54 [1.51, 1.58] | 1.55 [1.51, 1.58] | 3 / 3 |
| 0 / math128 / b8 | offtheshelf | none | 1.41 [1.39, 1.43] | 1.41 [1.39, 1.43] | 3 / 3 |
| 0 / math128 / b8 | offtheshelf | reuse | 1.06 [1.03, 1.09] | 1.06 [1.03, 1.09] | 3 / 3 |
| 0 / math128 / b8 | offtheshelf | full | 0.69 [0.67, 0.70] | 0.69 [0.67, 0.70] | 3 / 3 |
| 0 / math128 / b8 | reuse | none | 1.33 [1.31, 1.36] | 1.33 [1.30, 1.36] | 3 / 3 |
| 0 / math128 / b8 | reuse | full | 0.65 [0.63, 0.66] | 0.65 [0.63, 0.66] | 3 / 3 |
| 0 / speed128 / b1 | distilled | none | 1.55 [1.53, 1.58] | 1.56 [1.53, 1.58] | 3 / 3 |
| 0 / speed128 / b1 | distilled | reuse | 1.16 [1.13, 1.19] | 1.16 [1.13, 1.20] | 3 / 3 |
| 0 / speed128 / b1 | distilled | full | 0.84 [0.80, 0.88] | 0.84 [0.80, 0.88] | 3 / 3 |
| 0 / speed128 / b1 | full | none | 1.85 [1.76, 1.94] | 1.85 [1.75, 1.94] | 3 / 3 |
| 0 / speed128 / b1 | full | reuse | 1.38 [1.35, 1.42] | 1.38 [1.34, 1.42] | 3 / 3 |
| 0 / speed128 / b1 | offtheshelf | none | 1.38 [1.36, 1.40] | 1.38 [1.35, 1.40] | 3 / 3 |
| 0 / speed128 / b1 | offtheshelf | reuse | 1.03 [1.00, 1.06] | 1.03 [1.00, 1.06] | 3 / 3 |
| 0 / speed128 / b1 | offtheshelf | full | 0.74 [0.71, 0.78] | 0.74 [0.71, 0.79] | 3 / 3 |
| 0 / speed128 / b1 | reuse | none | 1.34 [1.30, 1.38] | 1.34 [1.29, 1.38] | 3 / 3 |
| 0 / speed128 / b1 | reuse | full | 0.72 [0.70, 0.74] | 0.72 [0.70, 0.74] | 3 / 3 |
| 0 / speed128 / b8 | distilled | none | 1.38 [1.33, 1.42] | 1.38 [1.34, 1.42] | 3 / 3 |
| 0 / speed128 / b8 | distilled | reuse | 1.28 [1.19, 1.38] | 1.29 [1.20, 1.39] | 3 / 3 |
| 0 / speed128 / b8 | distilled | full | 1.07 [0.93, 1.22] | 1.08 [0.93, 1.22] | 3 / 3 |
| 0 / speed128 / b8 | full | none | 1.28 [1.11, 1.50] | 1.28 [1.11, 1.50] | 3 / 3 |
| 0 / speed128 / b8 | full | reuse | 1.19 [1.12, 1.29] | 1.20 [1.12, 1.30] | 3 / 3 |
| 0 / speed128 / b8 | offtheshelf | none | 1.22 [1.19, 1.24] | 1.22 [1.20, 1.24] | 3 / 3 |
| 0 / speed128 / b8 | offtheshelf | reuse | 1.14 [1.05, 1.23] | 1.14 [1.05, 1.23] | 3 / 3 |
| 0 / speed128 / b8 | offtheshelf | full | 0.95 [0.82, 1.09] | 0.95 [0.82, 1.09] | 3 / 3 |
| 0 / speed128 / b8 | reuse | none | 1.07 [0.99, 1.17] | 1.07 [0.98, 1.16] | 3 / 3 |
| 0 / speed128 / b8 | reuse | full | 0.84 [0.78, 0.89] | 0.83 [0.77, 0.89] | 3 / 3 |
| 1 / math128 / b1 | distilled | none | 1.74 [1.72, 1.77] | 1.74 [1.72, 1.77] | 3 / 3 |
| 1 / math128 / b1 | distilled | reuse | 1.33 [1.31, 1.35] | 1.33 [1.31, 1.35] | 3 / 3 |
| 1 / math128 / b1 | distilled | full | 0.79 [0.78, 0.80] | 0.79 [0.78, 0.80] | 3 / 3 |
| 1 / math128 / b1 | full | none | 2.21 [2.18, 2.25] | 2.21 [2.18, 2.25] | 3 / 3 |
| 1 / math128 / b1 | full | reuse | 1.69 [1.67, 1.71] | 1.69 [1.67, 1.71] | 3 / 3 |
| 1 / math128 / b1 | offtheshelf | none | 1.51 [1.49, 1.52] | 1.51 [1.49, 1.52] | 3 / 3 |
| 1 / math128 / b1 | offtheshelf | reuse | 1.15 [1.14, 1.16] | 1.15 [1.14, 1.16] | 3 / 3 |
| 1 / math128 / b1 | offtheshelf | full | 0.68 [0.67, 0.69] | 0.68 [0.67, 0.69] | 3 / 3 |
| 1 / math128 / b1 | reuse | none | 1.31 [1.29, 1.33] | 1.31 [1.29, 1.33] | 3 / 3 |
| 1 / math128 / b1 | reuse | full | 0.59 [0.58, 0.60] | 0.59 [0.58, 0.60] | 3 / 3 |
| 1 / math128 / b8 | distilled | none | 1.56 [1.52, 1.60] | 1.56 [1.52, 1.60] | 3 / 3 |
| 1 / math128 / b8 | distilled | reuse | 1.30 [1.26, 1.34] | 1.30 [1.26, 1.34] | 3 / 3 |
| 1 / math128 / b8 | distilled | full | 0.80 [0.79, 0.81] | 0.80 [0.79, 0.81] | 3 / 3 |
| 1 / math128 / b8 | full | none | 1.96 [1.90, 2.01] | 1.96 [1.90, 2.01] | 3 / 3 |
| 1 / math128 / b8 | full | reuse | 1.63 [1.58, 1.68] | 1.63 [1.58, 1.68] | 3 / 3 |
| 1 / math128 / b8 | offtheshelf | none | 1.36 [1.33, 1.38] | 1.36 [1.33, 1.38] | 3 / 3 |
| 1 / math128 / b8 | offtheshelf | reuse | 1.13 [1.11, 1.15] | 1.13 [1.11, 1.15] | 3 / 3 |
| 1 / math128 / b8 | offtheshelf | full | 0.69 [0.68, 0.71] | 0.69 [0.68, 0.71] | 3 / 3 |
| 1 / math128 / b8 | reuse | none | 1.20 [1.18, 1.21] | 1.20 [1.18, 1.21] | 3 / 3 |
| 1 / math128 / b8 | reuse | full | 0.61 [0.60, 0.63] | 0.61 [0.60, 0.63] | 3 / 3 |
| 1 / speed128 / b1 | distilled | none | 1.56 [1.53, 1.60] | 1.57 [1.52, 1.63] | 3 / 3 |
| 1 / speed128 / b1 | distilled | reuse | 1.19 [1.15, 1.23] | 1.21 [1.15, 1.27] | 3 / 3 |
| 1 / speed128 / b1 | distilled | full | 0.85 [0.80, 0.90] | 0.85 [0.80, 0.91] | 3 / 3 |
| 1 / speed128 / b1 | full | none | 1.84 [1.74, 1.94] | 1.85 [1.72, 1.97] | 3 / 3 |
| 1 / speed128 / b1 | full | reuse | 1.40 [1.35, 1.44] | 1.42 [1.36, 1.49] | 3 / 3 |
| 1 / speed128 / b1 | offtheshelf | none | 1.45 [1.43, 1.47] | 1.45 [1.40, 1.49] | 3 / 3 |
| 1 / speed128 / b1 | offtheshelf | reuse | 1.10 [1.06, 1.14] | 1.11 [1.07, 1.15] | 3 / 3 |
| 1 / speed128 / b1 | offtheshelf | full | 0.79 [0.74, 0.84] | 0.78 [0.73, 0.84] | 3 / 3 |
| 1 / speed128 / b1 | reuse | none | 1.32 [1.28, 1.36] | 1.31 [1.25, 1.36] | 3 / 3 |
| 1 / speed128 / b1 | reuse | full | 0.72 [0.69, 0.74] | 0.71 [0.67, 0.74] | 3 / 3 |
| 1 / speed128 / b8 | distilled | none | 1.47 [1.42, 1.52] | 1.47 [1.43, 1.51] | 3 / 3 |
| 1 / speed128 / b8 | distilled | reuse | 1.28 [1.19, 1.38] | 1.28 [1.20, 1.39] | 3 / 3 |
| 1 / speed128 / b8 | distilled | full | 1.01 [0.86, 1.18] | 1.01 [0.86, 1.18] | 3 / 3 |
| 1 / speed128 / b8 | full | none | 1.45 [1.26, 1.70] | 1.45 [1.25, 1.70] | 3 / 3 |
| 1 / speed128 / b8 | full | reuse | 1.26 [1.15, 1.40] | 1.27 [1.14, 1.42] | 3 / 3 |
| 1 / speed128 / b8 | offtheshelf | none | 1.35 [1.31, 1.40] | 1.32 [1.30, 1.34] | 3 / 3 |
| 1 / speed128 / b8 | offtheshelf | reuse | 1.17 [1.10, 1.27] | 1.16 [1.09, 1.24] | 3 / 3 |
| 1 / speed128 / b8 | offtheshelf | full | 0.93 [0.79, 1.07] | 0.91 [0.78, 1.06] | 3 / 3 |
| 1 / speed128 / b8 | reuse | none | 1.15 [1.07, 1.23] | 1.14 [1.07, 1.21] | 3 / 3 |
| 1 / speed128 / b8 | reuse | full | 0.79 [0.71, 0.87] | 0.79 [0.70, 0.88] | 3 / 3 |
Timing intervals resample process and paired prompt batch; cold/startup and output mismatches are retained in the source JSON.

R1 dedicated-gap recovery at matched K4; the ratio is recomputed in each paired resample.

| Variant | Panel | n / seeds | Recovery % [95% CI] |
|---|---|---|---|
| distilled_k4 | math128 | 128 / 1 | 78.6 [76.7, 80.4] |
| offtheshelf_k4 | math128 | 128 / 1 | 54.8 [53.0, 56.6] |
| distilled_k4 | speed128 | 128 / 1 | 103.3 [96.0, 112.5] |
| offtheshelf_k4 | speed128 | 128 / 1 | 62.6 [56.5, 70.1] |

Result status: 40 completed non-reference cells in this snapshot; no unfinished outcome inferred.
GPU-hours: 135.9 completed, including failures; active runtime additional.
Sources: /home/heck2/sbhansali8/ReFit/rebuttal/E45_analysis_watch_20261124_1645/20261126_170336_932613/results.json
Failed runs retained: [{"run": "E5_t0_timing_distilled_math128_b1_r0", "status": "failed"}, {"run": "E5_t0_timing_distilled_math128_b1_r1", "status": "failed"}, {"run": "E5_t0_timing_distilled_math128_b1_r2", "status": "failed"}, {"run": "E5_t0_timing_distilled_speed128_b1_r0", "status": "failed"}, {"run": "E5_t0_timing_distilled_speed128_b1_r1", "status": "failed"}, {"run": "E5_t0_timing_distilled_speed128_b1_r2", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_math128_b1_r0", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_math128_b1_r1", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_math128_b1_r2", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_speed128_b1_r0", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_speed128_b1_r1", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_speed128_b1_r2", "status": "failed"}, {"run": "E5_t0_timing_offtheshelf_speed128_b1_r2_retry1", "status": "failed"}]

## E6 — Tree drafting
Status: not run (preflight and reproduction in progress)
GPU-hours: 0 measured for new runs.

## E8 — Multilingual repair
Status: not run (preflight and reproduction in progress)
GPU-hours: 0 measured for new runs.

## E7 — Long-trace domain repair
Status: not run (preflight and reproduction in progress)
GPU-hours: 0 measured for new runs.

## E9 — Crossover add-ons
Status: not run (preflight and reproduction in progress)
GPU-hours: 0 measured for new runs.


## E4/E5 implementation status — Nov24 16:18ET
Status: partial; production training/evaluation pending. Both EDA private sizes completed native TTT3 training and export smoke checks. Both independent1B targets completed full-vocabulary forward-KL training/export smoke checks. These smoke runs are implementation evidence, not trained-baseline acceptance results. Teacher full-vocabulary reconstruction agrees exactly with direct teacher logits on five checked samples for each target. Full16k captures and the separate2000-prompt EDA reference generation are running.

## E2 — new R1 three-seed decomposition, Nov24
Status: partial; R1 existing-checkpoint decomposition complete, new matched decoder/head runs pending. n128 per benchmark, seeds0/1/2,10000 paired seed/query bootstrap resamples.

| Benchmark | Variant | tau | Delta tau vs interface [95% CI] |
|---|---|---:|---|
| SPEED | Whole LoRA |2.4650|+0.0452 [0.0267,0.0646]|
| SPEED | Whole LoRA, interface delta removed |2.3579|-0.0618 [-0.0881,-0.0363]|
| SPEED | Only whole-LoRA interface delta retained |1.9710|-0.4488 [-0.4784,-0.4178]|
| MATH128 | Whole LoRA |2.8622|+0.0705 [0.0506,0.0885]|
| MATH128 | Whole LoRA, interface delta removed |2.7344|-0.0572 [-0.0752,-0.0382]|
| MATH128 | Only whole-LoRA interface delta retained |2.1893|-0.6024 [-0.6232,-0.5812]|

Result: the joint whole-LoRA model modestly exceeds dense-interface repair; either post-training removal reduces its acceptance. These are interventions on jointly trained weights, not separately optimized component-only controls. Sources: rebuttal/E2/reduction_20261124_1613/results.json and immutable raw per_prompt files listed there. All invalid v1 ablations remain excluded by the previously recorded physical-key bug criterion.

## E1-D61 — derivative-text raw crossover cells

Pilot; n=64 paired contexts per target, 10,000 sequence resamples. Values a–d and d−a are percentage points. a=parent taps/parent verifier, b=parent taps/child verifier, c=child taps/parent verifier, d=child taps/child verifier. These are fixed-text HF agreement measurements, not served acceptance.

| Target | a | b | c | d | d−a | (d−b)/(d−a) |
|---|---:|---:|---:|---:|---:|---:|
| deepseek-ai/DeepSeek-R1-Distill-Llama-8B | 50.989 [48.539, 53.274] | 44.836 [42.402, 47.205] | 45.905 [43.521, 48.221] | 46.005 [43.532, 48.430] | -4.983 [-5.763, -4.220] | -0.235 [-0.402, -0.103] |
| nvidia/Llama-3.1-Nemotron-Nano-8B-v1 | 59.565 [56.456, 62.354] | 52.046 [49.117, 54.841] | 48.814 [45.921, 51.525] | 48.944 [46.036, 51.645] | -10.621 [-11.726, -9.481] | 0.292 [0.226, 0.354] |
| deepseek-ai/DeepSeek-R1-0528-Qwen3-8B | 58.105 [55.008, 60.922] | 51.344 [48.400, 54.204] | 52.858 [49.972, 55.525] | 52.403 [49.442, 55.219] | -5.701 [-6.447, -4.954] | -0.186 [-0.288, -0.096] |
| shufanshen/Qwen3-8B-GRPO-DeepMath-50-steps | 65.916 [63.013, 68.744] | 65.873 [62.957, 68.685] | 65.863 [62.982, 68.677] | 65.875 [62.993, 68.676] | -0.041 [-0.242, 0.163] | -0.053 [-6.855, 8.672] |

The requested ratio is recomputed from macro contrasts in each paired resample; it is not the prior averaged-feature share. A denominator CI crossing zero makes the ratio unstable (see JSON flags); it is not a percentage of an identified causal mechanism. No additional GPU runs. Source: /home/heck2/sbhansali8/ReFit/rebuttal/planner_analysis_20261126_1730/results.json.

## E2-restoration — checkpoint interventions

Pilot; three paired training seeds, n=128 queries per seed and panel. All differences below are versus the same seed’s intact whole-drafter LoRA checkpoint. These are eval-time restorations, not separately trained variants.

| Target | Panel | Kept trained deltas | Tau [95% CI] | Delta tau versus whole LoRA [95% CI] |
|---|---|---|---:|---:|
| R1 | speed128 | all | 2.465 [2.391, 2.537] | 0.000 [0.000, 0.000] |
| R1 | speed128 | interface only; restore all other weights | 1.971 [1.916, 2.025] | -0.494 [-0.527, -0.461] |
| R1 | speed128 | all except interface; restore interface | 2.358 [2.287, 2.428] | -0.107 [-0.132, -0.083] |
| R1 | math128 | all | 2.862 [2.825, 2.896] | 0.000 [0.000, 0.000] |
| R1 | math128 | interface only; restore all other weights | 2.189 [2.157, 2.221] | -0.673 [-0.697, -0.646] |
| R1 | math128 | all except interface; restore interface | 2.734 [2.699, 2.768] | -0.128 [-0.145, -0.111] |
| Nemotron | speed128 | all | 2.439 [2.351, 2.523] | 0.000 [0.000, 0.000] |
| Nemotron | speed128 | interface only; restore all other weights | 1.987 [1.924, 2.050] | -0.452 [-0.493, -0.410] |
| Nemotron | speed128 | all except interface; restore interface | 2.301 [2.223, 2.378] | -0.138 [-0.166, -0.111] |
| Nemotron | math128 | all | 2.743 [2.700, 2.785] | 0.000 [0.000, 0.000] |
| Nemotron | math128 | interface only; restore all other weights | 2.054 [2.026, 2.085] | -0.688 [-0.713, -0.662] |
| Nemotron | math128 | all except interface; restore interface | 2.546 [2.506, 2.587] | -0.197 [-0.215, -0.177] |

Only audited corrected shard exports are included. Independent raw-counter reduction; source: /home/heck2/sbhansali8/ReFit/rebuttal/planner_analysis_20261126_1730/results.json.

## E3-cost — measured scratch and data costs

Original generation logs are present for all 64,000 examples: **36.078938 A40 GPU-hours**, including reused 16k plus the 48k Alpaca/Dolly extension. This is a sum of recorded successful generation wall times, not an estimate.

| Exported epoch | Step | Cumulative training GPU-h | Generation GPU-h | Data + training GPU-h |
|---|---:|---:|---:|---:|
| 1 | 18448 | 14.106598 | 36.078938 | 50.185536 |
| 2 | 36886 | 27.330982 | 36.078938 | 63.409920 |

sum of recorded successful generation wall_s on one A40 per shard; training is cumulative trainer elapsed_s on one A40 including initialization/checkpoint exports, excluding outer launch wrapper, acceptance and failed attempts; no inferred missing times.
existing16k Alpaca +48k Alpaca/Dolly extension; continuous20epoch cosine schedule; mandatory stop Nov28 noon ET. Epoch-5 evaluation is already wired to the existing export watcher. E3a’s separate one-epoch lower-bound extrapolation awaits measured 200-step training runs. Source: /home/heck2/sbhansali8/ReFit/rebuttal/planner_analysis_20261126_1730/results.json.

## E4-selected50M — explicit paired comparison with full repair

Pilot; same EDA-selected 8k, same native recipe/steps, paired seeds 0 and 1, n=128. EDA50M has 50,339,840 trainable parameters; ReFit-full has 424,689,664. This comparison is data/step matched, not capacity matched.

| Panel | EDA50M tau | ReFit-full tau | Full minus EDA50M tau |
|---|---:|---:|---:|
| math128 | 2.344 [2.310, 2.377] | 2.655 [2.618, 2.691] | 0.311 [0.290, 0.333] |
| speed128 | 2.144 [2.085, 2.201] | 2.437 [2.363, 2.508] | 0.293 [0.267, 0.317] |

All intervals are paired seed/query bootstrap 95% CIs. Source: /home/heck2/sbhansali8/ReFit/rebuttal/planner_analysis_20261126_1730/results.json.

## E4c — capacity-matched method × subset comparison

Pilot. ReFit-interface: 50,331,648 parameters; EDA50M: 50,339,840 (routing accounts for the 8,192 difference). Same selected/random 8k, steps, optimizer and native objective within each seed. Seeds 0 and 1; n=128 per evaluation panel. Pending results are not inferred.

| Panel / method | EDA-selected 8k tau [95% CI] | Random 8k tau [95% CI] |
|---|---:|---:|
| speed128 / eda50m | 2.144 [2.085, 2.201] (seeds [0, 1]) | pending |
| speed128 / interface | pending | pending |
| math128 / eda50m | 2.344 [2.310, 2.377] (seeds [0, 1]) | pending |
| math128 / interface | pending | pending |

| Panel / subset | Paired interface − EDA50M tau [95% CI] | Seeds / n |
|---|---:|---:|
| speed128 / selected | pending | pending |
| speed128 / random | pending | pending |
| math128 / selected | pending | pending |
| math128 / random | pending | pending |

New E4c completed cost 0.000/15 GPU-h; active time is additional and enforced by the live guard. Historical selected EDA is reused, not charged again. Old automatic E4 rows may include E4c because the exact pipeline retains experiment=E4; this E4c prefix accounting is the separate approved budget.
Source: /home/heck2/sbhansali8/ReFit/rebuttal/planner_analysis_20261126_1730/results.json.

## Timing-divergence — required E5 characterization

Pilot CPU audit of 120 completed fresh processes. Full pair-level details are in /home/heck2/sbhansali8/ReFit/rebuttal/timing_divergence_20261126_all120/process-pairs.csv; every arm and all cross-process pairings included. Warm repeats use the same repeat index in each pair. Identical completion means exact token-ID equality, including length. First-divergence quartiles (in CSV) use zero-based token index among nonidentical completions; a strict prefix diverges at its first missing token.

| Target / panel / batch | No-spec vs no-spec identical % | Spec vs no-spec identical % | Spec vs spec identical % |
|---|---:|---:|---:|
| (0, 'math128', 1) | 47.40 | 20.38 | 39.71 |
| (0, 'math128', 8) | 22.92 | 20.64 | 27.90 |
| (0, 'speed128', 1) | 36.98 | 4.82 | 20.21 |
| (0, 'speed128', 8) | 5.38 | 5.12 | 9.99 |
| (1, 'math128', 1) | 22.66 | 21.90 | 38.44 |
| (1, 'math128', 8) | 32.81 | 22.84 | 28.47 |
| (1, 'speed128', 1) | 46.88 | 18.47 | 34.45 |
| (1, 'speed128', 8) | 33.16 | 16.83 | 20.14 |

ReFit-full / distilled-1B warm throughput ratios; 10,000 paired process/query-batch bootstrap 95% CIs. Output-matching subset requires equality across all six processes and all three warm repeats. For batch8, only entire matching original batches have measured elapsed time.

| Target / panel / batch | All 128 queries | Matching queries | Timed matching queries | Matching-output ratio |
|---|---:|---:|---:|---:|
| R1 / math128 / b1 | 1.290 [1.277, 1.302] | 16 | 16 | 1.280 [1.249, 1.309] |
| R1 / math128 / b8 | 1.280 [1.252, 1.308] | 7 | 0 | not estimable |
| R1 / speed128 / b1 | 1.191 [1.136, 1.244] | 1 | 1 | 1.411 [1.408, 1.416] |
| R1 / speed128 / b8 | 0.932 [0.818, 1.075] | 0 | 0 | not estimable |
| Nemotron / math128 / b1 | 1.270 [1.257, 1.284] | 8 | 8 | 1.321 [1.249, 1.391] |
| Nemotron / math128 / b8 | 1.252 [1.229, 1.273] | 12 | 0 | not estimable |
| Nemotron / speed128 / b1 | 1.179 [1.108, 1.246] | 11 | 11 | 1.334 [1.194, 1.420] |
| Nemotron / speed128 / b8 | 0.989 [0.851, 1.159] | 5 | 0 | not estimable |

Divergence is present in every no-spec/spec category, including repeated fresh no-spec processes, but its rates vary substantially by arm pairing, workload and batch; the evidence does **not** establish that all arms are affected alike. Batch1 matching-output subsets retain the measured ReFit-full advantage, with only 1–16 queries per panel, so they do not establish equivalence on the full population. No complete batch8 matching subset survives. First-divergence-truncated throughput is not identifiable from total batch elapsed time: no per-token timestamps were recorded, and prorating by token count would manufacture a timing measurement. The root numerical/engine cause is unestablished. These observations qualify E5 as observed serving throughput under the recorded outputs, not a proof of bit-identical execution across methods.

The newly requested one-prompt, same-process no-spec three-repeat check is queued as TD_t0_none_sameprocess_threewarm_20261126; results pending. Existing within-process pair counts are in within-process.csv. Harness unchanged. Source: /home/heck2/sbhansali8/ReFit/rebuttal/timing_divergence_20261126_all120/results.json.

## D61-scope — deadline and exclusions

Final numbers: Nov28 EOD ET. E6, E7, E9, EDA native20epoch schedule and EDA seed2: **not run for the response**, per owner-approved Nov26 scope. No SGLang integration. E8-lite is conditional P1, R1 only, 12GPUh; its results remain pending and will be marked not run if not final by the deadline. No paper edits or OpenReview posting.

