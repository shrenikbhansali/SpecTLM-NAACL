# Updated return handoff to the rebuttal planning agent

**Prepared by codex-1, November 27, 2026, 17:15 Eastern.** This supersedes the November 26 return handoff for current status. It incorporates the owner-approved November 26 planner update (D-61) and accelerated deadline (D-62). The historical document is retained.

**All required P0 results were published by 10:40am November 27, before the noon target.** Independent operator verification at 16:40 reproduced the numerical report exactly, checked all 24 newly required GPU jobs exited successfully, and reran 78 regression tests. All new results remain **pilot** until the owner approves their use. No paper files were edited and nothing was posted to OpenReview.

The only outstanding new experiment is optional **E8-lite multilingual repair**. Its training is running; there is no repaired multilingual result yet. The original scratch process also remains active under its November 28 noon stop, but the requested fifth-epoch result is complete. The planner can work from the required results now.

## 1. What changed since the previous handoff

| Item | Current status | Evidence / result |
|---|---|---|
| E4c, matched-capacity EDA 2×2 | Complete | Interface beats EDA-50M on both selected and random 8k, on both panels; two seeds. |
| Timing-divergence characterization | Complete | All 120 serving processes; 840 cross-process pairs; matching-output comparisons and same-process diagnostic. Divergence is not equal across arms. |
| E3a measured throughput | Complete | Three 200-step trials; audited data and explicit length policy; labelled one-epoch extrapolation. |
| E3b scratch epoch 5 | Complete | SPEED/MATH acceptance and cumulative measured training/data GPU-hours. |
| E1 raw cells and requested ratio | Complete | Four derivative-text targets, a/b/c/d, d−a and (d−b)/(d−a), with paired CIs. |
| E2 restoration table | Complete | Three-seed checkpoint interventions recorded in RESULTS.md. |
| E4 selected EDA-50M versus full | Complete | Explicit two-seed paired comparison in RESULTS.md. |
| E5 final off-the-shelf repeat | Complete | Final matrix is 120/120 processes; no timing repeat remains. |
| E8-lite | Training | Aya generation and reference evaluations complete; mixed-data repair and its evaluations pending. |
| E6, E7, E9, EDA native 20 epochs, EDA seed 2 | Not run for the response | Dropped by D-61. No SGLang integration. Do not queue them. |
| E10 | Complete | Environment inventory and all ten exact acceptance-anchor reproductions passed. |

The original E1/E2/E4/E5 results remain available. The old handoff's unfinished-cost, 119/120 timing and proposed-only E4c statements are obsolete. The new fifth-epoch checkpoint was evaluated at 10:39am and included in the 10:40am publication.

## 2. Measurement contract

Acceptance uses frozen harness `6da2e4265c0398ec0de5affaf23b0bd1df0be445`, vLLM **0.31.0**, A40, greedy decoding, EAGLE-3 K=4, batch 8 and a 512-token cap. Compared arms use identical target-rendered prompt token IDs. Tau includes the bonus token. New panels are **SPEED-128 and the first 128 MATH-500 problems**; do not call a 128-query mean a full MATH-500 mean.

Acceptance uncertainty uses 10,000 paired seed/query bootstrap resamples: two seeds for E4c/E4, three for E2, one for the scratch and trained-1B comparisons. The headline panels have n=128 with no zero-step exclusions. Timing uses seed-0 checkpoints, three fresh processes × three warm passes, with cold/startup retained separately. Its CIs resample processes and paired prompt batches; they do not include training-seed variation.

The official drafter uses the FIX-24 target-embedding path. Both targets use their default template/chat mode; Nemotron has no reasoning system turn. The current acceptance references reproduced the required paper anchors within the specified tolerance. Current seed-0 references and original three-seed paper means should not be interchanged.

## 3. E4c: the new matched-capacity EDA result

ReFit-interface trains **50,331,648** parameters; EDA-50M trains **50,339,840** (the 8,192 difference is routing). Within each subset/seed, data hashes, batch plans, steps, optimizer, learning rate, native objective and source drafter match. Seeds are 0 and 1. The six new trainings and twelve evaluations consumed **11.343 A40 GPU-hours**, within the 15-hour budget.

| Panel | Data | EDA-50M tau [95% CI] | ReFit-interface tau [95% CI] | Paired interface − EDA [95% CI] |
|---|---|---:|---:|---:|
| SPEED-128 | EDA-selected 8k | 2.144 [2.085, 2.201] | 2.343 [2.275, 2.409] | +0.199 [0.173, 0.224] |
| SPEED-128 | Random 8k | 2.168 [2.106, 2.228] | 2.382 [2.309, 2.451] | +0.214 [0.185, 0.243] |
| MATH-128 | EDA-selected 8k | 2.344 [2.310, 2.377] | 2.583 [2.550, 2.616] | +0.239 [0.222, 0.257] |
| MATH-128 | Random 8k | 2.488 [2.452, 2.522] | 2.734 [2.697, 2.770] | +0.246 [0.220, 0.269] |

This supplies a close parameter-count comparison without assigning the methods different training subsets. The advantage occurs on both subsets. Random data gives higher mean acceptance for both methods here; preserve that observation.

The earlier ReFit-full comparison also remains: on selected 8k, full minus EDA-50M is **+0.293 [0.267, 0.317] SPEED** and **+0.311 [0.290, 0.333] MATH**. Full versus the larger 176M EDA port gives **+0.260 [0.228, 0.290] / +0.282 [0.256, 0.309]**. Those full-repair comparisons are not parameter matched.

EDA port details remain material:

- Pinned released code: `a29f0381479a92d0f3114fd264cd790bab3a208b`. Its default shared/private expert pair uses independent singleton gates, yielding additive experts, rather than a joint two-expert softmax. Shared weights remain frozen and were audited.
- PCA-128 and the 90th-percentile Mahalanobis score are documented port choices fixed before evaluation. Both private widths are reported.
- This is **EDA adapted to EAGLE-3 under the matched repair protocol**, not a reproduction of the original architecture and native 20-epoch schedule.
- The port **does serve in unmodified vLLM**, by folding the additive experts into a wider ordinary SwiGLU. The distinction is that ReFit keeps the released architecture; do not claim EDA cannot deploy.
- Standalone first-draft medians (released 3.317ms, EDA-50M 3.364ms, larger EDA 3.378ms) exclude the verifier and full decoding context. They do not establish a large end-to-end EDA penalty.

Sources: [verified numerical/provenance JSON](verify_P0_20261127_1640/results.json), [E4 port notes](E4/notes.md), [full tables](RESULTS.md).

## 4. E3: measured scratch curve and cost

Scratch uses 64k R1 responses, one seed and one continuing 20-epoch cosine schedule. Intermediate exports are not separately annealed short runs. All acceptance below is n=128.

| Epoch | Training GPU-h, cumulative | Generation + training GPU-h | SPEED tau [95% CI] | MATH tau [95% CI] |
|---|---:|---:|---:|---:|
| 1 | 14.107 | 50.186 | 1.745 [1.702, 1.787] | 1.981 [1.943, 2.017] |
| 2 | 27.331 | 63.410 | 1.926 [1.875, 1.976] | 2.306 [2.265, 2.347] |
| 5 | 67.017 | 103.096 | 2.155 [2.090, 2.218] | 2.612 [2.568, 2.655] |

All 61 original successful generation logs were recovered and reconciled: **36.078938 A40 GPU-hours for 64k**, including the reused 16k Alpaca responses and the 48k Alpaca/Dolly extension. Training costs above are cumulative trainer elapsed time through each export, including initialization/export, excluding outer launch overhead, failed attempts and evaluation. They are checkpoint costs, not the total runtime of the still-active process.

The reproduced warm-start 16k full repair has tau **2.524 / 2.989** on these same panels. Its paired advantage over epoch-5 scratch is **+0.369 [0.323, 0.416] SPEED** and **+0.377 [0.346, 0.409] MATH**. Prompt IDs and rendered token IDs were checked exactly, including the first-128 extraction from the full-MATH reference. This measures the advantage at this checkpoint; it does not establish eventual scratch saturation or a scratch/repair crossover budget.

E3a is now complete as a separate measured-throughput exercise. The same 2,000 ShareGPT/UltraChat prompts were regenerated at 512 and 2,048 caps; 2,000 pinned native OpenThoughts math answers were also profiled. Each trial ran 200 training steps, including online teacher capture. Both all-step rates and steady steps 21–200 are retained.

| Regeneration cap | Projected generation, 532k | Projected training, 532k regenerated + 114k native | One-epoch total |
|---|---:|---:|---:|
| 512 | 294.93 GPU-h | 245.87 GPU-h | 540.80 GPU-h |
| 2,048 | 1,097.46 GPU-h | 547.22 GPU-h | 1,644.68 GPU-h |

These are **one-epoch lower-bound extrapolations from measured throughput**, not measured training costs of the released dedicated drafter. The logged policy preserves prompts and clips responses to 2,049 input IDs (2,048 shifted tokens): 0/2,000, 225/2,000 and 1,763/2,000 examples were clipped in the 512, 2,048 and native samples respectively. The native response-model revision is unpublished; its dataset revision pins the exact text. Do not omit the length policy when using the projection.

Sources: [scratch/raw/cost reconciliation](verify_P0_20261127_1640/results.json), [paired scratch comparison](verify_P0_20261127_1640/scratch-vs-warm.json), [throughput evidence](verify_P0_20261127_1640/throughput/results.json).

## 5. E5: trained 1B and completed timing diagnosis

The student is a full Llama-3.2-1B fine-tune with exact full-vocabulary forward KL. Both targets selected LR1e-5/three epochs from the four-setting held-out grid. Student training uses 15,744 responses plus 256 held-out queries; the source ReFit checkpoints trained on all16k. At matched K=4, the student has **higher acceptance on all four panels**, by tau +0.367/+0.425 for R1 SPEED/MATH and +0.441/+0.394 for Nemotron. All four paired CIs exclude zero.

Timing K was selected on held-out throughput, separately by batch, not on these evaluation panels. R1 student uses K3 at both batches; Nemotron uses K4 at b1/K3 at b8; ReFit uses K4. All120 final processes, including the last off-the-shelf repeat, are complete. Ratios below are ReFit-full/student warm output-token throughput, n=128:

| Target / panel | Batch1 ratio [95% CI] | Batch8 ratio [95% CI] |
|---|---:|---:|
| R1 SPEED | 1.191 [1.136, 1.244] | 0.932 [0.818, 1.075] |
| R1 MATH | 1.290 [1.277, 1.302] | 1.280 [1.252, 1.308] |
| Nemotron SPEED | 1.179 [1.108, 1.246] | 0.989 [0.851, 1.159] |
| Nemotron MATH | 1.270 [1.257, 1.284] | 1.252 [1.229, 1.273] |

Both SPEED-b8 comparisons remain inconclusive. Higher student acceptance and its additional drafting cost must be distinguished.

The requested divergence characterization is finished; the underlying cause is not resolved. It covers every arm/process pair (840 pairs), within-process repetitions, exact completion equality and first-divergence quartiles. **No-spec versus no-spec exact equality ranges from 5.38% to47.40% across panels/batches.** Divergence therefore is not exclusive to speculative arms, but rates differ across arms: the evidence does not establish that it affects them alike.

Restricting to query outputs identical across all six full/student processes and all three warm repetitions leaves:

| Batch1 panel | Matching n | ReFit/student ratio [95% CI] |
|---|---:|---:|
| R1 SPEED | 1 | 1.411 [1.408, 1.416] |
| R1 MATH | 16 | 1.280 [1.249, 1.309] |
| Nemotron SPEED | 11 | 1.334 [1.194, 1.420] |
| Nemotron MATH | 8 | 1.321 [1.249, 1.391] |

These are small selected subsets, especially n=1; they cannot establish an effect over the full population. No complete original batch8 survives the matching condition, so matching-output batch8 timing is not estimable. First-divergence-truncated timing is also not identifiable: no per-token timestamps were saved, and prorating total time by tokens would invent a measurement.

The extra one-prompt, same-process no-spec check passed: three warm completions were identical. That limited diagnostic does not establish fresh-process determinism. The throughput results describe measured serving on the recorded outputs, not a proof of bit-identical execution across methods.

Sources: [all timing diagnostics and matching subsets](timing_divergence_20261126_all120/results.json), [every process pair and divergence quartiles](timing_divergence_20261126_all120/process-pairs.csv), [within-process pairs](timing_divergence_20261126_all120/within-process.csv), [same-process check](verify_P0_20261127_1640/determinism.md), [E5 selection and timing tables](RESULTS.md).

## 6. E1/E2 interpretation and report-only additions

All requested derivative-text a/b/c/d cells and CIs are in RESULTS.md, with a=parent taps/parent verifier, b=parent/child, c=child/parent, d=child/child. The requested deployment ratio is `(d−b)/(d−a)`, recomputed in every paired resample; it differs from the averaged-feature share.

| Target | d−a, percentage points [95% CI] | Requested ratio [95% CI] |
|---|---:|---:|
| R1-Llama | −4.983 [−5.763, −4.220] | −0.235 [−0.402, −0.103] |
| Nemotron | −10.621 [−11.726, −9.481] | 0.292 [0.226, 0.354] |
| R1-Qwen3 | −5.701 [−6.447, −4.954] | −0.186 [−0.288, −0.096] |
| GRPO control | −0.041 [−0.242, 0.163] | −0.053 [−6.855, 8.672] |

Each uses64 paired contexts. The RL denominator crosses zero; its ratio is unstable. These are fixed-text HF agreement measurements, not served acceptance. Feature and policy averaged effects sum to d−a; interaction d−b−c+a is not a third additive contribution. Public-reference contexts also differ in questions from the generated-text contexts.

E2's three-seed matched-capacity result is unchanged: whole-drafter LoRA modestly exceeds dense-interface repair on both targets and panels. Interface retains about92.5–94.6% of its improvement over reuse, a secondary descriptive ratio rather than a noninferiority result. Matched decoder/head adaptation also slightly exceeds interface. The new E4c win does not reverse these E2 findings.

The requested checkpoint-restoration table is in RESULTS.md. Restoring the interface or restoring all non-interface weights reduces acceptance versus intact whole-LoRA. These are interventions on jointly trained weights, not independently trained component-only models. Corrected shard exports are used; invalid v1 cells remain excluded and preserved.

Sources: [full raw-cell and restoration tables](RESULTS.md), [independent E1/E2 reduction](verify_P0_20261127_1640/results.json), [three-seed capacity evidence](E2/reduction_20261125_2010/results.json).

## 7. Optional E8-lite and operational handoff

At17:14ET, mixed-data full repair is healthy at **784/4,492steps** on heck-srv4:0. It started16:38. Forecast for training plus frozen evaluation is **20:00–21:00ET**, conditional on continued progress. No multilingual improvement is claimed before those evaluations finish.

The data contain12k unchanged original Alpaca responses plus4k Aya instructions replacing uniformly selected seed0 positions. Language labels follow SPEED's multilingual subset: Arabic, English (including translation tasks), French, Spanish, Thai and Vietnamese. Aya training counts are1,667/1,000/334/333/333/333; held-out128 counts are53/32/11/11/11/10. All evaluation sets, original English training prompts and the new Aya test panel were used in the documented deduplication.

Generation finished Thursday23:27, then waited for the required manual decoded-response/mask audit until Friday16:37; that interval was not training. All4k identities/masks were verified and five decoded examples inspected. The target sometimes switches languages or makes factual mistakes; outputs were preserved, not selected for quality. 2,511/4,000responses hit the512cap. The existing English-repair and reuse Aya128 evaluations are complete. The watcher will evaluate the mixed repair on Aya128 and SPEED128 and reduce the multilingual12 subset pairwise against both references.

Scratch remains on srv4:1,101,571steps at17:14. Its requested epoch5 result is final; the original process must stop no later than **November28noon ET**. No new scratch recipe/export schedule is authorized here.

Do not start another dispatcher. Canonical queue PID1202986 uses `--owner method-M1 --exclusive-owner`, manifest `rebuttal/preflight_20261124_exactfamily/jobs.jsonl` and log `artifacts/M2_D28_20261006/response_queue.log`. CPU dependency/report processes are2771095 (D61 publisher),2966750 (deadline-priority controller),836737 (export watcher). No current watcher alerts. The publisher successfully refreshed at16:42; data audits are finished, so E8 has no further manual gate before evaluation.

Budgets: completed original E4=16.519GPUh; new E4c=11.343/15; E2≈31.182/40; E5=135.870/150 completion ceiling. E8 retains12GPUh; E3a37.5; scratch has its time stop. E4c retains experiment=E4 in the reused pipeline, so some automatic E4 totals already include it—do not add it twice. Campaign totals include searches/evaluation/failures and are not single-model repair costs.

No new owner decision is needed for the remaining approved E8 work. E6/E7/E9, native20-epoch EDA, EDAseed2 and SGLang remain out of scope. If E8 is not final by November28EOD, report it as not run for the response.

## 8. Evidence and next actions for the planner

Use E4c for the close capacity/data comparison, E3b for the measured longer scratch control, and E3a only as a labelled throughput extrapolation. Keep the trained student's acceptance advantage, E2 LoRA advantage and SPEED-b8 nulls alongside favorable results. The timing characterization answers the requested diagnostic; it does not establish equal divergence or a numerical root cause. Final wording and research framing remain owner decisions.

| Deliverable | Source |
|---|---|
| Complete current tables | [RESULTS.md](RESULTS.md) |
| Short verified update | [LANDED-20261127.md](LANDED-20261127.md) |
| P0 completion, all24 jobs and verification | [completion.json](verify_P0_20261127_1640/completion.json), [verification.json](verify_P0_20261127_1640/verification.json) |
| Frozen numerical/provenance snapshot | [results.json](verify_P0_20261127_1640/results.json) |
| Latest automatic snapshot pointer | [latest.json](D61_controller_20261126_1722/latest.json) |
| Original planner scope | [PLANNER-UPDATE-20261126.md](PLANNER-UPDATE-20261126.md) |
| Live progress / process handoff | [STATUS.md](STATUS.md), [JOURNAL.md](JOURNAL.md) |
| Formal pilot ledger | [EXP-ATL-031.md](ledger/EXP-ATL-031.md) |

The cluster agent will finish and verify E8, then update RESULTS.md and the board. The planner can prepare the response from the completed P0 evidence now. There is no paper-edit or OpenReview-posting authorization in this handoff.
