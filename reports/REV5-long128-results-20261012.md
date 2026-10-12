# REV5 — expanded long-generation acceptance

Supplementary first128 MATH500,8192 cap,greedy EAGLE3 K4,batch8,A40,official16k seed0 repairs; paired10000-query bootstrap, frozen6da2e42; no timing claim

| Target | Arm | n | p1 [95% CI] | τ [95% CI] | Δτ vs reuse [95% CI] | Gap recovery [95% CI] | Mean output tokens |
|---|---|---:|---|---|---|---|---:|
| 0 | reuse | 128 | 0.482 [0.467,0.497] | 1.897 [1.853,1.941] | 0.000 [0.000,0.000] | 0.000 [0.000,0.000] | 3396.7 |
| 0 | fc | 128 | 0.643 [0.618,0.667] | 2.508 [2.415,2.598] | 0.610 [0.546,0.672] | 0.384 [0.353,0.413] | 3301.9 |
| 0 | full | 128 | 0.675 [0.651,0.699] | 2.652 [2.554,2.748] | 0.755 [0.683,0.825] | 0.475 [0.443,0.506] | 3302.0 |
| 0 | oracle | 128 | 0.809 [0.785,0.831] | 3.486 [3.353,3.616] | 1.589 [1.483,1.690] | 1.000 [1.000,1.000] | 3090.8 |
| 1 | reuse | 128 | 0.412 [0.397,0.426] | 1.622 [1.591,1.653] | 0.000 [0.000,0.000] | — | 2928.3 |
| 1 | fc | 128 | 0.623 [0.601,0.645] | 2.400 [2.321,2.478] | 0.778 [0.723,0.832] | — | 3068.1 |
| 1 | full | 128 | 0.661 [0.635,0.686] | 2.582 [2.487,2.675] | 0.960 [0.890,1.029] | — | 3086.7 |

Targets:0=R1-Distill-Llama,1=Nemotron (main empty-system/default mode). Same exact rendered IDs within target, fixed first128 order; no outcome-based selection. Cap8192 is not a guarantee that every response reaches8192. One training seed, so CIs measure paired query uncertainty. All per-depth conditional acceptance and paired exclusions are retained in JSON.

Raw inputs, hashes and complete estimates: `/home/heck2/sbhansali8/SpecTLM/artifacts/REV5_long128_20261012_1430/analysis/results.json`. Prior32-query panel is separate and not pooled. Paper unchanged.
