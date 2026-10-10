# A4 long-workload dedicated-gap recovery — pilot

Official16k short-response repairs, matched fixed MATH32, frozen greedy K4. Recovery is ratio of paired mean differences, not mean of per-query ratios; oracle/repair/reuse share each query draw.

| Cap | Arm | n | τ | Δτ [95% CI] | Gap closed [95% CI] |
|---:|---|---:|---:|---|---|
| 512 | fc | 32 | 2.761 | 0.862 [0.798, 0.926] | 43.5% [40.5, 46.5] |
| 512 | full | 32 | 2.958 | 1.060 [0.990, 1.134] | 53.5% [50.2, 57.0] |
| 2048 | fc | 32 | 2.858 | 0.777 [0.718, 0.839] | 41.9% [39.9, 44.0] |
| 2048 | full | 32 | 3.042 | 0.961 [0.897, 1.026] | 51.8% [49.3, 54.6] |
| 8192 | fc | 32 | 2.585 | 0.616 [0.500, 0.731] | 34.0% [28.2, 39.4] |
| 8192 | full | 32 | 2.680 | 0.710 [0.557, 0.858] | 39.2% [32.0, 45.7] |
