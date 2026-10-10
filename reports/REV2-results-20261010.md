# REV2: additional ReFit evidence — pilot

D-54, codex-1. Updated 2026-10-10T06:16:54.021592-04:00 Eastern. Analysis for integration by claude-ops; `paper/claude_final` is untouched. New GPU numbers will be added only after completion and independent raw-counter checks. Existing observations below retain their original initialization, budget, protocol and sample size.

All new primary acceptance: frozen 6da2e42, vLLM 0.31.0, A40, greedy K4, identical target-rendered IDs across arms. Long caps are supplementary workload extensions. Training uses FIX-24 initialization. Uncertainty jointly resamples paired training seeds and queries where multiple seeds exist; single-seed estimates use paired queries. Wall-clock measurements separately resample processes and paired prompt batches. Artifacts are immutable, compact checkpoints omit final optimizer state, and every launcher enforces the350GB free-space floor. Code/tag: `run-REV2-train-20261010-0425` /62cecc1.

Full evaluation-query exclusion audit:208 actual census/focused/served-MATH500 prompt files contain11,024 unique normalized raw queries, exactly the recorded forbidden set. Both16k training corpora have zero overlap; E9/E12 use those approved query subsets. [Audit sources/hashes](../artifacts/REV2_eval_exclusion_audit_20261010_0600_v2/proof.json).

## Midday results — 12:52 ET

E8 matched-capacity, E10 reasoning/MATH wall-clock, E11 batch scaling, E12 Qwen16k, E14 MATH500 and E16 resource profiles are complete and independently reduced. A1–A10 are complete. E17 final seed-group evaluations, E13 scratch64k and R1 E15 remain in flight. E9 is delayed by eight first-backward out-of-memory failures at4096 packed tokens; all failed artifacts are retained and all eight arms are restarting at2304 packed tokens in new directories. Every complete response fits (maximum shifted sequence2115R1/2118Nemotron), and no data or response is truncated. The owner-approved E9 packing adjustment changes the number of optimizer steps within one epoch; both repair scopes use identical packing within each data condition.

The strongest new generality result is Qwen full repair: SPEED128 τ2.302, Δ+.377[.335,.415]; MATH500 τ2.791, Δ+.473[.456,.491], n128/500, one seed. Warm SPEED batch1 speedup versus no speculation1.850[1.744,1.953], compared with reuse1.551[1.484,1.621]; paired full/reuse1.193[1.155,1.232], n32, three processes×three warm passes. Batch8 full speedup1.234[1.114,1.373], n128/three processes.

Long-MATH32 at8192 ceiling, batch1: full/no-spec1.767[1.437,2.272] on R1 and1.634[1.371,2.020] on Nemotron. Paired full/reuse1.327[1.151,1.622] and1.465[1.282,1.654], respectively; n32/three processes. These are warm panel wall times; output lengths differ across arms, and token-normalized ratios, cold panels and startup are retained separately in the complete table. At512 cap on the MATH500 subset, R1 full/no-spec is2.305[2.255,2.360] atb1/n32 and2.053[2.006,2.097] atb8/n128.

The capacity-matched location study does **not** show a general interface advantage. Three-seed R1 dense50M interface−decoder Δτ is−.001[−.025,.023] on SPEED and−.019[−.049,.011] on MATH64; Nemotron+.023[−.006,.052]/+.008[−.017,.033]. All four low-rank three-seed τ intervals also include zero. Seed0 R1MATH500 favors decoder by.029[.018,.041] at50M and.019[.009,.030] at1.229M; all rows remain reported. The compatible whole-drafter LoRA50M baseline is competitive: on R1SPEED it exceeds interface by.038[.015,.060], but full repair exceeds it by.090[.068,.112], n128/three seeds. On NemotronSPEED full exceeds whole-LoRA by.057[.033,.080], n128/one seed.

Resource evidence supports the smaller interface update independently of a location claim: first200 matched batches peak25.69GiB allocated for interface versus29.08GiB full; steady step time1.570s versus1.773s. Mutable fp32 exports are201.3MB versus1698.8MB. Shared frozen-body tensor checks are in A9. Larger-batch results remain mixed: R1full/no-spec atb32 is.840[.813,.869], despite1.101[1.072,1.123] improvement over reuse; Nemotronfull/no-spec.984[.880,1.161].

Sources: [matched-capacity table](../artifacts/REV2_live_analysis_20261010_0550/20261010_124623_480893/E8/report.md), [acceptance and paired baseline contrasts](../artifacts/REV2_live_analysis_20261010_0550/20261010_124623_480893/acceptance/results.json), [latency CIs](../artifacts/REV2_live_analysis_20261010_0550/20261010_124623_480893/timing/report.md), [profiles](../artifacts/REV2_live_analysis_20261010_0550/20261010_124623_480893/E16/report.md). All are pilots; the owner selects paper content. No paper file was edited.

## E8 — matched-capacity location at16k

First complete capacity-matched group: **Nemotron, MATH-64, dense50M, three seeds**. Interface τ2.71249 versus decoder q+o τ2.70453; paired Δτ+.00796[−.01748,+.03318], Δp1+.00725[−.00057,+.01531], n64/3seeds. No speculative-step exclusions; all output lengths512. This group does not resolve a location advantage. All intended data, steps, schedules and parameter counts match; remaining groups stay pending. [Independent raw evidence](../artifacts/REV2_live_analysis_20261010_0550/20261010_061318_285942/E8/results.json).

**Run matrix:**20 new trainings. R1 and Nemotron, three seeds: dense q+o50,331,648 parameters; interface LoRA r75 and decoder q/v+MLP LoRA r16 both1,228,800. Nemotron interface seeds1–2 complete the dense-interface comparator; R1 interface seeds0–2 and Nemotron seed0 are reused. Live parameter logs match all requested counts. Data, seed-specific batches, optimizer, learning rate and native TTT3 objective are shared within each location contrast. The learning rate is2e−5; LoRA alpha is2×rank in both locations, so both use the same adapter multiplier2. No learning-rate search is performed in this fixed comparison. All runs save one final checkpoint; SPEED128/MATH64 for every seed, MATH500 for seed0, through an automatic frozen-evaluation watcher. Completed comparisons appear in the live raw-result tables below.

[Plan and jobs](../artifacts/REV2_E8_20261010_0425/plan.json).

**First completed checkpoint (partial seed group):** Nemotron interface-LoRA r75, seed1, MATH64: τ2.518[2.474,2.564], compared with reuse1.703[1.679,1.727]; paired Δτ+.815[.782,.847]. p1 .6645[.6533,.6756], paired Δp1+.2128[.2042,.2215], n64, one training seed. This verifies the export in the frozen serving path; the location comparison still requires all three seeds of both matched arms. [Independent raw check](../artifacts/REV2_first_export_check_20261010_0552/proof.json).

## E14 — MATH500 completion

**Run matrix:** Nemotron reuse/interface/full/independent1B and R1 interface/full seeds1–2, eight cells. New Nemotron and Qwen MATH500 renders match all64 existing MATH64 token-ID sequences under their respective templates. Five decoded prompts inspected for each new render. Initial rendering with the system tokenizer failed before producing any cells; the pinned evaluation environment succeeded in a new directory.

[Plan](../artifacts/REV2_panels_20261010_0430_v2/plan.json), [render audit](../artifacts/REV2_panels_20261010_0430_v2/render-audit.json).

## E12 — Qwen-family16k repair

**Data, repair and evaluations complete:**16,000 existing approved Alpaca queries, eight disjoint2k shards, Qwen R1's own greedy512-token responses. Family EAGLE drafter pin is the existing P3-D48 Qwen checkpoint. All five Qwen decoded responses/masks have been inspected; all five reach the approved512-token cap during reasoning. Training/evaluation follow completed full-dataset sealing and exact reviewed-sample checks. SPEED128/MATH500 and b1/b8 timing are complete; see the midday and live tables. The existing256-example result is positive but is not a16k result: full Δτ+.234[.199,.266] on SPEED n128 and+.207[.177,.237] on MATH n64, one seed ([source](P3-D48-seeds-generality-20261008.md)).

[Data plan](../artifacts/REV2_data_20261010_0430/plan.json).

## E9 — long-response repair

**R1 data sealed at06:17 ET:**4,000 long responses,3,530,565 answer tokens (mean882.6),165 capped at2,048; two exceed the repeated4gram diagnostic and remain included. Measured generation7.014A40GPUh across the four shards. The mixed corpus has20,000 response records/11,049,369 answer tokens. Exact inspected-sample checks passed for both paths, and all four one-epoch training jobs were published automatically. [Sealed data and audits](../artifacts/REV2_followups_20261010_0500/sealed-t0), [training plan](../artifacts/REV2_followups_20261010_0500/training-t0/plan.json).

**Data generation and audits complete; training retries active:** first4k queries from each target's existing16k Alpaca collection, generated afresh with a2,048-response-token cap, four1k shards per target. Explicit4,096 training context budget; no truncation. Interface/full will train on long4k alone and short16k+long4k. Five short and five long decoded samples/masks have been inspected for both targets. The mixture preserves the two responses to the same4k queries as explicitly labeled `short512`/`long2048` records with identical prompt IDs/tokens and distinct sample IDs; ordinary duplicate-query rejection remains the default. See the live tables for completed long-response comparisons.

The existing short-response repair closes39.2%[32.0,45.7] of R1's oracle gap at the8,192 evaluation ceiling (full, n32), compared with53.5%[50.2,57.0] at512. This is the measured motivation for E9, not its outcome. [A4 table](REV2-evidence-20261010/long-recovery.md).

Supplementary sampling acceptance is already complete under D53: at an8,192-token ceiling and T=.6/top-p=.95, full repair addsτ+.622[.470,.771] on R1 and+.989[.904,1.067] on Nemotron (MATH32,n32,one evaluation seed). These are acceptance measurements, separate from E10 greedy wall-clock and any optional sampled timing. [Prior raw-verified sampling evidence](REV1-paper-strengthening-20261010.md).

## E10 — reasoning wall-clock

**Run matrix:**27 long-MATH32 timing processes (8,192 cap, b1) plus66 MATH500-subset timing processes (512 cap, b1 n32/b8 n128). Three independent processes×three warm passes; first panel and startup retained separately. R1 none/reuse/interface/full/dedicated; Nemotron none/reuse/interface/full; short panels also independent1B. All use the selected official16k seed0 repairs and target-rendered prompts. Completed latency estimates appear in the live tables.

[Long plan](../artifacts/REV2_E10a_20261010_0430/plan.json), [short plan](../artifacts/REV2_E10b_20261010_0430/plan.json). Prerequisite data and completed-model acceptance are prioritized ahead of the long timing jobs without restarting the canonical queue.

## E11 — batches16/32

**Run matrix:**66 timing processes. Timing extension built and tested; Same SPEED128 panels, methods and three-process protocol. Defaults remain b8/cap512.

## E17 — whole-drafter LoRA

Most seed groups complete; final R1r16 evaluations are running. Scope built and tested, including head gradients and merged-checkpoint equivalence. Every drafter linear is adapted: fc, q/k/v/o, gate/up/down, LM head; target, embeddings and norms remain fixed. Rank16 has2,347,008 parameters; rank343 has50,313,984 (0.035% below the dense interface's50,331,648). R1 seeds0–2 and Nemotron seed0, same16k data/native objective. Results are added below after the required seed group completes. This is a compatible whole-LoRA baseline, not a claim to reproduce an architecture-changing method.

## E13 — scratch64k

**Run matrix:** one epoch from scratch on the existing64k data, official drafter architecture/vocabulary with target embeddings fixed. Preserve the Alpaca+Dolly source-mixture label. Measured GPU-hours and final SPEED/MATH64/MATH500 are added below on completion.

## E16 — training resource profile

Synchronized200-step profile implemented behind an opt-in flag. Measures target capture/data, drafter forward/backward and optimizer time, excluding exports. Peak allocated/reserved memory and serialized checkpoint bytes retained. Interface/full/whole-LoRA r16/r343 use the same first200 batches and original4477-step scheduler horizon. Status and measured resources appear in the live tables.

## E15 — vocabulary reselection

Opt-in training-response-only32k selection implemented and unit-tested: answer tokens only, deterministic frequency/ID ties, shared head rows preserved, newly included rows initialized from target head, both vocabulary maps updated. Two matched official16k full-repair runs queued at P2 priority; frozen export evaluation required before any number is used.

## E18 — tree feasibility

**Infeasible in the pinned engine.** The installed speculative configuration exposes no EAGLE static-token-tree field; proposer retains a FIXME for future tree-based forward-pass scheduling. EAGLE and rejection-sampling paths expose no tree implementation. Suffix-tree lookup is a different method. [Field inventory, source hashes and line evidence](../artifacts/REV2_diagnostics_20261010_0445/E18-feasibility.json). No environment or frozen engine change was made.

## A1 — per-domain SPEED results

**Complete.** [Full11-domain table](REV2-evidence-20261010/domains.md); [independent reducer output](../artifacts/REV2_A1_20261010_0445/domains.json). R1 repairs use three seeds, Nemotron one; all arms use paired query IDs. Both p1 and τ plus lengths/CIs are retained. Domain sample sizes are explicit; no domain is selected based on its outcome. Main-table official16k initialization throughout. Both repairs improve τ in all11 domains on both targets, with each pointwise95% interval above zero; these are pointwise rather than simultaneous intervals. Full-repair Δτ ranges+.325–.971 for R1 and+.183–1.068 for Nemotron.

## A2 — census composition and provenance

**Complete raw recomputation:** [model-level CSV](REV2-evidence-20261010/census.csv), [composition table](REV2-evidence-20261010/census-table.md), [raw audit](../artifacts/REV2_A2_20261010_0440/audit.json). All414 method/checkpoint/workload entries reproduce their archived p1 retention to1e−8:348 historical plus66 focused. Historical174 models:87 Llama/87 Qwen;163 derivative-own64-query workloads and11 general-fallback128-query workloads;42 unknown training histories. Combinations are retained, not forced into mutually exclusive single-stage categories. Groups separate family, lineage and workload, with equal checkpoint weights and10,000 hierarchical checkpoint/paired-query draws. A separate [predeclared eligible focused table](REV2-evidence-20261010/focused21-table.md) removes the2 pretrained controls and2 previously flagged collapsed GRPO models, leaving21 SPEED checkpoints; the all-model CSV retains every row and flag. [Filter counts](../artifacts/REV2_A2_eligible_source_20261010_0500/filters.json).

“Own-domain” denotes derivative-specific query sets, not shared prefixes or identical generated responses. A00/A10 have identical rendered query IDs but generate their own continuations. The fixed-prefix diagnostics address a different estimand. Historical engine0.31 generation was audited by FIX23; its recorded pre-freeze harness commits are preserved in the CSV audit, rather than relabeled6da2e42.

Probe prevalence: own-domain EAGLE14/163 degraded, DFlash17/163. Full16-request AUROC .908[.668,.983]/.934[.745,.993], respectively; thresholds remain frozen. The wider .91–1.00 range mixes distinct populations/methods, not repeated trials of one population. [Detailed probe counts and intervals](P5-census-triage-20261008.md).

## A3 — fixed-text and lineage evidence

Existing paired HF diagnostics, n64 sequences/origin,10,000 paired draws: feature-source effects on **parent-generated** text are R1−.0431[−.0527,−.0329] and Nemotron−.0924[−.1041,−.0811]. On public-reference text they are−.0504[−.0591,−.0417]/−.1020[−.1131,−.0913]. The GRPO50 parent's-text control is−.0007[−.0018,+.0005]. These effects persist without derivative-generated reasoning text. They are HF agreement effects, not online p1 or an additive decomposition of the online retention loss. [Full2×2 matrices, interactions, tap swaps and sources](P2-crossover-20261008.md).

R1 is a sibling from Base, not a direct Instruct child. The per-model census preserves that label and the Tülu multi-stage ladder. Parent-supervised training on identical R1 response IDs improves reuse, while child-supervised full repair adds+.190τ[.162,.216] on SPEED128 and+.152[.115,.181] on MATH64, one seed/256 examples. [Matched supervision control](REV1-paper-strengthening-20261010.md). [Typed lineage/online-control table](REV2-evidence-20261010/lineage-controls.md) includes the Base control, Tülu SFT→DPO→RLVR ladder and GRPO controls, with n/CIs. The same-weight Qwen thinking intervention gives EAGLE p1 retention1.038[1.000,1.080], but DFlash.923[.898,.951], n128; its effect is architecture-dependent ([source](T1-phase1b-20261008.md)).

## A4 — long-gap recovery and draft support

**Long recovery complete:** [paired three-arm recovery at all caps](REV2-evidence-20261010/long-recovery.md). Full R1 recovery:53.5%[50.2,57.0] at512;51.8%[49.3,54.6] at2048;39.2%[32.0,45.7] at8192, n32 each, official16k short-response training. These denominators are the oracle measured on the same panel/cap, not a reused SPEED denominator.

OOV must compare teachers on the **same** prefixes. On R1 child text, parent OOV is5.96%, child6.03%; comparing child6.03% against parent7.39% from parent-generated text mixes context distributions. [Per-query OOV CIs and paired differences](../artifacts/REV2_diagnostics_20261010_0445/oov.md) were recomputed from the saved HF diagnostic arrays. This support ceiling is conditional on the fixed-prefix diagnostic, not an online acceptance ceiling measured on another trajectory.

Supplementary A4c: [acceptance by generated-prefix length](REV2-evidence-20261010/prefix-bins.md), [raw inputs and paired CIs](../artifacts/REV2_A4c_20261010_0608/results.json). On existing8192-cap runs, full repair retains positive gains in the2048–4095 prefix bin: R1 Δτ+.321[.105,.555], Δp1+.101[.032,.166], n14; Nemotron Δτ+.490[.413,.567], Δp1+.215[.177,.248], n9, seed0. The4096–8191 bin contains only6 jointly continuing R1 queries (Δτ+.113[−.066,.277]) and2 Nemotron queries; its estimates remain in the table. These are paired online, length-conditioned subsets, not fixed-text effects or the same cohort across bins. Terminal speculative steps are omitted in this supplementary analysis to avoid EOS/nominal-bonus clipping; the whole-panel primary metrics are unchanged.

## A5 — exact native objective

Online capture selects target logits at draft-vocabulary token IDs **before** the native loss. The native fused `kl_div` normalizes both target and draft logits on that32k support. For selected support Vd, target q(v)=exp(z_target(v))/Σu∈Vd exp(z_target(u)); loss is KL(q||p_draft), over answer positions. It is not an unnormalized restriction of a full-vocabulary probability vector.

The installed native EAGLE implementation rolls forward predicted hidden states but feeds **shifted original ground-truth token IDs** at successive TTT steps (`core.py` lines329–342), not its argmax predictions. TTT3 and unit step-loss weights are unchanged in every repair arm. This distinction matters when describing training-time rollout or comparing with online policy adaptation. Sources: `followspec/online_capture.py:_forward`, native `speculators/models/eagle3/core.py`, native `speculators/losses/fused.py`. No trainer recipe was changed by this audit.

## A6 — measured versus estimated cost

Measured official16k R1: data8.916GPUh plus2.206 interface/2.211 full =11.122/11.127A40GPUh. Nemotron data8.588 plus1.240/1.398 =9.828/9.986. These count generation once per alternative; target capture is inside measured training. [Measured sources](P3-primary-official-20261010.md).

The dedicated reference is a **recipe-scale estimate**, not the oracle's training bill. Public recipe532k–646k examples;40 epochs is a public script default, actual oracle epochs unknown. At10–40 assumed epochs, generation+training projects1,348–19,232GPUh: roughly121–1,728× the measured11.127GPUh repair. A one-epoch sensitivity gives397–825GPUh (36–74×), so a two-orders claim depends on the stated multi-epoch assumption. Generation is explicitly included as291–353GPUh, extrapolated from the measured capped-response generation path; this is not a measurement of uncapped dedicated reasoning data. [Full decomposition, source pins and assumptions](P6-dedicated-cost-estimate-20261008.md). The pinned upstream training implementation also invokes its target inside `dataprepare` on every forward (`cnets.py:713–746`), rather than reading cached feature tensors; our proxy therefore does not accidentally charge per-epoch target capture against a cache-only recipe. Distributed throughput, TTT depth and sequence-length assumptions still differ; the estimate is not a measured training bill. [Pinned upstream implementation](https://github.com/SafeAILab/EAGLE/blob/cb7e0841fe0c206c6ed74a197ad5e2a1f13f5a2b/eagle/traineagle3/cnets.py#L713).

## A7 — Nemotron templates and mode

Main repair data and held-out evaluation apply the released target template with a user message, no `detailed thinking on/off` system instruction, and `enable_thinking=False` as a template argument. The actual rendered template has an **empty system turn**; it must be labeled default/empty-system, not conflated with an explicit “thinking off” intervention. E14/E10 preserve this template exactly. The explicit on/off study is separate and changes rendered prompts while preserving raw questions: EAGLE Δp1−.0296[−.0437,−.0157], Δτ−.1184[−.1645,−.0729], n128. [Toggle evidence](P2-nemotron-toggle-20261008.md).

## A8 — family reference versus main-table drafter

The focused census uses the **production** family drafter: R1 parent p1 .56634, child .41082, retention .72539; Nemotron .62619/.43587/.69606 on SPEED128. The main table uses the **official** family drafter selected by D51. Dividing an official child p1 by a production retention is not a valid reconstruction of parent p1. These values are independently reproduced in the A2 CSV. “Parent” here is the family drafter's reference target, not always the derivative's immediate ancestor.

## A9 — shareable interface storage

Official interface50,331,648 parameters is100.663MB in bf16 (96MiB). Full mutable drafter424,689,664 parameters is849.379MB bf16 (810.031MiB). Existing interface export metadata lists only `fc.weight` as mutable. [Fresh tensor audit](../artifacts/REV2_A9_20261010_0452/proof.json) verifies all14 frozen release tensors for both targets, exactly after the logged fp16→fp32 load conversion; the decoder/head values therefore remain identical at the common serving dtype. These are tensor-size accounting in bf16, distinct from current fp32 training/export file sizes and complete engine resident memory. E16 will supply actual serialized bytes and memory/time measurements.

## A10 — self-elicited versus Alpaca4k

Existing production, one-epoch, one-seed controls: on SPEED128, generic minus self Δτ is+.004[−.012,.020] for interface and+.009[−.012,.031] for full; Δp1+.001[−.004,.007]/+.002[−.006,.009]. On MATH64, Δτ+.028[.007,.049]/+.045[.007,.083]. These are source ablations with different sequence lengths/token totals/step counts, not token-matched equivalence tests. [Raw-verified source-ablation table](P3-D50-consolidated-20261009.md). Self-elicitation avoids reliance on the external instruction dataset; both variants remain training-set-free rather than data-free.

<!-- REV2 LIVE RAW RESULTS BEGIN -->
## Live raw-result tables

Independent reduction snapshot: 2026-10-10T17:07:38.377443-04:00. Incomplete groups remain pending; no provisional acceptance values are substituted.

### E8 matched-capacity
Completed comparison rows: 12; pending inputs: 0.
[Immutable table](../artifacts/REV2_live_analysis_20261010_1255/20261010_170613_478699/E8/report.md) · [Numbers, intervals, n and sources](../artifacts/REV2_live_analysis_20261010_1255/20261010_170613_478699/E8/results.json)

| Target | Parameters | Panel | n/seeds | Interface τ | Decoder τ | Δτ [95% CI] | Δp1 [95% CI] |
|---|---|---|---:|---:|---:|---|---|
| 0 | dense50M | speed128 | 128/3 | 2.414 | 2.415 | -0.001 [-0.025,+0.023] | +0.006 [-0.003,+0.015] |
| 0 | dense50M | math64 | 64/3 | 2.817 | 2.836 | -0.019 [-0.049,+0.011] | -0.001 [-0.009,+0.007] |
| 0 | dense50M | math500 | 500/1 | 2.773 | 2.803 | -0.029 [-0.041,-0.018] | -0.002 [-0.005,+0.002] |
| 0 | lowrank1.229M | speed128 | 128/3 | 2.300 | 2.302 | -0.002 [-0.022,+0.017] | +0.002 [-0.004,+0.009] |
| 0 | lowrank1.229M | math64 | 64/3 | 2.633 | 2.650 | -0.017 [-0.048,+0.010] | -0.000 [-0.008,+0.007] |
| 0 | lowrank1.229M | math500 | 500/1 | 2.598 | 2.617 | -0.019 [-0.030,-0.009] | +0.000 [-0.003,+0.003] |
| 1 | dense50M | speed128 | 128/3 | 2.406 | 2.383 | +0.023 [-0.006,+0.052] | +0.008 [-0.001,+0.016] |
| 1 | dense50M | math64 | 64/3 | 2.712 | 2.705 | +0.008 [-0.017,+0.033] | +0.007 [-0.001,+0.015] |
| 1 | dense50M | math500 | 500/1 | 2.664 | 2.660 | +0.003 [-0.005,+0.012] | +0.006 [+0.003,+0.008] |
| 1 | lowrank1.229M | speed128 | 128/3 | 2.276 | 2.263 | +0.014 [-0.015,+0.042] | +0.002 [-0.009,+0.014] |
| 1 | lowrank1.229M | math64 | 64/3 | 2.514 | 2.496 | +0.018 [-0.010,+0.045] | +0.009 [+0.000,+0.017] |
| 1 | lowrank1.229M | math500 | 500/1 | 2.455 | 2.451 | +0.004 [-0.005,+0.014] | +0.005 [+0.002,+0.009] |

### E9/E12/E13/E14/E15/E17 acceptance
Completed comparison rows: 71; pending inputs: 0.
[Immutable table](../artifacts/REV2_live_analysis_20261010_1255/20261010_170613_478699/acceptance/report.md) · [Numbers, intervals, n and sources](../artifacts/REV2_live_analysis_20261010_1255/20261010_170613_478699/acceptance/results.json)

| Experiment | Target | Arm / data | Panel | n/seeds | p1 [95% CI] | τ [95% CI] | Δτ vs reuse [95% CI] | Oracle recovery [95% CI] |
|---|---|---|---|---:|---|---|---|---|
| E12 | 2 | fc / generic16k | math500 | 500/1 | 0.692 [0.687,0.697] | 2.599 [2.578,2.619] | 0.281 [0.268,0.293] | -- |
| E12 | 2 | fc / generic16k | speed128 | 128/1 | 0.581 [0.560,0.600] | 2.179 [2.121,2.237] | 0.254 [0.228,0.278] | -- |
| E12 | 2 | full / generic16k | math500 | 500/1 | 0.728 [0.723,0.733] | 2.791 [2.767,2.815] | 0.473 [0.456,0.491] | -- |
| E12 | 2 | full / generic16k | speed128 | 128/1 | 0.603 [0.579,0.625] | 2.302 [2.233,2.371] | 0.377 [0.335,0.415] | -- |
| E12 | 2 | independent /  | math500 | 500/1 | 0.737 [0.731,0.742] | 3.181 [3.149,3.212] | 0.862 [0.838,0.886] | -- |
| E12 | 2 | independent /  | speed128 | 128/1 | 0.603 [0.590,0.617] | 2.413 [2.345,2.483] | 0.487 [0.431,0.546] | -- |
| E12 | 2 | reuse /  | math500 | 500/1 | 0.625 [0.620,0.630] | 2.318 [2.300,2.337] | 0.000 [0.000,0.000] | -- |
| E14 | 0 | fc /  | math500 | 500/3 | 0.723 [0.719,0.727] | 2.775 [2.755,2.794] | 0.847 [0.833,0.860] | 0.442 [0.435,0.449] |
| E14 | 0 | full /  | math500 | 500/3 | 0.755 [0.750,0.759] | 2.967 [2.945,2.988] | 1.039 [1.020,1.056] | 0.543 [0.535,0.550] |
| E14 | 1 | fc /  | math500 | 500/1 | 0.702 [0.697,0.707] | 2.664 [2.643,2.684] | 0.978 [0.961,0.995] | -- |
| E14 | 1 | full /  | math500 | 500/1 | 0.738 [0.733,0.743] | 2.859 [2.838,2.882] | 1.173 [1.154,1.193] | -- |
| E14 | 1 | independent /  | math500 | 500/1 | 0.664 [0.659,0.669] | 2.785 [2.763,2.808] | 1.099 [1.077,1.122] | -- |
| E14 | 1 | reuse /  | math500 | 500/1 | 0.444 [0.440,0.448] | 1.686 [1.675,1.697] | 0.000 [0.000,0.000] | -- |
| E15 | 0 | full-reselect32k /  | math500 | 500/1 | 0.755 [0.750,0.760] | 2.982 [2.958,3.006] | 1.054 [1.034,1.074] | 0.551 [0.542,0.560] |
| E15 | 0 | full-reselect32k /  | math64 | 64/1 | 0.763 [0.751,0.775] | 3.017 [2.953,3.085] | 1.094 [1.035,1.155] | 0.552 [0.529,0.577] |
| E15 | 0 | full-reselect32k /  | speed128 | 128/1 | 0.644 [0.617,0.668] | 2.521 [2.440,2.598] | 0.757 [0.708,0.804] | 0.698 [0.672,0.724] |
| E15 | 1 | full-reselect32k /  | math500 | 500/1 | 0.737 [0.732,0.742] | 2.853 [2.831,2.876] | 1.167 [1.146,1.187] | -- |
| E15 | 1 | full-reselect32k /  | math64 | 64/1 | 0.746 [0.733,0.759] | 2.902 [2.847,2.958] | 1.199 [1.149,1.250] | -- |
| E15 | 1 | full-reselect32k /  | speed128 | 128/1 | 0.621 [0.591,0.648] | 2.470 [2.379,2.556] | 0.707 [0.646,0.766] | -- |
| E17 | 0 | whole-r16 /  | math500 | 500/3 | 0.702 [0.697,0.706] | 2.685 [2.667,2.703] | 0.757 [0.745,0.769] | 0.395 [0.389,0.402] |
| E17 | 0 | whole-r16 /  | math64 | 64/3 | 0.710 [0.699,0.720] | 2.715 [2.666,2.765] | 0.792 [0.759,0.825] | 0.400 [0.381,0.420] |
| E17 | 0 | whole-r16 /  | speed128 | 128/3 | 0.606 [0.580,0.630] | 2.345 [2.272,2.416] | 0.581 [0.543,0.619] | 0.536 [0.514,0.558] |
| E17 | 0 | whole-r343 /  | math500 | 500/3 | 0.734 [0.729,0.738] | 2.849 [2.828,2.869] | 0.921 [0.905,0.937] | 0.481 [0.473,0.489] |
| E17 | 0 | whole-r343 /  | math64 | 64/3 | 0.741 [0.730,0.752] | 2.882 [2.825,2.940] | 0.959 [0.916,1.004] | 0.484 [0.463,0.507] |
| E17 | 0 | whole-r343 /  | speed128 | 128/3 | 0.631 [0.603,0.656] | 2.452 [2.374,2.528] | 0.688 [0.643,0.731] | 0.635 [0.612,0.657] |
| E17 | 1 | whole-r16 /  | math500 | 500/1 | 0.673 [0.668,0.677] | 2.554 [2.536,2.574] | 0.868 [0.853,0.883] | -- |
| E17 | 1 | whole-r16 /  | math64 | 64/1 | 0.685 [0.673,0.696] | 2.607 [2.562,2.652] | 0.904 [0.869,0.939] | -- |
| E17 | 1 | whole-r16 /  | speed128 | 128/1 | 0.595 [0.568,0.619] | 2.342 [2.260,2.420] | 0.579 [0.531,0.626] | -- |
| E17 | 1 | whole-r343 /  | math500 | 500/1 | 0.710 [0.706,0.715] | 2.720 [2.700,2.740] | 1.033 [1.017,1.050] | -- |
| E17 | 1 | whole-r343 /  | math64 | 64/1 | 0.723 [0.711,0.734] | 2.764 [2.714,2.815] | 1.061 [1.019,1.103] | -- |
| E17 | 1 | whole-r343 /  | speed128 | 128/1 | 0.615 [0.585,0.642] | 2.430 [2.343,2.515] | 0.667 [0.612,0.720] | -- |
| E9 | 0 | fc / long4k | math32-2048 | 32/1 | 0.728 [0.716,0.739] | 2.816 [2.747,2.881] | 0.736 [0.681,0.793] | 0.397 [0.375,0.417] |
| E9 | 0 | fc / long4k | math32-512 | 32/1 | 0.710 [0.697,0.722] | 2.677 [2.607,2.746] | 0.778 [0.724,0.835] | 0.393 [0.369,0.418] |
| E9 | 0 | fc / long4k | math32-8192 | 32/1 | 0.672 [0.633,0.707] | 2.565 [2.409,2.713] | 0.596 [0.481,0.707] | 0.329 [0.271,0.381] |
| E9 | 0 | fc / long4k | math64 | 64/1 | 0.712 [0.701,0.723] | 2.703 [2.653,2.755] | 0.780 [0.745,0.816] | 0.394 [0.374,0.415] |
| E9 | 0 | fc / long4k | speed128 | 128/1 | 0.611 [0.584,0.635] | 2.353 [2.278,2.423] | 0.589 [0.549,0.627] | 0.543 [0.519,0.566] |
| E9 | 0 | fc / mixed20k | math32-2048 | 32/1 | 0.742 [0.731,0.753] | 2.903 [2.834,2.972] | 0.823 [0.759,0.885] | 0.444 [0.421,0.467] |
| E9 | 0 | fc / mixed20k | math32-512 | 32/1 | 0.728 [0.713,0.742] | 2.802 [2.725,2.877] | 0.904 [0.841,0.965] | 0.456 [0.428,0.485] |
| E9 | 0 | fc / mixed20k | math32-8192 | 32/1 | 0.680 [0.637,0.718] | 2.636 [2.474,2.782] | 0.666 [0.543,0.782] | 0.368 [0.305,0.426] |
| E9 | 0 | fc / mixed20k | math64 | 64/1 | 0.733 [0.721,0.744] | 2.833 [2.779,2.887] | 0.910 [0.870,0.949] | 0.459 [0.438,0.480] |
| E9 | 0 | fc / mixed20k | speed128 | 128/1 | 0.627 [0.600,0.652] | 2.425 [2.347,2.497] | 0.661 [0.619,0.703] | 0.610 [0.585,0.634] |
| E9 | 0 | full / long4k | math32-2048 | 32/1 | 0.760 [0.746,0.772] | 3.006 [2.923,3.085] | 0.925 [0.859,0.993] | 0.499 [0.473,0.524] |
| E9 | 0 | full / long4k | math32-512 | 32/1 | 0.740 [0.726,0.756] | 2.854 [2.770,2.940] | 0.956 [0.891,1.024] | 0.483 [0.451,0.516] |
| E9 | 0 | full / long4k | math32-8192 | 32/1 | 0.703 [0.660,0.741] | 2.750 [2.584,2.906] | 0.781 [0.657,0.899] | 0.431 [0.373,0.484] |
| E9 | 0 | full / long4k | math64 | 64/1 | 0.745 [0.734,0.756] | 2.911 [2.858,2.964] | 0.988 [0.939,1.035] | 0.499 [0.478,0.519] |
| E9 | 0 | full / long4k | speed128 | 128/1 | 0.635 [0.607,0.660] | 2.484 [2.406,2.559] | 0.721 [0.677,0.762] | 0.664 [0.639,0.691] |
| E9 | 0 | full / mixed20k | math32-2048 | 32/1 | 0.775 [0.761,0.790] | 3.088 [2.998,3.177] | 1.008 [0.936,1.082] | 0.543 [0.512,0.576] |
| E9 | 0 | full / mixed20k | math32-512 | 32/1 | 0.757 [0.741,0.773] | 2.960 [2.884,3.033] | 1.061 [0.993,1.132] | 0.536 [0.506,0.568] |
| E9 | 0 | full / mixed20k | math32-8192 | 32/1 | 0.694 [0.643,0.739] | 2.705 [2.508,2.895] | 0.735 [0.580,0.884] | 0.406 [0.329,0.475] |
| E9 | 0 | full / mixed20k | math64 | 64/1 | 0.761 [0.749,0.772] | 3.009 [2.950,3.070] | 1.086 [1.037,1.137] | 0.548 [0.526,0.571] |
| E9 | 0 | full / mixed20k | speed128 | 128/1 | 0.649 [0.621,0.675] | 2.545 [2.462,2.625] | 0.782 [0.732,0.829] | 0.721 [0.695,0.746] |
| E9 | 1 | fc / long4k | math32-2048 | 32/1 | 0.700 [0.688,0.711] | 2.687 [2.629,2.744] | 0.955 [0.905,1.006] | -- |
| E9 | 1 | fc / long4k | math32-512 | 32/1 | 0.684 [0.668,0.701] | 2.561 [2.498,2.623] | 0.872 [0.823,0.919] | -- |
| E9 | 1 | fc / long4k | math32-8192 | 32/1 | 0.651 [0.622,0.676] | 2.469 [2.358,2.573] | 0.819 [0.737,0.896] | -- |
| E9 | 1 | fc / long4k | math64 | 64/1 | 0.688 [0.676,0.701] | 2.611 [2.561,2.660] | 0.908 [0.869,0.947] | -- |
| E9 | 1 | fc / long4k | speed128 | 128/1 | 0.596 [0.568,0.621] | 2.346 [2.263,2.425] | 0.582 [0.535,0.627] | -- |
| E9 | 1 | fc / mixed20k | math32-2048 | 32/1 | 0.719 [0.708,0.730] | 2.771 [2.714,2.826] | 1.040 [0.994,1.086] | -- |
| E9 | 1 | fc / mixed20k | math32-512 | 32/1 | 0.705 [0.687,0.724] | 2.684 [2.614,2.756] | 0.994 [0.937,1.050] | -- |
| E9 | 1 | fc / mixed20k | math32-8192 | 32/1 | 0.676 [0.640,0.709] | 2.578 [2.446,2.701] | 0.927 [0.828,1.027] | -- |
| E9 | 1 | fc / mixed20k | math64 | 64/1 | 0.719 [0.707,0.732] | 2.735 [2.682,2.787] | 1.032 [0.986,1.078] | -- |
| E9 | 1 | fc / mixed20k | speed128 | 128/1 | 0.616 [0.588,0.642] | 2.426 [2.339,2.511] | 0.663 [0.609,0.715] | -- |
| E9 | 1 | full / long4k | math32-2048 | 32/1 | 0.739 [0.728,0.750] | 2.871 [2.809,2.935] | 1.140 [1.071,1.208] | -- |
| E9 | 1 | full / long4k | math32-512 | 32/1 | 0.721 [0.705,0.739] | 2.752 [2.677,2.828] | 1.062 [1.003,1.124] | -- |
| E9 | 1 | full / long4k | math32-8192 | 32/1 | 0.698 [0.666,0.727] | 2.696 [2.563,2.823] | 1.046 [0.925,1.165] | -- |
| E9 | 1 | full / long4k | math64 | 64/1 | 0.732 [0.720,0.745] | 2.810 [2.753,2.865] | 1.107 [1.057,1.156] | -- |
| E9 | 1 | full / long4k | speed128 | 128/1 | 0.623 [0.595,0.649] | 2.464 [2.378,2.548] | 0.701 [0.647,0.754] | -- |
| E9 | 1 | full / mixed20k | math32-2048 | 32/1 | 0.752 [0.741,0.763] | 2.951 [2.888,3.015] | 1.220 [1.162,1.275] | -- |
| E9 | 1 | full / mixed20k | math32-512 | 32/1 | 0.743 [0.726,0.760] | 2.879 [2.804,2.955] | 1.189 [1.128,1.254] | -- |
| E9 | 1 | full / mixed20k | math32-8192 | 32/1 | 0.711 [0.679,0.740] | 2.776 [2.634,2.907] | 1.126 [1.022,1.221] | -- |
| E9 | 1 | full / mixed20k | math64 | 64/1 | 0.752 [0.740,0.764] | 2.928 [2.873,2.983] | 1.225 [1.175,1.276] | -- |
| E9 | 1 | full / mixed20k | speed128 | 128/1 | 0.632 [0.603,0.659] | 2.510 [2.420,2.595] | 0.747 [0.690,0.802] | -- |
| Training arm | Target | Seed | Examples | Steps | Batch tokens | Measured train GPUh |
|---|---|---:|---:|---:|---:|---:|
| E12 fc generic16k | 2 | 0 | 16000 | 4797 | 2048 | 2.078 |
| E12 full generic16k | 2 | 0 | 16000 | 4797 | 2048 | 2.769 |
| E15 full-reselect32k  | 0 | 0 | 16000 | 4477 | 2048 | 2.745 |
| E15 full-reselect32k  | 1 | 0 | 16000 | 2625 | 2048 | 1.369 |
| E17 whole-r16  | 0 | 0 | 16000 | 4477 | 2048 | 2.527 |
| E17 whole-r16  | 0 | 1 | 16000 | 4472 | 2048 | 2.717 |
| E17 whole-r16  | 0 | 2 | 16000 | 4481 | 2048 | 2.039 |
| E17 whole-r343  | 0 | 0 | 16000 | 4477 | 2048 | 2.154 |
| E17 whole-r343  | 0 | 1 | 16000 | 4472 | 2048 | 2.219 |
| E17 whole-r343  | 0 | 2 | 16000 | 4481 | 2048 | 2.138 |
| E17 whole-r16  | 1 | 0 | 16000 | 2625 | 2048 | 1.628 |
| E17 whole-r343  | 1 | 0 | 16000 | 2625 | 2048 | 1.314 |
| E9 fc long4k | 0 | 0 | 4000 | 2052 | 2304 | 1.209 |
| E9 fc mixed20k | 0 | 0 | 20000 | 5856 | 2304 | 3.003 |
| E9 full long4k | 0 | 0 | 4000 | 2052 | 2304 | 1.154 |
| E9 full mixed20k | 0 | 0 | 20000 | 5856 | 2304 | 3.965 |
| E9 fc long4k | 1 | 0 | 4000 | 833 | 2304 | 0.497 |
| E9 fc mixed20k | 1 | 0 | 20000 | 3134 | 2304 | 1.817 |
| E9 full long4k | 1 | 0 | 4000 | 833 | 2304 | 0.501 |
| E9 full mixed20k | 1 | 0 | 20000 | 3134 | 2304 | 1.867 |

### E10/E11/E12 timing
Completed comparison rows: 90; pending inputs: 0.
[Immutable table](../artifacts/REV2_live_analysis_20261010_1255/20261010_170613_478699/timing/report.md) · [Numbers, intervals, n and sources](../artifacts/REV2_live_analysis_20261010_1255/20261010_170613_478699/timing/results.json)

| Experiment | Target | Batch | Arm / reference | n/processes | Warm panel speedup [95% CI] | Warm token ratio [95% CI] | Cold+startup [95% CI] |
|---|---|---:|---|---:|---|---|---|
| E10a | 0 | 1 | fc / none | 32/3 | 1.627 [1.288,2.076] | 1.647 [1.496,1.862] | 1.569 [1.254,1.966] |
| E10a | 0 | 1 | fc / reuse | 32/3 | 1.222 [1.008,1.495] | 1.201 [1.117,1.311] | 1.212 [1.011,1.466] |
| E10a | 0 | 1 | full / none | 32/3 | 1.767 [1.437,2.272] | 1.729 [1.570,1.965] | 1.691 [1.390,2.130] |
| E10a | 0 | 1 | full / reuse | 32/3 | 1.327 [1.151,1.622] | 1.261 [1.187,1.379] | 1.307 [1.142,1.571] |
| E10a | 0 | 1 | oracle / none | 32/3 | 2.108 [1.677,2.751] | 2.149 [1.895,2.538] | 2.002 [1.616,2.543] |
| E10a | 0 | 1 | oracle / reuse | 32/3 | 1.583 [1.265,2.064] | 1.567 [1.421,1.794] | 1.547 [1.256,1.974] |
| E10a | 0 | 1 | reuse / none | 32/3 | 1.331 [1.095,1.640] | 1.372 [1.289,1.471] | 1.294 [1.071,1.578] |
| E10a | 1 | 1 | fc / none | 32/3 | 1.538 [1.315,1.861] | 1.671 [1.514,1.894] | 1.475 [1.278,1.750] |
| E10a | 1 | 1 | fc / reuse | 32/3 | 1.378 [1.216,1.550] | 1.409 [1.331,1.513] | 1.351 [1.203,1.501] |
| E10a | 1 | 1 | full / none | 32/3 | 1.634 [1.371,2.020] | 1.754 [1.573,2.028] | 1.566 [1.332,1.894] |
| E10a | 1 | 1 | full / reuse | 32/3 | 1.465 [1.282,1.654] | 1.480 [1.386,1.616] | 1.435 [1.267,1.594] |
| E10a | 1 | 1 | reuse / none | 32/3 | 1.116 [0.999,1.282] | 1.186 [1.126,1.262] | 1.092 [0.982,1.244] |
| E10b | 0 | 1 | fc / none | 32/3 | 2.141 [2.095,2.188] | 2.141 [2.095,2.188] | 1.637 [1.591,1.682] |
| E10b | 0 | 1 | fc / reuse | 32/3 | 1.444 [1.409,1.480] | 1.444 [1.409,1.480] | 1.295 [1.272,1.319] |
| E10b | 0 | 1 | full / none | 32/3 | 2.305 [2.255,2.360] | 2.305 [2.255,2.360] | 1.769 [1.738,1.800] |
| E10b | 0 | 1 | full / reuse | 32/3 | 1.555 [1.516,1.594] | 1.555 [1.516,1.594] | 1.400 [1.357,1.438] |
| E10b | 0 | 1 | independent / none | 32/3 | 1.525 [1.485,1.569] | 1.525 [1.485,1.569] | 1.320 [1.291,1.352] |
| E10b | 0 | 1 | independent / reuse | 32/3 | 1.029 [0.999,1.060] | 1.029 [0.999,1.060] | 1.045 [1.000,1.088] |
| E10b | 0 | 1 | oracle / none | 32/3 | 2.872 [2.797,2.952] | 2.872 [2.797,2.952] | 1.977 [1.901,2.041] |
| E10b | 0 | 1 | oracle / reuse | 32/3 | 1.937 [1.867,2.007] | 1.937 [1.867,2.007] | 1.564 [1.518,1.614] |
| E10b | 0 | 1 | reuse / none | 32/3 | 1.483 [1.444,1.523] | 1.483 [1.444,1.523] | 1.264 [1.223,1.310] |
| E10b | 0 | 8 | fc / none | 128/3 | 1.934 [1.889,1.977] | 1.935 [1.889,1.978] | 1.328 [1.278,1.406] |
| E10b | 0 | 8 | fc / reuse | 128/3 | 1.455 [1.422,1.486] | 1.453 [1.422,1.485] | 1.241 [1.221,1.260] |
| E10b | 0 | 8 | full / none | 128/3 | 2.053 [2.006,2.097] | 2.055 [2.009,2.098] | 1.371 [1.320,1.453] |
| E10b | 0 | 8 | full / reuse | 128/3 | 1.544 [1.509,1.578] | 1.544 [1.508,1.579] | 1.282 [1.262,1.302] |
| E10b | 0 | 8 | independent / none | 128/3 | 1.386 [1.356,1.418] | 1.387 [1.357,1.420] | 1.146 [1.100,1.204] |
| E10b | 0 | 8 | independent / reuse | 128/3 | 1.042 [1.010,1.074] | 1.042 [1.009,1.074] | 1.072 [1.047,1.098] |
| E10b | 0 | 8 | oracle / none | 128/3 | 2.535 [2.427,2.629] | 2.537 [2.428,2.631] | 1.564 [1.480,1.639] |
| E10b | 0 | 8 | oracle / reuse | 128/3 | 1.906 [1.812,1.994] | 1.906 [1.812,1.992] | 1.462 [1.414,1.517] |
| E10b | 0 | 8 | reuse / none | 128/3 | 1.330 [1.300,1.357] | 1.331 [1.302,1.358] | 1.070 [1.032,1.123] |
| E10b | 1 | 1 | fc / none | 32/3 | 2.079 [2.023,2.137] | 2.079 [2.023,2.137] | 1.595 [1.539,1.661] |
| E10b | 1 | 1 | fc / reuse | 32/3 | 1.569 [1.535,1.604] | 1.569 [1.535,1.604] | 1.377 [1.329,1.437] |
| E10b | 1 | 1 | full / none | 32/3 | 1.944 [1.583,2.249] | 1.944 [1.583,2.249] | 1.550 [1.396,1.667] |
| E10b | 1 | 1 | full / reuse | 32/3 | 1.467 [1.192,1.693] | 1.467 [1.192,1.693] | 1.338 [1.213,1.434] |
| E10b | 1 | 1 | independent / none | 32/3 | 1.315 [1.079,1.522] | 1.315 [1.079,1.522] | 1.151 [0.959,1.318] |
| E10b | 1 | 1 | independent / reuse | 32/3 | 0.992 [0.813,1.149] | 0.992 [0.813,1.149] | 0.994 [0.836,1.132] |
| E10b | 1 | 1 | reuse / none | 32/3 | 1.325 [1.290,1.362] | 1.325 [1.290,1.362] | 1.158 [1.129,1.190] |
| E10b | 1 | 8 | fc / none | 128/3 | 2.118 [1.824,2.640] | 2.118 [1.824,2.640] | 1.588 [1.375,1.974] |
| E10b | 1 | 8 | fc / reuse | 128/3 | 1.552 [1.516,1.587] | 1.552 [1.516,1.587] | 1.339 [1.296,1.377] |
| E10b | 1 | 8 | full / none | 128/3 | 2.228 [1.919,2.749] | 2.228 [1.919,2.749] | 1.592 [1.329,1.998] |
| E10b | 1 | 8 | full / reuse | 128/3 | 1.633 [1.584,1.682] | 1.633 [1.584,1.682] | 1.342 [1.313,1.375] |
| E10b | 1 | 8 | independent / none | 128/3 | 1.499 [1.294,1.842] | 1.499 [1.294,1.842] | 1.297 [1.108,1.557] |
| E10b | 1 | 8 | independent / reuse | 128/3 | 1.099 [1.061,1.136] | 1.099 [1.061,1.136] | 1.093 [1.058,1.126] |
| E10b | 1 | 8 | reuse / none | 128/3 | 1.364 [1.185,1.690] | 1.364 [1.185,1.690] | 1.186 [1.005,1.461] |
| E11 | 0 | 16 | fc / none | 128/3 | 1.006 [0.912,1.138] | 1.010 [0.913,1.145] | 0.853 [0.803,0.915] |
| E11 | 0 | 16 | fc / reuse | 128/3 | 1.070 [1.024,1.119] | 1.073 [1.034,1.122] | 1.000 [0.953,1.054] |
| E11 | 0 | 16 | full / none | 128/3 | 1.043 [0.930,1.209] | 1.040 [0.928,1.201] | 0.876 [0.814,0.952] |
| E11 | 0 | 16 | full / reuse | 128/3 | 1.110 [1.052,1.183] | 1.105 [1.050,1.176] | 1.027 [0.981,1.067] |
| E11 | 0 | 16 | independent / none | 128/3 | 1.037 [1.016,1.059] | 1.035 [1.012,1.060] | 0.889 [0.877,0.901] |
| E11 | 0 | 16 | independent / reuse | 128/3 | 1.104 [1.002,1.197] | 1.099 [0.995,1.196] | 1.042 [0.984,1.096] |
| E11 | 0 | 16 | oracle / none | 128/3 | 1.080 [0.965,1.229] | 1.082 [0.968,1.227] | 0.882 [0.820,0.956] |
| E11 | 0 | 16 | oracle / reuse | 128/3 | 1.150 [1.063,1.241] | 1.150 [1.069,1.240] | 1.034 [0.989,1.091] |
| E11 | 0 | 16 | reuse / none | 128/3 | 0.940 [0.862,1.041] | 0.941 [0.865,1.044] | 0.853 [0.809,0.905] |
| E11 | 0 | 32 | fc / none | 128/3 | 0.833 [0.809,0.864] | 0.834 [0.808,0.865] | 0.723 [0.697,0.745] |
| E11 | 0 | 32 | fc / reuse | 128/3 | 1.091 [1.070,1.117] | 1.093 [1.073,1.116] | 1.024 [0.969,1.123] |
| E11 | 0 | 32 | full / none | 128/3 | 0.840 [0.813,0.869] | 0.839 [0.810,0.867] | 0.740 [0.683,0.796] |
| E11 | 0 | 32 | full / reuse | 128/3 | 1.101 [1.072,1.123] | 1.099 [1.066,1.125] | 1.048 [0.962,1.132] |
| E11 | 0 | 32 | independent / none | 128/3 | 0.817 [0.715,0.894] | 0.815 [0.716,0.892] | 0.804 [0.752,0.860] |
| E11 | 0 | 32 | independent / reuse | 128/3 | 1.070 [0.942,1.180] | 1.069 [0.940,1.182] | 1.139 [1.062,1.223] |
| E11 | 0 | 32 | oracle / none | 128/3 | 0.913 [0.824,1.013] | 0.910 [0.823,1.008] | 0.739 [0.686,0.818] |
| E11 | 0 | 32 | oracle / reuse | 128/3 | 1.196 [1.095,1.310] | 1.193 [1.093,1.308] | 1.046 [0.982,1.107] |
| E11 | 0 | 32 | reuse / none | 128/3 | 0.763 [0.748,0.782] | 0.763 [0.749,0.780] | 0.706 [0.655,0.756] |
| E11 | 1 | 16 | fc / none | 128/3 | 1.288 [1.026,1.668] | 1.309 [1.053,1.687] | 0.946 [0.871,1.033] |
| E11 | 1 | 16 | fc / reuse | 128/3 | 1.152 [1.062,1.272] | 1.149 [1.072,1.256] | 1.148 [1.087,1.212] |
| E11 | 1 | 16 | full / none | 128/3 | 1.352 [1.053,1.794] | 1.367 [1.085,1.801] | 0.919 [0.829,1.034] |
| E11 | 1 | 16 | full / reuse | 128/3 | 1.209 [1.091,1.367] | 1.200 [1.100,1.340] | 1.114 [1.043,1.208] |
| E11 | 1 | 16 | independent / none | 128/3 | 1.269 [1.119,1.512] | 1.281 [1.120,1.532] | 0.934 [0.885,1.011] |
| E11 | 1 | 16 | independent / reuse | 128/3 | 1.135 [1.043,1.224] | 1.125 [1.030,1.214] | 1.133 [1.070,1.203] |
| E11 | 1 | 16 | reuse / none | 128/3 | 1.118 [0.956,1.362] | 1.139 [0.970,1.387] | 0.824 [0.783,0.866] |
| E11 | 1 | 32 | fc / none | 128/3 | 0.974 [0.878,1.134] | 0.980 [0.877,1.145] | 0.755 [0.715,0.801] |
| E11 | 1 | 32 | fc / reuse | 128/3 | 1.089 [1.032,1.178] | 1.085 [1.024,1.172] | 1.004 [0.953,1.047] |
| E11 | 1 | 32 | full / none | 128/3 | 0.984 [0.880,1.161] | 0.990 [0.881,1.158] | 0.743 [0.706,0.795] |
| E11 | 1 | 32 | full / reuse | 128/3 | 1.101 [1.023,1.220] | 1.095 [1.020,1.206] | 0.989 [0.943,1.037] |
| E11 | 1 | 32 | independent / none | 128/3 | 1.057 [1.011,1.110] | 1.056 [1.013,1.100] | 0.860 [0.841,0.882] |
| E11 | 1 | 32 | independent / reuse | 128/3 | 1.183 [1.040,1.299] | 1.168 [1.022,1.282] | 1.145 [1.050,1.248] |
| E11 | 1 | 32 | reuse / none | 128/3 | 0.894 [0.843,0.991] | 0.903 [0.849,1.002] | 0.751 [0.700,0.805] |
| E12 | 2 | 1 | fc / none | 32/3 | 1.744 [1.655,1.833] | 1.749 [1.659,1.838] | 1.413 [1.327,1.508] |
| E12 | 2 | 1 | fc / reuse | 32/3 | 1.125 [1.099,1.148] | 1.125 [1.105,1.144] | 1.083 [1.045,1.122] |
| E12 | 2 | 1 | full / none | 32/3 | 1.850 [1.744,1.953] | 1.853 [1.748,1.955] | 1.464 [1.382,1.544] |
| E12 | 2 | 1 | full / reuse | 32/3 | 1.193 [1.155,1.232] | 1.192 [1.159,1.224] | 1.122 [1.078,1.178] |
| E12 | 2 | 1 | independent / none | 32/3 | 1.519 [1.449,1.599] | 1.524 [1.456,1.601] | 1.310 [1.251,1.371] |
| E12 | 2 | 1 | independent / reuse | 32/3 | 0.980 [0.940,1.029] | 0.980 [0.944,1.029] | 1.004 [0.975,1.043] |
| E12 | 2 | 1 | reuse / none | 32/3 | 1.551 [1.484,1.621] | 1.555 [1.490,1.623] | 1.304 [1.256,1.356] |
| E12 | 2 | 8 | fc / none | 128/3 | 1.175 [1.065,1.296] | 1.177 [1.067,1.298] | 1.003 [0.933,1.080] |
| E12 | 2 | 8 | fc / reuse | 128/3 | 1.081 [1.036,1.155] | 1.080 [1.035,1.153] | 1.035 [0.994,1.087] |
| E12 | 2 | 8 | full / none | 128/3 | 1.234 [1.114,1.373] | 1.238 [1.117,1.378] | 0.996 [0.926,1.068] |
| E12 | 2 | 8 | full / reuse | 128/3 | 1.135 [1.088,1.201] | 1.135 [1.090,1.201] | 1.028 [0.998,1.074] |
| E12 | 2 | 8 | independent / none | 128/3 | 1.115 [1.081,1.150] | 1.117 [1.083,1.151] | 0.934 [0.891,0.990] |
| E12 | 2 | 8 | independent / reuse | 128/3 | 1.026 [0.944,1.111] | 1.025 [0.941,1.109] | 0.964 [0.901,1.037] |
| E12 | 2 | 8 | reuse / none | 128/3 | 1.087 [1.005,1.179] | 1.090 [1.006,1.184] | 0.969 [0.916,1.025] |

### E16 resources
Completed comparison rows: 4; pending inputs: 0.
[Immutable table](../artifacts/REV2_live_analysis_20261010_1255/20261010_170613_478699/E16/report.md) · [Numbers, intervals, n and sources](../artifacts/REV2_live_analysis_20261010_1255/20261010_170613_478699/E16/results.json)

| Arm | Steps | Mean all / steady s | Steady p10–p90 s | Peak allocated / reserved GiB | Mutable export MB | Compact checkpoints MB |
|---|---:|---|---|---|---:|---:|
| interface |200|1.636 / 1.570|1.523–1.642|25.69 / 29.64|201.327|201.329|
| full |200|1.833 / 1.773|1.724–1.845|29.08 / 31.64|1698.760|1698.762|
| whole-r16 |200|2.151 / 2.093|1.988–2.187|25.34 / 29.67|1698.694|9.392|
| whole-r343 |200|1.839 / 1.783|1.658–2.080|25.94 / 29.85|1698.694|201.260|
| Arm / interface | Steps / blocks | Step-time ratio [95% CI] | Difference seconds [95% CI] |
|---|---:|---|---|
| full / interface |190 /19|1.129 [1.127,1.132]|+0.203 [+0.200,+0.207]|
| whole-r16 / interface |190 /19|1.333 [1.319,1.346]|+0.523 [+0.501,+0.544]|
| whole-r343 / interface |190 /19|1.136 [1.101,1.177]|+0.213 [+0.158,+0.279]|

### E9/E12 response data
Completed comparison rows: 3; pending inputs: 0.
[Immutable table](../artifacts/REV2_live_analysis_20261010_1255/20261010_170613_478699/data/report.md) · [Numbers, intervals, n and sources](../artifacts/REV2_live_analysis_20261010_1255/20261010_170613_478699/data/results.json)

| Target | Data | n | Answer tokens | Mean length | Capped | Repeated4gram >50% | Generation GPUh |
|---|---|---:|---:|---:|---:|---:|---:|
|0|new_responses|4000|3530565|882.6|165|2|7.014|
|0|paired_short_responses|4000|1875707|468.9|2846|1|previously recorded|
|0|all_short_responses|16000|7518804|469.9|11517|5|previously recorded|
|1|new_responses|4000|1475280|368.8|106|4|4.751|
|1|paired_short_responses|4000|1074092|268.5|763|4|previously recorded|
|1|all_short_responses|16000|4333373|270.8|3019|14|previously recorded|
|2|new_responses|16000|7846034|490.4|13225|0|8.751|

### Run-list completion

| Level | Successful jobs / planned / final expected | Analysis complete | Ready for review |
|---|---:|---|---|
| P0 | 270 / 270 / 270 | True | True |
| P1 | 102 / 103 / 106 | False | False |
| P2 | 8 / 8 / 8 | True | True |
<!-- REV2 LIVE RAW RESULTS END -->
