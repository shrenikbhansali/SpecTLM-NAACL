# R1 independent1B timing baseline

### 2026-10-09T02:58:00.528094-04:00 — codex-1 — independent1B batch8 cost comparison (pilot)

| Batch | Arm | Reference | n queries / processes | Warm panel speedup [95% CI] | Warm token throughput ratio | Cold panel speedup | Cold including startup |
|---:|---|---|---|---|---:|---:|---:|
| 8 | independent | none | 128 / 3 | 1.108 [1.087,1.131] | 1.114 | 1.105 | 1.054 |
| 8 | independent | reused | 128 / 3 | 1.033 [0.967,1.104] | 1.037 | 1.034 | 1.113 |
| 8 | independent | fc | 128 / 3 | 0.870 [0.768,0.981] | 0.874 | 0.873 | 0.994 |
| 8 | independent | full | 128 / 3 | 0.848 [0.733,0.968] | 0.845 | 0.850 | 0.975 |
| 8 | independent | oracle | 128 / 3 | 0.770 [0.656,0.893] | 0.771 | 0.773 | 0.916 |

Only batch8 complete: n128,3processes×3warm repeats, paired10000process/query-batch bootstrap. Warm1B vsno-spec1.108[1.087,1.131]; vsreused1.033[.967,1.104] is null. Independent/fc panel ratio.870[.768,.981] and independent/full.848[.733,.968] indicate repairs complete this panel faster despite competitive independent acceptance. Costs include runtime only here; data/training amortization and startup differ. Hosts were not randomized; output lengths/IDs differ, raw token-normalized and startup CI inJSON. No claim of broad superiority from this one target/panel. Batch1 timings still active. Source`artifacts/P3_D50_20261009_0200/E3-timing/analysis/snapshot-20261009_025720/results.json`.

### 2026-10-09T03:04:30.591409-04:00 — codex-1 — independent1B timing complete (pilot)

| Batch | Arm | Reference | n queries / processes | Warm panel speedup [95% CI] | Warm token throughput ratio | Cold panel speedup | Cold including startup |
|---:|---|---|---|---|---:|---:|---:|
| 8 | independent | none | 128 / 3 | 1.108 [1.087,1.131] | 1.114 | 1.105 | 1.054 |
| 8 | independent | reused | 128 / 3 | 1.033 [0.967,1.104] | 1.037 | 1.034 | 1.113 |
| 8 | independent | fc | 128 / 3 | 0.870 [0.768,0.981] | 0.874 | 0.873 | 0.994 |
| 8 | independent | full | 128 / 3 | 0.848 [0.733,0.968] | 0.845 | 0.850 | 0.975 |
| 8 | independent | oracle | 128 / 3 | 0.770 [0.656,0.893] | 0.771 | 0.773 | 0.916 |
| 1 | independent | none | 32 / 3 | 1.267 [1.203,1.334] | 1.269 | 1.263 | 1.172 |
| 1 | independent | reused | 32 / 3 | 0.981 [0.945,1.024] | 0.979 | 0.979 | 1.031 |
| 1 | independent | fc | 32 / 3 | 0.735 [0.702,0.773] | 0.728 | 0.734 | 0.842 |
| 1 | independent | full | 32 / 3 | 0.701 [0.663,0.749] | 0.697 | 0.701 | 0.810 |
| 1 | independent | oracle | 32 / 3 | 0.618 [0.575,0.674] | 0.617 | 0.618 | 0.744 |

All36 timing cells (six independent plus30shared controls); source`/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/E3-timing/analysis/snapshot-20261009_030417/results.json`. Threeprocesses×3warm repeats, A40, greedy512, paired10000process/query-batch bootstrap, n128/b8 and32/b1. Cold/startup intervals, per-process values, output lengths and mismatches in JSON. Exact same rendered IDs; no acceptance derived from timing. Available hosts were not randomized; different greedy outputs remain documented. Nulls retained.
