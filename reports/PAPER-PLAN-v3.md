# Paper plan v3: the official pivot (D-45)

claude-ops, Thu 2026-10-08 ~02:45 ET, on the owner's instruction ("make this the official pivot"). Supersedes PAPER-PLAN-v2 (D-43) and the
FollowSpec framing. Heck A40s only (D-41). ARR deadline Mon Oct 12 23:59 AoE (≈ Tue 08:00 ET).

## 1. The paper

**Working title:** *Speculators Break Under Distillation, Not RL: Diagnosing and Cheaply Repairing Family Drafters for Post-Trained LLMs.*

**Problem.** Target-conditioned drafters (EAGLE-3, DFlash: the production standard) are trained once per official model, yet most models people
deploy are post-trained derivatives of that model's family: fine-tunes, RL policies, reasoning distills, alternative post-training of the same
base. Practitioners reuse the family drafter or train a new one (costly, and done only for popular models).

**Findings so far (pilot, n = 128 prompts per pair; see §4):**
1. Family drafters transfer to most public derivatives of the official model (census of 174: median per-token retention ≈ 0.99–1.00).
2. They fail on **distilled / off-lineage post-training**: R1-Distill-Llama-8B −27% (EAGLE-3) / −26% (DFlash) per-token, τ ×0.77 / ×0.61; Nemotron-Nano-8B
   −30% / −29%; R1-0528-Qwen3-8B −14% / −19%; Tülu-3 DPO/RLVR −19% / −17%.
3. **On-policy RL** from the drafter's target, or even from the pretrained base, keeps drafters (Qwen3 GRPO 50–250 steps ≈ 1.0; GT-DAPO from
   Qwen3-8B-Base 1.03 / 0.90). This is consistent with RL's Razor: RL stays KL-close; SFT/distillation can move far.
4. The loss is not just reasoning *text*: the same Qwen3 weights in thinking mode keep EAGLE-3 (1.04). Teacher-forced on identical derivative text,
   the drafter agrees less with the derivative than with Instruct (−0.06 R1, −0.10 Nemotron; n = 8, a hint of feature-level shift).
5. **A dedicated drafter recovers it**: R1-Distill + its own EAGLE-3 gives τ 2.85 vs 1.73 with the reused Instruct drafter (×1.65), but costs full
   drafter training and exists only for few models (none found for Nemotron-Nano, R1-0528-Qwen3, DFlash on any distill).

**Method (to build and test).** Cheap, data-free repair of the family drafter for a flagged derivative:
- **Self-elicited data:** the derivative's own responses to self-generated (Magpie) or public generic prompts; no original training data.
- **Interface repair (main hypothesis):** both EAGLE-3 and DFlash read the target through a small learned projection of concatenated target hidden states (`fc` in
  speculators `eagle3/core.py` and `dflash/core.py`; EAGLE-3 Llama: 12288→4096). If the derivative's shift lives mostly in those features (finding 4), re-fitting only the
  interface (or the interface + LoRA) recovers most of the dedicated-drafter gap at a fraction of the cost.
- **Baselines and controls:** reused family drafter; dedicated drafter (oracle, R1-Distill-Llama only); full-drafter self-distillation at matched budget;
  generic-data vs self-elicited data; init from the family drafter vs from scratch; our M3 bank-trained drafter (known null).
- **Triage:** a cheap probe (teacher-forced agreement and/or 16 short real requests on self-elicited prompts) predicts which derivatives need repair,
  validated on the census plus the distillation set.

**Contributions (target):** (1) population study of which post-training breaks target-conditioned drafters, with the RL vs distillation contrast
and a mechanism; (2) a cheap, data-free repair that recovers most of the dedicated-drafter gain; (3) cost/benefit (GPU-hours vs speedup) and triage.

## 2. Workstreams (rows P1–P6)

| Row | What | Priority |
| --- | --- | --- |
| P1 | **Population expansion.** (a) Label all 174 atlas derivatives + T1 by post-training type from model cards (distillation from a foreign teacher, SFT on own/synthetic data, DPO, on-policy RL, merge, quantization, abliteration, adapter), and report per-token retention by type for both drafters. (b) Add 6–10 more distilled/reasoning derivatives per base family (architecture-compatible, licensed), e.g. Skywork-o1-Open-Llama-3.1-8B, DeepHermes-3-Llama-3-8B-Preview, Magpie-Align Llama-3.1-8B SFT (non-reasoning distillation from a larger teacher), more Qwen3-8B distills; plus 2–3 more on-policy RL checkpoints. Same harness, 128 SPEED prompts + a reasoning set (MATH-500 subset) | P0 |
| P2 | **Mechanism.** Teacher-forced agreement at larger n (64 traces) for R1/Nemotron/R1-0528/Tülu; separate text vs model shift; tap-level displacement (A6 code) per layer for distilled vs RL models; thinking-mode control for DFlash | P1 |
| P3 | **Repair pilot (EAGLE-3).** Targets: R1-Distill-Llama-8B (has oracle), Nemotron-Nano-8B, R1-0528-Qwen3-8B. Variants: interface-only (fc), interface + LoRA, full drafter; data: self-elicited vs generic prompts with derivative responses; budgets ~50 / 200 / 800 steps; init family vs scratch (one budget). Metrics: p1, τ, per-position, lengths, on held-out prompts (SPEED-128 + MATH-500 subset, deduplicated against training) | **P0, start now** |
| P4 | **Repair for DFlash** (if the B10 training path is ready): same variants on the two Llama targets | P1 |
| P5 | **Triage probe** validated on census + P1 (AUROC for retention < 0.9; cost vs a direct short measurement) | P1 |
| P6 | **Economics.** A40 wall-clock speedup (same config) for reused vs repaired vs dedicated; repair GPU-hours vs dedicated-drafter training cost (estimate from EAGLE-3 recipe if the card lacks it) | P1, Sat |

Track I (independent drafters) is **concluded as a secondary result**. I1 census (finish Qwen): independent drafters degrade little and share
failures. I3–I5: per-child repair works where a loss exists, but cross-derivative reuse fails. These go into the paper as contrast and negative results; no new
Track I work. FollowSpec (M3/M4) is archived as a negative result (bank training gives uniform gains, nothing derivative-specific).

## 3. Rules for this phase

- Speed with credibility. Pilot quickly, then re-run the result that matters with more prompts and paired CIs. Report n, intervals and nulls.
- Frozen evaluation harness (6da2e42 / pinned vLLM 0.31.0) for every acceptance number; greedy; same rendered prompts for every arm of a comparison; A40 only.
- Data hygiene: repair training data deduplicated against every evaluation prompt (SPEED, MATH-500 subset, atlas sets). Five decoded samples and masks per new
  data path. Never overwrite artifacts. Licenses checked before download (AGENTS rule 9).
- One canonical queue; check queues and stage dirs before every launch. Disk: about 0.9 TB free, so cap new downloads at about 250 GB and delete nothing.
- Ledger entries (`pilot`) for every number; owner reviews framing.

## 4. Evidence index

- T1 phase 1: `reports/T1-phase1-20261008.md`, `artifacts/T1_cells_20261007_2350/report/`; operator re-derivation in `notes/T1.md`.
- Phase 1b (C1–C3): `reports/T1-phase1b-20261008.md`, `ledger/EXP-ATL-015.md`; operator check of C2 in `notes/T4.md`.
- Census: `ledger/EXP-ATL-005.md`, `artifacts/ATLAS_lencontrolled_20261007/`, covariates `ledger/EXP-ATL-007.md`.
- Independent drafters: `notes/I1.md`, `reports/I3-pilot-complete-20261008.md`.
- FollowSpec: `ledger/EXP-ATL-006/009/010.md`.

## 5. Timeline (targets, ET)

| When | Milestone |
| --- | --- |
| Thu 03:00–12:00 | P3 pilot running (interface vs full, two budgets, R1-Distill + Nemotron); P1(a) labels; P1(b) downloads |
| Thu 12:00 | Owner checkpoint: does a cheap repair recover a large share of the oracle gap? |
| Thu pm–Fri am | P1(b) evaluations, P3 budget curve + data ablation + Qwen3 target, P2, P4 if feasible |
| Fri 18:00 | Owner checkpoint: freeze the method and the final experiment list |
| Sat | Final runs with more prompts; P5 triage; P6 wall-clock; figures/ledger |
| Sun–Mon | Writing |

## 6. Decisions after external review (D-46, claude-ops, Thu ~04:00 ET)

External review (astra) was read critically: its experimental-design advice is adopted, its preference for scoping down to an analysis paper is
not. **This remains a method paper with a study as motivation.** The dedicated drafter proves the gap is learnable (×1.65 τ); we build the story
around the repair that wins and its mechanism. Contemporary work (EDA, H-Spec, Draft-OPD, EAGLE 3.1, EvoSpec, the vLLM DFlash-LoRA RFC) is cited
as concurrent and positioned against, not avoided.

**Story template (final wording after the Thu 12:00 checkpoint):**
1. Family drafters transfer to most derivatives (174-model census, paired A00/A10). Acceptance-length comparisons are distorted by output length.
2. A predictable class breaks them: reasoning distillation and off-lineage post-training (associated, with lineage and training history labelled
   separately; on-policy RL largely preserves compatibility, consistent with RL's Razor and successors).
3. Mechanism via a fixed-prefix 2×2 crossover (feature source × verifier policy) and per-layer feature swaps.
4. Method: training-set-free repair localized to the component the mechanism points at (`fc` interface if it wins; otherwise the smallest
   winning component), recovering X% of the dedicated-drafter gap at Y GPU-hours, with real speedups.
5. Triage: a 16–32-prompt probe decides when to repair.

**P3 matrix (replaces the earlier variant list).** R1-Distill-Llama-8B first (oracle exists), EAGLE-3 K4, family-drafter init, native multi-step
(TTT) objective unchanged, held-out SPEED-128 + MATH-500 subset:
| Variant | Trainable | Note |
| --- | --- | --- |
| Calibration | none (per-layer mean/RMS affine on taps, fit on paired forwards) | training-free baseline |
| fc-only | `fc` | primary hypothesis |
| fc-LoRA | low-rank residual on `fc` (r 8/32) | cheaper interface variant |
| decoder-LoRA | LoRA on the drafter layer (q/v + MLP), `fc` frozen | EDA/RFC-style proxy; label honestly |
| fc + decoder-LoRA | both | capacity control |
| full warm-start | all drafter params | matched steps, data and wall-clock |
| scratch (once) | all, random init | budget-matched cold-start lower bound |
| head-only (optional) | `lm_head` | diagnostic |
One run per variant with checkpoints at 50 / 150 / 300 steps (extend only the winner). Data: self-elicited first; generic-prompt and mixed data as
an ablation on the top two variants. **Three seeds** on the winning configuration. Primary outputs: absolute Δp1, τ, per-depth conditional acceptance,
**recovery = (τ_repair − 1.73) / (2.85 − 1.73)** on R1-Distill, GPU-hours including data generation. Then the top two variants on Nemotron-Nano and
R1-0528-Qwen3, plus one on-policy RL derivative as a negative control (repair should be unnecessary there).

**P2 mechanism (now P0, cheap).** Fixed-prefix 2×2 crossover on parent-, derivative- and public-generated texts: first-draft top-1 agreement
with {parent, derivative} verifier × {parent, derivative} taps, giving feature-source effect, verifier-policy effect and interaction. Plus
per-layer tap swaps, parent/derivative top-1 disagreement and margin, and top-1 OOV bound. Targets: R1-Distill-Llama, Nemotron-Nano, R1-0528-Qwen3,
Tülu-3 DPO, and one GRPO control. Nemotron reasoning on/off toggle cells (same weights).

**P1 taxonomy.** Two labels per checkpoint: lineage (direct child of the drafter's target / sibling from the pretrained base / composite) and
training history (SFT, teacher distillation, on-policy RL, offline preference, CPT, merge, quantization, combinations), with card evidence. Target
about 24 typed checkpoints, prioritizing direct-child reasoning models and same-start SFT vs RL pairs over raw count. Class results reported as
associations with checkpoint-level bootstrap (hierarchical by family/lineage); census provenance and filter counts documented.

**Reporting rules added.** Absolute Δp1 is the primary compatibility metric (retention secondary). Wall-clock vs the same derivative without
speculation (batch 8, plus a small batch-1 panel). "Training-set-free / self-elicited", never "data-free". Repaired drafters are evaluated only
on held-out prompts, never on training prompts.
