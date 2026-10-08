# Dedicated EAGLE-3 training cost: A40-equivalent estimate

**This is a recipe-scale projection, not a measurement of the released oracle checkpoint’s training cost.** Its actual admitted data, epochs and timing are unavailable. The estimate is useful as a sensitivity analysis; it cannot establish an exact repair-versus-oracle cost ratio.

The [EAGLE-3 paper, §4](https://arxiv.org/html/2503.01840v3#S4) lists approximately 68k ShareGPT and 464k UltraChat entries, target-generated responses, and additional OpenThoughts-114k-math data for the R1 drafter. The exact admitted math subset is unspecified. We therefore bracket nominal dataset sizes at 532k–646k; 646k assumes all 114k additional entries.

The [pinned public training script](https://github.com/SafeAILab/EAGLE/blob/cb7e0841fe0c206c6ed74a197ad5e2a1f13f5a2b/eagle/traineagle3/main.py#L19) defaults to 40 epochs and a 2048-token truncation cap. This is a code default, not evidence that the released oracle ran 40 epochs. The [pinned model implementation](https://github.com/SafeAILab/EAGLE/blob/cb7e0841fe0c206c6ed74a197ad5e2a1f13f5a2b/eagle/traineagle3/cnets.py#L498) uses seven training-time rollout steps; our measured repair path uses three.

Our three completed full-repair A40 runs each process 2,228,270 input tokens. Whole-run throughput is 778.6 tokens/s median, observed range 730.3–819.3. This includes online target capture, training, initialization and checkpoint/export overhead. It is a measured proxy for our implementation, not a benchmark of the upstream trainer.

Training projection: `N × epochs × mean sequence tokens / (tokens per second × 3600)`. Length scenarios use our observed 557.1 tokens/example and the published 2048-token cap. The latter is explicitly a full-cap scenario, not a claimed corpus average. Hardware, precision, rollout count, batching and length effects prevent treating linear extrapolation as a precise runtime forecast.

| Epochs | Interpretation | Training A40 GPUh: 532k–646k examples, 557–2048 tokens | Generation+training proxy GPUh |
|---:|---|---:|---:|
| 1 | Sensitivity assumption | 106–472 | 397–825 |
| 10 | Sensitivity assumption | 1,057–4,720 | 1,348–5,073 |
| 40 | Public code default; actual oracle budget unknown | 4,229–18,879 | 4,520–19,232 |

The nominal 646k-example, 40-epoch, 557-token scenario gives about 5,135 training GPUh, or 5,488 GPUh including the response-generation proxy. This is not an oracle training bill. For comparison, choosing 10 epochs instead gives one quarter of the training projection. Report the sensitivity rather than selecting an assumption to maximize the apparent savings.

The generation add-on scales our generic 4k run: observed response throughput 238.3 tokens/s and 468.9 answer tokens/example, including engine initialization. It adds about 291–353 GPUh across the nominal data sizes. This assumes 512-token-capped target responses like our pilot; longer original reasoning, different batching or cached teacher features could change costs substantially.

| Repair (measured) | Interface only GPUh | Full GPUh |
|---|---:|---:|
| self 256 | 0.465 | 0.452 |
| self 4k | 5.398 | 5.555 |
| generic 4k | 2.798 | 2.849 |

Repair costs include successful data generation and training for each alternative; shared generation is counted once per alternative, not repeatedly in campaign totals. Search, engineering and evaluation are excluded. Projection ranges are assumption sensitivity, not 95% confidence intervals. No dedicated training run was launched and no projected budget is paired with a claim that it would reproduce the observed oracle acceptance.

Inputs, pinned source files, formulas, all sensitivity scenarios and three measured-run hashes: [artifacts/P6_D49_recipe_estimate_20261008_1800/estimate.json](../artifacts/P6_D49_recipe_estimate_20261008_1800/estimate.json). [Economics cost figure](figures/P6-recipe-cost-estimate-D49-20261008.pdf).
