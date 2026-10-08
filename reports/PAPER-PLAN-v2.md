# Exploration plan v2: measure, repair, reuse (D-43, exploratory)

claude-ops, Thu 2026-10-08 ~00:45 ET. Interprets the owner's external brainstorm ("astra") against our evidence and constraints:
heck A40s only (D-41), ARR deadline Mon Oct 12 23:59 AoE.

**This is an exploratory phase.** The goal is to find out quickly which direction has real signal, not to certify a result. Use small n, fast
pilots and short runs. Report what we see, including null and negative results, and let the owner choose the direction at each checkpoint.
Nothing here is a preregistered test, a gate threshold or a paper claim. Numbers below are rough signals for discussion, not pass/fail rules.

## 1. Working hypothesis (to probe, not to prove)

> Fine-tuned derivatives may degrade **independent** (standalone) draft models much more than target-conditioned drafters. Zero-data,
> per-derivative distillation may repair them, and a small **bank of repairs** from earlier derivatives might cover many new derivatives,
> chosen by a cheap cached probe.

If the signal is there, a paper could rest on three parts: **population** (how drafter families degrade across the 174 derivatives), **repair and
reuse** (per-child repair vs reuse from a bank), and **economics** (onboarding cost vs speed). If not, the exploration tells us what to write instead.

Novelty context: per-target KD, Magpie draft data, adapter subspaces (EigenLoRAx), adapter composition (LoraHub), cross-model LoRA transfer (Cross-LoRA,
CAST), delta distillation (OPD²) and online drafter adaptation (OSD, OmniDraft) all exist. Any eventual claim would be about population-scale
reuse and economics, not adaptation itself.

## 2. Exploration questions, in order

| # | Question | Quick probe | What would be interesting |
| --- | --- | --- | --- |
| Q1 | Do independent drafters degrade on derivatives, and how much more than EAGLE-3/DFlash? | codex-1's I1 census (D-42: Llama-3.2-1B → Llama-3.1-8B derivatives, stratified 60), position-1 acceptance and τ vs the atlas | Large, common losses (e.g. 10%+ per-token on a sizable share) with a visible contrast to target-conditioned drafters |
| Q2 | Does zero-data per-child repair work? | Magpie from the child → child greedy responses → small LoRA KD of the 1B drafter (128/512 examples) on a handful of degraded children; controls D₀ (stock), D_B (base-distilled), D_pool (pooled donors) | Most of the lost acceptance comes back, and more on the child than on the base (child-specific) |
| Q3 | Do repairs transfer between derivatives? | Small bank (about 8 donors): evaluate each donor's repair on a few *other* degraded children, plus a cached greedy-agreement probe to see if it ranks donors sensibly | Some donor recovers much of a new child's loss and beats D_pool; the probe roughly finds it |
| Q4 | Is the output head enough? | Head-only KD vs LoRA KD on about 4 children (short, capped) | Head-only gets a good fraction of the gain, which would make a shared head basis worth a look |
| Q5 | Does anything break target-conditioned drafters? | T1 (lineage, reasoning, RL checkpoints × EAGLE-3/DFlash), continues in parallel | Any shift class with large losses for both drafter families |

Out of scope for now (revisit only if the owner asks): weight-space transfer, online verification-feedback updates, damage-directed data
selection, Qwen3 replication, multi-family generality. Possible later steps once a direction is chosen: Qwen3-0.6B replication, 1.7B capacity check,
wall-clock economics.

## 3. Settings (keep simple and comparable)

Pinned vLLM 0.31.0 `draft_model` mode (D-42); greedy target and draft; K = 4; batch 8; 512 tokens; fresh compile; A00 vs A10 on identical
rendered prompts; A40 only. Look at position-1 conditional acceptance, τ and output length together (τ alone is length-confounded).

Light hygiene that keeps later options open:
- Draw donors and pilot children from the **pre-cutoff** pool. **Leave the post-cutoff test pool untouched** so a later confirmation stays possible.
- Never evaluate on training prompts: Magpie data is deduplicated against evaluation prompts.
- Five decoded samples and masks per new data path.
- Never overwrite artifacts.
- Record results as exploratory ledger entries (status `pilot`), with n and spread.

## 4. Checkpoints with the owner (times are targets, ET)

| When | What we bring | Owner chooses |
| --- | --- | --- |
| Thu ~12:00 | Q1 census picture (+ T1 so far) | Continue Track I repair, switch emphasis, or write a population/analysis paper |
| Thu ~22:00 | Q2 pilot (+ Q4 if quick) | Whether repair is worth building on |
| Fri ~12:00 | Q3 transfer picture | Main direction for the paper and what (if anything) to run as a confirmation on the untouched test pool over the weekend |

## 5. Build list for codex (heck), lightweight

1. **I1**: done by codex-1 (D-42: opt-in `draft_model` mode, stratified census of 60 running). Summarize it for Q1.
2. **I3** (Q2): a small, working drafter-KD path is enough. Steps: Magpie training split for a derivative (dedup) → child greedy responses →
   LoRA KD of the 1B drafter (answer-only hard labels) → merged checkpoint loadable by `draft_model`. Add D_B and D_pool controls.
3. **I4** (Q3): cross-evaluate donor repairs on other children. Teacher-forced greedy top-1 agreement probe (16–32 synthetic sequences, cached
   per candidate) as a cheap ranking signal.
4. **I5** (Q4, capped at a few hours): head-only KD variant.

Placement: Track I on heck-srv4 + heck-srv2:0–3 (+ heck-srv5 when live-free); T1 on heck-srv1 + heck-srv3.
