# I1 completed census — 2026-10-08T03:17:45.597459-04:00

All **180/180 cells**, 90 paired comparisons over 60 stratified atlas targets, finished. Single seed, greedy, A40, vLLM0.31.0, K4; exact existing atlas rendered prompts. This is the historical D41/D42 independent-drafter harness **959b003**, distinct from D45's frozen 6da2e42 target-conditioned comparisons. No new Track I runs are planned.

| Drafter | Targets | Prompt n per pair | Median p1 retention | p1 range | Below .90 | Median τ retention |
| --- | ---: | --- | ---: | --- | ---: | ---: |
| llama-3.2-1b-instruct | 30 | [64] | 0.9731 | 0.731–1.010 | 4 | 0.9806 |
| qwen3-0.6b | 30 | [64, 128] | 1.0122 | 0.908–1.508 | 0 | 1.0231 |
| qwen3-1.7b | 30 | [64, 128] | 1.0010 | 0.888–1.338 | 2 | 0.9945 |

These are descriptive medians/ranges over the stratified targets, not representative unweighted estimates of all174. Prompt-paired bootstrap95% intervals, per-position counters, τ and lengths for every target (including nulls/regressions) are in `artifacts/I1_census_20261007_2355/report/results.json`; source/config provenance is in the adjacent config.json. Matched Llama EAGLE/DFlash contrast was independently audited in `artifacts/I1_Q1_20261008_0045`. Qwen independent-drafter median losses are small; do not infer a repair benefit from the completed census.

All data and failure/retry history retained. D45 concludes this as a secondary contrast; no new I1/I3–I5 work.
