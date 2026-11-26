# Return handoff to the rebuttal planning agent

**Prepared by codex-1 on November 26, 2026, 16:05 ET.** This is a return against your November 24 E1–E10 plan, not a completion certificate. Verified result cutoff: November 26, 15:35 ET; live job check: 16:03 ET. New outcomes are **pilot** until the owner approves their use. No files under `paper/` were edited, and nothing was posted to OpenReview.

## Read this first

The requested **trained EDA baseline, matched-capacity component comparisons, crossover reanalysis and trained independent-1B comparison now have useful measured results**. The trained 1B timing comparison is complete; one off-the-shelf timing repeat remains. Cost measurements and the longer scratch curve are unfinished. Tree drafting, multilingual repair and the two P2 experiments have no new results yet.

The strongest supported response is that warm-start repair restores useful serving performance while preserving the released drafter architecture, with interface-only repair as a modular option. Three findings must accompany that account:

1. ReFit-full beats both EDA ports under the matched-data/step protocol, now replicated at two seeds. This is an EAGLE-3 port, not the original EDA training setup.
2. Whole-drafter LoRA and matched decoder/head adaptation modestly beat dense-interface adaptation. Interface-only nevertheless retains roughly 93–95% of whole-LoRA's improvement over reuse.
3. The trained independent 1B beats ReFit-full on K=4 acceptance. ReFit-full is faster in the measured batch-1 and MATH batch-8 comparisons; both SPEED batch-8 comparisons are inconclusive. Timing-output divergence remains an unresolved diagnostic.

Use the tables below as the current snapshot. [RESULTS.md](RESULTS.md) contains the full tables; dated historical implementation notes there and in journals are not current status statements. [STATUS.md](STATUS.md) is the live status log. The final reporting deadline remains November 28 EOD Eastern.

## 1. Status against every requested experiment

| ID | Status at this handoff | Delivered / remaining |
|---|---|---|
| E1 | Complete, independently verified | All 12 crossover groups, raw a/b/c/d, conditional contrasts and paired CIs; n=64 per group. |
| E2 | Complete, three seeds | Both targets and both panels; whole-LoRA, matched decoder/head and dense-interface comparisons, plus checkpoint-restoration ablations. |
| E3a | Generation running; training/reduction unfinished | Same 2,000 ShareGPT/UltraChat queries at caps 512/2,048. Retries had 848/216 responses at 16:03. Five-response/mask audits and 200-step trainer measurements still required. OpenThoughts source staged; native-data integration incomplete. |
| E3b | Running; epochs 1 and 2 evaluated | Continuous 20-epoch scratch run on 64k; approximately 3.6 epochs at last check. Next scheduled export epoch 5; mandatory stop November 28 noon. |
| E4 + E4b | Matched branch complete, two seeds | Both EDA widths s0/s1; ReFit-full selected/random 8k s0/s1; loadability, frozen-weight checks and standalone latency. Optional native 20-epoch EDA schedule and seed 2 not run. |
| E5 | Training/acceptance and all trained-student timing complete | Four LR/epoch settings per target, held-out selection, K2–5 sweep. 119/120 final timing processes complete; only R1 off-the-shelf SPEED/b1 repeat 2 remains, currently retrying. |
| E6 | Not run | No new SGLang/reference-engine tree-versus-chain comparison. Framework integration and fair same-engine references remain. |
| E8 | Not run | Aya pinned/downloaded; language selection, training/eval split, generation, repair and evaluation remain. |
| E7 | Not run | OpenThoughts source staged; no new 16k math-prompt long-response repair experiment. |
| E9 | Not run | No new repaired cell-d or 21-model CKA/cosine analysis. |
| E10 | Complete | Environment inventory and all ten exact acceptance reference reproductions pass. |

A proposed **ReFit-interface on EDA's exact selected 8k** arm is not in these completed results and has not been launched. Do not describe it as measured. It would add a close data-and-capacity match to the 50M EDA port if the owner elects to expand the plan.

## 2. Shared measurement contract

- Frozen acceptance harness: `6da2e4265c0398ec0de5affaf23b0bd1df0be445`; vLLM **0.31.0**; NVIDIA A40. Greedy, cap 512, identical target-rendered prompt IDs across compared arms. Acceptance batch 8; EAGLE-3 K=4; tau includes the bonus token.
- New benchmark panels: **SPEED-128 and the first 128 MATH-500 queries**. Exact paper-anchor reproduction separately used full MATH-500. Do not label the new 128-query means as MATH-500 means.
- Acceptance CIs: 10,000 paired prompt/seed bootstrap resamples; E2 has three seeds, E4 has two, E5 student has one. Zero-speculation-step queries are excluded pairwise. The headline comparisons below have n=128 and zero such exclusions.
- Timing: seed-0 checkpoints, three fresh processes × three warm passes; cold pass/startup retained separately. CIs resample process and prompt batch, not training seeds. Speedups below are output-token throughput ratios relative to same-campaign autoregressive references.
- Both targets use their default chat mode/template; Nemotron has no reasoning system turn. Training uses the FIX-24 target-embedding path for the official EAGLE-3 release.
- Ten acceptance anchors reproduced within the specified 0.03-tau tolerance. Original paper seed averages and current seed-0 references are not interchangeable.

## 3. E4: direct trained EDA comparison

Same selected 8k responses, same native TTT3 objective, tokens, steps and repair recipe. Two paired training seeds, n=128 per panel. Comparison to the larger released-default-width port:

| Panel | EDA tau | ReFit-full tau | ReFit minus EDA, paired 95% CI |
|---|---:|---:|---:|
| MATH first 128 | 2.373 | 2.655 | 0.282 [0.256, 0.309] |
| SPEED-128 | 2.178 | 2.437 | 0.260 [0.228, 0.290] |

The smaller EDA port also trails ReFit-full. EDA-selected versus random 8k ReFit-full, paired over seeds 0/1, gives delta tau **−0.05 [−0.08, −0.02] on SPEED** and **−0.28 [−0.31, −0.24] on MATH**. Selection did not help under this protocol; retain the result.

**Port facts that matter to the response:**

- Pinned released EDA code: `a29f0381479a92d0f3114fd264cd790bab3a208b`. One shared and one private expert use independent singleton softmax gates, making the release additive; these gates have zero gradient. This differs from a joint two-expert softmax description.
- The shared FFN, interface, attention, norms and head stay frozen. Both ports pass direct frozen-tensor checks. Private widths 4,096 and 14,336 train **50,339,840** and **176,168,960** parameters, respectively; ReFit-full trains **424,689,664**. Thus the full-repair comparison is not parameter matched or exactly GPU-hour matched.
- PCA-128 and the 90th-percentile Mahalanobis score are documented port choices because the release does not specify them. They were fixed before evaluation; both widths are reported.
- **EDA does serve in unmodified vLLM.** The additive experts can be folded into a wider ordinary SwiGLU. Do not claim that engine patches are required or serving is impossible. ReFit preserves the original architecture; this EDA port adds a wider MLP.
- Standalone b1 first-draft medians: released 3.317 ms, EDA-50M 3.364 ms, larger EDA 3.378 ms (1,000 forwards after 50 warm-up). These exclude verifier/KV-context costs and are not end-to-end speedups or evidence of a large EDA penalty.
- The original EDA architecture and optional 20-epoch native schedule were not reproduced. Call this **EDA adapted to EAGLE-3 under the matched repair protocol**.

Evidence: [E4 implementation notes](E4/notes.md), [E4 CSV](E4/results.csv), [verified raw reduction](E45_verify_20261126_1535/results.json).

## 4. E5: trained independent drafter

The baseline is a full fine-tune of Llama-3.2-1B-Instruct with exact full-vocabulary forward KL. Four settings per target (LR 1e-5/2e-5 × 1/3 epochs) were evaluated on 256 held-out repair queries. Both targets selected **LR 1e-5, three epochs**. Each student trained on 15,744 of the 16,000 responses; source ReFit checkpoints used all 16,000. State this small training-count difference.

K=2–5 acceptance sweeps are complete. Timing K was chosen by throughput on 32 held-out repair queries, separately by batch size, never on SPEED/MATH: trained R1 K=3 at b1/b8; trained Nemotron K=4 at b1 and K=3 at b8; off-the-shelf K=2 throughout. ReFit uses K=4.

### Matched-K=4 acceptance

Seed 0, n=128; paired 95% CIs. The independent student wins all four comparisons:

| Target / panel | ReFit-full tau | Distilled 1B tau | Student minus ReFit, paired 95% CI |
|---|---:|---:|---:|
| R1-Llama / MATH first 128 | 2.989 | 3.414 | 0.425 [0.384, 0.469] |
| R1-Llama / SPEED-128 | 2.524 | 2.891 | 0.367 [0.296, 0.448] |
| Nemotron / MATH first 128 | 2.881 | 3.275 | 0.394 [0.357, 0.432] |
| Nemotron / SPEED-128 | 2.496 | 2.937 | 0.441 [0.355, 0.534] |

### Throughput comparison

Same-campaign timing, n=128 per panel. Ratios greater than one favor ReFit. All eight trained-student comparisons have their three processes:

| Target / panel | Batch | Distilled speedup | ReFit-full speedup | ReFit / student, paired 95% CI |
|---|---:|---:|---:|---:|
| R1-Llama / SPEED-128 | 1 | 1.55× | 1.85× | 1.19 [1.14, 1.24] |
| R1-Llama / SPEED-128 | 8 | 1.38× | 1.28× | 0.93 [0.82, 1.08] |
| R1-Llama / MATH first 128 | 1 | 1.79× | 2.31× | 1.29 [1.28, 1.30] |
| R1-Llama / MATH first 128 | 8 | 1.61× | 2.06× | 1.28 [1.25, 1.31] |
| Nemotron / SPEED-128 | 1 | 1.56× | 1.84× | 1.18 [1.11, 1.25] |
| Nemotron / SPEED-128 | 8 | 1.47× | 1.45× | 0.99 [0.85, 1.16] |
| Nemotron / MATH first 128 | 1 | 1.74× | 2.21× | 1.27 [1.26, 1.28] |
| Nemotron / MATH first 128 | 8 | 1.56× | 1.96× | 1.25 [1.23, 1.27] |

**Important unresolved diagnostic:** greedy completion token IDs differ between some timing arms and also between some fresh processes of the same arm. For example, Nemotron no-spec MATH differs on 94/128 queries between processes 0 and 1. This shows that the mismatch is not unique to the student, but does not prove its cause or establish lossless equivalence. The reducer preserves mismatches, token totals and panel-time ratios. Treat throughput findings as provisional pending the fixed-prefix/output investigation; do not silently call them quality-equivalent speedups.

Both SPEED batch-8 CIs include a tie. The independent model's higher acceptance should be reported alongside its throughput. Timing intervals do not cover independently trained seed variation. One **off-the-shelf** R1 SPEED/b1 repeat remains; its absence does not remove any of the trained-student comparisons above.

Evidence: [E5 notes](E5/notes.md), [full sweep](E5/sweep.csv), [timing contrasts](E5/timing.csv), [selection grid](E5/selection.csv), [Nov26 verified summary](LANDED-20261126.md).

## 5. E2: capacity and adaptation location

Three paired seeds, n=128 per seed/panel. Whole-drafter LoRA beats dense-interface tuning by the following small but nonzero amounts:

| Target / panel | Interface tau | Whole-LoRA tau | Whole-LoRA minus interface, paired 95% CI |
|---|---:|---:|---:|
| R1-Llama / MATH first 128 | 2.792 | 2.862 | 0.070 [0.051, 0.088] |
| R1-Llama / SPEED-128 | 2.420 | 2.465 | 0.045 [0.027, 0.065] |
| Nemotron / MATH first 128 | 2.686 | 2.743 | 0.057 [0.040, 0.074] |
| Nemotron / SPEED-128 | 2.391 | 2.439 | 0.048 [0.024, 0.070] |

Matched decoder/head-only tuning also beats dense interface: delta tau **0.024 [0.002, 0.044] / 0.064 [0.045, 0.084]** for R1 SPEED/MATH and **0.046 [0.024, 0.067] / 0.045 [0.028, 0.063]** for Nemotron. Do not say the interface is the uniquely best parameter-matched location.

A secondary descriptive analysis quantifies the tradeoff: `(tau_interface − tau_reuse) / (tau_whole_LoRA − tau_reuse)`, recomputed within each paired seed/query resample. Interface-only retains:

| Target | SPEED | MATH |
|---|---:|---:|
| R1 | 93.4% [90.7, 96.0] | 92.5% [90.7, 94.5] |
| Nemotron | 93.0% [89.9, 96.5] | 94.6% [93.1, 96.1] |

This supports a modular option that leaves the decoder/head unchanged; it is not a predeclared noninferiority test or proof that most damage originates in the interface. Equal-capacity LoRA also has a small adapter payload. Multi-tenant shared-decoder serving has not been measured.

Checkpoint-restoration ablations are interventions on an already jointly trained LoRA checkpoint, not independently trained component-only models. Four initial ablation cells were invalidated for duplicate physical shard keys; corrected exports replaced them without deleting the originals.

Evidence: [E2 reduction](E2/reduction_20261125_2010/results.json), [invalid-run record](E2/INVALID-v1.md), [ratio audit](review_audit_20261125/derived.json).

## 6. E1 and E10: direct answers to interpretation and version questions

All 12 E1 groups reproduce: four targets × three text sources, n=64 sequences each, 10,000 paired resamples. With a=P taps/P verifier, b=P/C, c=C/P, d=C/C:

- Feature effect = `((c−a)+(d−b))/2`; policy effect = `((b−a)+(d−c))/2`.
- These sum to `d−a`. Interaction is `d−b−c+a`; it is **not** a third additive term in that identity.
- On derivative-generated R1 text, `c−a = −5.1 pp [−5.7, −4.5]`, but deployment contrast `d−b = +1.2 pp [0.6, 1.8]`; interaction **+6.3 pp [5.7, 6.8]**.
- On derivative-generated Nemotron text, `c−a = −10.8 pp [−11.7, −9.8]`, `d−b = −3.1 pp [−3.9, −2.3]`; interaction **+7.6 pp [6.7, 8.6]**.

Report the requested raw a/b/c/d table, not just averaged effects. The diagnosis is conditional feature/policy compatibility; it does not establish that changed features independently explain most deployment degradation. Public-reference contexts are MATH64 solutions while generated contexts use SPEED, so cross-source comparisons also change questions.

Paper and current engine are both vLLM0.31.0. Current inference: Python3.11.5, PyTorch2.13.0, CUDA13.0, transformers5.17.0, A40. Trainer uses transformers5.16.1 and Speculators0.9.0a0. Full freezes are retained. No SGLang experiment has run.

Evidence: [all E1 cells](E1/cells.csv), [E1 definitions](E1/notes.md), [version inventory](E10/versions.txt).

## 7. E3: what can be said about cost now

Scratch uses 64k R1 responses, seed0, one cosine schedule over20epochs. Epoch1/2 results, n128:

| Epoch | SPEED tau,95%CI | MATH tau,95%CI |
|---|---:|---:|
| 1 | 1.75 [1.70, 1.79] | 1.98 [1.94, 2.02] |
| 2 | 1.93 [1.87, 1.98] | 2.31 [2.26, 2.35] |

Current seed0 warm-full references on these panels are2.52/2.99. Intermediate points are not fully annealed short runs. Do not claim scratch never catches up or assign an unmeasured crossover cost. Cumulative checkpoint GPU-hour table and historical64k generation-cost reconciliation remain unfinished.

E3a is not yet a measured one-epoch cost estimate. It has 2,000 deduplicated prompts (256 ShareGPT,1,744 UltraChat), the same queries at caps512/2048, and staged OpenThoughts math sources. After generation, review five responses/masks, run the specified200-step training measurements, then compute the explicit one-epoch lower-bound extrapolation. Native OpenThoughts provenance/length handling still needs integration. Do not replace the unknown dedicated-checkpoint training cost with this extrapolation as though it were measured.

Campaign totals at the verified snapshot: E2 **31.2GPUh**, E4 **16.5GPUh**, E5 **134.4GPUh**, including failed attempts. These include baseline sweeps/evaluation/timing and are **not per-model adaptation costs**. E5 selected-training plus teacher-pass costs are about4.07GPUh R1 and3.21GPUh Nemotron, excluding original response generation, search and serving evaluation.

Owner budget decisions: E2 increased to40GPUh; E5 first120, then authorization to finish after the cap-stop, implemented with a bounded150GPUh operator guard. E4 remains18.75 and E3a37.5 (original budgets plus25%). Scratch retains its time deadline. No additional budget or recipe approval is needed for the currently running jobs.

## 8. Suggested use in the author response

This is advice for the owner/planner, not a change to the paper's framing:

- **JAeB:** explicitly answer novelty, crossover interpretation and missing baselines in that order; they identified these as score-changing issues. The contribution supported here is the empirical study and a deployment-compatible repair recipe, not a newly invented distillation objective.
- **RLU2:** give the conditional crossover cells, three-seed capacity comparison, trained EDA/1B baselines and measured scratch progress. Their multilingual question remains unanswered by new experiments.
- **u4ad:** give the exact engine version, quantitative interface/LoRA tradeoff and measured cost evidence. Keep the dedicated-cost extrapolation separate.

Lead with completed comparisons and their intervals. Preserve the student acceptance advantage, LoRA advantage, selected-data regression and SPEED-b8 nulls. Do not claim EDA cannot deploy, that tree/multilingual tests have run, that all new MATH means use500queries, or that all P0 work is finished. No experiment guarantees a score increase.

## 9. Remaining execution and evidence map

The cluster agent remains responsible for execution. Do not start another dispatcher while writing the response. Active at16:03: scratch on heck-srv4:1, final off-the-shelf timing retry on srv4:0, E3a generation caps512/2048 on srv4:2/3. Current usable capacity is four A40s, not the16slots listed in the queue; the other historical slots are occupied. The three retries passed startup after prior free-memory failures. Failed outputs/costs remain preserved. Terminal failures were not automatically retried, which caused idle time before the15:33 recovery.

Next execution priorities: finish/reduce that timing repeat; resolve the output diagnostic; complete E3a sample audits and throughput training; keep scratch checkpoints/evaluations advancing, stopping by Nov28noon; then E6/E8 and P2 as capacity permits. The proposed same8kinterface-versus-EDA arm is an owner choice, not a dependency of the current comparison.

| Item | Where |
|---|---|
| Current summary | [Nov26 results](LANDED-20261126.md), [full results](RESULTS.md), [status](STATUS.md) |
| Detailed interpretation proposal | [Reviewer strategy audit](REBUTTAL-STRATEGY-20261125.md) |
| Verified E4/E5 numerical snapshot | [results.json](E45_verify_20261126_1535/results.json), [exact-match verification](E45_verify_20261126_1535/verification.json) |
| Recompute E4/E5 | `.venv-transport/bin/python -m rebuttal.reduce_e45 --workspace /home/heck2/sbhansali8/ReFit --output <NEW_DIRECTORY>` |
| Run-level provenance | `rebuttal/runs/<run>/config.yaml`, `cmd.txt`, `git_commit.txt`, `metrics.json`, `cell/config.json`, raw per-prompt/timing JSON |
| Ledger | [EXP-ATL-031](ledger/EXP-ATL-031.md) — pilot, append-only updates |
| Operator journal | [JOURNAL.md](JOURNAL.md) — latest handoff gives process IDs and remaining integration |
| Canonical queue | PID1202986, owner method-M1/exclusive; manifest `rebuttal/preflight_20261124_exactfamily/jobs.jsonl`; log `artifacts/M2_D28_20261006/response_queue.log` |
| Latest retries | `rebuttal/startup_retries_20261126_1540/`; unchanged pinned code, settings and input hashes, fresh output directories |

Everything numerical in this document comes from completed records or explicitly identified partial measurements. Forecasts are operational only. Planning and final wording remain with the owner; pending experiments may strengthen or change the response and must be incorporated as they actually land.
