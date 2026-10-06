# FIX-4 — M1/M2 production assembler (filed by claude-ops)

## 2026-10-06T02:37-04:00 — claude-ops — Filed

The B5/B6 pieces pass, but M1/M2 production involves ~10 manual stages (followspec/ONLINE_TRAINING.md) and needed recipe choices that are now
fixed by **§13 D-27** (owner-delegated). Please build one orchestrator (CPU planning + launcher-ready job files; operator launches GPU jobs via
`ops/launch.py`/`ops/queue.py`, fresh compile, HF_HUB_OFFLINE) that:
1. samples mixture candidates (§5.4, fixed seed) and emits atlas.filter_pool jobs for the 33 bank + candidates on a shared 128-query
   **training-general** reference, then runs `followspec.mixture_targets` admission (2 rounds max; ≥ 20 needed);
2. assigns per-target prompts per D-27 (MVD 1,000/bank child; FS round(33,000/n)/target; 50:50 Magpie:general; disjoint seeded general split;
   parent share 25% base-on-general);
3. emits generation job lists (child responses, base responses for PO-D and parent share) with `--allow-a40-production`;
4. runs paired trimming (D-21), builds FS/MVD/PO-D/PO-T manifests, and applies D-27(6)'s logged tail truncation to equalize tokens/steps;
5. runs `followspec.audit_batches` and the 5-sample decoded/mask audits; writes a single readiness report.
Inputs ready: frozen pools `atlas/pools/`; bank Magpie training prompts are coming from A3 phase 2 (operator, 500 per bank child).

## 2026-10-06T02:58:48-04:00 — codex-1 — Claim

Claimed FIX-4 ahead of P1 B10; owner method priority. Read D-27, §5.4–5.5, B5/B6 specs, ONLINE_TRAINING and filed FIX-4 request. Existing B3/B5 operator done; B6 D-26 acceptance passed, review. Build CPU planner/orchestrator under followspec, branch codex/FIX-4; operator launches production GPU jobs. Tests first for deterministic sampling/rank limits, shared training-only filter reference, admitted≥20/≤30 and≤2rounds, prompt allocation/disjointness/50:50/parent25%, exact generation flags, D-21 pair integrity, logged tail matching, native batch audit and readiness fail-closed. No pause marker; B10 OOM preserved, no production launch.

## 2026-10-06T03:22:19-04:00 — codex-1 — Planner, assembly and real-bank compatibility

Branch f461298 pushed, unmerged;97 followspec CPU tests PASS (`artifacts/build_logs/FIX4_full_views_20261006.log`). Tests first: FIX4_before (missing planner), FIX4_assembly_before (missing assembler), FIX4_adapter_views_before (missing bank-view helper); all preserved. Pure contract tests and a CPU end-to-end fixture exercise paired originals, all4 arms,25% parent/50:50 child ratios, source tampering, real B5 dataset views, native-audit interface, mask-review hashes and final config resolution. Fixture uses a stand-in sampler/tokenizer and does not claim GPU or production-corpus acceptance. Exact native sampler and launcher dry runs still required. One initial planner test was terminated (own pytest PID943185) because an unnecessarily repeated hash-set construction was slow; precomputed that set, retry passed.

Implementation: followspec.production CLI stages prepare/materialize/admit/mixture-prompts/responses/render-local/assemble/finalize, docs PRODUCTION_DATA.md. Two candidate rounds frozen before scores; no third round. Explicit operator validation-query input (subset of general20000), disjoint parent/child general partition, shared general reuse across child targets, no within-target repeats. Per-target integer rounding can drop one final query to make halves exact, logged. Fixed eight-record ordering blocks (6 children,2 parents) allow suffix-only matching while retaining ratios. Largest common token prefix that passes every native seed is selected; no feasible prefix is a recorded failure, no resampling/threshold relaxation. Parent order stays shared across arms. All GPU work is emitted as argv-based ops/queue jobs with fresh compile; none launched.

Real CPU preparation PASS on all33 frozen bank entries (`artifacts/FIX4_planner_acceptance_20261006/plan`), immutable e80d648, seed0,rankcap256,60 frozen candidate definitions,128 training-general references. Commands and PIDs in launch.json/materialize_launch.json. First CPU materialization failed on third candidate; first2 outputs and failure log preserved. Two Hiranmai49 bank adapters include saved `lm_head.base_layer.weight`, which strict B3 refuses. Read-only full tensor check (`artifacts/FIX4_saved_heads_20261006`) found159176 differing values each, maxabs2.9802322387695312e-8; they are NOT exact base copies. An attempted exact-copy-only test was abandoned before code implementation; failing output FIX4_saved_head_before retained.

Pinned local vLLM0.31.0 source supplies the actual fix: LoRAModel.from_lora_tensors explicitly skips is_base_embedding_weights, exactly `.embed_tokens.base_layer.weight` and `.lm_head.base_layer.weight` (lora/lora_model.py139; lora/utils.py223). PEFT loads these into its base_layer, so original files would contaminate the shared base in online capture. New explicit materialization-only factor views retain all LoRA factors bitwise and adapter config bytes; omit only the two vLLM-skipped suffixes; record original hashes/keys/pin; reject any other extra tensor. Registry uses views for B3 mixtures and PEFT capture; vLLM generation continues to use original pinned adapters with the same effective factors. B3 strict default is unchanged. Next: rerun actual round1 materialization from f461298, verify real pinned vLLM loader equivalence and PEFT base restoration, then end-to-end native CPU audit and launch-command validation before merge.

No active pause markers. Reserved methodGPU6/7 remain free. Referenced legacy protocol files are absent under this checkout's documented paths; MASTER pause/ledger contracts apply. No research cutoffs changed.

## 2026-10-06T03:33:07-04:00 — codex-1 — Acceptance PASS / Handoff

Merged0fa2368 (branch ec4b322), now review. Aggregate `artifacts/FIX4_acceptance_20261006/acceptance.json` + config/evidence hashes/ledger. Final98 tests PASS (`python -m pytest -q followspec/tests`, build_logs/FIX4_final_suite_20261006.log); no existing defaults changed. All33 actual frozen bank identities/A2 proofs verified,60 candidates fixed before scores,30 first-round adapters constructed with exact preserved original factors in `artifacts/FIX4_planner_acceptance_20261006/round1_engine_views`. 64 real launcher configurations and cell CLI dry runs PASS (`FIX4_launch_dryruns_20261006`):1 baseline +33 bank +30 mixtures. No production GPU submissions.

Actual pinned vLLM0.31.0 CPU loader gives bitwise identical effective LoRA factors/scaling for both original/view adapters (225 modules each), `FIX4_vllm_view_equivalence_cuda_20261006`; CUDA-visible6 was needed only for pinned host memory after a CPU-visible-none attempt failed. Original failed run/log retained. Tiny native PEFT CPU fixture verifies exact base-state and parent-logit restoration with a deliberately different saved head (`FIX4_native_bank_views_20261006`). More importantly, real Llama A40 switch acceptance PASS (`FIX4_real_bank_switch_20261006/check/results.json`): both canonical Hiranmai adapters, first→second→first, base features/labels bitwise exact throughout, child reload exact, all teacher weights frozen, one model/one resident adapter,15.29s,peak15.089GiB. Five reused B5 training strings/masks inspected below; this diagnostic capture does not relabel or add these CharlesLi responses to Hiranmai training data.

Full pipeline CPU fixture (`FIX4_fixture_20261006`) uses synthetic token IDs and a toy tokenizer, explicitly not production data. It tests immutable originals, response pairing,16 train/4 val records per arm,64 shifted tokens,32 assistant tokens,25% parent,50:50 child composition and mask review. Independent pinned native sampler re-run PASS for all4 arms×3seeds,1step each (`FIX4_native_fixture_audit_20261006`). All20 fixture decoded/mask records were inspected: samples c::c10,c::c11,c::c2,c::c1,c::c8, context TOKENS[1,2,3]; FS/MVD/PO-T answer[4,5], PO-D[8,9]; masks[0,0,0,1,1], shifted[0,0,1,1]. This is a data-mechanics check, not the M2 production quota audit.

**Operator next:** re-run tests and checks, then tag a main ancestor before queue submission. Existing64 job files reference immutable e80d648 (now on main ancestry; filter code unchanged) and need a run-* tag for launcher guards, or regenerate under your chosen tagged main checkout via followspec/PRODUCTION_DATA.md. First baseline, then63 filter jobs, then admission; run second30 only if first round admits<30. Bank Magpie training comes from A3 phase2; mixture Magpie/response job files follow admission. Supply an explicit validation subset of general20000 and complete evaluation exclusions at response planning. No implicit validation fraction. Inspect five actual production samples per arm before finalize. Deterministic suffix-only matching may have no feasible common budget/steps for real lengths; then it stops with evidence and needs a data-recipe decision, never silent resampling. B5/B3 are done, B6 D-26 passed/review. Both reserved method GPUs6/7 are now free. Next builder priority: primary Llama full-response/full-occupancy A40 capacity check, before P1 DFlash OOM work.

```json
{"sample_id": "alpaca-32435", "decoded_prompt": "<|begin_of_text|><|start_header_id|>user<|end_header_id|>Develop a script for a 30-second commercial for a new movie.\nMovie Title: Mission Impossible: Fallout<|eot_id|><|start_header_id|>assistant<|end_header_id|>", "decoded_answer": "Here\u2019s a script for a 30-second commercial for Mission Impossible: Fallout:\n\n[Scene: A dramatic aerial shot of Paris at night, with the Eiffel Tower in the background. The music starts with a suspenseful tone.]\n\nNarrator (in a deep, dramatic voice): \"The world needs a hero.\"\n\n", "response_start": 29, "mask_summary": "0x29,1x64"}
```

```json
{"sample_id": "alpaca-5330", "decoded_prompt": "<|begin_of_text|><|start_header_id|>user<|end_header_id|>Edit the following sentence to better express the idea.\nLying is bad because it damages relationships.<|eot_id|><|start_header_id|>assistant<|end_header_id|>", "decoded_answer": "Here's a revised sentence that conveys the idea more effectively:\n\nLying can have a profoundly negative impact on relationships, as it erodes trust and can lead to feelings of betrayal and hurt.\n\nThis revised sentence:\n\n*   Uses more descriptive language to paint a clearer picture\n*   Emphasizes the consequences of lying", "response_start": 27, "mask_summary": "0x27,1x64"}
```

```json
{"sample_id": "alpaca-44183", "decoded_prompt": "<|begin_of_text|><|start_header_id|>user<|end_header_id|>Calculate the cost of an item that is marked down from $50 to $35.<|eot_id|><|start_header_id|>assistant<|end_header_id|>", "decoded_answer": "To calculate the markdown, we can subtract the new price from the original price. \n\nOriginal Price = $50\nNew Price = $35\n\nMarkdown = Original Price - New Price\n= $50 - $35\n= $15\n\nSo, the item was marked down by $15. \n\nTo find the percentage", "response_start": 25, "mask_summary": "0x25,1x64"}
```

```json
{"sample_id": "alpaca-18788", "decoded_prompt": "<|begin_of_text|><|start_header_id|>user<|end_header_id|>Create the ending for this story\nThe man was walking down the street, trying to decide whether to go left or right, when he suddenly heard a voice calling him.<|eot_id|><|start_header_id|>assistant<|end_header_id|>", "decoded_answer": "As the man turned to see who was speaking to him, he noticed a figure standing behind a nearby streetlamp. The figure was shrouded in shadows, but the voice seemed to be coming from it.\n\n\"Which way?\" the man asked aloud, wondering if he was talking to himself.\n\n\"Left,\" the voice", "response_start": 42, "mask_summary": "0x42,1x64"}
```

```json
{"sample_id": "alpaca-18926", "decoded_prompt": "<|begin_of_text|><|start_header_id|>user<|end_header_id|>Read the following descriptions and identify the type of cuisine being described.\nA dish of ground lamb, onions and spices, wrapped in pastry, and baked or deep-fried.<|eot_id|><|start_header_id|>assistant<|end_header_id|>", "decoded_answer": "Based on the description, the type of cuisine being described is Middle Eastern or Mediterranean, specifically a traditional dish known as a \"Kibbeh\". Kibbeh is a popular dish in countries such as Turkey, Lebanon, and Iran.<|eot_id|>", "response_start": 42, "mask_summary": "0x42,1x48"}
```

## 2026-10-06T03:41-04:00 — claude-ops — Operator verification: PASS → done

Fresh checkout of main c185c3d: `python3 -m pytest -q followspec/tests` → **98 passed**. Independent re-run of the real A40 bank-switch check
(`followspec.tests.native_bank_check`, `.venv-transport`, heck-srv2:6, same registry/responses) → `artifacts/FIX4_operator_switch_recheck_20261006/`:
passed; base exact after all switches; reloaded child exact; 1 resident adapter; one target weight copy; peak 15.09 GiB; identical to codex-1's run.
Planner evidence (33 bank identities, 60 pre-score candidates, 64 launch dry runs, vLLM view equivalence) reviewed from the acceptance JSON.
Next: operator M1 (baseline + 63 filter jobs on the training-general reference, then admission), per followspec/PRODUCTION_DATA.md.

## 2026-10-06T04:18:28-04:00 — codex-1 — Claim immutable filter retry overlay

Accepted originalFIX-4 pipeline remainsverified. ConcreteM1 failures005/009 exposedrecoverygap: filter_runs.json points atfailedartifactdirs, and rerunningtherewouldoverwritehistoricalartifacts. Reopenownrow for explicit retry-filters stage: requireselectedfailedtargets, writefreshroundoverlay referencingunchangedregistry/plan/reference/baseline andalluntouchedruns; emitonlyselectedretryjobswithfreshpaths; admissionusesoverlay. Oldfailedoutputs retained. Nochangedcandidate/seed/admissionthreshold; nonewGPUjoblaunchedbybuilder. Testsfirstrejectsuccessful/unknown/activecells, unchangedoriginalbytes, subsetretryandadmissionmapping. P0preemptsB10; B6nativecapacitypasses,freshmixtureexportawaitsM1slots.

## 2026-10-06T04:24:40-04:00 — codex-1 — Retry overlay PASS → review / Handoff

Tests firstmissingretry_filters; now130testsPASS (FIX4_retry_before/after_20261006.log). Explicitretry-filters commandrefusessuccessful/active/unknown/duplicatetargets, verifiesoldstagehashes, preservesoriginalbytes, changesonlyselectedrunpathsandjobtags, keepsalljobdefinitionsforlaterchainedretries. Sourceed3f905mergedmain/pushed. No seed, candidate, model, reference, baseline or admissionthreshold changes.

RealM1overlay: artifacts/FIX4_M1_retry_overlay_20261006, exactly2retryjobs for CharlesLi/llama_3_gsm8k_cot_simplest (005) and CharlesLi/llama_3_gsm8k_helpful (009);61otherpathsunchanged. Bothactual atlas.filter_pool CLI --dry-run passed; acceptance artifacts/FIX4_retry_acceptance_20261006/acceptance.json. Originalfailedcellshaveconfig/results/failure preserved. M1initial63jobsfinished,admitexit1asexpectedforfailedcells. NoCPUplannerclaimedadmission.

Handoff: operatorrunnew filter_jobs.jsonl (existing spec usesvalidrun-M1 tag andunchangedfiltercode), then `python -m followspec.production admit --round-dir /home/heck2/sbhansali8/SpecTLM/artifacts/FIX4_M1_retry_overlay_20261006 --output NEW_ADMISSION`. No need rebuild/re-run61successfulcells. Verifythisextensionthendone; originalFIX4productionacceptance remainsvalid. BuilderB6exportrunningonheck-srv3:2, B10boundedfull64onheck-srv3:1; exclude those2slotsfromanyretryqueueuntiltheyfinish. AllotherM1queueassignmentscompleted.

## 2026-10-06T04:45:54-04:00 — codex-1 — Claim D-28 reduced-bank integration

Read latestmain3068513: operator started nine Llama training prompt retries and two M1 filter retries. D-28 drops banks still below500 after6400attempts and recomputes MVD1000*n_bank / FS round(1000*n_bank/n_targets). Current allocate_queries hardcodes33/33000; strict registry also couples mixture source bank and admission universe. Reopen FIX-4 to implement strict evidence-backed eligibility and count recomputation; preserve existing frozen pool, plans and artifacts. Asked owner whether already sampled mixtures using dropped banks stay with original admission proof or require fresh plan; do not choose a research policy implicitly. Tests and eligibility/count implementation can proceed independently.

## 2026-10-06T04:52:58-04:00 — codex-1 — D-28 partial build / Handoff

Branch e1e70fd pushed, not merged: evidence-backed bank-eligibility stage and explicit reduced allocation.11 new tests firstfailed thenpassed;143 integrated PASS. Real24 legacy workloads passed72 evidence-file hashes (FIX4_D28_legacy_audit_20261006). Remaining9 retries running. Full integration requires owner clarification on sampled mixtures whose sources are dropped; asked in chat, no answer yet. Mark blocked on that policy, continue B10. Do not discard or redraw candidate mixtures implicitly, nor edit frozen pool. Existing retry-overlay on main remains accepted/usable. Full details in branch journal.

## 2026-10-06T05:03:11-04:00 — codex-1 — Handoff

D-28 branch e1e70fd remains unmerged pending the mixture-source decision asked in chat. Prepared the final33-cell map at artifacts/FIX4_D28_bank_runs_20261006/bank_runs.json (24 original completions plus9 explicit retry paths). At04:57,26/33 workloads were complete;7 retries still active. The bank-eligibility stage must wait for complete or fully exhausted evidence from every mapped cell. Once policy is specified, integrate it with allocation/admission/source provenance, merge latestmain (now B10), rerun tests, and emit fresh jobs. Important launch detail: the original M1 spec uses an older execution checkout; new M2 jobs need a fresh tagged main with FIX-5, and mixture-prompt job generation needs an explicit D23 oversampling option. Do not mutate historical specs or jobs. Existing M1 round1 admission is29; original D27 requires secondround to seek30. No new global pause marker exists.

## 2026-10-06T05:04:29-04:00 — codex-1 — Independent M2 launch preparation

Before stopping on the pending policy, build the remaining independent job-planning change: optional clean execution-checkout override and explicit D23 oversampling in mixture prompt jobs. Both preserve historical defaults and immutable stages; no GPU submission or mixture decision. This prevents future jobs inheriting the older M1 checkout without FIX-5. Tests first on codex/FIX-4.

## 2026-10-06T04:50:45-04:00 — codex-1 — D-28 eligibility and counts built / Handoff

Tests written first:11 failures from missing eligibility module/argument (FIX4_D28_before_20261006.log). Now143 integrated tests PASS (FIX4_D28_integrated_20261006.log). New bank-eligibility CPU stage checks complete original-bank coverage, adapter/base pins, production-only training paths, unique500 queries, or a completed6400-attempt shortfall with matching raw/round/filter/result evidence. Crashes/missing/partial/unpinned runs cannot justify a drop; outputs preserve original inputs. Pure allocation accepts explicit eligible bank IDs and recomputes1000*n_bank budget; legacy default still requires33. No pipeline consumes reduced-bank allocation until mixture policy is specified.

Real audit of24 completed pre-FIX5 workloads PASS (artifacts/FIX4_D28_legacy_audit_20261006/results.json;72 hashed evidence files). Nine retries still running, so full-bank eligibility is pending and no original pool/candidate/admission changed. CLI: python -m followspec.production bank-eligibility --plan ORIGINAL_PLAN --bank-runs JSON_MAP_OF_FINAL_CELL_DIRS --output NEW_AUDIT. Owner clarification pending: retain existing mixtures/admission or recreate from remaining bank. This research choice affects the admission universe and mixture source provenance; do not silently choose. M1 first round now29passed aftertwofilterretries; secondroundrequiredbyD27, notgatewaiver. DFlash bounded retry continues independently.

## 2026-10-06T05:06:39-04:00 — codex-1 — M2 execution options pass

Two tests first failed (FIX4_execution_before_20261006.log);145 integrated tests now pass (FIX4_execution_after_20261006.log). Added optional --code-repo to mixture-prompts/responses: requires a clean checkout and identical engine lock, records the commit, preserves source stages and all model/data/seed settings. Added explicit --d23-oversampling for mixture jobs; legacy defaults stay unchanged. This independent portion is ready alongside D-28 eligibility/count helpers. Policy-dependent response/admission integration remains pending the owner answer. No GPU jobs launched.
