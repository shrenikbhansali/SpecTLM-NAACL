# ReFit: additional experimental evidence and analysis

2026-10-10, codex-1. Working evidence document for the selected **Claude final draft**. The manuscript is untouched. Results here are pilots; completed measurements, running experiments, and proposed interpretations are distinguished. This document supplies material for the paper's core argument, rather than writing a rebuttal into the paper.

## What the additional experiments establish

The central empirical question is whether inexpensive adaptation of an existing target-conditioned drafter recovers useful serving performance after the target changes. Three additions make this evidence substantially stronger: testing recovery deep into reasoning trajectories, separating response-domain adaptation from target-specific supervision, and comparing adaptation locations at matched capacity.

**First new result: recovery persists beyond the training length.** On a fixed 32-question MATH panel with a 2,048-token ceiling, the official R1 family drafter has τ=2.080 and p1=.536. The same 16k repairs trained on responses capped at 512 tokens reach:

| R1 arm | p1 | τ | Paired Δp1 [95% CI] | Paired Δτ [95% CI] |
|---|---:|---:|---|---|
| ReFit-interface | .736 | 2.858 | +.200 [.184, .215] | +.777 [.718, .839] |
| ReFit-full | .769 | 3.042 | +.232 [.216, .249] | +.961 [.897, 1.026] |
| Dedicated reference | .886 | 3.934 | +.349 [.330, .369] | +1.854 [1.756, 1.953] |

Frozen 6da2e42/vLLM 0.31.0, A40, K4, batch8, greedy seed0; n=32 paired queries, 10,000 paired bootstrap draws. Selection was the first32 of the existing MATH64 order before looking at outputs. Mean lengths are 1,861/1,795/1,717/1,807 tokens for reuse/interface/full/reference; 20/18/18/18 requests hit the cap. No output crosses the predeclared >50% repeated-4-gram coverage threshold. These are acceptance results, not new wall-clock speedups. Different arm completions/lengths are retained rather than silently treated as identical trajectories. [Raw independent analysis](../artifacts/REV1_analysis_20261010_0140/report.md), [raw counters and hashes](../artifacts/REV1_analysis_20261010_0140/results.json).

**8,192-token R1 result, first completed comparison.** Full repair improves τ from1.970 to2.680, Δτ **+.710 [.557,.858]**, and p1 from.511 to.689, Δp1 **+.179 [.144,.212]**, n32. Mean completions are3,050/3,329 tokens for reuse/full, with3/5 cap hits; no repeated4-gram flag. The benefit is clear overall and in the512–2048 progress bin (Δτ+.856 [.780,.931], n32). In the2048–8192 bin, among16 queries reaching it in both arms, Δτ is+.151 [−.067,.385] and Δp1+.037 [−.026,.100]. Thus the current repair delivers longer-workload gains, but the late-trace advantage is not established by this panel. This gives a concrete next scientific lever: training-prefix coverage, rather than assuming the first512-token repair covers the entire trajectory. [Snapshot with progress strata](../artifacts/REV1_analysis_20261010_0145/report.md).

**First matched-capacity result.** On MATH64, decoder LoRA r655 (50.304M parameters) reachesτ2.364 versus2.380 for the50.332M dense interface: paired difference−.016 [−.044,.012]. It improves over the old1.229M decoder LoRA by+.293 [.263,.321]. The small decoder baseline was capacity-sensitive; this result supports efficient interface repair but not an exclusive-location explanation. Full repair still exceeds r655 by.130 [.103,.157]. SPEED and the full-rank controls are pending. [Component snapshot](../artifacts/REV1_analysis_20261010_0145/components.md).

## Experiments added

| Experiment | Fixed factors / intervention | What it resolves | Status / source |
|---|---|---|---|
| Long reasoning | R1 and Nemotron; reused, interface16k, full16k; R1 dedicated reference; identical MATH32 rendered IDs; 512/2048/8192 ceilings | Whether short-response repair transfers to longer generation; acceptance by verified-generation progress | 21 cells, [plan](../artifacts/REV1_20261010_0130/plan.json) |
| Sampled reasoning | Same 7 arms and MATH32, 8192 ceiling, T=.6, top-p=.95, seed0 | Whether recovery persists under stochastic rejection sampling | 7 supplementary cells, [plan](../artifacts/REV1_sampled_20261010_0140/plan.json) |
| Matched low-rank capacity | Interface LoRA r75 vs existing decoder q/v+MLP LoRA r16: exactly 1,228,800 trainable parameters each | Location at equal small parameter budget | [plan](../artifacts/REV1_20261010_0130/plan.json) |
| Matched dense-interface capacity | Decoder q/v+MLP LoRA r655: 50,304,000 parameters vs dense interface 50,331,648 (0.055% difference) | Whether original decoder-LoRA comparison was simply capacity-limited | Same plan |
| Full-rank decoder | Whole decoder-only update; separate q/o-only dense update (50,331,648 parameters, exactly matches interface) | Full-rank location control; head and interface frozen | [control plan](../artifacts/REV1_controls_20261010_0140/plan.json) |
| LoRA optimization control | Decoder r16 at 1e-4, compared with the existing 2e-5 run | A bounded check of learning-rate sensitivity | Same control plan |
| Parent-supervision control | Same derivative-generated input IDs/masks/order, same production initialization and native TTT3; parent supplies both features and soft next-token labels; interface/full each 300 steps | Whether adapting to the text alone repairs derivative serving without derivative-specific supervision | Same control plan |

All component controls use the existing 256-example self-elicited data, seed0, 300 steps, identical batches and native objective; final exports are evaluated on frozen SPEED128 and MATH64. This connects directly to the original component experiment. It does not mix the official16k main-table results with production256 component estimates. All exports are compact, use shared shards, and respect the 350GB floor. Each new job went through cell and launcher dry runs and the existing exclusive canonical queue. Watchers enqueue completed training exports automatically.

The sampled cells use an explicit opt-in extension of the cell harness, with unchanged default greedy behavior and the same pinned vLLM engine. Their configs mark them **D53 supplementary sampled pilot** and record their actual code hash, temperature and top-p. They do not replace the frozen primary numbers. Prompt-paired intervals describe this fixed panel and sampling seed; trajectories are not identical across arms under sampling.

The parent-supervision control preserves every original token ID. R1 renames seven reserved/special token IDs relative to Instruct, including its role/thinking markers. These aliases are recorded in the training config; ordinary lexical token mappings are verified identical. No role-token remapping or re-rendering is silently introduced. Thus this tests whether **the original parent's supervision on the same derivative contexts** is sufficient, including those contexts' special markers.

## Existing evidence that already strengthens the paper

### A second target family already has a positive repair result

R1-0528-Qwen3-8B was repaired with the Qwen family EAGLE-3 drafter on 256 self-elicited examples for 300 steps. Frozen greedy K4, one training seed, n128 SPEED / n64 MATH:

| Workload | Arm | τ | Paired Δτ [95% CI] |
|---|---|---:|---|
| SPEED128 | Interface | 2.076 | +.150 [.119, .179] |
| SPEED128 | Full | 2.160 | +.234 [.199, .266] |
| MATH64 | Interface | 2.513 | +.151 [.124, .178] |
| MATH64 | Full | 2.569 | +.207 [.177, .237] |

SPEED Δp1 is +.036 [.023,.047] for interface and +.055 [.042,.067] for full. This is measured cross-family evidence, although its data budget is smaller than the main Llama16k experiment. GRPO150 and Hermes3 controls also exist. [Verified generality report](P3-D48-seeds-generality-20261008.md).

### Measured speedup intervals are available

Three independent processes, three warm passes/process, paired prompts/process resampling; A40 SPEED, batch1 n32 and batch8 n128. Values below use the selected official drafter:

| Target | Arm | Batch1 speedup [95% CI] | Batch8 speedup [95% CI] |
|---|---|---|---|
| R1 | Reuse | 1.312 [1.230,1.393] | 1.075 [.989,1.168] |
| R1 | Interface | 1.738 [1.577,1.894] | 1.268 [1.104,1.473] |
| R1 | Full | 1.828 [1.652,1.992] | 1.287 [1.117,1.505] |
| R1 | Dedicated | 2.054 [1.855,2.249] | 1.406 [1.203,1.665] |
| Nemotron | Reuse | 1.291 [1.204,1.376] | 1.129 [1.055,1.204] |
| Nemotron | Interface | 1.694 [1.483,1.887] | 1.393 [1.218,1.600] |
| Nemotron | Full | 1.803 [1.629,1.977] | 1.424 [1.228,1.670] |

The directly paired full/reuse speed ratio is 1.393 [1.322,1.466] on R1 and 1.396 [1.309,1.484] on Nemotron at batch1. These measurements support a strong practical result without relying on the estimated dedicated-training bill. [Primary results, timing and costs](P3-primary-official-20261010.md).

Similar τ need not produce equal speedup: speedup is relative to each target's own no-spec latency and also depends on lengths, batch utilization, target verification and drafter costs. The existing cost model treats these separately. The observed Nemotron/R1 batch8 point-estimate difference is not evidence that τ uniquely determines throughput.

### The census can be documented from existing verified data

The [portable evidence export](REV1-evidence-20261010/per-model.csv) contains model IDs, revisions, family, lineage, combined training histories, n, p1-retention intervals, τ/length retention, card evidence and raw source paths. [Group composition and family/workload-specific intervals](REV1-evidence-20261010/census-groups.md), [all card evidence](REV1-evidence-20261010/card-inventory.json), and [source hashes/counts](REV1-evidence-20261010/provenance.json) are included.

The historical census has 174 checkpoints (87 per family), 348 paired comparisons and 42 unknown training histories. The focused frozen SPEED study contains 25 checkpoints; separating two pretrained controls and two collapsed checkpoints leaves 21. Its 42 SPEED pairs plus16 MATH pairs should not be silently pooled with the historical own-domain/general-fallback workloads. Mixed histories remain combinations rather than being assigned to a convenient final-stage category. The existing analysis uses a checkpoint/prompt hierarchical bootstrap. [Population and filter accounting](P1-typed-population-20261008.md), [pairing audit](P1-census-pairing-audit-20261008.md).

## Clarifying the scientific interpretation

**The crossover does not leave an identified “11-point domain residual.”** The review subtracts approximately five teacher-forced agreement points from an approximately16-point online acceptance drop. Those estimates use different context populations, position weighting and model/drafter configurations. That subtraction is not a decomposition. P2 already used parent-generated, child-generated and public-reference contexts, 64 sequences/origin/target, five targets. On R1 child contexts the average feature effect is −.0196, average policy effect −.0303, and interaction +.0625; the positive interaction means there is no single context-independent additive allocation. The direct parent-supervision training experiment above supplies the missing intervention rather than inferring it from the residual. [Complete crossover](P2-crossover-20261008.md).

**Lineage and training history are available, and matter.** R1-Llama starts from pretrained Llama3.1-8B, making it a sibling of the Instruct target used by the released family drafter. Nemotron has a composite SFT/RL/merge history. They establish an important family-drafter reuse problem; they do not isolate the causal effect of one post-training operation. The focused table includes direct-child distillation, direct-child RL and the Tülu ladder, with their actual histories. Using these distinctions makes the study more informative, rather than weakening the repair result.

**Component update scope is precisely known.** “Interface+decoder” in the small-data component experiment means dense fc plus decoder LoRA, not the full-rank decoder. The old decoder r16 arm has 1.23M trainable parameters, the dense fc has50.33M, and full repair also changes the head and norms. The new matched-capacity and full-rank controls will determine how much of the advantage survives a stronger comparison. “An effective repair location” is established by the current intervention; exclusive localization of all original damage is a different claim.

**The 256-example point must remain 256.** The production full300-step component result is not a0.5k-example experiment. Official4k/16k and production256/1k/4k/16k/64k also have different initialization/data/budget coordinates. The underlying reports retain these labels, so the plotting ambiguity can be resolved without rerunning data.

**TTT3 versus K4 has already been tested.** Native training unroll depth and serving draft length need not be identical. The matched generic4k TTT4 control gives SPEED Δτ versus TTT3 of −.004 [−.026,.017] for fc and −.007 [−.028,.013] for full. This is a useful measured robustness check, not an untested explanation of the gains. [Ablation table](P3-D50-consolidated-20261009.md).

**The probe AUROC range describes different populations/drafters.** The full16-request probe gives .908 [.668,.983] for EAGLE and .934 [.745,.993] for DFlash on163 own-domain historical checkpoints. On the separate21-checkpoint focused SPEED cohort it gives1.000 [.750,1.000] and.945 [.731,1.000]. Sixteen *requests* must not be confused with sixteen speculative *iterations*: the latter is a weaker short-prefix probe. Probe and label queries are disjoint; checkpoints are not held out. [Historical probe](P5-census-triage-20261008.md), [focused probe and prefix budgets](P5-triage-pilot-20261008.md).

**Pairwise zero-step exclusions are narrow.** If either arm terminates before any speculative proposal, its p1/τ is undefined. That query is excluded from both arms of that paired acceptance comparison, with requested n, usable n and IDs recorded. It is not assigned zero acceptance, and the whole checkpoint is not discarded. Length and completion behavior remain reported. The new MATH32 comparisons above have32 usable pairs.

**Recovery and speedup refer to distinct panels.** The60%/72% oracle-gap recovery is R1 SPEED; full MATH500 is44%/54%, seed0. Wall-clock numbers are SPEED, not MATH500. Nemotron's existing MATH evaluation is64, with no dedicated oracle. Its reasoning-mode toggle is separately measured: enabling reasoning reduces p1 by .0296 EAGLE / .0278 DFlash on128 prompts; it does not by itself explain the larger cross-checkpoint loss. [Toggle report](P2-nemotron-toggle-20261008.md).

**DFlash provides architecture transfer evidence at a smaller budget.** Its256-example full repair gains are roughly11–13% in τ; interface gains roughly7–8%. It uses its native block objective, not the EAGLE TTT objective. These are acceptance gains; no DFlash repair latency claim is supported yet.

**The compute bill can be stated directly.** R1 official16k costs8.916 A40 GPUh for data plus2.206/2.211 for interface/full training, totaling11.122/11.127. Nemotron totals9.828/9.986. Training time includes target forwards and drafter optimization; the present logs do not separately time these two components. The1.3k–19k dedicated-cost range is a recipe extrapolation, not a measured bill or a confidence interval. The measured repair bill and measured latency improvement are sufficient to support the economics result. [Estimate assumptions](P6-dedicated-cost-estimate-20261008.md).

## Prior-method comparison and next decisions

EDA is relevant prior work, with public code. It uses a gated shared/private FFN, target-regenerated data, and data selection. Its released implementation is a two-stage Qwen2.5 pipeline, not an EAGLE-3 checkpoint that the frozen vLLM loader can accept unchanged. Therefore our decoder-LoRA comparison is not an EDA reproduction. The shared/private nonlinear mixture cannot be merged into the original single FFN by the same linear LoRA merge. Source audit: [paper](https://arxiv.org/html/2603.09527v1), [repository](https://github.com/Lyn-Lucy/Efficient-Draft-Adaptation), pinned repository audit `artifacts/REV1_EDA_audit_20261010` at `a29f0381479a92d0f3114fd264cd790bab3a208b`. The repository API reports no license; no external code has been incorporated or executed.

The architecture-compatible comparisons are full warm-start, location-specific LoRA, matched dense attention updates and full decoder-only updates, using identical data/native objectives/serving. We should assess the new results before claiming which repair mechanism wins. Self-generated responses and warm-starting are established ingredients; the distinctive evidence concerns **where adaptation is effective, when family reuse fails, and the measured recovery/cost tradeoff without changing serving architecture**.

Experiments not yet supplied by this addition: matched16k distillation of the independent1B drafter, an exact EDA or online-adaptation reproduction, dynamic-tree comparisons, 70B repair, and multi-tenant shared-decoder serving. These must not be described as completed baselines. The1B baseline already has measured latency and sometimes higher acceptance than ReFit on Nemotron; the advantage demonstrated there is serving cost, not uniformly higher acceptance. A shared decoder plus per-target fc matrices is mechanically compatible with fc-only exports (about96MiB bf16 per50.33M-parameter interface), but multi-tenant scheduling benefits would need a separate serving measurement.

## Operational provenance

Claim/journal: [REV1](../notes/REV1.md); owner authorization D53. Test-first additions cover counter reconstruction, paired exclusion, repetition flags, exact training scopes, supervision provenance/vocabulary, unchanged greedy defaults and explicit sampled parameters. All jobs have independent config/raw records and immutable output directories. The original Claude manuscript and historical artifacts remain unchanged. New result snapshots will be linked here as they complete; no failed or null arm is dropped from the planned comparisons.
