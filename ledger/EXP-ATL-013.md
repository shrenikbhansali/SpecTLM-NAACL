# EXP-ATL-013 — Track I independent-drafter census

**Landed:** 2026-10-08, I1 / D-41–D-42.

**Status:** pilot; smoke complete, census pending.

**What / why:** Test frozen independent drafters against official targets and public atlas shifts. Use60outcome-independent stratified targets (30/base) from174, with the exact atlas rendered prompts paired A00/A10.

**New in this experiment:** Opt-in draft_model mode with vLLM token-level vocabulary mapping; Llama3.2-1B-Instruct and Qwen3-0.6B/1.7B drafters.180planned census cells, K4. No repair methods.

**Artifacts:** `artifacts/I1_models_20261007/verified_manifest.jsonl`, `artifacts/I1_smoke_20261007_2355`, `artifacts/I1_census_20261007_2355`.

**Config + results:** Pinned cell harness959b003, vLLM0.31.0, A40, greedyseed0, batch8, freshcompile. Smoke uses5atlas prompts/64outputtokens; census128prompts/512outputtokens. LoRA controls enable identical LoRAsettings onA00. Smoke rawcounter validation6/6PASS:

| Drafter | Target shift | Cell | n | Macro τ |
| --- | --- | --- | ---: | ---: |
| meta-llama/Llama-3.2-1B-Instruct | CharlesLi/llama_3_alpaca_per_class_reflect | A00 | 5 | 4.0746 |
| meta-llama/Llama-3.2-1B-Instruct | CharlesLi/llama_3_alpaca_per_class_reflect | A10 | 5 | 3.8937 |
| Qwen/Qwen3-0.6B | pkhare/qwen3-8b-biomedical | A00 | 5 | 3.5312 |
| Qwen/Qwen3-0.6B | pkhare/qwen3-8b-biomedical | A10 | 5 | 3.8000 |
| Qwen/Qwen3-1.7B | pkhare/qwen3-8b-biomedical | A00 | 5 | 3.9220 |
| Qwen/Qwen3-1.7B | pkhare/qwen3-8b-biomedical | A10 | 5 | 3.8000 |

**Caveats:** Smoke numbers only, not census evidence or speedup. Five-prompt smoke output prefixes matched historical atlas output in27/30cases; three continuations differ, first divergence atpositions16/40/46. Historical runs used128queries/batches of8 and a different drafter, so this is not a controlled bitwise replay; mismatches retained in `historical_prefix_audit.json`, no exact-replay claim. Full census remains outcome-independent, includes all selected successes/failures/regressions, and is stratified rather than a representative unweighted estimate of174models. I2 awaits owner brainstorm.
