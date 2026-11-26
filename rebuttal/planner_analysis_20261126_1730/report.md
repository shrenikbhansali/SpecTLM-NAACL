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

