# REV2: additional ReFit evidence — pilot

D-54, codex-1. Updated 2026-10-10T05:03:36.837620-04:00 Eastern. Analysis for integration by claude-ops; `paper/claude_final` is untouched. New GPU numbers will be added only after completion and independent raw-counter checks. Existing observations below retain their original initialization, budget, protocol and sample size.

All new primary acceptance: frozen 6da2e42, vLLM 0.31.0, A40, greedy K4, identical target-rendered IDs across arms. Long caps are supplementary workload extensions. Training uses FIX-24 initialization. Uncertainty jointly resamples paired training seeds and queries where multiple seeds exist; single-seed estimates use paired queries. Wall-clock measurements separately resample processes and paired prompt batches. Artifacts are immutable, compact checkpoints omit final optimizer state, and every launcher enforces the350GB free-space floor. Code/tag: `run-REV2-train-20261010-0425` /62cecc1.

## E8 — matched-capacity location at16k

**Running:**20 new trainings. R1 and Nemotron, three seeds: dense q+o50,331,648 parameters; interface LoRA r75 and decoder q/v+MLP LoRA r16 both1,228,800. Nemotron interface seeds1–2 complete the dense-interface comparator; R1 interface seeds0–2 and Nemotron seed0 are reused. Live parameter logs match all requested counts. Data, seed-specific batches, optimizer, learning rate and native TTT3 objective are shared within each location contrast. All runs save one final checkpoint; SPEED128/MATH64 for every seed, MATH500 for seed0, through an automatic frozen-evaluation watcher. No new acceptance result yet.

[Plan and jobs](../artifacts/REV2_E8_20261010_0425/plan.json).

## E14 — MATH500 completion

**Queued:** Nemotron reuse/interface/full/independent1B and R1 interface/full seeds1–2, eight cells. New Nemotron and Qwen MATH500 renders match all64 existing MATH64 token-ID sequences under their respective templates. Five decoded prompts inspected for each new render. Initial rendering with the system tokenizer failed before producing any cells; the pinned evaluation environment succeeded in a new directory.

[Plan](../artifacts/REV2_panels_20261010_0430_v2/plan.json), [render audit](../artifacts/REV2_panels_20261010_0430_v2/render-audit.json).

## E12 — Qwen-family16k repair

**Data queued:**16,000 existing approved Alpaca queries, eight disjoint2k shards, Qwen R1's own greedy512-token responses. Family EAGLE drafter pin is the existing P3-D48 Qwen checkpoint. Interface/full training and evaluation follow the five-sample data audits. SPEED128/MATH500 and b1/b8 timing remain to run. The existing256-example result is positive but is not a16k result: full Δτ+.234[.199,.266] on SPEED n128 and+.207[.177,.237] on MATH n64, one seed ([source](P3-D48-seeds-generality-20261008.md)).

[Data plan](../artifacts/REV2_data_20261010_0430/plan.json).

## E9 — long-response repair

**Data running/queued:** first4k queries from each target's existing16k Alpaca collection, generated afresh with a2,048-response-token cap, four1k shards per target. Explicit4,096 training context budget; no truncation. Interface/full will train on long4k alone and short16k+long4k. The mixture preserves the two responses to the same4k queries as explicitly labeled `short512`/`long2048` records with identical prompt IDs/tokens and distinct sample IDs; ordinary duplicate-query rejection remains the default. No newly trained long-response result yet.

The existing short-response repair closes39.2%[32.0,45.7] of R1's oracle gap at the8,192 evaluation ceiling (full, n32), compared with53.5%[50.2,57.0] at512. This is the measured motivation for E9, not its outcome. [A4 table](REV2-evidence-20261010/long-recovery.md).

## E10 — reasoning wall-clock

**Queued:**27 long-MATH32 timing processes (8,192 cap, b1) plus66 MATH500-subset timing processes (512 cap, b1 n32/b8 n128). Three independent processes×three warm passes; first panel and startup retained separately. R1 none/reuse/interface/full/dedicated; Nemotron none/reuse/interface/full; short panels also independent1B. All use the selected official16k seed0 repairs and target-rendered prompts. New latency results pending.

[Long plan](../artifacts/REV2_E10a_20261010_0430/plan.json), [short plan](../artifacts/REV2_E10b_20261010_0430/plan.json). Prerequisite data and completed-model acceptance are prioritized ahead of the long timing jobs without restarting the canonical queue.

## E11 — batches16/32

**Queued:**66 timing processes. Timing extension built and tested; Same SPEED128 panels, methods and three-process protocol. Defaults remain b8/cap512.

## E17 — whole-drafter LoRA

Scope built and tested, including head gradients and merged-checkpoint equivalence. Every drafter linear is adapted: fc, q/k/v/o, gate/up/down, LM head; target, embeddings and norms remain fixed. Rank16 has2,347,008 parameters; rank343 has50,313,984 (0.035% below the dense interface's50,331,648). R1 seeds0–2 and Nemotron seed0, same16k data/native objective. **Queued**; no result yet. This is a compatible whole-LoRA baseline, not a claim to reproduce an architecture-changing method.

## E13 — scratch64k

**Queued:** one epoch from scratch on the existing64k data, official drafter architecture/vocabulary with target embeddings fixed. Preserve the Alpaca+Dolly source-mixture label. GPU-hours and final SPEED/MATH64/MATH500 will be reported; no new result yet.

## E16 — training resource profile

Synchronized200-step profile implemented behind an opt-in flag. Measures target capture/data, drafter forward/backward and optimizer time, excluding exports. Peak allocated/reserved memory and serialized checkpoint bytes retained. Interface/full/whole-LoRA r16/r343 use the same first200 batches and original4477-step scheduler horizon. **Queued**.

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

## A5 — exact native objective

Online capture selects target logits at draft-vocabulary token IDs **before** the native loss. The native fused `kl_div` normalizes both target and draft logits on that32k support. For selected support Vd, target q(v)=exp(z_target(v))/Σu∈Vd exp(z_target(u)); loss is KL(q||p_draft), over answer positions. It is not an unnormalized restriction of a full-vocabulary probability vector.

The installed native EAGLE implementation rolls forward predicted hidden states but feeds **shifted original ground-truth token IDs** at successive TTT steps (`core.py` lines329–342), not its argmax predictions. TTT3 and unit step-loss weights are unchanged in every repair arm. This distinction matters when describing training-time rollout or comparing with online policy adaptation. Sources: `followspec/online_capture.py:_forward`, native `speculators/models/eagle3/core.py`, native `speculators/losses/fused.py`. No trainer recipe was changed by this audit.

## A6 — measured versus estimated cost

Measured official16k R1: data8.916GPUh plus2.206 interface/2.211 full =11.122/11.127A40GPUh. Nemotron data8.588 plus1.240/1.398 =9.828/9.986. These count generation once per alternative; target capture is inside measured training. [Measured sources](P3-primary-official-20261010.md).

The dedicated reference is a **recipe-scale estimate**, not the oracle's training bill. Public recipe532k–646k examples;40 epochs is a public script default, actual oracle epochs unknown. At10–40 assumed epochs, generation+training projects1,348–19,232GPUh: roughly121–1,728× the measured11.127GPUh repair. A one-epoch sensitivity gives397–825GPUh (36–74×), so a two-orders claim depends on the stated multi-epoch assumption. Generation is explicitly included as291–353GPUh, extrapolated from the measured capped-response generation path; this is not a measurement of uncapped dedicated reasoning data. [Full decomposition, source pins and assumptions](P6-dedicated-cost-estimate-20261008.md).

## A7 — Nemotron templates and mode

Main repair data and held-out evaluation apply the released target template with a user message, no `detailed thinking on/off` system instruction, and `enable_thinking=False` as a template argument. The actual rendered template has an **empty system turn**; it must be labeled default/empty-system, not conflated with an explicit “thinking off” intervention. E14/E10 preserve this template exactly. The explicit on/off study is separate and changes rendered prompts while preserving raw questions: EAGLE Δp1−.0296[−.0437,−.0157], Δτ−.1184[−.1645,−.0729], n128. [Toggle evidence](P2-nemotron-toggle-20261008.md).

## A8 — family reference versus main-table drafter

The focused census uses the **production** family drafter: R1 parent p1 .56634, child .41082, retention .72539; Nemotron .62619/.43587/.69606 on SPEED128. The main table uses the **official** family drafter selected by D51. Dividing an official child p1 by a production retention is not a valid reconstruction of parent p1. These values are independently reproduced in the A2 CSV. “Parent” here is the family drafter's reference target, not always the derivative's immediate ancestor.

## A9 — shareable interface storage

Official interface50,331,648 parameters is100.663MB in bf16 (96MiB). Full mutable drafter424,689,664 parameters is849.379MB bf16 (810.031MiB). Existing interface export metadata lists only `fc.weight` as mutable. [Fresh tensor audit](../artifacts/REV2_A9_20261010_0452/proof.json) verifies all14 frozen release tensors for both targets, exactly after the logged fp16→fp32 load conversion; the decoder/head values therefore remain identical at the common serving dtype. These are tensor-size accounting in bf16, distinct from current fp32 training/export file sizes and complete engine resident memory. E16 will supply actual serialized bytes and memory/time measurements.

## A10 — self-elicited versus Alpaca4k

Existing production, one-epoch, one-seed controls: on SPEED128, generic minus self Δτ is+.004[−.012,.020] for interface and+.009[−.012,.031] for full; Δp1+.001[−.004,.007]/+.002[−.006,.009]. On MATH64, Δτ+.028[.007,.049]/+.045[.007,.083]. These are source ablations with different sequence lengths/token totals/step counts, not token-matched equivalence tests. [Raw-verified source-ablation table](P3-D50-consolidated-20261009.md). Self-elicitation avoids reliance on the external instruction dataset; both variants remain training-set-free rather than data-free.
