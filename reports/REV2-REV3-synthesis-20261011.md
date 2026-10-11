# Completed REV2 and DFlash evidence — October 11

Status checked at 02:04 ET. This analysis is for the owner/claude-ops; no manuscript files changed. Numbers remain pilot, independently recomputed from raw counters and repeated timing, with sources and paired confidence intervals.

## Completion

X5: 86/86 successful jobs; finished October 10 at 17:01 ET. REV2: P0 270/270, P1 106/106, P2 8/8, all required analyses complete by 20:33 ET. P2 completion includes a documented finding that EAGLE token trees are unavailable in the pinned engine; it is not a tree experiment result. Earlier E9 OOM attempts remain preserved; approved packing retries succeeded. All these rows are in review, not scientifically promoted.

Only X5 appears among REV3 jobs in the canonical dispatch. This completion does not establish completion of X1/X2/X3/X4/X6/X8. Disk was about 349 GB at the last hourly check, below the 350 GB launch floor; no new jobs were launched at this check.

## What X5 establishes

DFlash repair improves both target models on every tested acceptance panel, and yields measured speed improvements over reuse at both batches. All 12 repair-versus-reuse acceptance-length intervals and all eight repair-versus-reuse warm timing intervals exclude zero/no improvement. These are pointwise 95% intervals. R1 acceptance uses three training seeds, Nemotron one; timing uses seed 0 with three independent processes and three warm passes, n=128 at both batch sizes.

| Target | Batch | Reuse / none | Interface / none | Full / none | Full / reuse, 95% CI |
|---|---:|---:|---:|---:|---|
| R1-Distill-Llama | 1 | 1.541 | 1.766 | 1.859 | 1.206 [1.175, 1.232] |
| Nemotron-Nano | 1 | 1.548 | 1.783 | 1.892 | 1.223 [1.185, 1.258] |
| R1-Distill-Llama | 8 | 1.227 | 1.383 | 1.441 | 1.175 [1.125, 1.226] |
| Nemotron-Nano | 8 | 1.340 | 1.557 | 1.623 | 1.211 [1.166, 1.254] |

These are warm panel wall-time ratios on SPEED-128. Cold/startup-inclusive and token-normalized ratios are separately available; output differences are retained.

On SPEED-128, R1 DFlash acceptance length rises from 2.051 to 2.389 (interface) / 2.521 (full); Nemotron from 2.077 to 2.434 / 2.590. Full repair adds 15.1 [14.1,16.1] and 15.0 [13.7,16.2] percentage points of first-position acceptance. On MATH-500, full repair adds acceptance length +0.583 [0.565,0.601] / +0.626 [0.611,0.641]. At the 8,192-token MATH32 ceiling, full gains are +0.605 [0.455,0.818] / +0.478 [0.303,0.595], respectively. Thus the DFlash improvement extends beyond the 512-token training/evaluation setting.

Native training takes 1.26–1.28 A40 GPUh for R1 interface and 1.48–1.50 for full; Nemotron 0.82/0.93. These are training costs only: response-generation costs must be included for end-to-end adaptation economics. No compatible dedicated R1 DFlash checkpoint was found; no DFlash oracle-gap claim is available.

[Full X5 results and raw evidence](REV3-results-20261010.md).

## What REV2 adds

- **Second target family:** Qwen R1 full repair adds acceptance length +0.377 [0.335,0.415] on SPEED (n=128) and +0.473 [0.456,0.491] on MATH-500 (n=500), one seed. Batch-1 SPEED full/no-spec is 1.850 [1.744,1.953], full/reuse 1.193 [1.155,1.232] (n=32, three processes).
- **Long reasoning serving:** existing 16k short-response EAGLE full repair accelerates MATH32 at the 8,192-token cap by 1.327 [1.151,1.622] over reuse on R1 and 1.465 [1.282,1.654] on Nemotron (n=32, three processes). Long-panel lengths differ; normalized token ratios are reported separately.
- **Warm-start value:** from-scratch EAGLE training on 64k examples took 10.164 GPUh excluding data generation, yet SPEED acceptance length was 1.743 [1.703,1.784], versus reuse 1.764; delta -0.021 [-0.065,0.024]. MATH-500 is 1.965 [1.947,1.983], far below 16k warm-start full repair 2.967 [2.945,2.988]. This supports warm-start efficiency within the tested schedules, not a claim that scratch training never works.
- **Competitive adaptation baseline:** whole-drafter LoRA at approximately 50M parameters beats interface on R1 SPEED by +0.038 [0.015,0.060], while full repair beats whole-LoRA by +0.090 [0.068,0.112] (n=128, three seeds). Full also beats whole-LoRA on Nemotron by +0.057 [0.033,0.080] (one seed).

## Which claims are supported

The evidence strengthens the practical claim that an existing target-conditioned drafter can be repaired with modest target-generated data, producing real speed gains across two drafter architectures, multiple targets and longer workloads. Interface-only repair is an effective, smaller update; full warm-start generally achieves larger gains.

The capacity-matched experiment does not establish unique interface localization. Dense 50M interface and decoder q+o are statistically unresolved on the three-seed SPEED/MATH64 comparisons; for example R1 SPEED interface-minus-decoder is -0.001 [-0.025,0.023]. Interface-versus-low-rank-decoder comparisons alone therefore cannot establish that damage resides predominantly in the interface. Interface storage and training-resource benefits remain independently measured.

More long training data is not yet a decisive improvement over the existing 16k recipe on R1's 8k evaluation panel. Full long4k versus full short16k adds +0.070 [-0.026,0.178] acceptance length; mixed20k adds +0.025 [-0.057,0.115], n=32, one seed. Vocabulary reselection also gives no resolved SPEED gain. High-batch speculation is not uniformly faster than no speculation: R1 full at batch32 is 0.840 [0.813,0.869], even though it improves over reuse.

These findings support an effective repair method and deployment study. They do not independently establish a universal causal attribution to post-training category, a uniquely privileged repair location, or a measured 400× training-cost ratio. The owner decides the final claims and presentation.

[Complete REV2 analysis, CIs, model-level census and sources](REV2-results-20261010.md).
