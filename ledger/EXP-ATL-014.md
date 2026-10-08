# EXP-ATL-014 — Exploratory independent-drafter repair and reuse (D-43)

**Landed:** 2026-10-08, I3/I4/I5.

**Status:** pilot; first three merged exports complete; native acceptance evaluation pending.

**What / why:** Probe whether small per-child hard-label KD repairs standalone Llama3.2-1B acceptance after target changes, whether repairs transfer, and whether head-only updates suffice. This is outcome-selected development exploration, not confirmation.

**New in this experiment:** Pre-cutoff child Magpie queries, greedy child/base responses on identical own-template contexts, answer-only LoRA KD; D0, paired base-distilled D_B and balanced pooled-donor D_pool controls. Optional head-only output projection, explicitly untied from frozen input embeddings. Reserved32-query synthetic greedy-agreement probe.

**Artifacts:** `artifacts/I3_pilot_20261008_0030/`; immutable code `run-I3-own-template-20261008` (90ae22f), native evaluations use unchanged I1 harness959b003. Full lineage, failed attempts, five-sample audits, trim logs and all outputs retained.

**Config + results:** Eight pre-cutoff donor plans: CharlesLi GSM8K/alpaca, watt, mlabonne, tohur storytelling, Vikhr RL, agentlans and near-null grimjim. First four have160 child+160 base greedy responses each; first128 training/last32probe. Generation vLLM0.31.0, seed7001+target-index, batch8,256outputtokens. Initial training seed0,128examples,twoepochs32steps, LoRA rank8/alpha16/LR2e-4/accumulation8; all attention+MLP projections. Child/base pairs trim responses to the shorter token count; full prompts/original responses preserved. First GSM8K pair has3926 supervised tokens/epoch and123/128 trimmed pairs. Native held-out evaluation K4,batch8,512tokens,seed0,exact atlas prompts and fresh compile; no outcome reported yet.

| GSM8K variant | n examples | Steps | Logged train+export seconds | Final batch loss |
| --- | ---: | ---: | ---: | ---: |
| child | 128 | 32 | 45.57 | 0.4728 |
| base | 128 | 32 | 42.48 | 0.1081 |
| head | 128 | 32 | 14.91 | 0.6998 |

These times exclude model loading and are not end-to-end onboarding speedups. Training losses are optimization diagnostics, not held-out repair results. D_pool and donor-transfer scores remain pending.

**Caveats:** One seed, small synthetic development samples, exploratory target selection and no multiplicity correction. Existing census includes post-cutoff targets under earlier authorization; no such target enters these repairs. Synthetic queries sometimes contain worked answers or contradictions. The GSM8K child produces incorrect arithmetic and repetition; this is behavior matching, not a target-quality result. Caps and paired truncation can remove EOS or truncate base reasoning. Pooled control matches examples/steps, with its actual token budget reported separately. Original rendering failed on a Transformers BatchEncoding return; recovered full-weight queries and reused pinned bank Magpie queries use each target's own template. No affected response data entered training. Six obsolete FollowSpec native validators were stopped after completed checkpoints/acceptance evaluations to release srv3; their unfinished native validation is not claimed complete. Owner decides direction at D-43 checkpoints.
