# Rebuttal results

E1 and E10 are complete. New GPU experiments await baseline reproduction and free A40 slots. Reference acceptance numbers are not represented as reproduced results.

## E10 — Software versions
Status: final (version inventory; fresh numerical reproductions pending GPU slots)
Answers: u4ad engine-version question

Paper and current inference environment both use vLLM 0.31.0. The frozen acceptance harness is 6da2e4265c0398ec0de5affaf23b0bd1df0be445. Current inference: Python 3.11.5, PyTorch 2.13.0, CUDA 13.0, transformers 5.17.0, NVIDIA A40, driver 620.70.06. Trainer: transformers 5.16.1, Speculators 0.9.0a0, same Python/PyTorch/CUDA. SGLang has not been used. Full environment freezes and source timing-config evidence are saved.

Result in one sentence: the current inference engine version matches the submitted timing runs; numerical reproduction remains a prerequisite for the new GPU experiments.
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

## E2 — LoRA decomposition
Status: not run (preflight and reproduction in progress)
GPU-hours: 0 measured for new runs.

## E4 — EDA baseline
Status: not run (preflight and reproduction in progress)
GPU-hours: 0 measured for new runs.

## E3 — Dedicated training cost
Status: not run (preflight and reproduction in progress)
GPU-hours: 0 measured for new runs.

## E5 — Distilled independent drafter
Status: not run (preflight and reproduction in progress)
GPU-hours: 0 measured for new runs.

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

