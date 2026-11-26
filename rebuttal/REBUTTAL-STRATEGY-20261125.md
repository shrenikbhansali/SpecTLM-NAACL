# Rebuttal evidence audit and recommended emphasis

November 25, 2026; codex-1. Proposal for the owner, not a change to the paper or its claims. Based on the three actual ARR reviews, the independently recomputed E1/E2/E4/E5 records, and the first two scratch checkpoints. All new benchmark means below use 128 queries; MATH means the first 128 problems. Results remain pilot.

## What is most likely to change a reviewer's assessment

The strongest supported case is **repairing an existing target-conditioned drafter is an effective way to recover serving performance, with a useful modular interface-only option**. It is not that interface tuning wins every adaptation comparison or that ReFit has the highest acceptance of every drafter.

JAeB explicitly says they can increase their score if weaknesses 1–3 are answered: novelty, crossover interpretation, and missing EDA/distilled-small-model baselines. RLU2 raises the same issues plus the dedicated-cost estimate. u4ad focuses on novelty, equal-capacity LoRA, and estimated cost. These shared objections should determine the response's order. Another broad census or another model scale would be less targeted than completing the existing controls.

No experiment or wording can force a score increase. The most persuasive response makes each requested comparison easy to assess and separates measured findings from proposed explanations.

## 1. Lead with the new direct adaptation baseline

On identical EDA-selected 8k examples, the larger released-default-width EDA port versus ReFit-full gives:

| Panel | EDA tau | ReFit-full tau | Paired ReFit minus EDA, 95% CI |
|---|---:|---:|---:|
| SPEED | 2.18 | 2.45 | +0.27 [0.24, 0.30] |
| MATH | 2.38 | 2.65 | +0.27 [0.25, 0.29] |

This directly addresses RLU2 W3 and JAeB W3. Report both EDA widths and the complete selection ablation; the smaller port also trails ReFit-full. The claim is about the **EAGLE-3 port under matched data, tokens, steps and native objective**. It is not a reproduction of the original EDA architecture and 20-epoch schedule, nor an identical-GPU-hour comparison. The larger EDA run used 1.43 training GPU-hours versus 2.01 for the paired ReFit-full seed.

Important distinction: the larger EDA port trains 176.17M parameters; the smaller trains 50.34M; ReFit-full trains 424.69M. Thus this result supports a practical method comparison but does not isolate an advantage at equal adaptation capacity. The cleanest small additional control is ReFit-interface on the same selected 8k, against the 50.34M EDA port. Its data, objective and optimizer should be fixed before running, and both outcomes reported. This control is proposed, not a result.

Do not argue that EDA cannot be deployed in unmodified vLLM: our released-code additive-expert port does load and serve without an engine patch. Its larger MLP changes the model architecture, but our measured standalone first-step latency increase is small. The advantage currently established for ReFit is the observed repair result and preservation of the released architecture, not a demonstrated large EDA serving penalty.

## 2. Answer the interface-versus-LoRA objection quantitatively

The three-seed comparison confirms that whole-drafter LoRA and matched decoder/head tuning slightly outperform dense-interface tuning. Arguing otherwise would conflict with both reviewers and our new data.

A more informative operational statement is how much improvement is obtained while leaving the decoder and head unchanged. Define, explicitly,

`fraction = (tau_interface - tau_reuse) / (tau_whole_LoRA - tau_reuse)`.

The ratio is recomputed within each paired seed/query bootstrap sample, rather than divided from separately computed CI endpoints:

| Target | Panel | Interface fraction of whole-LoRA improvement, 95% CI |
|---|---|---:|
| R1 | SPEED | 93.4% [90.7, 96.0] |
| R1 | MATH | 92.5% [90.7, 94.5] |
| Nemotron | SPEED | 93.0% [89.9, 96.5] |
| Nemotron | MATH | 94.6% [93.1, 96.1] |

All four settings and all three seeds are included. Present the absolute tau differences next to this derived ratio: whole-LoRA's advantages are 0.045/0.070 on R1 SPEED/MATH and 0.048/0.057 on Nemotron. Their paired intervals exclude zero. The ratio is a descriptive efficiency tradeoff, not a predeclared noninferiority test.

This supports the modular deployment option: most of this comparator's gain is available through one existing projection, with the released decoder/head bit-identical. It does not prove that most degradation was caused there. A shared-decoder, multi-tenant deployment is a plausible application, not a measured serving result in this campaign. Equal-parameter LoRA also has a small adapter payload, so payload size alone is not unique to the interface.

## 3. Make the trained independent model a serious comparison

The distilled 1B was trained with full-vocabulary KL, selected from four LR/epoch settings on held-out repair queries, and swept over K=2–5. It beats ReFit-full's K=4 acceptance on both targets and both panels. That fact should accompany the speed comparison.

The completed warm-throughput measurements give ReFit-full / distilled-1B ratios:

| Target | Panel / batch | Throughput ratio, paired 95% CI |
|---|---|---:|
| R1 | MATH / 8 | 1.28 [1.25, 1.31] |
| Nemotron | MATH / 1 | 1.27 [1.26, 1.28] |
| Nemotron | MATH / 8 | 1.25 [1.23, 1.27] |
| Nemotron | SPEED / 1 | 1.18 [1.11, 1.25] |
| R1 | SPEED / 8 | 0.93 [0.82, 1.08] |
| Nemotron | SPEED / 8 | 0.99 [0.85, 1.16] |

The observed distinction is acceptance versus drafting overhead: higher acceptance from a larger independent model does not ensure higher throughput. Both SPEED batch-8 comparisons are inconclusive. Do not remove them or redefine the benchmark aggregate to hide that.

**Timing qualification:** raw continuations differ across some greedy timing arms and also across some fresh processes of the same arm. The latter includes Nemotron no-spec MATH (94/128 queries differ across processes 0/1), so the mismatch is not unique to the distilled baseline. This does not establish its cause or prove the implementations lossless. Finish the fixed-prefix/output diagnostic before treating the speed ratios as a settled quality-preserving advantage. Report token totals and throughput normalization meanwhile.

The 12 missing R1 batch-1 timing processes are now authorized and queued in immutable retry directories; three are running on srv4. Completing these is more valuable than adding an unrelated benchmark. Timing CIs cover process/query variation, not training-seed variation.

## 4. Resolve the crossover question with the requested cells

Publish a, b, c and d and the conditional deployment contrasts. For derivative-generated R1 text, changing parent to child taps under the child verifier gives `d-b = +1.2 pp [0.6, 1.8]`; for Nemotron it gives `-3.1 pp [-3.9, -2.3]`. The interaction is `d-b-c+a`, +6.3 pp for R1 and +7.6 pp for Nemotron. Feature and policy effects as defined in the existing report sum to `d-a`; interaction is not an extra additive term in that identity.

These results do not support a general claim that derivative features by themselves cause most deployment degradation. They establish that feature compatibility depends on the verifier policy and context. Keep that diagnosis separate from the intervention result that changing the interface is useful. Showing the requested raw cells directly answers JAeB W2 and RLU2 W1 more convincingly than a stronger causal slogan.

## 5. Replace the cost argument with measured learning curves

Scratch training after one and two epochs reaches SPEED tau 1.75 and 1.93, and MATH tau 1.98 and 2.31. Warm-start ReFit-full is 2.52 and 2.99 on these same panels. The current evidence shows a substantial finite-budget advantage, not that scratch never catches up.

Keep the scratch run advancing and report cumulative measured GPU-hours at each checkpoint. Intermediate points are on one 20-epoch cosine schedule, not fully annealed independent short runs. E3a will measure generation/training throughput for the stated dedicated-data recipe; its one-epoch projection must remain explicitly extrapolated and cannot become the unknown actual training cost of the released oracle. Avoid making the rebuttal's main case depend on the old 400x estimate.

## Recommended use of remaining compute

1. Finish the fixed 12-process R1 timing matrix and investigate timing-output differences. Already running/queued; no new K or test-set selection.
2. Continue measured scratch training and complete E3a throughput. These answer the cost concern shared by all three reviews. Source datasets are now pinned, license-checked and downloaded.
3. Repeat the existing EDA configurations at an additional approved seed, paired with the already-trained ReFit selected-8k seed 1. This tests stability without changing the recipe or searching for a favorable baseline setting.
4. If adding one small controlled arm, use the matched-data/parameter ReFit-interface versus EDA-50M comparison described above. Keep this separate from the already completed full-repair comparison.
5. Then complete the prescribed multilingual and tree experiments as capacity allows. They answer RLU2's language question and JAeB's chain-only concern, respectively. They should not delay the explicitly requested baseline and cost evidence.

Do not spend the remaining window on a new 70B model, a broad hyperparameter sweep, or selecting favorable subdomains from these test sets. If a new operating regime is studied, state its practical rationale in advance and retain the complete original panels.

## Suggested response structure

Use one common response with a compact baseline table, then short reviewer-specific replies:

- **JAeB:** explicitly answer W1/W2/W3 in order: empirical contribution, raw deployment crossover cells, trained EDA and independent baselines. They identified these as score-changing questions.
- **RLU2:** the same baseline and crossover evidence, followed by three-seed capacity controls and measured scratch costs; add multilingual results if they complete.
- **u4ad:** acknowledge the precise capacity tradeoff quantitatively, distinguish empirical contribution from a new loss, and provide measured costs plus the exact engine version.

Lead with completed measurements. Keep missing/pending work in a separate short paragraph. Use current-campaign comparisons, preserve absolute values and null outcomes, and avoid promises of unmeasured performance.

Evidence: `LANDED-20261125.md`, `E45_verify_20261125_2010/results.json`, `E2/reduction_20261125_2010/results.json`, `review_audit_20261125/derived.json` and its `reduce.py`; actual reviews extracted to `review_audit_20261125/reviews.txt`. The ratio audit uses 10,000 paired seed/query resamples and no test-set selection.
