# ReFit: three-hour evidence and experiment triage

Prepared October 12, 2026, codex-1. Owner window: approximately 14:13–17:13 Eastern. All results below remain **pilot**. This is an evidence handoff for the Claude draft; no files under `paper/` were edited.

The highest-return work is to integrate completed controls and measured deployment economics. Several requests in the reviews already have results. A new continuous-drift analysis and a paired longer-training-data comparison are now complete. Neither supplies a uniformly positive new mechanism claim. The strongest evidence remains measured repair gains, matched adaptation controls, and the cost to recover those gains.

## What fits in three hours

| Work | Current status / realistic elapsed time | Recommendation for this window |
|---|---|---|
| Drift versus acceptance, family-stratified, with uncertainty | **Complete now** from existing 141-model A6 overlap and 17-model T1 diagnostics | Use the complete results below; do not claim a universal drift predictor. |
| Measured repair amortization | **Complete now**, independent reduction of raw batch timers | Add a deployment result based entirely on measured costs. |
| Longer-response repair comparison | Training and evaluation already complete; **new paired comparison complete now** | Integrate this instead of repeating expensive data generation. |
| Paired long-reasoning speedup; crossover interaction; Qwen repair; matched-capacity/whole-LoRA; batch16/32 | **Already complete** | Bring the appropriate existing evidence into the draft. |
| Larger MATH long-generation acceptance panel, first128 MATH500, cap8192, reuse/interface/full (+ R1 oracle) | Estimated **45–90 min per arm plus compilation/queue**, with parallel free A40s; allow **1–2 h including analysis** | Feasible computationally, but **not launched: insufficient disk headroom**. This would improve acceptance precision, not replace timing evidence. |
| Same n128 long panel with full batch1 timing protocol | Roughly **6.6 h per repaired process; 12 h per no-spec process**, plus startup, using observed32-query runtimes | Cannot finish in three hours without a new supplementary protocol. Three processes can run in parallel but each must finish. |
| Independent 1B drafter, matched16k response fine-tuning plus evaluation/timing | Roughly **4–6+ h**, low-confidence extrapolation; data audit/export/evaluation also needed | No credible three-hour completed-result promise. Existing128-example trainer took46.85s for two epochs/32steps; R1's16k corpus is much longer. |
| New moderate-domain16k repair target | New response generation, training and evaluation; **several hours or longer** | Not on the three-hour critical path unless a suitable existing corpus/export is identified. |
| Scratch50–500A40-GPUh curve | **At least50–500 h for the existing single-GPU training path**, excluding evaluations | Existing measured10.16GPUh scratch64k result is available; a new large-budget curve is outside this window. |
| Faithful EDA comparison, tree-serving change, or70B repair | No ready validated path within this window | Do not relabel an existing LoRA proxy as EDA or promise unvalidated serving numbers. |

Timing estimates are based on existing jobs, not reserved resources. The observed R1 full32-query8k panel took24.6min/pass; no-spec took44.9min/pass. Four passes (one cold plus three warm) and four times as many queries produce the6.6/12h estimates. The existing batch8 acceptance full32-query8192 cell took656.8s generation plus124.6s startup; its linear128-query extrapolation is about46min, before workload differences and other arms.

At14:20–14:23 ET free disk fluctuated around349.6–350.1GB against the350GB launch floor. The manifested D47 sweep found **zero eligible completed compile caches**; the scoped optimizer-state audit also found no remaining candidates. No weight/result/ledger deletion or floor change was made. One canonical queue remains, with no new REV5 GPU jobs submitted. A few hundred MB above the floor is not credible headroom for concurrent fresh compiles.

## 1. Stronger long-trace evidence already exists

The review compares overlapping intervals for two speedups against no speculation. That is not the test of whether repair improves on reuse. The existing **paired** comparison directly answers that question:

| MATH32,8192 cap, batch1 | Full repair / reuse [95% CI] | Protocol |
|---|---:|---|
| R1-Distill-Llama | **1.327 [1.151,1.622]** |32queries,3fresh processes,3warm passes/process|
| Nemotron-Nano | **1.465 [1.282,1.654]** |same|

Both intervals exclude1. These are measured speedups over reuse, not1.327×/1.465× over no speculation. They establish a gain on this32-query workload; they do not turn it into a128-query or complete-MATH500 long-generation measurement. Source: [REV2 E10a timing](REV2-results-20261010.md).

## 2. Longer training responses: completed, now paired against the short-response recipe

E9 generated4k responses at2048 tokens and trained both long-only4k and mixed20k (16k×512 plus4k×2048). The table below independently recomputes the **difference from the same-scope official16k short-response repair**, using the same32 MATH queries and8192 inference cap.

| Target | Scope | Long4k minus short16k, Δτ [95% CI] | Mixed20k minus short16k, Δτ [95% CI] |
|---|---|---:|---:|
|R1|interface|−0.020 [−0.136,+0.104]|+0.050 [−0.076,+0.182]|
|R1|full|+0.070 [−0.026,+0.178]|+0.025 [−0.057,+0.115]|
|Nemotron|interface|−0.058 [−0.156,+0.030]|+0.051 [+0.006,+0.100]|
|Nemotron|full|−0.030 [−0.109,+0.053]|+0.050 [−0.005,+0.108]|

One training seed;10,000 paired query resamples. Seven of eight contrasts are unresolved. This tested extension does not demonstrate that the remaining R1 gap is principally a512-token training-length mismatch. All long-data repairs still improve on **unrepaired reuse**, as recorded in E9. Data size, packed batch ceiling(2304 versus2048) and optimizer-step counts also differ, so this is a comparison of repair recipes, not an isolated length intervention.

Raw-counter analysis/script: [REV5 long-data analysis](../artifacts/REV5_longdata_20261012_1425/results.json). Source data audit: [REV2 response table](REV2-results-20261010.md). R1 short16k hits the512 cap on11,517/16,000 responses(72.0%); Nemotron3,019/16,000(18.9%). The4k2048 data average882.6 R1/368.8 Nemotron response tokens; only165/106 respectively reach the2048 cap. Raising a cap does not force complete traces to become longer.

## 3. New continuous-drift analysis

We joined the existing A6 diagnostics to archived, independently recomputed first-position retention: **141 models =80 Llama +61 Qwen**, each measured with two drafters. This overlap is not the complete174-model census. Each family/drafter is analyzed separately; models receive equal weight. KL is child‖reference on the archived context distribution. Hidden-state drift is mean cosine displacement or relativeL2 across the three recorded taps, **not CKA**.

| Family | Drafter | n models | KL Spearman ρ [95% CI] | Tap cosine-displacement ρ [95% CI] |
|---|---|---:|---:|---:|
|Llama|EAGLE-3|80|−0.083 [−0.321,+0.168]|+0.110 [−0.145,+0.341]|
|Llama|DFlash|80|−0.336 [−0.534,−0.116]|−0.207 [−0.422,+0.015]|
|Qwen3|EAGLE-3|61|+0.038 [−0.248,+0.296]|+0.104 [−0.204,+0.380]|
|Qwen3|DFlash|61|−0.143 [−0.419,+0.149]|−0.004 [−0.300,+0.292]|

These results do **not** support a universal monotonic drift–degradation explanation. The Llama/DFlash KL association is negative; the other family/method KL intervals include zero, and the recorded hidden-state distances do not resolve an association. A new matched-context study could answer a different question; these existing own-context diagnostics cannot remove the census's text/domain confounds.

The focused T1 analysis remains separate because its KL uses8 traces rather than64 and a different workload. For Llama/DFlash, excluding the two previously documented collapsed RL checkpoints givesρ=−0.786[−1.000,−0.103],n8; the corresponding EAGLE association is−0.619[−1.000,+0.291]. All-model and common-vocabulary-only sensitivity results, Qwen results, and retained above-unity retention values are in the full report. Tülu's finite KL is conditional on common vocabulary and is explicitly labelled.

Intervals:10,000 checkpoint bootstrap draws within family/cohort/method, conditional on measured checkpoint estimates; they do not propagate per-model diagnostic measurement noise or adjust for multiple comparisons. No favorable subset was selected as a replacement headline.

Sources: [complete new analysis](../artifacts/REV5_cpu_20261012_1430/report.md), [per-model CSV](../artifacts/REV5_cpu_20261012_1430/drift-models.csv), [machine-readable results and input hashes](../artifacts/REV5_cpu_20261012_1430/results.json). Census composition/counts and the focused21 cohort are already available in [REV4 Y9](../artifacts/REV4_Y9_20261011_0300/report.md).

## 4. New deployment result: measured repair amortization

Use measured repair GPU-seconds divided by measured warm GPU-seconds saved per request. R1 official16k costs **11.122GPUh interface /11.127GPUh full**, including8.916GPUh shared data generation charged to each alternative. This calculation needs **no estimate of the dedicated drafter's original training cost**.

| Batch1 workload, n128 | Interface requests to break even vs reuse [95% CI] | Full requests to break even vs reuse [95% CI] |
|---|---:|---:|
|SPEED-128|15,061 [14,128,16,101]|**13,582 [12,774,14,503]**|
|First128 MATH500|13,532 [13,084,14,014]|**11,706 [11,374,12,058]**|

At the measured output lengths, full repair corresponds to approximately6.81million generated SPEED tokens or5.91million MATH tokens to amortize the cost. Relative to **no speculation**, full repair pays back after6,179[5,843,6,600] SPEED requests or4,960[4,902,5,024] MATH requests.

Uncertainty is10,000 paired process/query-batch bootstrap draws, with3warm passes averaged within each of3processes. Cost is the observed seed0 value; intervals reflect serving uncertainty, not training-seed uncertainty. This is conditional on the measured warm workload, A40, batch1 and512 cap. No extrapolation to arbitrary conversations, idle-serving power or hardware pricing is implied. Engineering, failed jobs, search and evaluation are excluded from the chosen-repair cost.

The interface's measured advantages are primarily its mutable parameter/storage footprint and frozen decoder, with smaller training memory/time savings. End-to-end cost is nearly equal because generation dominates. The report should not attribute the overall11GPUh budget specifically to freezing the decoder. Full Nemotron and other reference comparisons are retained in the linked JSON; its original MATH reuse timing has broad process variation and should be read alongside the later OPS control rerun.

## 5. Existing evidence that should be handed to the writer

- **Matched adaptation baselines:** REV2 E8 and E17 contain dense parameter-matched interface/decoder and whole-drafter LoRA comparisons at16k. These are the completed fair capacity controls. They are not an empirical EDA reproduction.
- **New text versus new supervision:** REV4 Y7 keeps derivative token sequences fixed. Relative to parent-supervised full repair, derivative-supervised full repair adds **+0.314τ[+0.288,+0.340] SPEED** and **+0.397[+0.383,+0.411] MATH500**,n128/500,seed0. Parent-supervised training also helps; both findings belong together. [REV4 results](REV4-results-20261011.md).
- **Crossover interaction:** already estimated, not missing data. On derivative contexts: R1 **+0.0625[+0.0568,+0.0683]**, Nemotron **+0.0765[+0.0670,+0.0860]**,n64 each. Feature and verifier effects are not an additive exhaustive decomposition of online retention. [P2 crossover](P2-crossover-20261008.md).
- **Qwen EAGLE repair:** E12 full adds **+0.473τ[+0.456,+0.491] on MATH500**,n500,seed0; SPEED timing full/reuse **1.193[1.155,1.232] at batch1**,n32,3processes. Already complete. [REV2](REV2-results-20261010.md).
- **DFlash scope:** successful Llama repairs and timing are complete, but **Qwen DFlash repair regresses** in REV4 Y4. The positive Qwen EAGLE result cannot be substituted for a positive Qwen DFlash result. Preserve this distinction in the evidence packet.
- **Batch16/32:** E11 complete; some full/no-spec speedups are null or below1 at batch32. No new run is needed to supply larger-batch measurements. [REV2](REV2-results-20261010.md).
- **Scratch/scaling:** E13 scratch64k takes10.164 measured trainingGPUh; SPEEDτ1.743 versus reuseΔ−0.021[−0.065,+0.024]. Official warm64k full reachesτ2.622SPEED/3.067MATH500 and1.905×[1.802,2.007] batch1 SPEED speedup. Source mixture changes from Alpaca to Alpaca+Dolly at64k. A50–500GPUh scratch curve is a distinct, uncompleted experiment.
- **Thinking mode:** main Nemotron uses the empty-system/default template, not an explicit thinking-off intervention. REV4 Y3a/Y3b contain explicit thinking-on evaluation and regenerated-data repair; full thinking-on repair/reuse timing is1.406SPEED/1.691MATH at batch1,n128. [REV4](REV4-results-20261011.md).
- **Timing anomaly:** the additional OPS Nemotron MATH batch1 reuse/no-spec rerun gives **1.296[1.218,1.383]**,n128,3processes. It does not independently audit batch8. Different batching can alter target/drafter cost ratios, so a higher batch8 ratio is not itself an invalid result; the actual cause cannot be asserted from that observation alone. [rerun raw reduction](../artifacts/OPS_REV4R1_rerun_20261012_0046/analysis_20261012_0500/results.json).
- **Figure consistency:** `fig_method.tex` and `fig_cost.tex` still show1.31→1.83/dedicated2.05, while current main n128 results are1.335→1.854/dedicated2.083. Either use the current main panel throughout or explicitly label the older panel. No GPU work required; files left unchanged for Claude integration.
- **Release statements:** D56 explicitly removes release promises. No new promise is proposed in response to the reviews.

## Reproduction and state

CPU implementation: `followspec/rev5_analysis.py`; four tests pass (`python -m unittest followspec.tests.test_rev5_analysis`). Tests cover rank rather than magnitude correlation, undefined constant covariates, single counting of batch time and no break-even under a slowdown. No evaluation/training defaults changed. Code commit `a3ebdaa`.

Commands:

```
python -m followspec.rev5_analysis --workspace /home/heck2/sbhansali8/SpecTLM --output artifacts/<fresh-output>
PYTHONPATH=/home/heck2/sbhansali8/SpecTLM python artifacts/REV5_longdata_20261012_1425/analyze.py
```

The second script writes immutable results beside itself; copy it to a new output directory to rerun. GPU followup is resource-blocked, not running in the background. Existing REV4 P0/P1 results are complete; REV4 Y10 math-domain4096-response work remains blocked by failed data selection/launches and is not claimed as finished here.

Seven enlarged long-panel jobs are prepared at `artifacts/REV5_long128_20261012_1430`, with hashed source panels, inspected prompt samples and immutable job/plan files. They are **not submitted**. Latest preparation check:349.718GB free, below350GB. Board row `REV5-LONG` records the blocker separately from the completed CPU deliverable.

## Update 2026-10-12T14:37:16.547025-04:00: authorized cleanup completed; panel queued
Owner authorized documented deletion of old checkpoints. Removed30.401GB of original FIX24-invalid trainable weights, preserving all raw results/configs and corrected repairs; [inventory](REV5-checkpoint-cleanup-20261012.md). Seven long128 cells published successfully to the sole dispatcher. Disk approximately380GB free. All A40s currently occupied on srv1–5; no new cell has started yet. Elapsed estimate is1–2hours after parallel slots become available, not a guaranteed17:13finish. No longer alternatives launched.
