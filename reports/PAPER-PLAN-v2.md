# Paper plan v2: measure, repair, reuse (proposed; owner to confirm)

claude-ops, Thu 2026-10-08 ~00:30 ET. Interprets the owner's external brainstorm ("astra") against our evidence and constraints:
heck A40s only (D-41), deadline Mon Oct 12 23:59 AoE (≈ Tue 08:00 ET), about 2.5 days of experiments plus 1.5 days of writing.

## 1. Thesis (conditional on gate G1)

> Fine-tuned derivatives degrade **independent** (standalone) draft models far more than target-conditioned drafters. Zero-data,
> per-derivative distillation repairs them. **A small bank of repairs learned on earlier derivatives covers much of the repair needed by
> unseen derivatives.** One short cached probe selects the right repair, so new derivatives are onboarded with no drafter training.

Working title: *Repair Once, Reuse Often: Population-Scale Drafter Repair for Fine-Tuned LLMs.*

The paper rests on three results (the astra structure, which we adopt):
1. **Population.** How often and how badly each drafter family degrades across 174 public derivatives (EAGLE-3/DFlash: robust except a
   tail, already measured; independent drafters: G1), and the mechanisms behind it.
2. **Repairability and reuse.** Per-child zero-data repair as the reference. How much a donor bank covers on unseen (post-cutoff) derivatives;
   whether the selector finds it; where coverage fails.
3. **Economics.** Onboarding cost (target scoring, training, export) vs. measured serving speed on the same A40 configuration.

Novelty boundary (corrected from the earlier brief): per-target KD, Magpie draft data, adapter subspaces (EigenLoRAx), adapter composition
(LoraHub), cross-model LoRA transfer (Cross-LoRA, CAST), delta distillation (OPD²) and online drafter adaptation (OSD, OmniDraft) all
exist. Our claim is **population-scale evidence of repair reuse across unseen fine-tuned targets, with measured onboarding economics**. We do not
claim that adaptation or transfer is new.

## 2. What we run, and what we cut

| Item | Status | Why |
| --- | --- | --- |
| **G1 census**: Llama-3.2-1B-Instruct → Llama-3.1-8B-Instruct derivatives (same tokenizer; stratified 40 from the atlas: all types, both pools, plus the known EAGLE tail) | **run first** | Without large, common degradation there is no repair paper |
| **M0 per-child KD** (reference): Magpie queries from the child → child greedy responses → rank-8 LoRA on the drafter, answer-only, hard labels (= the child's greedy tokens; our decoding is greedy/greedy), 128 and 512 examples, ≤ 256 answer tokens | **run** | The baseline and the bank-construction procedure |
| Controls: D₀ (stock), D_B (distilled once on the base), D_pool (one LoRA on a balanced donor mixture) | **run** | D_pool is the decisive control: our FollowSpec null showed pooled training may already capture everything general |
| **M1 repair bank + cached-probe selection** (main): 8 pre-cutoff donors → 12–16; shared probe set of 16–32 synthetic sequences × 128–256 tokens; score = greedy top-1 agreement between child and candidate on teacher-forced prefixes; pick the argmax; report the pure selector and an optional 8-prompt finalist check separately | **run** | Highest value; directly tests reuse; cheap after caching |
| **M2 head-only ceiling** (gate for a shared head basis): head-only low-rank KD vs internal LoRA KD on 4 failures | **4-hour test** | If head-only reaches ≥ 50% of LoRA-KD gain → shared head basis with a convex coefficient fit; otherwise drop |
| Triage: signed top-1-agreement change on shared probes vs covariates vs 16 short real requests | **run (cheap, reuses probes)** | Supports the economics result |
| Qwen3-0.6B → Qwen3-8B replication; 1.7B capacity check on 0.6B failures | **Fri if G3 passes** | Generality |
| Weight-space transport, online verification-feedback updates, damage-directed data selection | **cut** (future work; damage-directed only as an ablation if time) | Close prior art, serving engineering, deadline |
| Track T T1 (lineage/reasoning/RL checkpoints × EAGLE-3/DFlash) | **continue, low priority** | Feeds the Population result (does any shift break target-conditioned drafters?); no method work on Track T |

Fixed settings (protocol frozen unless the owner changes them): pinned vLLM 0.31.0, `draft_model`, greedy target and draft, **K = 4**, batch 8, 512
tokens, fresh compile, A00 vs A10 on identical rendered prompts, A40 only. Metrics: per-position conditional acceptance (position 1 = headline),
prefix survival Pr(R ≥ j), accepted/proposed, τ (with bonus), output lengths; teacher-forced matched-prefix agreement for causal analysis;
wall-clock on the same A40 configuration; adaptation GPU-seconds including Magpie, scoring and export. Recovered gain
R_i = (α_method − α_D0) / (α_KD − α_D0), reported only when the denominator is meaningfully positive.

Splits: donors and development children come from the **pre-cutoff** pool (atlas pre-cutoff + bank). Final evaluation is on the **post-cutoff test
pool** (Llama 50), with probes, donors, hyperparameters and thresholds frozen first. Near-duplicates, quantized siblings and same-author series stay
in one split.

## 3. Gates (owner decides at each; times ET)

| Gate | When | Pass criterion | If it fails |
| --- | --- | --- | --- |
| **G1 motivation** | Thu ~12:00 | Independent drafter loses ≥ 10% position-1 acceptance on ≥ 30% of the 40, or ≥ 20% on ≥ 15% (vs EAGLE-3: 17/87 below 0.95) | Paper = population analysis across drafter families (+ T1) and the FollowSpec negative result; no repair method |
| **G2 repairability** | Thu ~22:00 | M0 KD (512 examples) recovers ≥ 50% of the lost acceptance on ≥ 5/8 failures, beats D_B on the child, and the gain is child-specific (D_i on child − D_i on base > 0) | Paper = population + "zero-data KD repairs X%" as a measured baseline |
| **G3 reuse** | Fri ~12:00 | On 4 unseen development children, the best bank candidate reaches ≥ 50% of own-KD gain, beats D_pool by > 1 point, and the selector picks within 1 point of the best | Best candidate fails → bank lacks coverage (report it); selector fails → report the oracle and the probe gap. Main method falls back to M0 + triage |
| **Freeze** | Fri ~20:00 | Probes, donors, selector, thresholds | — |
| Final eval | Sat | Post-cutoff test pool + Qwen3 replication + wall-clock | — |
| Writing | Sun–Mon | Atlas sections already evidenced (EXP-ATL-002/005/007/009/010) | — |

## 4. Build list for codex (heck)

1. **I1** `draft_model` mode in the frozen harness (new flag, defaults unchanged, tests first); stage pinned Llama-3.2-1B-Instruct, Qwen3-0.6B/1.7B;
   G1 census jobs (stratified 40, Llama first).
2. **I3** small-drafter KD: Magpie training split for any derivative (reuse atlas.generate_magpie with forbidden-file dedup against every evaluation
   prompt) → child greedy responses (reuse followspec.generate_responses) → LoRA KD trainer for a 1B HF model (hard-label answer-only; forward-KL
   variant behind a flag) → merged checkpoint export loadable by vLLM `draft_model`. Five decoded samples and masks per new data path.
3. **I4** cached probe scorer: teacher-forced greedy top-1 agreement of child vs each candidate on fixed probe sequences (HF bf16; cache candidate
   argmaxes once); selector; offline agreement vs measured acceptance correlation.
4. **I5** (4-hour cap) head-only KD variant for the M2 ceiling test.

All jobs go through ops/queue.py on live-free A40s. Proposed split: Track I on heck-srv4 + heck-srv2:0–3 + heck-srv5 when free; T1 on heck-srv1 + heck-srv3.
