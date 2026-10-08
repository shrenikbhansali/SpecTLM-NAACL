# Nemotron reasoning toggle — pilot

Same Nemotron weights and 128 raw SPEED queries, system-prompt reasoning on versus off. Each arm uses its own prescribed rendered IDs; this intentionally changes the prompt. Frozen `6da2e42`, vLLM 0.31.0, A40, greedy seed 0, batch 8 and 512 new tokens. EAGLE-3 K4 and DFlash K10 remain fixed within each comparison.

| Drafter | n | p1 off → on | Δp1 [paired 95% CI] | τ off → on | Δτ [paired 95% CI] | Mean tokens off → on |
|---|---:|---|---|---|---|---|
| EAGLE-3 | 128 | .4654 → .4358 | −.0296 [−.0437, −.0157] | 1.9202 → 1.8019 | −.1184 [−.1645, −.0729] | 315.7 → 358.8 |
| DFlash | 128 | .5264 → .4986 | −.0278 [−.0448, −.0113] | 2.2319 → 2.0477 | −.1842 [−.2584, −.1130] | 316.0 → 358.7 |

The intervention lowers p1 for both drafters. It also changes output length and content. Only 35–36% of on-arm completions contain the literal `<think>` marker, versus 0.8% off; the system toggle is not a perfect reasoning-text classifier. This is evidence about the specified prompt intervention, not an isolated causal effect of reasoning text or a replacement for the fixed-prefix crossover.

Independent counter reconstruction and 10,000 paired-query bootstrap draws (seed 0): `artifacts/P2_toggle_report_20261008_1512/{analyze.py,results.json,table.md}`. Code checks target/drafter/engine settings and identical raw-query identities. Per-query lengths, paired uncertainty and source hashes are retained. Study figures, with source hashes and PDF/SVG/PNG exports: `artifacts/STUDY_figures_20261008_1530/`. The companion P2 figure reports HF agreement, not online acceptance; the P3 figure explicitly labels RMS calibration as training-free.
