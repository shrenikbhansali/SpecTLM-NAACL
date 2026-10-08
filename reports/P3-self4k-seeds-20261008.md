# P3: self-elicited 4k replication across three seeds

Pilot: 12 frozen acceptance cells, four reused seed-0 cells plus eight new seed-1/2 cells. Frozen `6da2e42`, vLLM 0.31.0, A40, EAGLE-3 K4, greedy, batch 8, 512 tokens, identical derivative-rendered prompts. Intervals resample training seeds and paired queries jointly (10,000 draws). Three seeds provide limited information about population seed variance.

| Arm | Panel | n / seeds | Δp1 [95% CI] | τ | Δτ [95% CI] | Oracle-gap recovery [95% CI] |
|---|---|---|---|---:|---|---|
| fc | speed128 | 128 / 3 | +0.1778 [+0.1652, +0.1896] | 2.2236 | +0.4934 [+0.4584, +0.5259] | 44.1% [41.9, 46.3] |
| fc | math64 | 64 / 3 | +0.1711 [+0.1583, +0.1830] | 2.4965 | +0.5489 [+0.5082, +0.5874] | 28.1% [25.8, 30.3] |
| full | speed128 | 128 / 3 | +0.2084 [+0.1949, +0.2209] | 2.3607 | +0.6305 [+0.5891, +0.6680] | 56.4% [54.3, 58.5] |
| full | math64 | 64 / 3 | +0.2183 [+0.2070, +0.2294] | 2.7327 | +0.7851 [+0.7444, +0.8307] | 40.1% [37.9, 42.7] |

All runs use the same 4,000 examples and 2,228,270 selected tokens for one epoch. Packing and scheduler horizons follow the actual seed-specific steps: 1,315 / 1,314 / 1,313. Fc and full arms match within each seed on data, order, objective and optimizer. Both arms improve p1 and τ on both panels across these seeds.

These self-elicited replications began before the generic-4k comparison completed. They are not replications of the newly selected generic source. Training prompts exclude all evaluation prompts; the evaluation panels are nevertheless used for configuration selection and are development evidence. Output lengths, per-depth rates, per-seed results, costs and matched-arm audits remain in the raw analysis. Shared generation must not be counted repeatedly across seeds.

Source: [artifacts/P3_D48_followup_analysis_20261008_1700/snapshot-20261008_175927/results.json](../artifacts/P3_D48_followup_analysis_20261008_1700/snapshot-20261008_175927/results.json).
