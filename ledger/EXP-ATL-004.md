### EXP-ATL-004 — Completed atlas pairs: evidence for method motivation

**Landed:** 2026-10-06 · NAACL sprint, atlas/method motivation analysis.

**Status:** pilot.

**What / why.** Summarize completed matched A00/A10 cells while method generation takes priority. Check the distribution across derivatives, both frozen drafters and held-out pools; this is descriptive evidence, not a method result or selection rule.

**New in this experiment.** CPU-only reconstruction from raw acceptance counters with pair validation, derivative bootstrap intervals and identical-cohort EAGLE depth comparisons. No new GPU cells.

**Artifacts:** `/home/heck2/sbhansali8/SpecTLM/artifacts/ATLAS_method_motivation_20261006/`: analyze.py, results.json, per_derivative.json (all source paths, effects and paired sample sizes), input_hashes.json (every source config/result/per-prompt hash).

**Config + results.** Pinned vLLM 0.31.0, greedy, seed 0, batch 8, max_new_tokens 512. Each derivative comparison uses identical prompts/settings/drafter revision; 64 or 128 paired prompts per derivative. Retention is child macro acceptance length / base macro acceptance length, including bonus token. n below counts derivatives. Intervals are 10,000 derivative bootstrap draws, seed 20261006. Exact model revisions, prompt hashes and per-cell code commits remain in the hashed source configs.

| Campaign / base / K | n | Median retention [95% CI] | Minimum | <0.95 | <0.80 |
| --- | ---: | --- | ---: | ---: | ---: |
| A4/llama/K2 | 86 | 1.0017 [0.9974, 1.0054] | 0.6840 | 13 | 4 |
| A4/llama/K4 | 86 | 1.0008 [0.9947, 1.0105] | 0.5490 | 18 | 5 |
| A4/llama/K8 | 86 | 0.9985 [0.9895, 1.0122] | 0.4767 | 20 | 6 |
| A4/qwen3/K2 | 81 | 1.0041 [0.9997, 1.0075] | 0.9424 | 1 | 0 |
| A4/qwen3/K4 | 81 | 1.0087 [1.0014, 1.0210] | 0.8731 | 1 | 0 |
| A4/qwen3/K8 | 81 | 1.0198 [1.0020, 1.0372] | 0.9137 | 3 | 0 |
| A7/llama/K10 | 86 | 0.9900 [0.9823, 1.0079] | 0.4780 | 26 | 12 |
| A7/llama/K4 | 10 | 0.9898 [0.8746, 1.0911] | 0.5740 | 4 | 2 |
| A7/qwen3/K16 | 81 | 1.0098 [0.9994, 1.0271] | 0.7985 | 12 | 2 |
| A7/qwen3/K4 | 10 | 1.0094 [0.9879, 1.0871] | 0.9213 | 1 | 0 |

A4 = EAGLE-3; A7 = DFlash. On the 50 completed Llama test derivatives, EAGLE K4 has 7 below 0.95 and 3 below 0.8; DFlash native K10 has 12 below 0.95 and 4 below 0.8. Five Llama LoRAs fall below 0.8 in both drafters; three are held-out. Across the same 86 Llama derivatives, EAGLE's minimum retention is 0.6840 / 0.5490 / 0.4767 at K2/4/8; medians remain near one. Full pool/type breakdowns and matched-depth intervals are in results.json.

**Caveats.** Incomplete observational census; excluded failures may be nonrandom. Derivative-bootstrap intervals do not estimate fresh-compile or repeated-run uncertainty. Prompt sets vary by derivative, although every A00/A10 pair is matched. DFlash K4 is a selected subset along EAGLE retention, not a random cohort and not directly comparable with the full native-depth cohort. These acceptance ratios do not establish wall-clock speedup or FollowSpec transfer. Typical retention stays near one, especially on Qwen; no universal degradation conclusion follows. No gate, threshold, protocol or paper framing changed.

**Supplement (2026-10-06, same analysis campaign):** tail_uncertainty.py / tail_uncertainty.json provide 10,000 paired-prompt bootstrap intervals (seed20261006) for the five lowest completed EAGLE K4 Llama retentions and their DFlash K10 counterparts. All use64 paired prompts. For held-out lucieranraven/osiris-checkpoints: EAGLE retention0.549 [0.523,0.575]; DFlash0.478 [0.444,0.517]. These are conditional on observed runs and are unadjusted for selecting the worst cases; not replicate/compile uncertainty. Full ten-row effects and intervals are in the artifact.
