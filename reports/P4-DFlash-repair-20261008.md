# P4 DFlash repair — completed pilot

2026-10-08, codex-1. Four native training runs and24 frozen evaluation cells are complete: R1-Distill-Llama and Nemotron ×fc-only/full ×50/150/300 steps ×SPEED128/MATH64. Both scopes improve p1 on both targets at300 steps. This establishes a positive result for these two tested DFlash targets, not universal cross-architecture generality.

## Setup

Each target uses256 audited self-elicited prompts and its own greedy512-token responses. Within a target, fc/full match data, packed order, optimizer and step budget. The B10 path uses native DFlash block KL,2048-token batch ceiling,64 anchors,gamma4,fixed exponential block weighting,AdamW2e-5,cosine300-step schedule,.03warmup,.01weightdecay,seed0. Saved-tensor offload and nonreentrant layer checkpointing make this fit A40. The full-vocabulary verifier-owned head remains frozen/omitted on export. Fc has83,886,080 trainable parameters; full has1,048,626,432.

Evaluation: unmodified frozen6da2e42/vLLM0.31.0,A40,DFlashK10,greedyseed0,batch8,max512,identical target-rendered IDs across reused/fc/full. Each cell compiles fresh. SPEED n128; MATH n64. Ten thousand paired-query bootstrap draws, conditional on the single training seed. Raw per-step counters independently reproduce reported τ and p1. Data+training costs include generation and the cumulative training time to each export; engineering smokes/evaluation are separate.

## All checkpoints

| Target | Arm | Step | Workload | n | Δp1 [paired95% CI] | τ | Δτ [paired95% CI] | Mean output tokens | Data+train GPUh |
|---|---|---:|---|---:|---|---:|---|---:|---:|
| R1-Llama | fc | 50 | math64 | 64 | +0.0318 [+0.0249,+0.0390] | 2.5309 | +0.1017 [+0.0688,+0.1402] | 502.3 | 0.305 |
| R1-Llama | fc | 50 | speed128 | 128 | +0.0350 [+0.0275,+0.0427] | 2.1411 | +0.0635 [+0.0311,+0.0988] | 501.1 | 0.305 |
| R1-Llama | fc | 150 | math64 | 64 | +0.0541 [+0.0422,+0.0661] | 2.5898 | +0.1606 [+0.1101,+0.2107] | 501.9 | 0.342 |
| R1-Llama | fc | 150 | speed128 | 128 | +0.0578 [+0.0495,+0.0659] | 2.2025 | +0.1249 [+0.0964,+0.1534] | 500.0 | 0.342 |
| R1-Llama | fc | 300 | math64 | 64 | +0.0590 [+0.0475,+0.0703] | 2.6062 | +0.1770 [+0.1279,+0.2270] | 501.5 | 0.391 |
| R1-Llama | fc | 300 | speed128 | 128 | +0.0686 [+0.0608,+0.0767] | 2.2246 | +0.1470 [+0.1143,+0.1829] | 499.5 | 0.391 |
| R1-Llama | full | 50 | math64 | 64 | +0.0563 [+0.0475,+0.0648] | 2.5854 | +0.1563 [+0.1110,+0.2020] | 502.3 | 0.320 |
| R1-Llama | full | 50 | speed128 | 128 | +0.0627 [+0.0550,+0.0707] | 2.2116 | +0.1340 [+0.1012,+0.1693] | 499.3 | 0.320 |
| R1-Llama | full | 150 | math64 | 64 | +0.0820 [+0.0700,+0.0932] | 2.6709 | +0.2417 [+0.1909,+0.2894] | 504.2 | 0.373 |
| R1-Llama | full | 150 | speed128 | 128 | +0.0924 [+0.0835,+0.1007] | 2.2858 | +0.2082 [+0.1623,+0.2429] | 495.7 | 0.373 |
| R1-Llama | full | 300 | math64 | 64 | +0.0902 [+0.0781,+0.1021] | 2.6875 | +0.2583 [+0.2110,+0.3038] | 505.9 | 0.430 |
| R1-Llama | full | 300 | speed128 | 128 | +0.1003 [+0.0918,+0.1086] | 2.3129 | +0.2353 [+0.1947,+0.2687] | 499.5 | 0.430 |
| Nemotron | fc | 50 | math64 | 64 | +0.0248 [+0.0169,+0.0332] | 2.2640 | +0.0610 [+0.0357,+0.0867] | 512.0 | 0.211 |
| Nemotron | fc | 50 | speed128 | 128 | +0.0225 [+0.0132,+0.0318] | 2.1167 | +0.0344 [-0.0026,+0.0691] | 349.2 | 0.211 |
| Nemotron | fc | 150 | math64 | 64 | +0.0595 [+0.0520,+0.0671] | 2.3555 | +0.1524 [+0.1301,+0.1748] | 512.0 | 0.245 |
| Nemotron | fc | 150 | speed128 | 128 | +0.0538 [+0.0430,+0.0642] | 2.2062 | +0.1239 [+0.0864,+0.1579] | 348.7 | 0.245 |
| Nemotron | fc | 300 | math64 | 64 | +0.0686 [+0.0603,+0.0769] | 2.3782 | +0.1752 [+0.1550,+0.1958] | 512.0 | 0.294 |
| Nemotron | fc | 300 | speed128 | 128 | +0.0681 [+0.0587,+0.0779] | 2.2380 | +0.1558 [+0.1173,+0.1928] | 350.2 | 0.294 |
| Nemotron | full | 50 | math64 | 64 | +0.0562 [+0.0486,+0.0640] | 2.3474 | +0.1443 [+0.1232,+0.1660] | 512.0 | 0.225 |
| Nemotron | full | 50 | speed128 | 128 | +0.0602 [+0.0504,+0.0699] | 2.2342 | +0.1519 [+0.1206,+0.1812] | 353.7 | 0.225 |
| Nemotron | full | 150 | math64 | 64 | +0.1048 [+0.0950,+0.1146] | 2.4921 | +0.2891 [+0.2556,+0.3231] | 512.0 | 0.280 |
| Nemotron | full | 150 | speed128 | 128 | +0.0872 [+0.0767,+0.0978] | 2.3390 | +0.2567 [+0.2176,+0.2958] | 355.0 | 0.280 |
| Nemotron | full | 300 | math64 | 64 | +0.1142 [+0.1052,+0.1233] | 2.5319 | +0.3289 [+0.2979,+0.3613] | 512.0 | 0.338 |
| Nemotron | full | 300 | speed128 | 128 | +0.0970 [+0.0861,+0.1080] | 2.3552 | +0.2729 [+0.2247,+0.3215] | 352.2 | 0.338 |

## Direct full-minus-fc contrast at300 steps

| Target | Workload | n | Δp1 [paired95% CI] | Δτ [paired95% CI] |
|---|---|---:|---|---|
| R1-Llama | speed128 | 128 | +0.0317 [+0.0240,+0.0395] | +0.0882 [+0.0458,+0.1256] |
| R1-Llama | math64 | 64 | +0.0313 [+0.0241,+0.0387] | +0.0813 [+0.0377,+0.1226] |
| Nemotron | speed128 | 128 | +0.0289 [+0.0207,+0.0370] | +0.1172 [+0.0875,+0.1443] |
| Nemotron | math64 | 64 | +0.0456 [+0.0386,+0.0530] | +0.1537 [+0.1266,+0.1820] |

Fc-only improves acceptance across these two drafter architectures when considered alongside P3 EAGLE results. Full DFlash training improves further. The architecture comparison also changes the native training objective and drafter size, so it is not a controlled estimate of an architecture effect. No DFlash-specific dedicated oracle was measured; the EAGLE oracle is not used to invent a DFlash recovery percentage.

Nulls are retained: Nemotron fc50 has Δτ+.0344 [−.0026,+.0691] on SPEED, despite positive p1. Lengths and all conditional-depth statistics remain available in the machine-readable report. A single seed per target/arm limits generalization.

Artifacts: `artifacts/P4_D48_20261008_1505/`; nativecodeef0b0db, backend261a82d. Independent results: `artifacts/D48_analysis_20261008_1528/snapshot-20261008_154917/results.json`; direct contrasts: `artifacts/D48_scope_comparison_20261008_1553/{analyze.py,results.json}`. Matched data/order/optimizer audits pass. Native/frozen8-query export smokes passed before publication;27 implementation/alignment/checkpoint tests passed. Shared export shards are exact immutable hardlinks; final compact checkpoints retain recovery state. Intermediate optimizer copies from completed runs were cleaned by the operator under D-47, with the cleanup manifest retained. Future storage-only revision3ad9c0c omits such intermediate optimizer writes; no completed run was altered or rerun.
