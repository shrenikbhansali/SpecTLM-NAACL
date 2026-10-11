# REV4 results — pilot

Owner D56. New acceptance/timing cells use frozen6da2e42 / vLLM0.31 / A40, greedy, identical rendered IDs within comparisons. Y9 separately re-analyzes historical census runs with their original commit provenance. Independent raw counters and paired confidence intervals; all outcomes retained. No manuscript edits or release promises.

## Y1 — EAGLE precision timing
All 66 processes queued: two targets, SPEED128 and first128 MATH500, batch1, three processes × three warm passes, none/reuse/interface/full/independent and R1 dedicated. Establishes precision at n128; complete; see the independently reduced P0 summary below.

## Y2 — DFlash MATH timing
All 48 processes queued: two targets, first128 MATH500, batches1/8, none/reuse/interface/full, X5 seed0 exports. Complete; independently reduced estimates and what they establish are in the live P0 summary below.

## Y3a — Nemotron thinking-on evaluation
Nine frozen acceptance cells and18 timing processes queued. Explicit detailed-thinking-on system turn, same raw questions across arms. Five decoded prompts inspected for each SPEED/MATH500/MATH32 render; loss masks are inapplicable to evaluation-only prompts. Complete; independently reduced estimates and what they establish are in the live P0 summary below.

## Y3b — Thinking-on repair
Eight2k-prompt shards queued; first shard running. Five complete decoded responses and exact masks inspected at03:00; the sealer must reproduce those exact IDs/text/masks before the recorded review can unlock training. Exact existing 16k Alpaca questions, explicit thinking-on system, cap512. Sealing and training require matching five-sample decoded/mask audit.

## Y4 — Qwen DFlash
MIT license, ungated, pinned revision9b41424b7109f9c5413454f481b09a82b85333f4 already cached. Existing pinned native converter produces block16 and taps[2,10,18,26,34]; no trainer behavior change required. E12 16k responses reused. Outcomes pending.

## Y5 — Nemotron DFlash seeds
Seeds1–2 for interface/full follow X5 seed0, with identical native objective/data. Outcomes pending.

## Y6 — Official scaling
The production plotted0.5k point is generic520, not the separate256-example component pilot. Exact existing520 responses will be reused, with n520 explicitly recorded; one epoch per D56. The old production point was200 steps, so it is not a matched-step initialization control. The64k point preserves the Alpaca+Dolly source mixture. Outcomes pending.

## Y7 — Parent supervision
Official init, identical R1 response tokens; alternate parent supplies taps and soft labels. Outcomes pending.

## Y8 — Linear alignment
R1 fit completed: n4000 responses,1,875,707 fitted token positions,1823.95s =0.507A40GPU-h, peak31.14GiB. Both LS/Procrustes exports share the identical frozen15-key body and change only fc.weight; FIX24 embedding hash matches the target exactly. Four frozen SPEED/MATH500 cells queued; acceptance pending. Nemotron fit remains queued. Per-tap least squares/orthogonal Procrustes, no affine bias, first4k audited training-response contexts. Exact block-diagonal folding into fc; no optimizer. Frozen evaluations publish after exports.

## Y9 — Census statistics
Complete CPU reduction: 163/174 checkpoints have own-domain panels (326 drafter/checkpoint rows); the 11 fallback-panel checkpoints are excluded from these pooled statistics. Multi-stage histories contribute to each applicable category. Unknown/repack/adversarial histories remain in provenance but are not assigned to the requested groups.

Both families pooled, equal checkpoint weights,10,000 hierarchical checkpoint/paired-query draws. Categories overlap for recorded multistage histories; group differences are associations. Unknown histories excluded from category means, retained in provenance. General-fallback queries excluded.

| Category | Drafter | Checkpoints | Family counts | Query pairs | p1 retention [95% CI] |
|---|---|---:|---|---:|---|
| SFT | dflash | 30 | {'llama': 11, 'qwen3': 19} | 1899 | 0.985 [0.930,1.039] |
| SFT | eagle3 | 30 | {'llama': 11, 'qwen3': 19} | 1899 | 1.052 [1.003,1.101] |
| abliteration | dflash | 30 | {'llama': 22, 'qwen3': 8} | 1920 | 0.977 [0.956,1.000] |
| abliteration | eagle3 | 30 | {'llama': 22, 'qwen3': 8} | 1920 | 0.998 [0.978,1.024] |
| distillation | dflash | 9 | {'llama': 4, 'qwen3': 5} | 576 | 1.071 [0.907,1.262] |
| distillation | eagle3 | 9 | {'llama': 4, 'qwen3': 5} | 576 | 1.141 [0.924,1.449] |
| merge | dflash | 7 | {'llama': 3, 'qwen3': 4} | 448 | 0.980 [0.947,1.017] |
| merge | eagle3 | 7 | {'llama': 3, 'qwen3': 4} | 448 | 0.992 [0.949,1.040] |
| on_policy_RL | dflash | 9 | {'llama': 1, 'qwen3': 8} | 570 | 0.995 [0.971,1.020] |
| on_policy_RL | eagle3 | 9 | {'llama': 1, 'qwen3': 8} | 570 | 1.041 [0.994,1.104] |
| preference | dflash | 17 | {'llama': 13, 'qwen3': 4} | 1087 | 0.927 [0.883,0.967] |
| preference | eagle3 | 17 | {'llama': 13, 'qwen3': 4} | 1087 | 0.959 [0.916,1.005] |
| quantization | dflash | 34 | {'llama': 11, 'qwen3': 23} | 2176 | 0.999 [0.989,1.008] |
| quantization | eagle3 | 34 | {'llama': 11, 'qwen3': 23} | 2176 | 1.001 [0.992,1.010] |

**What this establishes.** Weight transformations retain approximately all first-token acceptance on own-domain prompts. The broad distillation group does not show a reliable mean loss here (wide intervals); this workload/population does not reproduce the focused reasoning-cohort association. Neither analysis substitutes for the other.

[Focused 21-model table](../artifacts/REV4_Y9_20261011_0300/focused21.md), [CSV with identifiers, lineage, history and raw sources](../artifacts/REV4_Y9_20261011_0300/focused21.csv), [pooled estimates](../artifacts/REV4_Y9_20261011_0300/pooled.json), [provenance/filter counts](../artifacts/REV4_Y9_20261011_0300/provenance.json). No release package. Historical own-domain source commits are423d3b6 (638 unique cell paths) andf00992f (14 paths), not newly generated6da2e42 cells. All41,728 prompt records, including44 zero-step records, pass the6da2e42 raw metric validator; differences in the earlier harness concern zero-step handling/validation rather than the generation path. [Explicit provenance audit and source diffs](../artifacts/REV4_Y9_harness_audit_20261011_0340/audit.json).

## Y10 — Math-domain long-budget data
Prepared and pinned2,000 MATH-train +2,000 GSM8K-main-train questions, selected by deterministic salted hash before generation; alternate sources in fixed order. Both source cards specify MIT. One duplicate MATH question removed; no selected question overlaps the11,024 evaluation exclusions or existing Alpaca training queries. [Selection, pins, licenses and file hashes](../artifacts/REV4_Y10_queries_20261011_0315/selection.json). No dispatch yet: an explicit110-job P1 prerequisite gate includes all downstream evaluations/timing, not only initial training submissions.

Long training uses a new opt-in native SDPA attention path to avoid the6GB dense-attention backward allocation that failed for E9 at4096 tokens. Packed native TTT3 loss/metrics/gradients match eager in the bounded test; existing defaults unchanged. Frozen serving remains unchanged. Real GPU memory/performance validation remains pending. Samples will be manually inspected before training. Source cards: [MATH](https://huggingface.co/datasets/EleutherAI/hendrycks_math), [GSM8K](https://huggingface.co/datasets/openai/gsm8k).

## Operations
D47 finished-run compile-cache reclamation: artifacts/REV4_disk_cleanup_20261011_0235/manifest.jsonl;805 remaining caches removed,18 already gone from the preceding serial pass. No outputs, model weights, ledger or environments deleted. P0 stage artifacts/REV4_P0_20261011_0240. One canonical dispatcher;350GB floor. Initial P0 tests10pass; P1 tests11pass. All run tags created/pushed before immutable checkout and launch.

<!-- REV4 LIVE BEGIN -->
Updated 2026-10-11T09:16:58.075564-04:00. P0 141/141 successful; pilot.

| Experiment | Arm | Workload | n | Reuse τ | Repair τ [95% CI] | Δτ [95% CI] | Δp1 [95% CI] |
|---|---|---|---:|---:|---|---|---|
| Y3a | fc | math32-8192 | 32 | 1.676 | 2.542 [2.408,2.666] | 0.866 [0.763,0.962] | 0.233 [0.205,0.261] |
| Y3a | fc | math500 | 500 | 1.700 | 2.658 [2.638,2.680] | 0.959 [0.942,0.976] | 0.250 [0.245,0.254] |
| Y3a | fc | speed128 | 128 | 1.741 | 2.352 [2.272,2.427] | 0.610 [0.560,0.659] | 0.175 [0.159,0.189] |
| Y3a | full | math32-8192 | 32 | 1.676 | 2.688 [2.551,2.813] | 1.012 [0.906,1.111] | 0.266 [0.245,0.287] |
| Y3a | full | math500 | 500 | 1.700 | 2.855 [2.833,2.877] | 1.155 [1.136,1.175] | 0.287 [0.283,0.292] |
| Y3a | full | speed128 | 128 | 1.741 | 2.458 [2.374,2.539] | 0.717 [0.660,0.775] | 0.198 [0.181,0.214] |

All timing uses n=128, three fresh processes × three warm passes. Workloads and template modes are separate strata.

**Y1: measured full-repair speedups so far.** target0 math128 batch1: 2.318 [2.287,2.350]×; target1 math128 batch1: 2.215 [2.183,2.250]×; target0 speed128 batch1: 1.854 [1.762,1.945]×; target1 speed128 batch1: 1.837 [1.703,1.969]×. These quantify panel completion time on the specified A40 workloads; cold/startup and output-length effects are retained below.

**Y2: measured full-repair speedups so far.** target0 math128 batch1: 2.262 [2.223,2.305]×; target0 math128 batch8: 1.927 [1.872,1.977]×; target1 math128 batch1: 2.112 [2.072,2.155]×; target1 math128 batch8: 1.793 [1.756,1.830]×. These quantify panel completion time on the specified A40 workloads; cold/startup and output-length effects are retained below.

**Y3a: same-mode repair contrasts so far.** math32-8192 Δp1 0.266 [0.245,0.287], Δτ 1.012 [0.906,1.111]; math500 Δp1 0.287 [0.283,0.292], Δτ 1.155 [1.136,1.175]; speed128 Δp1 0.198 [0.181,0.214], Δτ 0.717 [0.660,0.775]. The thinking-on renders are shared across reuse and repairs.
| Experiment | Target | Batch | Arm / reference | n/processes | Warm panel speedup [95% CI] | Warm token ratio [95% CI] | Cold+startup [95% CI] |
|---|---|---:|---|---:|---|---|---|
| Y1-math128 | 0 | 1 | fc / none | 128/3 | 2.155 [2.127,2.184] | 2.154 [2.127,2.182] | 1.733 [1.679,1.776] |
| Y1-math128 | 0 | 1 | fc / reuse | 128/3 | 1.449 [1.433,1.465] | 1.451 [1.437,1.466] | 1.330 [1.293,1.368] |
| Y1-math128 | 0 | 1 | full / none | 128/3 | 2.318 [2.287,2.350] | 2.312 [2.283,2.341] | 1.841 [1.807,1.871] |
| Y1-math128 | 0 | 1 | full / reuse | 128/3 | 1.558 [1.541,1.576] | 1.557 [1.540,1.574] | 1.414 [1.367,1.456] |
| Y1-math128 | 0 | 1 | independent / none | 128/3 | 1.577 [1.551,1.603] | 1.576 [1.551,1.603] | 1.367 [1.329,1.400] |
| Y1-math128 | 0 | 1 | independent / reuse | 128/3 | 1.060 [1.044,1.077] | 1.061 [1.045,1.078] | 1.050 [1.016,1.084] |
| Y1-math128 | 0 | 1 | oracle / none | 128/3 | 2.941 [2.900,2.983] | 2.933 [2.893,2.975] | 2.107 [2.068,2.142] |
| Y1-math128 | 0 | 1 | oracle / reuse | 128/3 | 1.977 [1.948,2.007] | 1.976 [1.947,2.005] | 1.618 [1.581,1.649] |
| Y1-math128 | 0 | 1 | reuse / none | 128/3 | 1.487 [1.468,1.507] | 1.485 [1.466,1.503] | 1.302 [1.270,1.335] |
| Y1-math128 | 1 | 1 | fc / none | 128/3 | 2.069 [2.038,2.101] | 2.069 [2.038,2.101] | 1.797 [1.746,1.846] |
| Y1-math128 | 1 | 1 | fc / reuse | 128/3 | 1.873 [1.564,2.444] | 1.873 [1.564,2.444] | 1.440 [1.420,1.461] |
| Y1-math128 | 1 | 1 | full / none | 128/3 | 2.215 [2.183,2.250] | 2.215 [2.183,2.250] | 1.871 [1.834,1.910] |
| Y1-math128 | 1 | 1 | full / reuse | 128/3 | 2.006 [1.675,2.613] | 2.006 [1.675,2.613] | 1.499 [1.444,1.584] |
| Y1-math128 | 1 | 1 | independent / none | 128/3 | 1.498 [1.476,1.522] | 1.498 [1.476,1.522] | 1.412 [1.389,1.435] |
| Y1-math128 | 1 | 1 | independent / reuse | 128/3 | 1.356 [1.131,1.770] | 1.356 [1.131,1.770] | 1.131 [1.099,1.172] |
| Y1-math128 | 1 | 1 | reuse / none | 128/3 | 1.105 [0.845,1.323] | 1.105 [0.845,1.323] | 1.248 [1.202,1.286] |
| Y1-speed128 | 0 | 1 | fc / none | 128/3 | 1.786 [1.701,1.870] | 1.786 [1.701,1.870] | 1.532 [1.464,1.601] |
| Y1-speed128 | 0 | 1 | fc / reuse | 128/3 | 1.337 [1.304,1.373] | 1.333 [1.301,1.366] | 1.241 [1.211,1.272] |
| Y1-speed128 | 0 | 1 | full / none | 128/3 | 1.854 [1.762,1.945] | 1.858 [1.765,1.949] | 1.544 [1.479,1.610] |
| Y1-speed128 | 0 | 1 | full / reuse | 128/3 | 1.389 [1.350,1.428] | 1.386 [1.350,1.423] | 1.251 [1.220,1.285] |
| Y1-speed128 | 0 | 1 | independent / none | 128/3 | 1.286 [1.259,1.315] | 1.287 [1.263,1.313] | 1.113 [1.088,1.137] |
| Y1-speed128 | 0 | 1 | independent / reuse | 128/3 | 0.963 [0.937,0.991] | 0.960 [0.935,0.987] | 0.901 [0.878,0.927] |
| Y1-speed128 | 0 | 1 | oracle / none | 128/3 | 2.083 [1.971,2.191] | 2.087 [1.973,2.195] | 1.594 [1.528,1.657] |
| Y1-speed128 | 0 | 1 | oracle / reuse | 128/3 | 1.560 [1.507,1.613] | 1.557 [1.507,1.605] | 1.291 [1.259,1.324] |
| Y1-speed128 | 0 | 1 | reuse / none | 128/3 | 1.335 [1.295,1.376] | 1.340 [1.301,1.379] | 1.234 [1.199,1.270] |
| Y1-speed128 | 1 | 1 | fc / none | 128/3 | 1.745 [1.631,1.857] | 1.774 [1.679,1.870] | 1.421 [1.335,1.507] |
| Y1-speed128 | 1 | 1 | fc / reuse | 128/3 | 1.313 [1.252,1.370] | 1.339 [1.294,1.384] | 1.243 [1.202,1.282] |
| Y1-speed128 | 1 | 1 | full / none | 128/3 | 1.837 [1.703,1.969] | 1.843 [1.739,1.946] | 1.515 [1.427,1.597] |
| Y1-speed128 | 1 | 1 | full / reuse | 128/3 | 1.382 [1.326,1.436] | 1.392 [1.342,1.439] | 1.325 [1.286,1.365] |
| Y1-speed128 | 1 | 1 | independent / none | 128/3 | 1.433 [1.381,1.492] | 1.419 [1.385,1.454] | 1.235 [1.164,1.303] |
| Y1-speed128 | 1 | 1 | independent / reuse | 128/3 | 1.078 [1.035,1.129] | 1.071 [1.034,1.114] | 1.080 [1.027,1.145] |
| Y1-speed128 | 1 | 1 | reuse / none | 128/3 | 1.329 [1.268,1.392] | 1.324 [1.284,1.365] | 1.143 [1.091,1.196] |
| Y2-math128 | 0 | 1 | fc / none | 128/3 | 2.095 [2.055,2.137] | 2.098 [2.060,2.137] | 1.635 [1.587,1.682] |
| Y2-math128 | 0 | 1 | fc / reuse | 128/3 | 1.167 [1.157,1.179] | 1.167 [1.156,1.179] | 1.104 [1.074,1.130] |
| Y2-math128 | 0 | 1 | full / none | 128/3 | 2.262 [2.223,2.305] | 2.260 [2.222,2.300] | 1.605 [1.555,1.657] |
| Y2-math128 | 0 | 1 | full / reuse | 128/3 | 1.260 [1.246,1.276] | 1.257 [1.243,1.272] | 1.084 [1.060,1.111] |
| Y2-math128 | 0 | 1 | reuse / none | 128/3 | 1.795 [1.763,1.828] | 1.798 [1.766,1.831] | 1.480 [1.453,1.507] |
| Y2-math128 | 0 | 8 | fc / none | 128/3 | 1.784 [1.733,1.837] | 1.784 [1.732,1.837] | 0.767 [0.689,0.836] |
| Y2-math128 | 0 | 8 | fc / reuse | 128/3 | 1.164 [1.136,1.192] | 1.164 [1.135,1.192] | 1.113 [1.020,1.184] |
| Y2-math128 | 0 | 8 | full / none | 128/3 | 1.927 [1.872,1.977] | 1.928 [1.873,1.978] | 0.854 [0.775,0.926] |
| Y2-math128 | 0 | 8 | full / reuse | 128/3 | 1.257 [1.231,1.284] | 1.257 [1.231,1.285] | 1.240 [1.147,1.319] |
| Y2-math128 | 0 | 8 | reuse / none | 128/3 | 1.533 [1.486,1.573] | 1.533 [1.486,1.573] | 0.689 [0.653,0.725] |
| Y2-math128 | 1 | 1 | fc / none | 128/3 | 1.955 [1.921,1.993] | 1.955 [1.921,1.993] | 1.573 [1.539,1.611] |
| Y2-math128 | 1 | 1 | fc / reuse | 128/3 | 1.184 [1.175,1.194] | 1.184 [1.175,1.194] | 1.138 [1.122,1.156] |
| Y2-math128 | 1 | 1 | full / none | 128/3 | 2.112 [2.072,2.155] | 2.112 [2.072,2.155] | 1.685 [1.640,1.729] |
| Y2-math128 | 1 | 1 | full / reuse | 128/3 | 1.279 [1.269,1.290] | 1.279 [1.269,1.290] | 1.219 [1.191,1.260] |
| Y2-math128 | 1 | 1 | reuse / none | 128/3 | 1.651 [1.623,1.682] | 1.651 [1.623,1.682] | 1.383 [1.346,1.419] |
| Y2-math128 | 1 | 8 | fc / none | 128/3 | 1.684 [1.655,1.714] | 1.684 [1.655,1.714] | 0.684 [0.643,0.724] |
| Y2-math128 | 1 | 8 | fc / reuse | 128/3 | 1.178 [1.163,1.194] | 1.178 [1.163,1.194] | 0.973 [0.925,1.032] |
| Y2-math128 | 1 | 8 | full / none | 128/3 | 1.793 [1.756,1.830] | 1.793 [1.756,1.830] | 0.970 [0.927,1.003] |
| Y2-math128 | 1 | 8 | full / reuse | 128/3 | 1.254 [1.234,1.275] | 1.254 [1.234,1.275] | 1.380 [1.341,1.413] |
| Y2-math128 | 1 | 8 | reuse / none | 128/3 | 1.430 [1.404,1.458] | 1.430 [1.404,1.458] | 0.703 [0.678,0.720] |
| Y3a-math128 | 1 | 1 | fc / reuse | 128/3 | 1.572 [1.553,1.590] | 1.572 [1.553,1.590] | 1.392 [1.370,1.413] |
| Y3a-math128 | 1 | 1 | full / reuse | 128/3 | 1.685 [1.662,1.707] | 1.685 [1.662,1.707] | 1.535 [1.514,1.558] |
| Y3a-speed128 | 1 | 1 | fc / reuse | 128/3 | 1.332 [1.285,1.377] | 1.334 [1.296,1.369] | 1.225 [1.167,1.275] |
| Y3a-speed128 | 1 | 1 | full / reuse | 128/3 | 1.394 [1.329,1.460] | 1.390 [1.344,1.436] | 1.336 [1.286,1.384] |

[Raw acceptance and per-depth/length/source evidence](../artifacts/REV4_P0_live_20261011_0322/20261011_091644_963445/acceptance.json); [timing evidence](../artifacts/REV4_P0_live_20261011_0322/20261011_091644_963445/timing/results.json); [completion](../artifacts/REV4_P0_live_20261011_0322/20261011_091644_963445/progress.json).
<!-- REV4 LIVE END -->

<!-- REV4 FOLLOWUP BEGIN -->
Updated 2026-10-11T09:16:57.505103-04:00; pilot. Independent raw counters;10,000 paired seed/query draws. Training seeds and query counts explicit.

| Experiment | Target | Data | Arm / reference | Workload | n/seeds | τ [95% CI] | Δτ [95% CI] | Δp1 [95% CI] |
|---|---|---|---|---|---:|---|---|---|
| Y6 | 0 | generic520 | fc / reuse | math500 | 500/1 | 2.502 [2.485,2.520] | 0.574 [0.562,0.586] | 0.170 [0.166,0.174] |
| Y6 | 0 | generic520 | fc / reuse | speed128 | 128/1 | 2.203 [2.137,2.265] | 0.439 [0.409,0.470] | 0.142 [0.132,0.152] |
| Y6 | 0 | generic520 | full / reuse | speed128 | 128/1 | 2.344 [2.270,2.412] | 0.580 [0.543,0.617] | 0.176 [0.164,0.187] |

Timing: paired process/query-batch intervals; workloads, data budgets and thinking mode separate.
| Experiment | Target | Batch | Arm / reference | n/processes | Warm panel speedup [95% CI] | Warm token ratio [95% CI] | Cold+startup [95% CI] |
|---|---|---:|---|---:|---|---|---|
| Y4--speed128 | 2 | 8 | reuse / none | 128/3 | 0.993 [0.975,1.013] | 0.994 [0.976,1.014] | 0.743 [0.701,0.779] |

Measured per-run costs exclude unmeasured dedicated-drafter estimates. Data generation is listed separately and shared across repair arms; no zero cost is imputed for incomplete data.
| Experiment | Target | Kind | Arm | n | GPU-h |
|---|---|---|---|---:|---:|
| Y6 | 0 | train | fc | 520 | 0.096 |
| Y6 | 0 | train | full | 520 | 0.111 |
| Y3b | 1 | data |  | 2000 | 1.099 |
| Y8 | 0 | fit |  | 4000 | 0.507 |

[Raw acceptance, lengths and per-depth evidence](../artifacts/REV4_P1_live_20261011_0322/20261011_091655_724457/acceptance.json); [costs/configs](../artifacts/REV4_P1_live_20261011_0322/20261011_091655_724457/costs.json); [completion counts](../artifacts/REV4_P1_live_20261011_0322/20261011_091655_724457/progress.json).
<!-- REV4 FOLLOWUP END -->
