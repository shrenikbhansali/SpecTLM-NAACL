# Problem brief: independent draft models vs fine-tuned targets (Track I)

Self-contained brief for a research assistant (prepared by claude-ops, 2026-10-07 23:xx ET) to brainstorm **methods** and **experiments**.
Hard deadline: paper submission (ARR → NAACL 2027) **Mon Oct 12, 2026, 23:59 AoE**. About 3.5 working days remain, so ideas must be
implementable and testable in about 1–2 days on our infrastructure (below).

## 1. Problem setting

Speculative decoding: a cheap **draft model** proposes K tokens; the **target** LLM verifies them in one forward pass. The output is unchanged
(lossless under greedy/standard verification). Speedup grows with the **acceptance length** τ, the mean number of tokens accepted per target forward
(including the target's bonus token).

Two families of drafters exist:
- **Target-conditioned drafters** (EAGLE-3, DFlash, P-EAGLE, MTP heads) read the target's hidden states. In our census of 174 public fine-tuned
  derivatives (87 of Llama-3.1-8B-Instruct, 87 of Qwen3-8B), these **transfer almost perfectly**: median per-token acceptance retention ≈ 0.99–1.00.
  Failures are confined to about 15–20% of derivatives (language localization, a few DPO tests, odd LoRAs). That is studied in a separate track.
- **Independent drafters** are small standalone LMs of the same family that see only tokens, e.g. Llama-3.2-1B-Instruct drafting for Llama-3.1-8B-Instruct, or
  Qwen3-0.6B/1.7B for Qwen3-8B. They are simple, need no target-specific training, work across serving stacks, and are used in production
  (e.g. low-concurrency chat APIs; vLLM `draft_model`).

**The problem (Track I).** A fine-tuned **derivative** of the target (LoRA adapter, full fine-tune, merge, RL/DPO tune, quantized checkpoint,
localization) changes the target's next-token distribution. An independent drafter has no access to the derivative's internals, so its proposals
are mismatched and acceptance can collapse. Prior work reports, for domain fine-tunes of Qwen2.5-7B with a standalone drafter, τ falling from 4.37
(drafter retrained for the target) to **1.17** without adaptation (EDA, arXiv 2603.09527). Organizations fine-tune constantly (thousands of public
derivatives per base on Hugging Face; multi-LoRA serving puts hundreds of adapters behind one base). Retraining a drafter per derivative is
costly, and the derivative owner usually does not share training data.

**Research question.** How can an independent drafter be repaired for an arbitrary derivative **cheaply, at scale, and without the derivative's
training data** (zero-data repair), ideally amortized across many derivatives?

## 2. What is known (literature, 2023–2026)

- **Distillation of the drafter on target outputs**: DistillSpec (ICLR 2024); Online Speculative Decoding (OSD, ICML 2024; continual distillation on
  live queries); *Training Domain Draft Models: Best Practices* (arXiv 2503.07807): offline distillation beats online by 11–25%; white-box beats
  black-box by 2–10%; **Magpie self-generated data reaches 80–93%** of training on real user queries.
- **Efficient per-target adaptation**: EDA (arXiv 2603.09527): shared + private experts, adapt only the private part with target-regenerated
  data and Mahalanobis-based sample selection; recovers τ 1.17 → 4.79 at about 61% of full-retraining cost (3 public Qwen2.5 domain models: Math,
  Coder, Meditron). OmniDraft (2507.02659): one drafter, online LoRA plus cross-vocabulary mapping, adapts to many targets. FlexSpec (2601.00644):
  frozen edge drafter compatible with evolving cloud targets via a shared backbone. EvoSpec (2605.27390): verification-guided online LoRA plus dynamic
  vocabulary. vLLM RFC #52038: per-domain LoRA on drafters for multi-LoRA serving (adapter about 28× smaller than the drafter, within about 2% of a full
  per-domain drafter).
- **Caveat**: PEFT drafters that require a full-backbone pass are not cheaper than verification (arXiv 2607.12422: no speedup). The drafter must stay
  small.
- **Related transfer ideas** (not yet applied to drafters, as far as we know): LoRA transfer across base models via synthetic data (Trans-LoRA,
  2024); task arithmetic / model merging; weight-space alignment between model sizes of one family.

**Gap we believe exists.** All adaptation work studies 1–3 author-chosen fine-tunes and assumes adaptation is needed. None measures how
independent drafters degrade across a large, realistic population of public derivatives, which derivative properties predict it, or how to repair at
scale with no data. Zero-data, amortized, or training-free transfer of the derivative's change into the drafter is open.

## 3. Our assets (usable immediately)

- **Census infrastructure**: pinned vLLM 0.31.0 (supports `draft_model` with vocabulary mapping), exact rendered prompts, fresh compile per cell,
  matched A00 (base target + drafter) vs A10 (derivative + same drafter) on identical prompts, per-prompt and per-position acceptance counters, macro
  τ with bonus token, pairwise exclusion of zero-step prompts. 174 derivatives already pinned, filtered (loadable, PPL ≤ 2× base, non-degenerate),
  typed (LoRA 31, full fine-tune 34, abliterated 36, RL/DPO 27, quantized FP8/AWQ/GPTQ 28, merges, other), split into a pre-cutoff pool and a
  held-out post-cutoff test pool, with own-domain evaluation prompts (64 Magpie prompts generated by each derivative itself) and a shared 128-prompt
  general set.
- **Covariates per derivative**: child‖base KL on the child's own generations, hidden-state displacement at three depths, weight-update norm,
  LM-head change, out-of-vocabulary mass.
- **Data-free generation**: Magpie self-elicitation of queries and responses from any derivative (500+ per derivative in about 10 minutes on one A40),
  deduplicated against all evaluation prompts.
- **Training code**: online paired-feature distillation for EAGLE-3 (target-conditioned); standard KD for small LMs is straightforward.
- **Compute**: about 40 A40s (shared), plus an H100/H200 Slurm cluster from tonight. Small drafters (0.6B–1.7B) train in minutes to hours.
- **Pairs to study**: Llama-3.1-8B-Instruct ↔ Llama-3.2-1B-Instruct (same tokenizer); Qwen3-8B ↔ Qwen3-0.6B / Qwen3-1.7B (same tokenizer).

## 4. Experiments planned first (to establish the motivation)

1. **Independent-drafter census**: for all 174 derivatives (or a stratified 60), measure τ and per-position acceptance with the independent drafter
   (A00 vs A10), next to the existing EAGLE-3/DFlash numbers on the same prompts. Expected: large, common degradation for independent drafters vs
   robustness for target-conditioned ones. This contrast is itself a finding.
2. **Predictors**: which derivative properties (type, KL, displacement, weight norm, language shift) predict independent-drafter loss.

## 5. What we want from you

Please propose **methods** (ranked by expected impact × feasibility in about 2 days) for zero-data or low-cost repair of independent drafters for
fine-tuned derivatives, with:
- the core idea and why it should work (mechanism);
- exactly what data and compute it needs (aim: no derivative training data; minutes per derivative; ideally amortized over many derivatives or
  training-free);
- how it differs from DistillSpec / OSD / EDA / OmniDraft / Magpie distillation (novelty a NAACL reviewer would accept);
- the minimal experiment that would falsify it on our setup, and the expected effect size;
- risks.

Directions we have not ruled out (feel free to go beyond them):
- **Weight-space transfer**: map the derivative's update ΔW (8B) onto the drafter (1B) without data (e.g. via learned or analytic layer/subspace
  alignment between family members; for LoRA derivatives, project A·B into the drafter's spaces).
- **Self-elicited distillation at scale**: Magpie from the derivative, then a small drafter LoRA; amortize across derivatives with a hypernetwork
  or a shared basis of drafter-LoRAs (do many derivatives' drafter corrections lie in a low-dimensional subspace?).
- **Verification-time free supervision**: every verification step yields the target's full next-token distribution; adapt online with zero
  extra target compute (OSD-like, but per-adapter and hot-swappable in multi-LoRA serving).
- **Logit-space correction**: combine the drafter with cheap signals of the derivative (e.g. a derivative-specific token prior or contrastive
  correction estimated from a few hundred self-generated tokens).
- **Triage**: predict from cheap probes which derivatives need repair at all.

Constraints: lossless speculative decoding; the drafter must stay much cheaper than the target; evaluation uses our pinned vLLM; report
per-token acceptance (not only τ, which is confounded by output length) and wall-clock speedup.
