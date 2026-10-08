# P5 CPU triage pilot

A 16-query direct measurement ranks degradation well on this small frozen checkpoint panel; a much shorter prefix measurement is unreliable, especially for EAGLE-3. This is a retrospective diagnostic, not a certified deployment probe.

Two batch indices were selected by a fixed SHA256 rule without examining acceptance. Their 16 SPEED queries provide the probe; the remaining 112 queries define degradation as first-position retention below 0.9. Scores use A00/A10 paired raw counters from frozen `6da2e42` / vLLM 0.31.0 / A40. There are 21 noncollapsed post-trained checkpoints per drafter, with pretrained controls excluded. One immediate-EOS query has no acceptance opportunities and is excluded pairwise; exact effective n is recorded per checkpoint. No model was fitted, no cutoff tuned, and no post-cutoff training pool was used.

| Drafter | Probe | Checkpoints / degraded | AUROC [checkpoint bootstrap 95% interval] | TP / FP / FN / TN at fixed 0.9 cutoff |
|---|---|---|---|---|
| EAGLE-3 | 16 full requests, max512 tokens | 21 / 7 | 1.000 [1.000, 1.000] | 7 / 3 / 0 / 11 |
| EAGLE-3 | First16 speculative iterations on those requests | 21 / 7 | .602 [.204, 1.000] | 4 / 3 / 3 / 11 |
| DFlash | 16 full requests, max512 tokens | 21 / 10 | .945 [.818, 1.000] | 9 / 3 / 1 / 8 |
| DFlash | First16 speculative iterations on those requests | 21 / 10 | .773 [.518, .971] | 8 / 3 / 2 / 8 |

The EAGLE perfect-ranking interval is a degenerate empirical bootstrap on 21 observed models, **not evidence of perfect population accuracy**. Related lineages and the failure-enriched convenience sample further limit generalization. Ranking and the fixed decision cutoff differ: even the full probe gives false positives.

The captured two-batch generation times, counting each batch once and summing both target arms, have medians 45.2 seconds for EAGLE and 39.3 seconds for DFlash. Separate engine startups add median totals of 274.7 and 302.4 seconds. These are observed costs of the full request subset. The shortened prefix was reconstructed from saved counters; its wall-clock cost was not measured, and it is not equivalent to a fresh short run under altered serving settings.

Existing child‖parent KL is available on only ten included checkpoints with identical vocabulary support. For this comparator, its eight saved context queries are additionally removed from the label set, leaving104 disjoint label queries; both probes are compared against that same label set. Both KL and the full direct probe have AUROC 1.0 on that same small subset (four degraded checkpoints per drafter). This gives no evidence that KL beats direct measurement. Tülu's finite common-vocabulary conditional KL is excluded from this full-KL comparison. KL uses eight saved contexts and does not include their generation cost; there is no end-to-end cost claim.

Artifacts: `artifacts/P5_triage_20261008_1533/analyze_v2.py` and `analysis-v2/{plan.json,results.json}`; the disjoint KL comparator is `compare_kl_disjoint.py` / `KL-disjoint-results.json`. The initial KL comparison overlapped eight label queries and is superseded by this disjoint recomputation (same AUROCs). AUROC implementation passed synthetic perfect/reversed/tied/single-class checks before analysis; runtime assertions verify prompt pairing, frozen settings, unique batches and raw counters. The first script correctly stopped on the immediate-EOS case; the new version records effective paired n rather than treating undefined acceptance as zero. Ten thousand checkpoint bootstrap draws, seed0; one-class draws excluded and counted.

The archived 174-checkpoint census remains separate until exact frozen-harness compatibility is verified. This probe uses SPEED prompts rather than newly self-elicited deployment requests, and no held-out checkpoint validation has been performed. Those gaps remain open.

## 2026-10-08T16:28:57.414669-04:00 — retrospective prefix budgets and query uncertainty

The same fixed 16 probe / 112 disjoint label queries were reanalyzed at 16, 32, 64 and 128 speculative iterations, plus the full records. All 21 eligible checkpoints per drafter are retained; no cutoff or threshold was fitted. The retention label and prediction threshold remain 0.9. Immediate-EOS records retain the paired exclusions documented above.

These intervals resample both checkpoints and paired query IDs, recomputing the noisy probe scores and held-out labels. The earlier checkpoint-only intervals conditioned on those query estimates. In particular, the full EAGLE-3 AUROC remains 1.0, but its interval becomes [0.75, 1.0] when query uncertainty is included. Original full/prefix-16 central estimates and labels are independently reproduced exactly.

| Drafter | Prefix iterations | AUROC [paired query + checkpoint 95% CI] | Median fraction of full-probe iterations | TP / FP / FN / TN at fixed 0.9 |
|---|---:|---|---:|---|
| eagle3 | 16 | 0.602 [0.250, 0.959] | 0.089 | 4 / 3 / 3 / 11 |
| eagle3 | 32 | 0.592 [0.250, 0.967] | 0.177 | 4 / 4 / 3 / 10 |
| eagle3 | 64 | 0.735 [0.357, 1.000] | 0.343 | 4 / 4 / 3 / 10 |
| eagle3 | 128 | 0.980 [0.653, 1.000] | 0.664 | 7 / 2 / 0 / 12 |
| eagle3 | Full | 1.000 [0.750, 1.000] | 1.000 | 7 / 3 / 0 / 11 |
| dflash | 16 | 0.773 [0.442, 1.000] | 0.125 | 8 / 3 / 2 / 8 |
| dflash | 32 | 0.882 [0.538, 1.000] | 0.240 | 7 / 3 / 3 / 8 |
| dflash | 64 | 0.945 [0.709, 1.000] | 0.447 | 10 / 2 / 0 / 9 |
| dflash | 128 | 0.991 [0.764, 1.000] | 0.775 | 10 / 3 / 0 / 8 |
| dflash | Full | 0.945 [0.731, 1.000] | 1.000 | 9 / 3 / 1 / 8 |

Short EAGLE-3 prefixes remain weak; longer prefixes rank this cohort better but consume more of the full-probe iterations. DFlash improves earlier, with wide uncertainty. The iteration fractions are retrospective work proxies, **not measured wall-clock savings**. Cold target-loading costs would remain. These results do not select a deployment cutoff or establish performance on new checkpoints; the cohort is small, related and enriched for known failures.

[Prefix budget figure](figures/P5-prefix-curve-D48-20261008.pdf). Source, raw input hashes, complete scores and prespecified budget list: `artifacts/P5_prefix_curve_20261008_1627/`. No GPU jobs or acceptance-harness changes were used.
