# P3: completed 1k/4k scaling and generic-prompt comparison

All 36 cells are complete. This remains a seed-0 pilot: frozen `6da2e42`, vLLM 0.31.0, A40, EAGLE-3 K4, greedy, batch 8, 512 generated tokens. Every comparison uses identical derivative-rendered token IDs. SPEED has n=128 and MATH n=64; intervals use 10,000 paired query bootstrap draws.

At 4k examples, generic prompts have small positive point differences over self-elicited prompts for both repair arms on both panels. SPEED intervals include zero. MATH intervals exclude zero for p1 and τ. Under D-49's conditional instruction, the next 16k point uses generic prompts. This choice uses development-panel evidence; it does not establish source superiority or constitute untouched confirmation.

The full matrix below includes every budget and null. Recovery is the fraction of the matched raw dedicated-drafter τ gap, with a paired numerator/denominator bootstrap.

| Data | Arm | Step/total | Workload | Delta p1 [95% CI] | tau | Paired oracle recovery [95% CI] | Data+train GPUh |
|---|---|---|---|---|---:|---|---:|
| generic4k | fc | 279/1115 | math64 | +0.1614 [+0.1518,+0.1707] | 2.4465 | +0.2550 [+0.2404,+0.2693] | 2.346 |
| generic4k | fc | 279/1115 | speed128 | +0.1653 [+0.1537,+0.1763] | 2.1683 | +0.3918 [+0.3706,+0.4136] | 2.346 |
| generic4k | fc | 558/1115 | math64 | +0.1776 [+0.1659,+0.1889] | 2.4883 | +0.2763 [+0.2593,+0.2932] | 2.499 |
| generic4k | fc | 558/1115 | speed128 | +0.1718 [+0.1589,+0.1836] | 2.2053 | +0.4249 [+0.4035,+0.4450] | 2.499 |
| generic4k | fc | 1115/1115 | math64 | +0.1809 [+0.1688,+0.1929] | 2.5316 | +0.2985 [+0.2765,+0.3212] | 2.798 |
| generic4k | fc | 1115/1115 | speed128 | +0.1781 [+0.1657,+0.1896] | 2.2239 | +0.4415 [+0.4189,+0.4652] | 2.798 |
| generic4k | full | 279/1115 | math64 | +0.2091 [+0.1953,+0.2217] | 2.6652 | +0.3667 [+0.3405,+0.3967] | 2.357 |
| generic4k | full | 279/1115 | speed128 | +0.1912 [+0.1788,+0.2027] | 2.2913 | +0.5018 [+0.4805,+0.5235] | 2.357 |
| generic4k | full | 558/1115 | math64 | +0.2165 [+0.2032,+0.2289] | 2.7174 | +0.3934 [+0.3662,+0.4249] | 2.522 |
| generic4k | full | 558/1115 | speed128 | +0.2040 [+0.1909,+0.2162] | 2.3425 | +0.5475 [+0.5247,+0.5712] | 2.522 |
| generic4k | full | 1115/1115 | math64 | +0.2285 [+0.2150,+0.2412] | 2.7847 | +0.4278 [+0.4003,+0.4588] | 2.849 |
| generic4k | full | 1115/1115 | speed128 | +0.2105 [+0.1974,+0.2229] | 2.3741 | +0.5758 [+0.5506,+0.6015] | 2.849 |
| self1k | fc | 83/329 | math64 | +0.1243 [+0.1128,+0.1352] | 2.3127 | +0.1866 [+0.1704,+0.2030] | 1.386* |
| self1k | fc | 83/329 | speed128 | +0.1325 [+0.1214,+0.1433] | 2.0725 | +0.3061 [+0.2829,+0.3291] | 1.386* |
| self1k | fc | 165/329 | math64 | +0.1329 [+0.1213,+0.1444] | 2.3740 | +0.2179 [+0.1988,+0.2376] | 1.426* |
| self1k | fc | 165/329 | speed128 | +0.1512 [+0.1394,+0.1625] | 2.1281 | +0.3558 [+0.3326,+0.3788] | 1.426* |
| self1k | fc | 329/329 | math64 | +0.1476 [+0.1362,+0.1588] | 2.4012 | +0.2318 [+0.2155,+0.2487] | 1.500* |
| self1k | fc | 329/329 | speed128 | +0.1519 [+0.1401,+0.1629] | 2.1370 | +0.3638 [+0.3403,+0.3875] | 1.500* |
| self1k | full | 83/329 | math64 | +0.1550 [+0.1429,+0.1666] | 2.4574 | +0.2605 [+0.2409,+0.2808] | 1.398* |
| self1k | full | 83/329 | speed128 | +0.1647 [+0.1523,+0.1766] | 2.1992 | +0.4194 [+0.3941,+0.4446] | 1.398* |
| self1k | full | 165/329 | math64 | +0.1750 [+0.1614,+0.1886] | 2.5546 | +0.3102 [+0.2841,+0.3395] | 1.447* |
| self1k | full | 165/329 | speed128 | +0.1793 [+0.1672,+0.1906] | 2.2448 | +0.4602 [+0.4385,+0.4824] | 1.447* |
| self1k | full | 329/329 | math64 | +0.1825 [+0.1676,+0.1970] | 2.5835 | +0.3250 [+0.2973,+0.3546] | 1.537* |
| self1k | full | 329/329 | speed128 | +0.1830 [+0.1707,+0.1945] | 2.2612 | +0.4748 [+0.4506,+0.4998] | 1.537* |
| self4k | fc | 329/1315 | math64 | +0.1620 [+0.1512,+0.1730] | 2.4506 | +0.2570 [+0.2411,+0.2730] | 4.955 |
| self4k | fc | 329/1315 | speed128 | +0.1634 [+0.1513,+0.1746] | 2.1733 | +0.3963 [+0.3737,+0.4192] | 4.955 |
| self4k | fc | 658/1315 | math64 | +0.1710 [+0.1593,+0.1824] | 2.4857 | +0.2750 [+0.2552,+0.2950] | 5.104 |
| self4k | fc | 658/1315 | speed128 | +0.1747 [+0.1635,+0.1853] | 2.2129 | +0.4317 [+0.4097,+0.4537] | 5.104 |
| self4k | fc | 1315/1315 | math64 | +0.1742 [+0.1628,+0.1850] | 2.5039 | +0.2843 [+0.2639,+0.3050] | 5.398 |
| self4k | fc | 1315/1315 | speed128 | +0.1766 [+0.1638,+0.1886] | 2.2196 | +0.4377 [+0.4142,+0.4614] | 5.398 |
| self4k | full | 329/1315 | math64 | +0.2039 [+0.1917,+0.2156] | 2.6570 | +0.3625 [+0.3401,+0.3878] | 4.997 |
| self4k | full | 329/1315 | speed128 | +0.1892 [+0.1767,+0.2010] | 2.2863 | +0.4973 [+0.4747,+0.5207] | 4.997 |
| self4k | full | 658/1315 | math64 | +0.2113 [+0.2004,+0.2221] | 2.6751 | +0.3718 [+0.3506,+0.3954] | 5.186 |
| self4k | full | 658/1315 | speed128 | +0.2029 [+0.1895,+0.2152] | 2.3366 | +0.5423 [+0.5181,+0.5676] | 5.186 |
| self4k | full | 1315/1315 | math64 | +0.2191 [+0.2066,+0.2313] | 2.7396 | +0.4047 [+0.3787,+0.4335] | 5.555 |
| self4k | full | 1315/1315 | speed128 | +0.2088 [+0.1948,+0.2218] | 2.3650 | +0.5677 [+0.5451,+0.5906] | 5.555 |

Generic minus self-elicited4k at finalepoch:

| Arm | Workload | Delta p1 [95% CI] | Delta tau [95% CI] |
|---|---|---|---|
| fc | speed128 | +0.0015 [-0.0041,+0.0070] | +0.0043 [-0.0115,+0.0197] |
| fc | math64 | +0.0068 [+0.0002,+0.0129] | +0.0278 [+0.0065,+0.0488] |
| full | speed128 | +0.0017 [-0.0055,+0.0091] | +0.0091 [-0.0120,+0.0309] |
| full | math64 | +0.0094 [+0.0004,+0.0186] | +0.0451 [+0.0071,+0.0825] |


Self-1k costs marked * are conservative generation-cost upper bounds through an early prefix snapshot. Other costs include successful generation of consumed sources, including oversampling, plus training through the export. Evaluation and engineering are excluded. Shared generation is counted once per alternative and must not be multiplied across seeds when quoting actual campaign spend.

Scaling changes data, optimizer steps and schedule together. The source comparison matches 4,000 examples and one epoch, not exact tokens or steps: self uses 2,228,270 tokens/1,315 steps; generic uses 1,960,165 tokens/1,115 steps. No task-accuracy claim follows from acceptance. Capped reasoning and factual errors are retained without quality selection.

[Independent raw acceptance analysis](../artifacts/D48_analysis_20261008_1528/snapshot-20261008_175358/results.json), [paired scaling contrasts](../artifacts/P3_D48_scaling_report_20261008_1615/snapshot-20261008_175402/results.json), and [generic-minus-self paired contrasts](../artifacts/P3_D48_scaling_report_20261008_1615/generic-vs-self4k.json) retain per-depth acceptance, lengths, hashes and matched training checks. [D-49 source choice](../artifacts/P3_D49_20261008_1800/source-choice.json) records the continuation.
