### EXP-ATL-005 — Complete atlas census (A4 EAGLE-3, A7 DFlash) after FIX-6 zero-step retries

**Landed:** 2026-10-06 · NAACL sprint, atlas.

**Status:** pilot.

**What / why.** Re-summarize every matched A00/A10 pair once the 34 FIX-6 retries (D-32 zero-step handling) finished, so each atlas cell
covers the full frozen atlas pool (87 Llama, 87 Qwen3). Supersedes the incomplete counts in EXP-ATL-004 (688 pairs); that entry is unchanged.

**New in this experiment.** No new analysis code: operator copy of EXP-ATL-004's `analyze.py` with two edits, a new output dir and
tag prefix `FIX6-` stripped so retry cells are read (diff in journal `notes/FIX-6.md`). Pairwise prompt exclusion per D-32 via
`atlas.paired_cells`. Run from `.worktrees/run-FIX7-20261006` (b4b5f86), system Python.

**Artifacts:** `$WS/artifacts/ATLAS_pairs_FIX6_20261006/` (analyze.py, results.json, per_derivative.json, input_hashes.json,
analysis.log, extreme_retention_lengths.txt).

**Config + results.** Pinned vLLM 0.31.0 (lock deb579cd…), greedy, seed 0, batch 8, 512 new tokens, fresh compile per cell (D-14), matched LoRA
setting (D-22), exact token input; A00/A10 on the derivative's own 64 (or 128 general-fallback) rendered prompts. Retention = A10 macro AL / A00
macro AL (bonus token included). 716 pairs; 29 failed source cells (originals superseded by retries; kept). Median CI: 10,000 derivative
bootstraps (an observational census, not repeated-run uncertainty; the fresh-compile noise floor is EXP-ATL-002: SD 0.0029 base, 0.0080 LoRA).

| Campaign / base / K | n | Median retention [95% CI] | Min | <0.95 | <0.80 | >1.05 |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| A4/llama/K2 | 87 | 1.0023 [0.9975, 1.0054] | 0.6840 | 13 | 4 | 13 |
| A4/llama/K4 | 87 | 1.0016 [0.9948, 1.0098] | 0.5490 | 18 | 5 | 21 |
| A4/llama/K8 | 87 | 0.9987 [0.9899, 1.0124] | 0.4767 | 20 | 6 | 24 |
| A4/qwen3/K2 | 87 | 1.0050 [1.0001, 1.0083] | 0.9424 | 1 | 0 | 16 |
| A4/qwen3/K4 | 87 | 1.0104 [1.0029, 1.0222] | 0.8731 | 1 | 0 | 24 |
| A4/qwen3/K8 | 87 | 1.0285 [1.0062, 1.0559] | 0.9137 | 3 | 0 | 36 |
| A7/llama/K10 | 87 | 0.9906 [0.9824, 1.0092] | 0.4780 | 26 | 12 | 21 |
| A7/llama/K4 | 10 | 0.9898 [0.8746, 1.0911] | 0.5740 | 4 | 2 | 2 |
| A7/qwen3/K16 | 87 | 1.0114 [1.0018, 1.0349] | 0.7985 | 12 | 2 | 31 |
| A7/qwen3/K4 | 10 | 1.0094 [0.9879, 1.0871] | 0.9213 | 1 | 0 | 3 |
Zero-step exclusions (D-32): 28 pairs across 7 derivatives (1–10 of 64 prompts each; largest mkd-hossain/Keural-Cortex 10, DynaGuard 6),
identical across K per derivative.

**Anomalies (flagged, not explained away).**
1. Most |retention − 1| > 0.15 pairs coincide with large output-length or repetition shifts between A00 and A10 (A4 K4,
   `extreme_retention_lengths.txt`). Examples:
   - higokri/RestoreKV-Qwen3-8B_plus: retention 2.141. All 64 A10 outputs hit 512 tokens; mean distinct-4-gram ratio 0.072 vs 0.912 for A00, i.e. looping.
   - Clinical-Reasoning-Hub (1.168): median A10 output 11 tokens vs 512 for A00.
   - DinoStackAI qasper (1.311): 20 vs 512.
   - Low tail, kai-xu MATH (0.582): 6.5 vs 235.5.
   - CharlesLi gsm8k_gold (0.770): 9 vs 197.
   - osiris (0.549): 82.5 vs 352.5.
   
   Retention is defined on each model's own generations, so this is in scope by protocol. Short or degenerate generations still change what
   macro AL measures. **Proposed for the owner (not applied):** a preregistered-style sensitivity analysis that reports the headline with and
   without pairs whose A10 median length < 32 tokens or distinct-4-gram < 0.5, plus output length as a covariate in A6.
2. Qwen3 medians are > 1 with CIs excluding 1 at every EAGLE K, and the >1.05 count grows with K (16/24/36). Full fine-tunes also skew > 1 (EXP-ATL-004).
3. DFlash Llama K10 has the heaviest low tail (26 < 0.95; 12 < 0.80) despite a median near 1.

**Caveats.** Prompt sets differ by derivative (own-domain vs general fallback). GPTQ desc_act and bitsandbytes derivatives are absent (engine
exclusion, A2). The DFlash K4 subset is n = 10 only. Derivative-bootstrap CIs do not include run-to-run noise.

**Mandatory fields:** predictions EXP-ATL-000 §6.3 items 1–3 (atlas; not evaluated here, which is an owner step); inputs hashed in input_hashes.json; code commit b4b5f86 plus the
operator analysis copy; engine lock deb579cd…; seeds 0 / bootstrap 20261006; n per row above; status pilot.
