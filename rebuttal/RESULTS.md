# Rebuttal results

E1 and E10 are complete. All10 exact acceptance reference checks passed. E2 has partial newly evaluated comparisons; eight training runs and the continuous scratch run are underway. E4 has a successful untrained-port sanity check, not a trained baseline result.

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
Status: partial (Nemotron seed0; seeds1–2 and matched decoder/head-only training still running; R1 evaluations in progress)
Answers: RLU2 W2, u4ad W2

Nemotron, n128 per panel, seed0, first128 MATH. All means and paired differences recomputed from raw per-step counters;10,000 query resamples. The LoRA ablations restore exact initial weights after training; they are not separately trained fc-only/no-fc models. p1 and full provenance are in the accompanying JSON/CSV.

| Variant | SPEED tau [95%CI] | MATH tau [95%CI] | Delta SPEED vs dense fc | Delta MATH vs dense fc |
|---|---|---|---|---|
| Dense interface | 2.39 [2.30, 2.47] | 2.68 [2.64, 2.73] | reference | reference |
| Whole LoRA | 2.44 [2.35, 2.52] | 2.75 [2.71, 2.79] | 0.05 [0.03, 0.08] | 0.07 [0.05, 0.08] |
| Whole LoRA with fc restored | 2.31 [2.23, 2.39] | 2.55 [2.51, 2.59] | -0.07 [-0.10, -0.05] | -0.13 [-0.15, -0.11] |
| Whole LoRA with only fc updates retained | 1.98 [1.92, 2.05] | 2.06 [2.03, 2.09] | -0.40 [-0.44, -0.36] | -0.62 [-0.65, -0.60] |

Result in one sentence: whole-drafter LoRA modestly exceeds the dense interface on this seed, while removing either group of its jointly trained updates reduces acceptance.
GPU-hours: 1.8 completed at the reduction snapshot, including failures/invalid attempts; active training additional (budget40GPUh approved by ownerNov24).
Deviations from spec: operational stride-preserving CPU offload fixes compiled backward layouts without changing the objective; four initial ablation cells were invalidated for duplicate physical tensor keys and rerun. No invalid numbers included. Three-seed dense-interface results are also saved, but this table pairs seed0 with seed0.
Sources: rebuttal/E2/reduction_20261124_1533/results.json and results.csv; eight exports in exports_v2; v2-audit.json proves unique physical tensor keys and bit-exact restored weights. INVALID-v1.md enumerates retained invalid cells.

## E4 — EDA baseline
Status: partial; automatic raw-counter reduction, pending operator completion check.
All acceptance cells use frozen6da2e42/vLLM0.31.0/A40, greedy, batch8, cap512. MATH is first128. Intervals are paired10,000 query/seed bootstrap95%CIs. Smoke runs are excluded. Reference rows use the identical rendered prefix of current-campaign gate cells; hashes verified.

R1-Distill-Llama:

| Variant / seed / K | Panel | n | tau [95% CI] | p1 % [95% CI] | Train GPUh |
|---|---|---:|---|---|---:|
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


Port: released additive singleton shared/private experts; shared FFN, fc, attention, norms and head frozen. Private widths4096/14336; PCA128 and90th-percentile Mahalanobis are predeclared port choices. Selected8k and random8k full-repair controls remain separate. Frozen tensor checks and FIX24 embedding proof gate production EDA evaluation.

| Standalone drafter | n | Median ms |
|---|---:|---:|
| /home/heck2/sbhansali8/ReFit/artifacts/P3_D50_20261009_0200/E1-official-native-v2-t0 | 1000 | 3.317 |
| /home/heck2/sbhansali8/ReFit/rebuttal/runs/E4_t0_train_smoke_w4096_s0/cell/export-2 | 1000 | 3.364 |
| /home/heck2/sbhansali8/ReFit/rebuttal/runs/E4_t0_train_smoke_w14336_s0/cell/export-2 | 1000 | 3.378 |
Standalone PyTorch first-draft forward:50warmup,1000measured CUDA-event steps, batch1, one-token context, no verifier. Not end-to-end speedup.

Result status: 0 completed non-reference cells in this snapshot; no unfinished outcome inferred.
GPU-hours: 0.5 completed, including failures; active runtime additional.
Sources: /home/heck2/sbhansali8/ReFit/rebuttal/E45_analysis_watch_20261124_1645/20261124_170935_022600/results.json
Failed runs retained: []

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
| offtheshelf_k2 / s0 / K2 | math128 | 128 | 2.28 [2.26, 2.31] | 73.2 [72.3, 74.1] | — |
| offtheshelf_k2 / s0 / K2 | speed128 | 128 | 2.02 [2.00, 2.05] | 62.3 [61.0, 63.6] | — |
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
| 0 / math128 | offtheshelf_k2 | reference_dedicated | 128 / 1 | 1.54 [1.49, 1.58] | 13.6 [12.9, 14.3] |
| 0 / math128 | offtheshelf_k2 | reference_full | 128 / 1 | 0.71 [0.67, 0.74] | 2.8 [1.9, 3.7] |
| 0 / math128 | offtheshelf_k2 | reference_reuse | 128 / 1 | -0.36 [-0.39, -0.33] | -23.9 [-24.9, -22.9] |
| 0 / speed128 | offtheshelf_k2 | reference_dedicated | 128 / 1 | 0.83 [0.74, 0.91] | 8.4 [5.4, 11.0] |
| 0 / speed128 | offtheshelf_k2 | reference_full | 128 / 1 | 0.50 [0.42, 0.57] | 2.2 [-0.8, 4.8] |
| 0 / speed128 | offtheshelf_k2 | reference_reuse | 128 / 1 | -0.24 [-0.28, -0.20] | -18.9 [-20.8, -17.1] |

Recipe: exact full-vocabulary forward KL,15744train/256heldout repair prompts per target, lr1e-5/2e-5 x1/3epochs. Select checkpoint by heldout tau atK4; select timing K by warm tokens/s on32heldout repair queries, separately b1/b8. Full K2–5 acceptance sweep retained. Teacher hidden-state/head factorization is exact, not top-k; lexical IDs match and export special-token aliases preserve training IDs.

Result status: 2 completed non-reference cells in this snapshot; no unfinished outcome inferred.
GPU-hours: 1.3 completed, including failures; active runtime additional.
Sources: /home/heck2/sbhansali8/ReFit/rebuttal/E45_analysis_watch_20261124_1645/20261124_170935_022600/results.json
Failed runs retained: []

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
