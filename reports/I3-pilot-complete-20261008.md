# Exploratory independent-drafter repair pilot — completed 2026-10-08

All 44 native evaluation pairs completed (88 cells, 64 fixed prompts/cell), alongside 23 short training exports. Training uses 128 synthetic examples, 32 optimizer steps, one seed. This is a development pilot; the owner selects the direction.

## Per-child repair

Changes below are versus the untouched 1B drafter on the same child; 95% paired prompt-bootstrap intervals (2,000 resamples).

| Target | LoRA Δ position-1 acceptance | LoRA Δ τ |
| --- | ---: | ---: |
| CharlesLi/llama_3_gsm8k_gold_answer | +0.068 [+0.004, +0.134] | +0.080 [-0.085, +0.246] |
| CharlesLi/llama_3_alpaca_per_class_reflect | +0.129 [+0.097, +0.160] | +0.633 [+0.475, +0.794] |
| watt-ai/watt-tool-8B | +0.076 [+0.038, +0.116] | +0.357 [+0.214, +0.506] |
| mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated | +0.009 [-0.008, +0.025] | +0.075 [+0.024, +0.128] |
| tohur/natsumura-storytelling-rp-1.0-llama-3.1-8b | +0.093 [+0.072, +0.115] | +0.355 [+0.283, +0.430] |

Base-distilled controls are near zero or negative on these children. The target-specific LoRA gains are concentrated on alpaca, tool-use and storytelling; GSM8K has positive first-position change but uncertain τ. The abliterated target has a small τ gain and an uncertain first-position change.

## Reuse and cheap ranking

| Recipient | Donors | Probe/native p1 Spearman | Probe/native τ Spearman | Proxy-selected Δ τ |
| --- | ---: | ---: | ---: | ---: |
| 0 | 7 | 0.750 | 0.357 | -0.129 [-0.282, +0.003] |
| 4 | 7 | 0.643 | 0.429 | +0.014 [-0.034, +0.059] |
| 5 | 8 | 0.762 | 0.262 | +0.019 [-0.049, +0.107] |

The 22 cross-child donor pairs are mostly near null; alpaca→GSM8K is a large regression (Δp1 −0.213, Δτ −0.535). Leave-recipient-out pooled controls are near null on GSM8K and storytelling. Pooling that includes the recipient improves alpaca/storytelling, but it does not establish transfer. The 32-query proxy can rank some donors without producing useful transfer; no reliable reuse claim follows.

## Head-only comparison

| Target | Head Δ p1 | Head Δ τ |
| --- | ---: | ---: | ---: |
| CharlesLi/llama_3_gsm8k_gold_answer | -0.040 [-0.101, +0.021] | -0.149 [-0.314, +0.014] |
| CharlesLi/llama_3_alpaca_per_class_reflect | +0.072 [+0.038, +0.105] | +0.260 [+0.110, +0.405] |
| watt-ai/watt-tool-8B | -0.003 [-0.048, +0.040] | -0.124 [-0.292, +0.041] |
| tohur/natsumura-storytelling-rp-1.0-llama-3.1-8b | +0.053 [+0.029, +0.080] | +0.128 [+0.058, +0.204] |

Head-only helps alpaca/storytelling less than LoRA in this pilot; GSM8K/tool-use are negative or uncertain. No added seeds or 512-example expansion were run.

## Evidence and limitations

- Raw-derived complete results: `artifacts/I3_pilot_20261008_0030/automatic-reports/snapshot-12-1791438300117089992/results.json`; input hashes in the adjacent `inputs.json`.
- Transfer ranking: `artifacts/I3_pilot_20261008_0030/automatic-reports/transfer-12/results.json`.
- Data, decoded samples/masks, matched child/base trimming and leave-recipient-out manifests remain under `artifacts/I3_pilot_20261008_0030/`.
- Frozen vLLM 0.31.0 / independent-drafter harness959b003; K4, greedy, fresh compile. No post-cutoff training or target selection.
- Synthetic response correctness is unchecked; errors, truncation and domain-specific content remain. Some short-answer children change output lengths across fresh compilations. Token budgets differ between pooled and single-donor data. These acceptance gains are not throughput or task-quality claims.
- All outcomes, including nulls and regressions, remain in EXP-ATL-014 and raw artifacts.
