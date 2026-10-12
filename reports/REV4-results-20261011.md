# REV4 results — pilot

Owner D56. New acceptance/timing cells use frozen6da2e42 / vLLM0.31 / A40, greedy, identical rendered IDs within comparisons. Y9 separately re-analyzes historical census runs with their original commit provenance. Independent raw counters and paired confidence intervals; all outcomes retained. No manuscript edits or release promises.

## Y1 — EAGLE precision timing
All 66 processes queued: two targets, SPEED128 and first128 MATH500, batch1, three processes × three warm passes, none/reuse/interface/full/independent and R1 dedicated. Establishes precision at n128; complete; see the independently reduced P0 summary below.

## Y2 — DFlash MATH timing
All 48 processes queued: two targets, first128 MATH500, batches1/8, none/reuse/interface/full, X5 seed0 exports. Complete; independently reduced estimates and what they establish are in the live P0 summary below.

## Y3a — Nemotron thinking-on evaluation
Nine frozen acceptance cells and18 timing processes queued. Explicit detailed-thinking-on system turn, same raw questions across arms. Five decoded prompts inspected for each SPEED/MATH500/MATH32 render; loss masks are inapplicable to evaluation-only prompts. Complete; independently reduced estimates and what they establish are in the live P0 summary below.

## Y3b — Thinking-on repair
All eight2k-prompt shards completed (16k total;8.71A40GPU-h summed generation). Both repair trainings hit the350GB disk guard and were restarted unchanged in new directories at13:45ET. Five complete decoded responses and exact masks inspected at03:00; the sealer must reproduce those exact IDs/text/masks before the recorded review can unlock training. Exact existing 16k Alpaca questions, explicit thinking-on system, cap512. Sealing and training require matching five-sample decoded/mask audit.

## Y4 — Qwen DFlash
MIT license, ungated, pinned revision9b41424b7109f9c5413454f481b09a82b85333f4 already cached. Existing pinned native converter produces block16 and taps[2,10,18,26,34]; no trainer behavior change required. E12 16k responses reused. Acceptance is complete and regresses: full Δτ −0.196 [−0.243,−0.157] on SPEED128 and −0.324 [−0.348,−0.300] on MATH500; interface also regresses (table below). What this establishes: this fixed native recipe does not transfer its Llama-family repair benefit to Qwen DFlash. Six batch1 timing processes require disk-interruption retries; batch8 completed.

## Y5 — Nemotron DFlash seeds
Complete, pooled with X5seed0 (3seeds). Full Δτ is0.499 [0.458,0.543] on SPEED128,0.626 [0.613,0.639] on MATH500,0.494 [0.324,0.604] on MATH32@8192. Interface also improves allthree panels. What this establishes: Nemotron DFlash repair gains reproduce across seeds and persist on longer math traces.

## Y6 — Official scaling
The production plotted0.5k point is generic520, not the separate256-example component pilot. Exact existing520 responses will be reused, with n520 explicitly recorded; one epoch per D56. The old production point was200 steps, so it is not a matched-step initialization control. The64k point preserves the Alpaca+Dolly source mixture; both trainings stopped at the disk floor after4320/4482 of18448steps and restart unchanged (no optimizer restart state saved). The520-example point is complete: full Δτ0.580 [0.543,0.617] SPEED128 and0.765 [0.752,0.779] MATH500; interface0.439/0.574. What this establishes: measurable gains are already present at520examples; the64k scaling conclusion remains pending.

## Y7 — Parent supervision
Both trainings complete. Interface evaluation complete; full evaluations recovered from a disk-refused publication and running. On SPEED128 the parent-supervised interface gains Δτ0.349 [0.322,0.377] over reuse, but is0.290 [0.259,0.319] below derivative-supervised interface; on MATH500 the corresponding shortfall is0.392 [0.380,0.403]. What this establishes: adapting to the derivative text with parent supervision helps, and derivative supervision adds a further gain at16k; this is not a feature-only causal decomposition.

## Y8 — Linear alignment
Both fits and all eight evaluations complete. R1 fit: n4000responses,1,875,707positions,0.507A40GPU-h,31.14GiBpeak; Nemotron0.334GPU-h. Exports change onlyfc.weight and retain the FIX24 target embedding. R1 Procrustes improves Δτ0.144 [0.121,0.167] SPEED128 and0.166 [0.157,0.176] MATH500; least squares regresses. Both mappings regress on Nemotron. What this establishes: the uncentered linear-map baselines do not provide a reliable replacement for native-objective repair across targets. Exact per-tap paired-pass maps and block-diagonal folding; no optimizer.

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
Updated 2026-10-12T04:53:01.608929-04:00; pilot. Independent raw counters;10,000 paired seed/query draws. Training seeds and query counts explicit.

| Experiment | Target | Data | Arm / reference | Workload | n/seeds | τ [95% CI] | Δτ [95% CI] | Δp1 [95% CI] |
|---|---|---|---|---|---:|---|---|---|
| Y3b | 1 | thinking16k | fc / reuse | math32-8192 | 32/1 | 2.556 [2.423,2.678] | 0.880 [0.777,0.976] | 0.234 [0.207,0.262] |
| Y3b | 1 | thinking16k | fc / reuse | math500 | 500/1 | 2.678 [2.657,2.699] | 0.978 [0.962,0.995] | 0.254 [0.250,0.258] |
| Y3b | 1 | thinking16k | fc / reuse | speed128 | 128/1 | 2.368 [2.288,2.445] | 0.627 [0.575,0.679] | 0.180 [0.165,0.195] |
| Y3b | 1 | thinking16k | full / reuse | math32-8192 | 32/1 | 2.731 [2.586,2.862] | 1.055 [0.939,1.156] | 0.276 [0.250,0.301] |
| Y3b | 1 | thinking16k | full / reuse | math500 | 500/1 | 2.869 [2.847,2.892] | 1.170 [1.150,1.190] | 0.289 [0.285,0.294] |
| Y3b | 1 | thinking16k | full / reuse | speed128 | 128/1 | 2.491 [2.402,2.575] | 0.750 [0.685,0.813] | 0.210 [0.192,0.227] |
| Y4 | 2 | generic16k | fc / reuse | math500 | 500/1 | 2.821 [2.778,2.865] | -0.398 [-0.423,-0.374] | -0.102 [-0.106,-0.097] |
| Y4 | 2 | generic16k | fc / reuse | speed128 | 128/1 | 1.937 [1.855,2.025] | -0.245 [-0.290,-0.204] | -0.088 [-0.097,-0.078] |
| Y4 | 2 | generic16k | full / reuse | math500 | 500/1 | 2.895 [2.850,2.941] | -0.324 [-0.348,-0.300] | -0.087 [-0.092,-0.083] |
| Y4 | 2 | generic16k | full / reuse | speed128 | 128/1 | 1.985 [1.901,2.074] | -0.196 [-0.243,-0.157] | -0.074 [-0.083,-0.066] |
| Y5 | 1 | generic16k | fc / reuse | math32-8192 | 32/3 | 2.729 [2.648,2.815] | 0.315 [0.152,0.423] | 0.105 [0.088,0.119] |
| Y5 | 1 | generic16k | fc / reuse | math500 | 500/3 | 2.590 [2.568,2.613] | 0.420 [0.407,0.432] | 0.136 [0.133,0.139] |
| Y5 | 1 | generic16k | fc / reuse | speed128 | 128/3 | 2.439 [2.355,2.528] | 0.362 [0.326,0.398] | 0.125 [0.114,0.135] |
| Y5 | 1 | generic16k | full / reuse | math32-8192 | 32/3 | 2.908 [2.819,2.997] | 0.494 [0.324,0.604] | 0.136 [0.115,0.154] |
| Y5 | 1 | generic16k | full / reuse | math500 | 500/3 | 2.796 [2.771,2.822] | 0.626 [0.613,0.639] | 0.177 [0.174,0.181] |
| Y5 | 1 | generic16k | full / reuse | speed128 | 128/3 | 2.576 [2.484,2.672] | 0.499 [0.458,0.543] | 0.150 [0.139,0.161] |
| Y6 | 0 | generic520 | fc / reuse | math500 | 500/1 | 2.502 [2.485,2.520] | 0.574 [0.562,0.586] | 0.170 [0.166,0.174] |
| Y6 | 0 | generic520 | fc / reuse | speed128 | 128/1 | 2.203 [2.137,2.265] | 0.439 [0.409,0.470] | 0.142 [0.132,0.152] |
| Y6 | 0 | generic520 | full / reuse | math500 | 500/1 | 2.693 [2.675,2.712] | 0.765 [0.752,0.779] | 0.209 [0.205,0.213] |
| Y6 | 0 | generic520 | full / reuse | speed128 | 128/1 | 2.344 [2.270,2.412] | 0.580 [0.543,0.617] | 0.176 [0.164,0.187] |
| Y6 | 0 | generic64k | fc / reuse | math500 | 500/1 | 2.874 [2.853,2.895] | 0.946 [0.930,0.962] | 0.247 [0.242,0.252] |
| Y6 | 0 | generic64k | fc / reuse | speed128 | 128/1 | 2.484 [2.405,2.559] | 0.720 [0.676,0.763] | 0.211 [0.198,0.223] |
| Y6 | 0 | generic64k | full / reuse | math500 | 500/1 | 3.067 [3.043,3.090] | 1.139 [1.119,1.158] | 0.278 [0.273,0.283] |
| Y6 | 0 | generic64k | full / reuse | speed128 | 128/1 | 2.622 [2.534,2.703] | 0.858 [0.802,0.911] | 0.235 [0.221,0.250] |
| Y7 | 0 | parent16k | fc / reuse | math500 | 500/1 | 2.382 [2.365,2.400] | 0.454 [0.443,0.464] | 0.141 [0.137,0.145] |
| Y7 | 0 | parent16k | fc / child16k | math500 | 500/1 | 2.382 [2.365,2.400] | -0.392 [-0.403,-0.380] | -0.087 [-0.091,-0.083] |
| Y7 | 0 | parent16k | fc / reuse | speed128 | 128/1 | 2.113 [2.049,2.174] | 0.349 [0.322,0.377] | 0.120 [0.110,0.129] |
| Y7 | 0 | parent16k | fc / child16k | speed128 | 128/1 | 2.113 [2.049,2.174] | -0.290 [-0.319,-0.259] | -0.073 [-0.082,-0.064] |
| Y7 | 0 | parent16k | full / reuse | math500 | 500/1 | 2.572 [2.553,2.591] | 0.644 [0.630,0.658] | 0.186 [0.181,0.190] |
| Y7 | 0 | parent16k | full / child16k | math500 | 500/1 | 2.572 [2.553,2.591] | -0.397 [-0.411,-0.383] | -0.076 [-0.079,-0.072] |
| Y7 | 0 | parent16k | full / reuse | speed128 | 128/1 | 2.222 [2.154,2.286] | 0.458 [0.424,0.491] | 0.152 [0.141,0.163] |
| Y7 | 0 | parent16k | full / child16k | speed128 | 128/1 | 2.222 [2.154,2.286] | -0.314 [-0.340,-0.288] | -0.069 [-0.076,-0.062] |
| Y8 | 0 |  | ls / reuse | math500 | 500/1 | 1.561 [1.550,1.572] | -0.367 [-0.376,-0.358] | -0.161 [-0.164,-0.157] |
| Y8 | 0 |  | ls / reuse | speed128 | 128/1 | 1.440 [1.412,1.470] | -0.324 [-0.347,-0.299] | -0.142 [-0.153,-0.132] |
| Y8 | 0 |  | procrustes / reuse | math500 | 500/1 | 2.094 [2.080,2.109] | 0.166 [0.157,0.176] | 0.046 [0.042,0.050] |
| Y8 | 0 |  | procrustes / reuse | speed128 | 128/1 | 1.907 [1.856,1.959] | 0.144 [0.121,0.167] | 0.046 [0.038,0.055] |
| Y8 | 1 |  | ls / reuse | math500 | 500/1 | 1.588 [1.578,1.598] | -0.099 [-0.106,-0.092] | -0.061 [-0.064,-0.057] |
| Y8 | 1 |  | ls / reuse | speed128 | 128/1 | 1.555 [1.517,1.593] | -0.208 [-0.241,-0.177] | -0.082 [-0.094,-0.071] |
| Y8 | 1 |  | procrustes / reuse | math500 | 500/1 | 1.623 [1.613,1.632] | -0.064 [-0.071,-0.056] | -0.025 [-0.028,-0.022] |
| Y8 | 1 |  | procrustes / reuse | speed128 | 128/1 | 1.679 [1.633,1.725] | -0.084 [-0.104,-0.064] | -0.020 [-0.029,-0.012] |

Timing: paired process/query-batch intervals; workloads, data budgets and thinking mode separate.
| Experiment | Target | Batch | Arm / reference | n/processes | Warm panel speedup [95% CI] | Warm token ratio [95% CI] | Cold+startup [95% CI] |
|---|---|---:|---|---:|---|---|---|
| Y3b-thinking16k-math500 | 1 | 1 | fc / reuse | 128/3 | 1.585 [1.566,1.605] | 1.585 [1.566,1.605] | 1.580 [1.520,1.678] |
| Y3b-thinking16k-math500 | 1 | 1 | full / reuse | 128/3 | 1.691 [1.669,1.712] | 1.691 [1.669,1.712] | 1.734 [1.712,1.756] |
| Y3b-thinking16k-speed128 | 1 | 1 | fc / reuse | 128/3 | 1.348 [1.283,1.414] | 1.340 [1.297,1.381] | 1.422 [1.336,1.518] |
| Y3b-thinking16k-speed128 | 1 | 1 | full / reuse | 128/3 | 1.406 [1.351,1.457] | 1.406 [1.359,1.450] | 1.505 [1.454,1.553] |
| Y4-generic16k-speed128 | 2 | 1 | fc / none | 128/3 | 1.400 [1.355,1.449] | 1.402 [1.358,1.449] | 1.514 [1.369,1.723] |
| Y4-generic16k-speed128 | 2 | 1 | fc / reuse | 128/3 | 0.898 [0.887,0.906] | 0.900 [0.892,0.908] | 1.112 [1.101,1.126] |
| Y4-generic16k-speed128 | 2 | 1 | full / none | 128/3 | 1.447 [1.399,1.498] | 1.447 [1.401,1.498] | 1.558 [1.405,1.789] |
| Y4-generic16k-speed128 | 2 | 1 | full / reuse | 128/3 | 0.928 [0.915,0.941] | 0.929 [0.919,0.939] | 1.145 [1.126,1.163] |
| Y4-generic16k-speed128 | 2 | 1 | reuse / none | 128/3 | 1.559 [1.506,1.620] | 1.557 [1.504,1.616] | 1.361 [1.232,1.546] |
| Y4-generic16k-speed128 | 2 | 8 | fc / none | 128/3 | 0.903 [0.883,0.924] | 0.902 [0.882,0.924] | 0.894 [0.873,0.914] |
| Y4-generic16k-speed128 | 2 | 8 | fc / reuse | 128/3 | 0.909 [0.892,0.923] | 0.907 [0.890,0.922] | 1.203 [1.142,1.273] |
| Y4-generic16k-speed128 | 2 | 8 | full / none | 128/3 | 0.924 [0.903,0.946] | 0.924 [0.901,0.946] | 0.939 [0.907,0.977] |
| Y4-generic16k-speed128 | 2 | 8 | full / reuse | 128/3 | 0.930 [0.910,0.948] | 0.929 [0.909,0.946] | 1.263 [1.175,1.393] |
| Y4-generic16k-speed128 | 2 | 8 | reuse / none | 128/3 | 0.993 [0.975,1.013] | 0.994 [0.976,1.014] | 0.743 [0.701,0.779] |
| Y6-generic64k-speed128 | 0 | 1 | fc / none | 128/3 | 1.459 [1.072,1.865] | 1.464 [1.070,1.878] | 1.594 [1.422,1.751] |
| Y6-generic64k-speed128 | 0 | 1 | fc / reuse | 128/3 | 1.092 [0.795,1.380] | 1.092 [0.794,1.377] | 1.291 [1.151,1.407] |
| Y6-generic64k-speed128 | 0 | 1 | full / none | 128/3 | 1.905 [1.802,2.007] | 1.911 [1.807,2.012] | 1.784 [1.695,1.869] |
| Y6-generic64k-speed128 | 0 | 1 | full / reuse | 128/3 | 1.426 [1.381,1.472] | 1.426 [1.382,1.469] | 1.445 [1.398,1.494] |
| Y6-generic64k-speed128 | 0 | 1 | reuse / none | 128/3 | 1.335 [1.295,1.376] | 1.340 [1.301,1.379] | 1.234 [1.199,1.270] |

Measured per-run costs exclude unmeasured dedicated-drafter estimates. Data generation is listed separately and shared across repair arms; no zero cost is imputed for incomplete data.
| Experiment | Target | Kind | Arm | n | GPU-h |
|---|---|---|---|---:|---:|
| Y4 | 2 | train | fc | 16000 | 1.922 |
| Y4 | 2 | train | full | 16000 | 2.074 |
| Y6 | 0 | train | fc | 520 | 0.096 |
| Y6 | 0 | train | full | 520 | 0.111 |
| Y7 | 0 | train | fc | 16000 | 2.473 |
| Y7 | 0 | train | full | 16000 | 2.484 |
| Y5 | 1 | train | fc | 16000 | 0.911 |
| Y5 | 1 | train | full | 16000 | 1.079 |
| Y5 | 1 | train | fc | 16000 | 0.911 |
| Y5 | 1 | train | full | 16000 | 1.078 |
| Y3b | 1 | data |  | 2000 | 1.099 |
| Y3b | 1 | data |  | 2000 | 1.082 |
| Y3b | 1 | data |  | 2000 | 1.086 |
| Y3b | 1 | data |  | 2000 | 1.088 |
| Y3b | 1 | data |  | 2000 | 1.089 |
| Y3b | 1 | data |  | 2000 | 1.089 |
| Y3b | 1 | data |  | 2000 | 1.082 |
| Y3b | 1 | data |  | 2000 | 1.093 |
| Y8 | 0 | fit |  | 4000 | 0.507 |
| Y8 | 1 | fit |  | 4000 | 0.334 |
| Y6 | 0 | train | fc | 64000 | 8.056 |
| Y6 | 0 | train | full | 64000 | 9.085 |
| Y3b | 1 | train | fc | 16000 | 1.303 |
| Y3b | 1 | train | full | 16000 | 1.695 |

[Raw acceptance, lengths and per-depth evidence](../artifacts/REV4_P1_live_20261011_1555/20261012_045228_886604/acceptance.json); [costs/configs](../artifacts/REV4_P1_live_20261011_1555/20261012_045228_886604/costs.json); [completion counts](../artifacts/REV4_P1_live_20261011_1555/20261012_045228_886604/progress.json).
<!-- REV4 FOLLOWUP END -->

## Recovery update — 2026-10-11T13:47:22.648660-04:00
P0 all141jobs successful, completed09:17ET. Ten P1jobs stopped at350GB guard around11:27 (four trainings,six timing); this was a storage interruption, not an OOM. D47 completed optimizer-state reclamation removed39 optimizer_state_dict.pt files (70.369GB), with hashes and exit0/results proofs in [manifest](../artifacts/REV4_disk_state_cleanup_20261011_1350/manifest.json); no weights/configs/results/records removed. Free space~420GB. Allten unchanged retries launched13:44–13:45 in [new immutable stage](../artifacts/REV4_disk_retries_20261011_1345/recovery-proof.json). Two Y7full evaluation jobs also launched. Old failures remain on disk; paired reductions resolve explicit replacement identities and never mix partial attempts. The interrupted attempts consumed approximately7.19 allocated training GPU-h and3.21 timing GPU-h (queue launch-to-exit, including setup), additional operational cost to the completed-run costs below. No budget or seed selection changed. Official64k training+evaluation ETA Mon01–03ET, conditional on current throughput; P1deadline is at risk. Y10 waits mandatory P1 publication and still requires actual new response/mask inspection.

## Followup — 2026-10-11 15:54 ET
**Y3b acceptance complete.** Thinking-on regenerated16k repairs retain large improvements with one training seed: full Δτ0.750[0.685,0.813] SPEED128,1.170[1.150,1.190] MATH500,1.055[0.939,1.156] MATH32@8192. Absolute long-panel τ rises1.676→2.731; p1 gains0.276[0.250,0.301]. Interface also improves allthree. This establishes successful repair with the mode-matched data recipe; differences relative to Y3a are not yet a separately tested paired claim. Timing remains underway.

**Y7 complete, both arms.** Same derivative tokens with parent supervision improve τ, but derivative supervision adds0.314[0.288,0.340] SPEED128 and0.397[0.383,0.411] MATH500 for full repair, and0.290[0.259,0.319]/0.392[0.380,0.403] for interface. This supports an incremental benefit of derivative supervision beyond text adaptation. Features and policy supervision change together here, so this control does not separate their individual contributions.

**Y4 timing complete.** All24processes successful after six disk retries. Full repair b1 speedup1.447[1.399,1.498] vs no-spec compared with reuse1.559[1.506,1.620]; paired full/reuse0.928[0.915,0.941]. Atb8 full0.924[0.903,0.946] vs no-spec, and0.930[0.910,0.948] vs reuse. Interface is also slower than reuse. Both acceptance and timing regress on this fixed QwenDFlash recipe. A CPU report grouping bug kept the no-data-label controls apart from generic16k repair arms; corrected with failing-then-passing test and independent raw reduction. No generation code/config/results changed. There are10mandatory Y4timing contrasts (five perbatch), not14; completion bookkeeping corrected to the actual declared four-arm matrix. Evidence: artifacts/REV4_P1_live_20261011_1555/20261011_155224_596831.

**Operations.** One new Y3binterface SPEED timing startup failed on srv2:0 with3.54GiBfree against31.09GiBrequired. Immutable same-settings retry published and launched on srv4:3 at15:51, artifacts/REV4_collision_retry_20261011_1553; failure retained. Disk~392GB,350GBguard unchanged. Both64ktrainings healthy,4771/4229 of18448steps at15:51. OvernightETA remains provisional; Y10 publication remains gated on64kexports.

## Overnight completion — 2026-10-12T13:32:17.767098-04:00
**P1 complete, pilot review.** Explicit audit found110/110 active logical jobs successful after preserving/replacing failed attempts;40acceptance contrasts and19timing contrasts independently reduced. [Completion evidence](../artifacts/REV4_status_20261012_1335/P1-proof.json). The automated completion check expected fourY6timing contrasts, but the reducer correctly emits an additional reuse/none reference, giving five. Manual audit verifies allrequiredoutputs; no scientific threshold changed.

**64k versus16k, paired seed0.** Official R1 interface τ2.484 on SPEED128 and2.874 on MATH500; full2.622 and3.067. Independent paired raw-counter comparison to16k gives interface Δτ0.0816[0.0577,0.1054] SPEED and0.1005[0.0889,0.1117] MATH; full0.0859[0.0604,0.1105] SPEED and0.0978[0.0846,0.1109] MATH. n128/500, one seed each. [Paired source evidence](../artifacts/REV4_status_20261012_1335/64k-vs16k.json). Gains are modest and positive;64k includes the Alpaca+Dolly source-mixture change, so this is not an isolated data-volume intervention. Training wall cost8.056A40GPU-h interface,9.085full, excluding shared data generation and previously disclosed interrupted attempts.

**64k timing.** Full SPEED128 b1 measured speedup1.905[1.802,2.007] over no-spec,1.426[1.381,1.472] over reuse; threeprocesses×threewarmpasses. Interface1.459[1.072,1.865] over no-spec has wide between-process variation; its versusreuse interval includes1. Do not present its latency gain as established.

**Thinking-on timing complete.** Mode-matched16k Nemotron full runs1.406[1.351,1.457]× faster than reuse on SPEED128 and1.691[1.669,1.712]× on MATH128; interface1.348[1.283,1.414] and1.585[1.566,1.605]. These are ratios versus reused drafter, not versus no speculation.

**Y10 not complete.** All16responsejobs failed:12query-count shortfalls after the inherited length filter rejected1–5of500questions, fourengine-startup memory failures. The4000-query CPU selection had checked token-budget fit and dedup but not the responsegenerator's character-length filter. No completed math-response dataset or Y10repair exists; no GPUjobs currentlyactive. Disk351GB is barely above350GBfloor. P2markedblocked; next recovery must preflight the exactgeneratorfilter, select replacements deterministically from licensed training splits, preserve4000total/sourcebalance/evalexclusions, use fresh outputs and inspectfiveactualresponses/masks beforetraining. No evaluation or failedartifact removed.
