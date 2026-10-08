# Historical census: compatibility audit and paired p1 correction

2026-10-08T16:47:21.871205-04:00, codex-1. Status: **pilot**. This is a CPU reconstruction of 348 completed A00/A10 pairs across 174 checkpoints. No GPU job, historical artifact, engine setting or threshold changed.

The operator’s compatibility check is reproduced here: 682 selected cell configurations record generation commit 423d3b6; 14 FIX-6 cells record f00992f. The latter’s `atlas/run_cell.py` is byte-identical to frozen 6da2e42. For 423d3b6, generation calls and unchanged helper functions match; saved diffs show metric validation and zero-step handling changes. Every saved counter array was reconstructed by the metric function extracted from frozen 6da2e42. Engine 0.31.0, A40, greedy seed 0, batch 8, 512 tokens, 4096 context, 0.70 memory fraction and paired prompt hashes/settings were checked. These historical cells retain their actual generation commits; they are not relabeled as new frozen-harness launches.

**Two distinct aggregation issues are now explicit.** The old length-controlled `pos1_ret` field pools speculative steps across prompts. New P1/P3 results average each prompt’s first-position acceptance before taking retention. Both estimands are now named and reported. In addition, the old pooled p1 summary did not remove a baseline prompt when only its child had zero speculative steps. D-32 requires excluding both sides. This changes 14 comparisons across seven checkpoints. The already-paired macro acceptance-length values from EXP-ATL-005 reproduce exactly and are unchanged.

| Checkpoint | Drafter | Paired n / original n | Historical unpaired pooled p1 retention | Corrected paired pooled p1 retention [95% CI] |
|---|---|---|---:|---|
| CharlesLi/llama_3_alpaca_per_class_reflect | eagle3 | 63 / 64 | 0.9976 | 0.9976 [0.9297, 1.0964] |
| DinoStackAI/Qwen3-8b-lora-bioasq-resplit | eagle3 | 63 / 64 | 0.9971 | 1.0093 [0.7524, 1.3543] |
| Tibogoss/Qwen3-8B-test | eagle3 | 63 / 64 | 1.0078 | 1.0088 [0.9274, 1.1407] |
| mkd-hossain/Keural-Cortex-8B-SFT-step903 | eagle3 | 54 / 64 | 1.5097 | 1.4520 [1.1493, 1.8396] |
| nabin2004/AOS-qwen3-8b-narrated-merged | eagle3 | 63 / 64 | 1.0272 | 1.0276 [0.9218, 1.1821] |
| nabin2004/AOS-qwen3-8b-narrated-sft-merged | eagle3 | 62 / 64 | 1.0368 | 0.9964 [0.9196, 1.1040] |
| tomg-group-umd/DynaGuard-8B | eagle3 | 58 / 64 | 0.8197 | 0.8247 [0.7027, 0.9771] |
| CharlesLi/llama_3_alpaca_per_class_reflect | dflash | 63 / 64 | 1.0051 | 1.0066 [0.9451, 1.0865] |
| DinoStackAI/Qwen3-8b-lora-bioasq-resplit | dflash | 63 / 64 | 1.1952 | 1.1982 [1.0171, 1.4287] |
| Tibogoss/Qwen3-8B-test | dflash | 63 / 64 | 0.9167 | 0.9076 [0.8548, 0.9834] |
| mkd-hossain/Keural-Cortex-8B-SFT-step903 | dflash | 54 / 64 | 1.1686 | 1.1657 [0.9814, 1.3830] |
| nabin2004/AOS-qwen3-8b-narrated-merged | dflash | 63 / 64 | 0.8852 | 0.8856 [0.8041, 0.9848] |
| nabin2004/AOS-qwen3-8b-narrated-sft-merged | dflash | 62 / 64 | 0.9419 | 0.9182 [0.8398, 1.0203] |
| tomg-group-umd/DynaGuard-8B | dflash | 58 / 64 | 0.9659 | 0.9620 [0.8867, 1.0497] |

All 348 historical unpaired pooled values reproduce exactly; 334 already equal their paired versions. The corrected source preserves both historical values and paired replacements, excluded IDs, raw hashes and source commits. No old ledger entry or source file was edited.

**Typed population.** [Complete lineage × training-history table](P1-census-typed-table-20261008.md) contains every class, including unknown histories. Of 174 cards, 42 remain unknown. Class means use prompt-macro p1 retention and 5,000 checkpoint-then-paired-prompt bootstrap draws. A singleton interval reflects prompt uncertainty only. Each derivative’s own 64-query workload is separated from 128-query general fallback; neither is pooled with the new SPEED-128/MATH-64 panel. All census checkpoints remain, including previously flagged short or degenerate outputs, whose lengths are retained per pair. Related checkpoints and differing own-domain prompts limit causal comparisons between recipe labels.

Validation: 11 targeted unit tests passed after a missing-module failure, covering one-sided zero-step exclusion, unequal sequence lengths, duplicate/missing IDs, invalid counters and undefined ratios. Full 348-pair reconstruction passed, including prompt identity, all historical pooled p1 values, paired τ and 14 correction checks. The new helper is `atlas/census_summary.py`, commit 48ed12a; the existing generation harness is unchanged.

Reproduce with `PYTHONPATH=. python artifacts/FIX23_census_20261008_1640/analyze.py` in a **new output copy**, since the script refuses to overwrite its audit files. Source code, test logs, frozen source hashes, compatibility diffs, all per-pair intervals and class draws’ summaries are under that directory.
