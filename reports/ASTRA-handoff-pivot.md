# Research handoff: family drafters break under distillation, not RL

A self-contained brief for an external research assistant. Prepared 2026-10-08 (~03:00 ET) for the owner of a NAACL 2027 submission
(ARR deadline **Mon Oct 12, 2026, 23:59 AoE**). All numbers below are our own pilot measurements unless cited.

---

## 0. What we need from you

We have just pivoted to a new paper direction (below) and need four things, in this order of priority:

1. **Literature review and novelty map** (most important). Find everything close to (a) speculative-decoding drafters under target fine-tuning,
   distillation or RL; (b) drafters for reasoning models; (c) cheap or partial drafter adaptation (interface/projection-only, LoRA, head-only,
   data-free); (d) on-policy RL vs SFT/distillation distribution shift (RL's Razor and successors); (e) drafter reuse across a model family.
   For each close paper: what it shows, its setup (drafter type, targets, data, cost), and exactly how our claims differ. Tell us plainly which of
   our claims are already known.
2. **Method design.** Assess our proposed method (§4) and propose better or complementary ways to recover most of the dedicated-drafter gain
   cheaply and without the derivative's training data. Rank them by expected impact × feasibility in about 2 days on our compute (§6).
3. **Experiment design for a robust paper.** What NAACL reviewers will demand: baselines, number of derivatives, ablations, metrics,
   statistics, wall-clock, and the strongest reviewer objections with how to pre-empt each.
4. **Framing.** Title and abstract options, and the 3 contributions in their strongest defensible form.

Please separate established facts (with citations) from your own priors and guesses.

---

## 1. Background and terminology

- **Speculative decoding**: a cheap drafter proposes K tokens; the target model verifies them in one forward pass (lossless). Speed depends on
  **τ**, the mean tokens emitted per target forward (accepted drafts + 1 bonus token). We also report **position-1 conditional acceptance (p1)**,
  the probability the first draft token is accepted. It is robust to output-length confounds, which strongly affect τ.
- **Target-conditioned drafters** read the target's hidden states (concatenated from three layers through a learned projection `fc`) and are trained
  once for one specific target model:
  - **EAGLE-3**: one decoder layer, autoregressive drafting, pruned 32k draft vocabulary for Llama.
  - **DFlash** (z-lab/NVIDIA, 2026): a block-diffusion drafter that proposes a block of K tokens in parallel.
  
  These are the production standard (vLLM, SGLang, TensorRT-LLM).
- **Family drafter**: the drafter released for the official model (e.g. `RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3`,
  `z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat`, `RedHatAI/Qwen3-8B-speculator.eagle3`, `z-lab/Qwen3-8B-DFlash-b16`).
- **Derivative**: any model post-trained from the same family, such as a fine-tune or adapter of the official model, an RL policy, a reasoning distill, a
  different post-training of the same pretrained base, a merge, or a quantization. Dedicated drafters exist for very few derivatives, so practitioners
  reuse the family drafter or skip speculation.
- **Independent drafters** (small standalone LMs, e.g. Llama-3.2-1B) read only tokens; we also measured them as a contrast.

## 2. Setup (fixed protocol)

Pinned vLLM 0.31.0; greedy target and draft; batch 8; 512 new tokens; fresh compile per cell. EAGLE-3 K = 4; DFlash at native K (10 for Llama,
16 for Qwen3). Each pair compares **A00** (official model + family drafter) with **A10** (derivative + the same drafter) on identical rendered
prompt token IDs (each model's own chat template). Pilot panels use 128 prompts (SPEED-derived general set) or 64 (each derivative's own
self-generated domain prompts). Intervals are paired prompt bootstraps conditional on one run. All A40 GPUs. Bases: Llama-3.1-8B-Instruct and Qwen3-8B.

## 3. Evidence so far

### 3.1 Census: family drafters mostly transfer (174 public derivatives of the official models)

87 Llama-3.1-8B-Instruct and 87 Qwen3-8B derivatives, filtered for loadability and non-degenerate outputs, typed: LoRA 31, full fine-tune 34,
abliterated 36, RL/DPO 27, quantized 28, merges 4, other 14. Median p1 retention (A10/A00):

| Drafter | Llama | Qwen3 |
| --- | --- | --- |
| EAGLE-3 | 0.999 (17/87 below 0.95) | 0.997 (12/87) |
| DFlash | 0.988 (22/87) | 0.989 (19/87) |

Quantized derivatives never degrade. The tail consists of:
- **language-localization tunes**: EAGLE-3's pruned vocabulary misses 30–67% of their next-token mass; out-of-vocabulary mass predicts EAGLE-3 per-token loss, ρ −0.36;
- a few DPO tests and odd LoRAs.

**Methodological note:** τ retention is badly confounded by output length and repetition. Short answers cap τ, and a looping derivative showed τ retention 2.14.
Several "worst" τ cases are length artifacts.

### 3.2 What breaks family drafters: post-training type (16 public checkpoints, n = 128 prompts each)

p1 retention, EAGLE-3 / DFlash [95% CI], plus child‖base KL on the derivative's own traces (nats; n = 8 traces):

| Derivative | Post-training | EAGLE-3 | DFlash | τ retention E / D | KL |
| --- | --- | --- | --- | --- | --- |
| DeepSeek-R1-Distill-Llama-8B | reasoning distillation onto Llama-3.1-8B base | 0.725 [.69,.77] | 0.735 [.71,.77] | 0.77 / 0.61 | 0.77 |
| Llama-3.1-Nemotron-Nano-8B-v1 | reasoning post-training from Instruct | 0.696 [.67,.72] | 0.708 [.69,.73] | 0.73 / 0.58 | 0.94 |
| DeepSeek-R1-0528-Qwen3-8B | reasoning distillation onto Qwen3-8B base | 0.858 [.83,.89] | 0.810 [.79,.84] | 0.84 / 0.72 | 1.03 |
| Qwen3-Swallow-8B-RL | Japanese CPT → SFT → RL | 0.836 | 0.711 | 0.86 / 0.57 | 1.07 |
| Tülu-3-8B SFT / DPO / RLVR | alternative post-training of Llama-3.1-8B base | 0.915 / 0.810 / 0.801 | 0.937 / 0.832 / 0.837 | — | 0.44 / 0.38 / 0.37 (shared-vocab conditional) |
| Hermes-3-Llama-3.1-8B | SFT on synthetic data from base | 0.981 | 0.921 | 0.99 / 0.88 | 0.56 |
| Qwen3-8B GRPO, 50 / 150 steps | on-policy RL from Qwen3-8B | 0.996 / 1.002 | 0.986 / 0.979 | ≈1.0 | 0.003 / 0.015 |
| Qwen3-8B classic GRPO 250 steps | on-policy RL | 1.109 | 1.048 | — | 0.18 |
| Open-R1-GRPO (Llama-3.1-8B-Instruct) | on-policy RL | 0.967 | 1.007 | — | 0.07 |
| GT-DAPO from Qwen3-8B-Base | on-policy RL from the pretrained base | 1.027 | 0.903 | 1.05 / 0.86 | 0.44 |
| Llama-3.1-8B (pretrained, Instruct template) | none | 1.216 | 1.158 | — | 0.25 |

Excluded from conclusions: a long Llama GRPO run whose checkpoints are collapsed into repetitive output (127/128 and 105/128 repetitive outputs), and
two repositories that turned out to be a different architecture.

Pattern: **distillation and off-lineage post-training cost 14–30% per token for both drafter families; on-policy RL is nearly free, even from the
pretrained base.** This is consistent with RL's Razor (Shenfeld et al., ICLR 2026: on-policy RL stays KL-close to the base, SFT can move arbitrarily
far). Counterexamples to a pure-KL story: Tülu has low conditional KL but notable loss; GT-DAPO has KL 0.44 but no EAGLE-3 loss.

### 3.3 Mechanism hints

- **Reasoning text alone is not the cause for EAGLE-3.** The same Qwen3-8B weights in thinking vs non-thinking mode give p1 retention 1.038 (EAGLE-3)
  and 0.923 (DFlash; τ ×0.69), n = 128. DFlash is more sensitive to the output domain.
- **Teacher-forced on identical derivative-generated text** (n = 8 traces), the drafter agrees less with the derivative than with the Instruct model:
  −0.058 [−0.080, −0.037] (R1-Distill), −0.097 [−0.130, −0.057] (Nemotron, which also shows a text-domain drop). This hints that a share of the loss is a
  shift in the hidden features the drafter reads, not only unfamiliar text.

### 3.4 A dedicated drafter recovers it, at full training cost

R1-Distill-Llama-8B, EAGLE-3 K4, 128 prompts:

| Drafter | p1 | τ |
| --- | --- | --- |
| Instruct model + Instruct drafter (reference) | 0.566 | 2.26 |
| R1-Distill + Instruct drafter (reused) | 0.411 | 1.73 |
| R1-Distill + its dedicated EAGLE-3 (`yuhuili/EAGLE3-DeepSeek-R1-Distill-LLaMA-8B`) | 0.705 | **2.85** |

That is **×1.65 τ** (Δτ +1.12 [+1.05, +1.18]). The model card does not state its training data or cost. We found no dedicated EAGLE-3 or DFlash drafter for
Nemotron-Nano-8B or R1-0528-Qwen3-8B, and no DFlash drafter for any R1 distill.

### 3.5 Negative and contrast results we will also report

- **FollowSpec (our original method):** training one EAGLE-3 drafter on a bank of 30 LoRA derivatives + 30 adapter mixtures with a derivative-delta loss
  gives a uniform +0.14 τ to every target, including the official model, but no derivative-specific benefit over matched controls. λ = 0 (no delta loss)
  performs the same. It does not repair the degraded tail.
- **Independent drafter (Llama-3.2-1B, 30 Llama derivatives):** median p1 retention 0.973. Failures are shared with the target-conditioned
  drafters, not unique. Per-derivative LoRA distillation on 128 self-generated examples improves τ by +0.36 to +0.63 on 3 of 5 degraded
  derivatives. **Reusing one derivative's repair on another mostly fails** (22 cross pairs near null, one large regression), and head-only repair helps
  2 of 4.

## 4. Proposed paper (our current plan, for you to critique)

**Working title:** *Speculators Break Under Distillation, Not RL: Diagnosing and Cheaply Repairing Family Drafters for Post-Trained LLMs.*

Three contributions:
1. **Study:** which post-training breaks target-conditioned drafters, across a population (census + typed post-training set expanded to roughly 20–30
   distilled/RL/SFT derivatives), with the RL vs distillation contrast, a mechanism analysis (text vs feature shift; per-layer displacement; KL) and
   the metric pitfall.
2. **Method:** cheap, data-free repair of the family drafter for a flagged derivative.
   - **Data:** the derivative's own responses to self-generated (Magpie) or public generic prompts.
   - **Repair:** re-fit only the **target-feature interface** (`fc`, ~50M parameters) or `fc` + LoRA, initialized from the family drafter, for 50–800 steps.
   - **Comparisons:** full-drafter fine-tuning at matched budget, generic vs self-elicited data, and the dedicated-drafter oracle. The question is what share of the oracle's
     ×1.65 it recovers, and at what GPU-hours.
3. **Triage + economics:** a cheap probe predicts which derivatives need repair (validated on the census), plus measured wall-clock speedups and
   repair cost vs dedicated training.

Infrastructure we already have:
- EAGLE-3 online training with target hidden-state capture (single A40, memory-saving flags);
- a DFlash training path (validated on small overfit tests);
- Magpie self-elicitation;
- the frozen evaluation harness;
- teacher-forced agreement and KL tools;
- census data for 174 derivatives.

## 5. Literature we already know (please extend and correct)

- **Drafter adaptation to targets:**
  - EDA (arXiv 2603.09527): shared/private experts; 3 Qwen2.5 domain fine-tunes; standalone drafters collapse, τ 4.37 → 1.17.
  - OmniDraft (2507.02659); FlexSpec (2601.00644); EvoSpec (2605.27390); OSD (2310.07177); DistillSpec.
  - *Training Domain Draft Models* (2503.07807): offline > online, and Magpie data reaches 80–93% of real-query performance.
  - vLLM RFC #52038: LoRA on DFlash drafters for multi-LoRA serving.
  - A PEFT block-diffusion negative result (2607.12422).
- **Reasoning models:**
  - Practitioner reports that chat-trained EAGLE-3 drafters lose acceptance on thinking traces and that on-policy thinking data fixes it.
  - Benchmark of speculative decoding for test-time scaling (2509.04474); acceptance across cognitive domains (2604.14682).
- **Robust and parallel drafters:** H-Spec (2609.24197, zero-shot transfer to fine-tuned targets); P-EAGLE (vLLM); DFlash (2602.06036).
- **Vocabulary:** FR-Spec, VocabTrim (2506.22694), SpecVocab (2602.13836), DynaSpec, NanoSpec.
- **Adapter reuse and transfer:** LoraHub, EigenLoRAx, Cross-LoRA, CAST; delta distillation OPD² (2607.15161).
- **RL vs SFT shift:** RL's Razor (2509.04259).

## 6. Constraints

- **About 2.5 days of experiments**, then 1.5 days of writing.
- **Compute:** about 40 NVIDIA A40 GPUs (48 GB), shared with other users; no H100s; 8B targets fit one A40; drafter training runs on one A40 with
  memory-saving flags (~1 step/min at 8k-token batches with paired capture).
- **Disk:** about 0.9 TB free.
- **Models:** public Hugging Face only, with an explicit license.
- **Protocol:** greedy decoding; all acceptance numbers from the pinned engine.
- **Data:** no use of a derivative's original training data; evaluation prompts never enter training.

## 7. Specific questions

1. Is "post-training type (distillation vs on-policy RL) determines family-drafter compatibility" already shown or implied anywhere?
2. Is cheap interface-only (`fc`) re-fitting of target-conditioned drafters known? What evidence suggests the shift lives in the features vs in
   the drafter's own layer or head?
3. Which repair variants would you add? Examples: feature-space alignment fitted in closed form from paired hidden states, KL-matched or on-policy data selection,
   draft-vocabulary re-selection for reasoning tokens, mixing family and derivative data, or a few minutes of on-policy distillation.
4. What is the minimum evidence for a convincing NAACL paper: how many derivatives per class, which baselines (including EAGLE-3 retraining from
   scratch at matched GPU-hours?), and which statistics?
5. How should we handle the reasoning-domain confound for Llama (the official Instruct model does not reason; distilled derivatives do)?
6. What are the top 5 reviewer objections, and the experiment or analysis that answers each?
7. Title, abstract and contribution phrasings.
