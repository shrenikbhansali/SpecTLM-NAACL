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

## 2026-10-08T00:10:14-04:00 — Census launch and prompt-count clarification

All180censuscells passed360preflights and were dispatched after6/6smokes passed. Correction to prospectivecountabove: exactreusedatlas workloads have64prompts for168cells and128prompts for12cells, not128everywhere. Analysiscountcheck corrected; underlyingcells unchanged. Firstpartialreport is being independentlyderived. No repairmethod run.

## 2026-10-08T00:29:23-04:00 — codex-1 — Q1 interim exploratory summary

Snapshot:46/180 I1 cells,23 completed Llama pairs,64 prompts/target; paired with existing atlas raw counters on exactly matching prompt hashes and decoding settings (zero mismatches). Independent raw re-derivation and input hashes: `artifacts/I1_Q1_20261008_0032/`. One seed, partial scheduling-biased census; prompt bootstrap intervals and every target retained in results.json.

| Drafter | n targets | Median position-1 retention | Range | Targets below0.90 | Median τ retention | Median target output length A00→A10 |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| Llama3.2-1B K4 | 23 | 0.9788 | 0.823–1.010 | 1 | 0.9877 | 212.0→153.5 |
| EAGLE3 K4 | 23 | 0.9986 | 0.747–1.123 | 1 | 0.9964 | 199.0→149.0 |
| DFlash K10 | 23 | 0.9878 | 0.601–1.109 | 4 | 0.9824 | 209.5→152.0 |

Early independent-drafter median loss is small; these results do not establish a broad or uniquely independent-drafter failure. Pre-cutoff subset n15 has median position1 retention .990/.997/.988 (1B/EAGLE3/DFlash). Selected development GSM8K adapter shows .823/.747/.601, so its failure is shared and larger for the target-conditioned drafters. Other pilot cases: CharlesLi alpaca .926/1.013/1.018; watt .931/1.102/.982; mlabonne .946/.918/.832. These contrasting cases motivate a small exploratory repair test, not a paper conclusion.

T1 snapshot:12 completed cells,8 architecture-incompatible planned cells excluded before execution. allenai/Llama-3.1-Tulu-3-8B-DPO / dflash: position1 retention 0.832, τ retention 0.698; allenai/Llama-3.1-Tulu-3-8B-DPO / eagle3: position1 retention 0.810, τ retention 0.819; allenai/Llama-3.1-Tulu-3-8B-SFT / dflash: position1 retention 0.937, τ retention 0.884; allenai/Llama-3.1-Tulu-3-8B-SFT / eagle3: position1 retention 0.915, τ retention 0.913; meta-llama/Llama-3.1-8B / dflash: position1 retention 1.158, τ retention 1.922; meta-llama/Llama-3.1-8B / eagle3: position1 retention 1.216, τ retention 1.355; all128prompts/pair. Full output lengths and uncertainty are in the artifact. No class-level conclusion yet.

Handoff: censuses continue under sole queue3531265; I1/T1 report processes3518990/3518508. D-43 now authorizes I3–I5 exploration; four pre-cutoff I3 data jobs published after8 dry-run checks. Existing post-cutoff census outcomes are kept in this census summary but excluded from repair selection. Update this Q1 snapshot when more pairs finish and again by the noon checkpoint.

## 2026-10-08T00:47:08-04:00 — codex-1 — Q1 Llama census complete / Handoff

All30 selected Llama targets now paired with EAGLE3/DFlash on identical atlas prompts (64each), frozen greedy vLLM0.31, no input/config mismatches. Raw re-derivation: `artifacts/I1_Q1_20261008_0045/`; Qwen census continues.

| Drafter | Median position1 retention | Range | Below.90 | Median τ retention | Median-of-target lengths A00→A10 |
| --- | ---: | --- | ---: | ---: | --- |
| 1B K4 | 0.9731 | 0.731–1.010 | 4/30 | 0.9806 | 209.75→156.75 |
| EAGLE3 K4 | 0.9974 | 0.742–1.123 | 3/30 | 0.9962 | 201.75→151.5 |
| DFlash K10 | 0.9886 | 0.601–1.109 | 6/30 | 0.9831 | 206.75→153.25 |

Most targets have small losses. The larger pre-cutoff failures are shared across drafter families. Storytelling (tohur): position1 retention .731 (95%prompt-bootstrap .693–.769), EAGLE3 .742, DFlash .614; 1B τ retention .701 and median lengths142→144, so this example is not explained by large output shortening. GSM8K: .823/.747/.601, but lengths193.5→9 for1B. Vikhr: .864/.874/.860, with1B lengths158.5→471.5. No broad independent-only failure established. Full paired uncertainty/lengths and nulls retained. Pre-cutoff subset18targets separately reported; no test-pool repair tuning.

T1 snapshot18cells/9pairs at this read; all n128, raw per-position/τ/length records embedded in the Q1artifact. Sole dispatcher3546069 and report processes3518990/3518508 continue; six obsolete post-training validators stopped to free srv3 forT1. I3 firstfour matched child/base greedy response jobs live/queued; expanded toward8donors using new degraded pre-cutoff tohur/Vikhr/agentlans plus a near-null grimjim control. Repair evidence remains exploratory and outcome-selected; owner direction checkpoints unchanged.

## 2026-10-08T03:17:45.597459-04:00 — codex-1 — census complete / Handoff

All **180/180 cells**, 90 paired comparisons over 60 stratified atlas targets, finished. Single seed, greedy, A40, vLLM0.31.0, K4; exact existing atlas rendered prompts. This is the historical D41/D42 independent-drafter harness **959b003**, distinct from D45's frozen 6da2e42 target-conditioned comparisons. No new Track I runs are planned.

| Drafter | Targets | Prompt n per pair | Median p1 retention | p1 range | Below .90 | Median τ retention |
| --- | ---: | --- | ---: | --- | ---: | ---: |
| llama-3.2-1b-instruct | 30 | [64] | 0.9731 | 0.731–1.010 | 4 | 0.9806 |
| qwen3-0.6b | 30 | [64, 128] | 1.0122 | 0.908–1.508 | 0 | 1.0231 |
| qwen3-1.7b | 30 | [64, 128] | 1.0010 | 0.888–1.338 | 2 | 0.9945 |

These are descriptive medians/ranges over the stratified targets, not representative unweighted estimates of all174. Prompt-paired bootstrap95% intervals, per-position counters, τ and lengths for every target (including nulls/regressions) are in `artifacts/I1_census_20261007_2355/report/results.json`; source/config provenance is in the adjacent config.json. Matched Llama EAGLE/DFlash contrast was independently audited in `artifacts/I1_Q1_20261008_0045`. Qwen independent-drafter median losses are small; do not infer a repair benefit from the completed census.

All data and failure/retry history retained. D45 concludes this as a secondary contrast; no new I1/I3–I5 work.
