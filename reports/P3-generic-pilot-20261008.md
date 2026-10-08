# P3 generic-data pilot — 2026-10-08

Status: **pilot**, single training seed. This is the completed D-45 generic520 experiment, kept separate from the D-46 self-elicited256 matrix and its 50/150/300 schedule. All 38 evaluation cells completed; two cells from the invalid scratch initialization are retained but excluded from comparisons. The other 36 cells cover three targets × three repair variants × two budgets × two workloads.

On R1 SPEED-128, fc-only at200steps improves absolute p1 by **0.1417 [0.1301,0.1523]**, τ1.7302→2.1014 (Δ0.3712 [0.3389,0.4008]); full warm-start improves p1 by **0.1772 [0.1648,0.1890]**, τ→2.2395 (Δ0.5092 [0.4742,0.5428]). Under the owner's fixed recovery formula, these recover33.2% and45.5% of the dedicated-drafter τ gap. End-to-end data-generation-plus-training cost is0.438 and0.437 A40 GPU-hours respectively; data generation is shared and charged in full to each standalone repair estimate. Evaluation, failed query-generation attempts and engineering overhead are excluded from this per-repair cost, not silently charged as zero. No wall-clock speedup claim yet.

**Which component repairs it (provisional):** fc-only recovers a substantial part of the R1/Nemotron acceptance loss on both workloads, but full warm-start yields larger improvements. The old fc+all-projection-LoRA arm is close to fc-only, especially for Nemotron; it is not the new fc-low-rank arm or the new decoder q/v+MLP proxy. Qwen gains are smaller. These observations support continuing the component comparison, but do not establish that the interface is the sole cause, that full repair is the cheapest winner, or that any improvement generalizes across seeds. D-46 calibration, decoder-only and scratch controls remain necessary.

Targets0=DeepSeek-R1-Distill-Llama-8B,1=Llama-3.1-Nemotron-Nano-8B-v1,2=DeepSeek-R1-0528-Qwen3-8B. Generic public prompts come from the pinned general20000 source; derivative greedy responses, n520, answer-position masks, native TTT3/KL, batch ceiling2048, AdamW2e-5,200-step cosine horizon shared by50/200 checkpoints. Failed unconditioned Magpie query paths supplied **no** training examples. Five decoded samples per successful path were reviewed; factual errors and capped reasoning responses were retained.

Evaluation: frozen6da2e4265c0398ec0de5affaf23b0bd1df0be445, vLLM0.31.0, A40, EAGLE-3 K4, greedy seed0, batch8,512-token cap, fresh compile. All arms use identical derivative-rendered prompt-token IDs; n128 SPEED and n64 outcome-independent MATH subset. All500 MATH problems plus existing evaluation queries were excluded from training. CIs are10,000 paired prompt bootstraps, seed0; they condition on one training seed and the selected workload, and do not quantify training-run uncertainty.

Independent analysis imports no followspec/atlas metric code: [script](../artifacts/P3_generic_report_20261008_0352/analyze.py), [raw audit and all per-depth/length estimates](../artifacts/P3_generic_report_20261008_0352/results.json). It recomputes τ and conditional acceptance from per-step raw counters, checks frozen commit/engine/A40 and matching settings/prompt hashes, aligns prompt IDs, and binds source hashes. Empty deeper-position denominators are reported as missing and not zero. Lengths and all conditional depths, including nulls, are in the JSON.

The original scratch path called HF initialization without clearing `_is_hf_initialized`, so its loaded tensors were not reset. Preserve those artifacts as invalid scratch controls. Fix1934d7e explicitly clears initialization guards only on the intended modules; tests and a native n5/2-step smoke confirm13 parameter tensors reset while family embeddings and vocabulary mapping remain fixed. The replacement D-46 scratch is separate.

| Target | Data | Arm | Steps | Workload | n | Δp1 [paired95%CI] | τ | Δτ [paired95%CI] | R1 recovery | Train+data GPUh |
|---|---|---|---:|---|---:|---|---:|---|---:|---:|
| 0 | generic520 | fc | 50 | speed128 | 128 | +0.1135 [+0.1027,+0.1237] | 2.0154 | +0.2852 [+0.2557,+0.3134] | 25.5% | 0.347 |
| 0 | generic520 | fc | 200 | speed128 | 128 | +0.1417 [+0.1301,+0.1523] | 2.1014 | +0.3712 [+0.3389,+0.4008] | 33.2% | 0.438 |
| 0 | generic520 | fc_lora | 50 | speed128 | 128 | +0.1077 [+0.0959,+0.1182] | 2.0041 | +0.2739 [+0.2436,+0.3006] | 24.5% | 0.341 |
| 0 | generic520 | fc_lora | 200 | speed128 | 128 | +0.1471 [+0.1355,+0.1578] | 2.1225 | +0.3923 [+0.3589,+0.4233] | 35.0% | 0.421 |
| 0 | generic520 | full | 50 | speed128 | 128 | +0.1496 [+0.1382,+0.1604] | 2.1477 | +0.4175 [+0.3824,+0.4496] | 37.3% | 0.345 |
| 0 | generic520 | full | 200 | speed128 | 128 | +0.1772 [+0.1648,+0.1890] | 2.2395 | +0.5092 [+0.4742,+0.5428] | 45.5% | 0.437 |
| 0 | generic520 | fc | 50 | math64 | 64 | +0.1115 [+0.1024,+0.1206] | 2.2735 | +0.3259 [+0.3045,+0.3479] | — | 0.347 |
| 0 | generic520 | fc | 200 | math64 | 64 | +0.1450 [+0.1342,+0.1553] | 2.3866 | +0.4390 [+0.4112,+0.4666] | — | 0.438 |
| 0 | generic520 | fc_lora | 50 | math64 | 64 | +0.1128 [+0.1019,+0.1233] | 2.2925 | +0.3448 [+0.3129,+0.3777] | — | 0.341 |
| 0 | generic520 | fc_lora | 200 | math64 | 64 | +0.1477 [+0.1377,+0.1574] | 2.4114 | +0.4638 [+0.4325,+0.4957] | — | 0.421 |
| 0 | generic520 | full | 50 | math64 | 64 | +0.1549 [+0.1441,+0.1657] | 2.4455 | +0.4979 [+0.4704,+0.5259] | — | 0.345 |
| 0 | generic520 | full | 200 | math64 | 64 | +0.1815 [+0.1703,+0.1928] | 2.5505 | +0.6029 [+0.5685,+0.6380] | — | 0.437 |
| 1 | generic520 | fc | 50 | speed128 | 128 | +0.1125 [+0.1021,+0.1229] | 2.1349 | +0.3115 [+0.2871,+0.3363] | — | 0.329 |
| 1 | generic520 | fc | 200 | speed128 | 128 | +0.1312 [+0.1200,+0.1422] | 2.2048 | +0.3813 [+0.3524,+0.4100] | — | 0.420 |
| 1 | generic520 | fc_lora | 50 | speed128 | 128 | +0.1131 [+0.1025,+0.1236] | 2.1435 | +0.3200 [+0.2935,+0.3474] | — | 0.334 |
| 1 | generic520 | fc_lora | 200 | speed128 | 128 | +0.1314 [+0.1209,+0.1419] | 2.2044 | +0.3809 [+0.3519,+0.4108] | — | 0.436 |
| 1 | generic520 | full | 50 | speed128 | 128 | +0.1417 [+0.1304,+0.1532] | 2.2395 | +0.4160 [+0.3837,+0.4480] | — | 0.336 |
| 1 | generic520 | full | 200 | speed128 | 128 | +0.1532 [+0.1418,+0.1645] | 2.2888 | +0.4654 [+0.4292,+0.5018] | — | 0.441 |
| 1 | generic520 | fc | 50 | math64 | 64 | +0.1221 [+0.1141,+0.1298] | 2.3182 | +0.3580 [+0.3370,+0.3785] | — | 0.329 |
| 1 | generic520 | fc | 200 | math64 | 64 | +0.1457 [+0.1372,+0.1542] | 2.3963 | +0.4361 [+0.4144,+0.4589] | — | 0.420 |
| 1 | generic520 | fc_lora | 50 | math64 | 64 | +0.1251 [+0.1162,+0.1338] | 2.3229 | +0.3627 [+0.3390,+0.3857] | — | 0.334 |
| 1 | generic520 | fc_lora | 200 | math64 | 64 | +0.1486 [+0.1392,+0.1581] | 2.4037 | +0.4436 [+0.4164,+0.4708] | — | 0.436 |
| 1 | generic520 | full | 50 | math64 | 64 | +0.1665 [+0.1565,+0.1762] | 2.4895 | +0.5294 [+0.4990,+0.5603] | — | 0.336 |
| 1 | generic520 | full | 200 | math64 | 64 | +0.1742 [+0.1647,+0.1839] | 2.5511 | +0.5909 [+0.5613,+0.6215] | — | 0.441 |
| 2 | generic520 | fc | 50 | speed128 | 128 | +0.0276 [+0.0195,+0.0360] | 2.0445 | +0.1188 [+0.0955,+0.1438] | — | 0.347 |
| 2 | generic520 | fc | 200 | speed128 | 128 | +0.0348 [+0.0263,+0.0432] | 2.0586 | +0.1330 [+0.1119,+0.1540] | — | 0.440 |
| 2 | generic520 | fc_lora | 50 | speed128 | 128 | +0.0264 [+0.0134,+0.0367] | 2.0355 | +0.1099 [+0.0801,+0.1377] | — | 0.343 |
| 2 | generic520 | fc_lora | 200 | speed128 | 128 | +0.0361 [+0.0233,+0.0464] | 2.0757 | +0.1501 [+0.1216,+0.1760] | — | 0.427 |
| 2 | generic520 | full | 50 | speed128 | 128 | +0.0479 [+0.0344,+0.0585] | 2.1126 | +0.1870 [+0.1563,+0.2135] | — | 0.351 |
| 2 | generic520 | full | 200 | speed128 | 128 | +0.0541 [+0.0464,+0.0617] | 2.1496 | +0.2240 [+0.2021,+0.2457] | — | 0.454 |
| 2 | generic520 | fc | 50 | math64 | 64 | +0.0173 [+0.0099,+0.0246] | 2.4544 | +0.0928 [+0.0680,+0.1157] | — | 0.347 |
| 2 | generic520 | fc | 200 | math64 | 64 | +0.0246 [+0.0162,+0.0333] | 2.4811 | +0.1195 [+0.0926,+0.1456] | — | 0.440 |
| 2 | generic520 | fc_lora | 50 | math64 | 64 | +0.0234 [+0.0158,+0.0308] | 2.4776 | +0.1160 [+0.0917,+0.1408] | — | 0.343 |
| 2 | generic520 | fc_lora | 200 | math64 | 64 | +0.0317 [+0.0240,+0.0395] | 2.5162 | +0.1546 [+0.1306,+0.1783] | — | 0.427 |
| 2 | generic520 | full | 50 | math64 | 64 | +0.0333 [+0.0234,+0.0435] | 2.5351 | +0.1735 [+0.1407,+0.2063] | — | 0.351 |
| 2 | generic520 | full | 200 | math64 | 64 | +0.0311 [+0.0223,+0.0401] | 2.5498 | +0.1882 [+0.1582,+0.2175] | — | 0.454 |
