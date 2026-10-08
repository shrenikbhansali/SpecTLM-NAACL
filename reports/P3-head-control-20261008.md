# P3 optional head-only control — pilot

2026-10-08T16:48:43.111084-04:00, codex-1. The D-46 head-only control ran on an otherwise free A40 after native two-step and frozen eight-prompt smoke checks. All six planned evaluations are complete.

The R1-Distill-Llama family EAGLE-3 drafter was trained on the identical self-elicited 256-example data, seed 0, native TTT objective, 300-step schedule, batch plan and optimizer settings used by the fc-only component pilot. Only `lm_head.weight` was trainable (131,072,000 parameters); the target-feature interface and decoder layer were frozen. Config-field equality against the original fc run passed. Trainable-only checkpoints and shared immutable export shards used 3ad9c0c; frozen evaluation used 6da2e42/vLLM0.31.0/A40/K4, greedy, batch 8, 512 tokens and exactly the same held-out rendered IDs.

| Step | Workload / n | Δp1 vs reused [paired 95% CI] | τ | Oracle-gap recovery [paired 95% CI] | Data + training GPU-hours |
|---:|---|---|---:|---|---:|
| 50 | speed128 / 128 | +0.0364 [+0.0276, +0.0452] | 1.8010 | 6.3% [4.2%, 8.4%] | 0.291 |
| 50 | math64 / 64 | +0.0322 [+0.0222, +0.0427] | 2.0103 | 3.2% [1.7%, 4.8%] | 0.291 |
| 150 | speed128 / 128 | +0.0582 [+0.0513, +0.0649] | 1.8372 | 9.6% [7.9%, 11.1%] | 0.315 |
| 150 | math64 / 64 | +0.0497 [+0.0399, +0.0589] | 2.0557 | 5.5% [4.3%, 6.7%] | 0.315 |
| 300 | speed128 / 128 | +0.0623 [+0.0539, +0.0707] | 1.8560 | 11.2% [9.3%, 13.1%] | 0.349 |
| 300 | math64 / 64 | +0.0581 [+0.0514, +0.0651] | 2.0792 | 6.7% [5.9%, 7.6%] | 0.349 |

Head-only training improves acceptance, but its 300-step SPEED recovery is 11.2%, compared with 35.5% for the matched seed-0 fc-only run. Direct paired head-minus-fc differences are:

| Workload / n | Δp1 (head − fc) [95% CI] | Δτ (head − fc) [95% CI] |
|---|---|---|
| speed128 / 128 | -0.0910 [-0.1006, -0.0814] | -0.2712 [-0.2939, -0.2480] |
| math64 / 64 | -0.0823 [-0.0938, -0.0700] | -0.3006 [-0.3348, -0.2637] |

Intervals use 10,000 paired prompt-bootstrap draws, conditional on this single training seed. Head-only cost at 300 steps is 0.349 A40 GPU-hours including the reused data generation charged to this alternative; engineering smokes and evaluation are excluded. The smaller elapsed training cost does not make head-only a recovery match for fc. No additional head-only tuning was performed.

All per-depth rates, output lengths, hashes, original family/oracle baselines and exact matched-training fields are retained in `artifacts/P3_head_optional_20261008_1618/snapshot-20261008_163453/results.json`. Mean 300-step output lengths are 502.1 tokens on SPEED and 504.7 on MATH. The analysis recomputes counters independently of followspec and verifies the frozen commit/engine/GPU/prompt settings. Raw jobs and sources are under `artifacts/P3_head_optional_20261008_1618/`.
