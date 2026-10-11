# REV4 results — pilot

Owner D56. New acceptance/timing cells use frozen6da2e42 / vLLM0.31 / A40, greedy, identical rendered IDs within comparisons. Y9 separately re-analyzes historical census runs with their original commit provenance. Independent raw counters and paired confidence intervals; all outcomes retained. No manuscript edits or release promises.

## Y1 — EAGLE precision timing
All 66 processes queued: two targets, SPEED128 and first128 MATH500, batch1, three processes × three warm passes, none/reuse/interface/full/independent and R1 dedicated. Establishes precision at n128; outcomes pending.

## Y2 — DFlash MATH timing
All 48 processes queued: two targets, first128 MATH500, batches1/8, none/reuse/interface/full, X5 seed0 exports. Outcomes pending.

## Y3a — Nemotron thinking-on evaluation
Nine frozen acceptance cells and18 timing processes queued. Explicit detailed-thinking-on system turn, same raw questions across arms. Five decoded prompts inspected for each SPEED/MATH500/MATH32 render; loss masks are inapplicable to evaluation-only prompts. Outcomes pending.

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
Two paired fits queued; R1 fitting started. Per-tap least squares/orthogonal Procrustes, no affine bias, first4k audited training-response contexts. Exact block-diagonal folding into fc; no optimizer. Frozen evaluations publish after exports.

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
Updated 2026-10-11T03:02:04.499619-04:00. P0 0/141 successful; pilot.

| Experiment | Arm | Workload | n | Reuse τ | Repair τ [95% CI] | Δτ [95% CI] | Δp1 [95% CI] |
|---|---|---|---:|---:|---|---|---|

All timing uses n=128, three fresh processes × three warm passes. Workloads and template modes are separate strata.
| Experiment | Target | Batch | Arm / reference | n/processes | Warm panel speedup [95% CI] | Warm token ratio [95% CI] | Cold+startup [95% CI] |
|---|---|---:|---|---:|---|---|---|

[Raw acceptance and per-depth/length/source evidence](../artifacts/REV4_P0_live_20261011_0315/20261011_030202_291708/acceptance.json); [timing evidence](../artifacts/REV4_P0_live_20261011_0315/20261011_030202_291708/timing/results.json); [completion](../artifacts/REV4_P0_live_20261011_0315/20261011_030202_291708/progress.json).
<!-- REV4 LIVE END -->

<!-- REV4 FOLLOWUP BEGIN -->
Updated 2026-10-11T03:13:15.763854-04:00; pilot. Independent raw counters;10,000 paired seed/query draws. Training seeds and query counts explicit.

| Experiment | Target | Data | Arm / reference | Workload | n/seeds | τ [95% CI] | Δτ [95% CI] | Δp1 [95% CI] |
|---|---|---|---|---|---:|---|---|---|

Timing: paired process/query-batch intervals; workloads, data budgets and thinking mode separate.
| Experiment | Target | Batch | Arm / reference | n/processes | Warm panel speedup [95% CI] | Warm token ratio [95% CI] | Cold+startup [95% CI] |
|---|---|---:|---|---:|---|---|---|

Measured per-run costs exclude unmeasured dedicated-drafter estimates. Data generation is listed separately and shared across repair arms; no zero cost is imputed for incomplete data.
| Experiment | Target | Kind | Arm | n | GPU-h |
|---|---|---|---|---:|---:|

[Raw acceptance, lengths and per-depth evidence](../artifacts/REV4_P1_live_20261011_0340/20261011_031314_188852/acceptance.json); [costs/configs](../artifacts/REV4_P1_live_20261011_0340/20261011_031314_188852/costs.json); [completion counts](../artifacts/REV4_P1_live_20261011_0340/20261011_031314_188852/progress.json).
<!-- REV4 FOLLOWUP END -->
