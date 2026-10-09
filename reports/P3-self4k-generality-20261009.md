# P3 self4k seeds and generality follow-up

Pilot completed 2026-10-08T18:32:04.709668-04:00;28cells(4seed0reused+8newseed+16generality), frozen6da2e42/vLLM0.31.0/A40, EAGLEK4, identical rendered IDs, greedy512/batch8; SPEED128+MATH64. Selectedself4koneepochrecipe replicated in parallel with generic4kablation; not a finalbest-dataclaim.

| Arm | Workload | n / seeds | Delta p1 [seed/query95% CI] | tau | Oracle recovery [95% CI] |
|---|---|---|---|---:|---|
| fc | speed128 | 128/3 | +0.1778 [+0.1652,+0.1896] | 2.2236 | +0.4412 [+0.4191,+0.4632] |
| fc | math64 | 64/3 | +0.1711 [+0.1583,+0.1830] | 2.4965 | +0.2805 [+0.2576,+0.3026] |
| full | speed128 | 128/3 | +0.2084 [+0.1949,+0.2209] | 2.3607 | +0.5638 [+0.5428,+0.5855] |
| full | math64 | 64/3 | +0.2183 [+0.2070,+0.2294] | 2.7327 | +0.4012 [+0.3787,+0.4268] |

Exactly4000examples/2228270tokensacrossR1seeds, oneepoch; packedsteps1315/1314/1313byseed and schedulerhorizonfollowactualsteps. Fc/fullmatchedwithineachseed. Three-seedvarianceprecisionlimited. Per-seed rawresultsand10000pairedquery/seedbootstrapretained.

| Target | Arm | Workload | n | Steps | Delta p1 [95% CI] | tau | Delta tau [95% CI] | Mean output tokens | Data+train GPUh |
|---|---|---|---:|---:|---|---:|---|---:|---:|
| nvidia/Llama-3.1-Nemotron-Nano-8B-v1 | fc | math64 | 64 | 1306 | +0.1727 [+0.1613,+0.1838] | 2.5209 | +0.5608 [+0.5269,+0.5940] | 512.0 | 3.695 |
| nvidia/Llama-3.1-Nemotron-Nano-8B-v1 | fc | speed128 | 128 | 1306 | +0.1540 [+0.1428,+0.1654] | 2.2911 | +0.4676 [+0.4356,+0.5000] | 351.7 | 3.695 |
| nvidia/Llama-3.1-Nemotron-Nano-8B-v1 | full | math64 | 64 | 1306 | +0.2102 [+0.1987,+0.2216] | 2.6806 | +0.7204 [+0.6854,+0.7547] | 512.0 | 3.737 |
| nvidia/Llama-3.1-Nemotron-Nano-8B-v1 | full | speed128 | 128 | 1306 | +0.1690 [+0.1563,+0.1819] | 2.3503 | +0.5268 [+0.4869,+0.5664] | 358.3 | 3.737 |
| deepseek-ai/DeepSeek-R1-0528-Qwen3-8B | fc | math64 | 64 | 1332 | +0.0397 [+0.0312,+0.0481] | 2.5696 | +0.2080 [+0.1823,+0.2339] | 512.0 | 6.234 |
| deepseek-ai/DeepSeek-R1-0528-Qwen3-8B | fc | speed128 | 128 | 1332 | +0.0506 [+0.0428,+0.0587] | 2.1257 | +0.2001 [+0.1776,+0.2229] | 502.0 | 6.234 |
| deepseek-ai/DeepSeek-R1-0528-Qwen3-8B | full | math64 | 64 | 1332 | +0.0737 [+0.0645,+0.0828] | 2.7098 | +0.3482 [+0.3150,+0.3814] | 512.0 | 6.263 |
| deepseek-ai/DeepSeek-R1-0528-Qwen3-8B | full | speed128 | 128 | 1332 | +0.0753 [+0.0611,+0.0869] | 2.2418 | +0.3162 [+0.2794,+0.3493] | 502.4 | 6.263 |
| shufanshen/Qwen3-8B-GRPO-DeepMath-150-steps | fc | math64 | 64 | 1185 | +0.0546 [+0.0448,+0.0648] | 2.9444 | +0.2712 [+0.2357,+0.3069] | 453.8 | 4.219 |
| shufanshen/Qwen3-8B-GRPO-DeepMath-150-steps | fc | speed128 | 128 | 1185 | +0.0168 [+0.0096,+0.0242] | 2.5423 | +0.1368 [+0.1115,+0.1629] | 357.4 | 4.219 |
| shufanshen/Qwen3-8B-GRPO-DeepMath-150-steps | full | math64 | 64 | 1185 | +0.0802 [+0.0686,+0.0920] | 3.1092 | +0.4360 [+0.3893,+0.4821] | 451.0 | 4.257 |
| shufanshen/Qwen3-8B-GRPO-DeepMath-150-steps | full | speed128 | 128 | 1185 | +0.0231 [+0.0141,+0.0320] | 2.5700 | +0.1644 [+0.1306,+0.2000] | 357.9 | 4.257 |
| NousResearch/Hermes-3-Llama-3.1-8B | fc | math64 | 64 | 892 | +0.1058 [+0.0862,+0.1254] | 2.6030 | +0.3762 [+0.3042,+0.4528] | 253.9 | 3.241 |
| NousResearch/Hermes-3-Llama-3.1-8B | fc | speed128 | 128 | 892 | +0.0860 [+0.0656,+0.1044] | 2.5384 | +0.3301 [+0.2740,+0.3861] | 182.6 | 3.241 |
| NousResearch/Hermes-3-Llama-3.1-8B | full | math64 | 64 | 892 | +0.0971 [+0.0787,+0.1162] | 2.6086 | +0.3819 [+0.3059,+0.4650] | 265.3 | 3.355 |
| NousResearch/Hermes-3-Llama-3.1-8B | full | speed128 | 128 | 892 | +0.1003 [+0.0829,+0.1178] | 2.5879 | +0.3796 [+0.3118,+0.4459] | 186.4 | 3.355 |

Nooracleassumedforgeneralitytargets. GRPO150isapreselectedRLcontrolandHermes3awell-transferringcontrol; reporttheiractualgains/nulls/regressions,notassumednegative/null. Same4000examples/oneepoch,actualtokenandstepbudgetvarybytarget. NativeTTTobjective/optimizerunchanged. All5sampleauditscompleteforeach17newsourcepaths; allmasks/forbidden/globaldedupvalidated; GRPOextra1100sourcechargedwithotherconsumedgeneration. Noanswerqualityfiltering,512tokenreasoningcaps/factualerrorsretained.
Trainingpanelsremainheldoutfromdata,but usedforconfigurationselection; no untouchedfinaltestclaim. Perdepthconditionalacceptance,lengthCIs,trainingconfig/datahashes,andmatchedarmchecksareintheJSON. Per-repaircostsincludeeachconsumedgenerationsourceincludingoversamplingplustraining; sharedgenerationnotrecountedincampaignspend. Search/evaluation/engineeringexcluded.

Source /home/heck2/sbhansali8/SpecTLM/artifacts/P3_D48_followup_analysis_20261008_1700/snapshot-20261008_183145/results.json; immutableanalysis/sourcehashesinthisstage. Nullintervalsretained; n128/64 pertarget,seed0onlyforgenerality.

Published 2026-10-09T02:28:13.739308-04:00; immutable original analysis at `artifacts/P3_D48_followup_analysis_20261008_1700/final-report.md`.
