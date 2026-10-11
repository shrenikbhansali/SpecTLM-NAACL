# REV4 results — pilot

Owner D56. Frozen 6da2e42 / vLLM0.31 / A40, greedy, identical rendered IDs within comparisons. Independent raw counters and paired confidence intervals; all outcomes retained. No manuscript edits or release promises.

## Y1 — EAGLE precision timing
All 66 processes queued: two targets, SPEED128 and first128 MATH500, batch1, three processes × three warm passes, none/reuse/interface/full/independent and R1 dedicated. Establishes precision at n128; outcomes pending.

## Y2 — DFlash MATH timing
All 48 processes queued: two targets, first128 MATH500, batches1/8, none/reuse/interface/full, X5 seed0 exports. Outcomes pending.

## Y3a — Nemotron thinking-on evaluation
Nine frozen acceptance cells and18 timing processes queued. Explicit detailed-thinking-on system turn, same raw questions across arms. Five decoded prompts inspected for each SPEED/MATH500/MATH32 render; loss masks are inapplicable to evaluation-only prompts. Outcomes pending.

## Y3b — Thinking-on repair
Implementation in progress; new data must pass five-sample decoded/mask review before training.

## Y4 — Qwen DFlash
MIT license, ungated, pinned revision9b41424b7109f9c5413454f481b09a82b85333f4 already cached. Existing pinned native converter produces block16 and taps[2,10,18,26,34]; no trainer behavior change required. E12 16k responses reused. Outcomes pending.

## Y5 — Nemotron DFlash seeds
Seeds1–2 for interface/full follow X5 seed0, with identical native objective/data. Outcomes pending.

## Y6 — Official scaling
The production plotted0.5k point is generic520, not the separate256-example component pilot. Exact existing520 responses will be reused, with n520 explicitly recorded; one epoch per D56. The old production point was200 steps, so it is not a matched-step initialization control. The64k point preserves the Alpaca+Dolly source mixture. Outcomes pending.

## Y7 — Parent supervision
Official init, identical R1 response tokens; alternate parent supplies taps and soft labels. Outcomes pending.

## Y8 — Linear alignment
Per-tap least squares/orthogonal Procrustes, no affine bias, fit only training-response contexts. Implementation in progress.

## Y9 — Census statistics
CPU pooled historical own-domain groups and focused21 per-model table; mixed histories and filter counts explicit. No supplementary/release package.

## Y10 — Math-domain long-budget data
Preparation after P0/P1 queued. No dispatch yet.

## Operations
D47 finished-run compile-cache reclamation: artifacts/REV4_disk_cleanup_20261011_0235/manifest.jsonl;805 remaining caches removed,18 already gone from the preceding serial pass. No outputs, model weights, ledger or environments deleted. P0 stage artifacts/REV4_P0_20261011_0240. One canonical dispatcher;350GB floor. Initial P0 tests10pass; P1 tests11pass. All run tags created/pushed before immutable checkout and launch.

<!-- REV4 LIVE BEGIN -->
Updated 2026-10-11T02:41:56.519927-04:00. P0 0/141 successful; pilot.

| Experiment | Arm | Workload | n | Reuse τ | Repair τ [95% CI] | Δτ [95% CI] | Δp1 [95% CI] |
|---|---|---|---:|---:|---|---|---|

All timing uses n=128, three fresh processes × three warm passes. Workloads and template modes are separate strata.
| Experiment | Target | Batch | Arm / reference | n/processes | Warm panel speedup [95% CI] | Warm token ratio [95% CI] | Cold+startup [95% CI] |
|---|---|---:|---|---:|---|---|---|

[Raw acceptance and per-depth/length/source evidence](../artifacts/REV4_P0_live_20261011_0250/20261011_024155_253198/acceptance.json); [timing evidence](../artifacts/REV4_P0_live_20261011_0250/20261011_024155_253198/timing/results.json); [completion](../artifacts/REV4_P0_live_20261011_0250/20261011_024155_253198/progress.json).
<!-- REV4 LIVE END -->
