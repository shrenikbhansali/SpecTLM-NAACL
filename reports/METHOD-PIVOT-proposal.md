# Method pivot proposal: detect-and-repair speculators for fine-tuned derivatives

Prepared by claude-ops, Wed 2026-10-07, about 23:00 ET, at the owner's request ("land on a method for a strong method paper … under time pressure").
**Owner decision needed.** This changes the paper's framing (MASTER §2.2). Nothing here is adopted; no jobs launched.

## 1. What our own evidence says (all numbers from existing artifacts)

| # | Finding | Evidence |
| --- | --- | --- |
| F1 | **Feature-conditioned drafters transfer to most public derivatives zero-shot.** Median per-token (first draft position) acceptance retention: EAGLE-3 Llama 0.999, Qwen3 0.997; DFlash Llama 0.988, Qwen3 0.989 (n = 87 each). Contrast: standalone drafters collapse on domain fine-tunes (EDA: τ 4.37 → 1.17 on Qwen2.5-Math). | EXP-ATL-005; length-controlled re-analysis below |
| F2 | **A real tail survives length control.** First-position acceptance retention < 0.95: EAGLE-3 Llama 17/87 (< 0.8: 5); DFlash Llama 22/87 (< 0.8: 8); EAGLE-3 Qwen3 12/87; DFlash Qwen3 19/87. Restricting to outputs ≥ 64 tokens keeps most of it. | `artifacts/ATLAS_lencontrolled_20261007/per_pair.json` |
| F3 | **Two mechanisms.** (a) *Vocabulary/language shift*: EAGLE-3's pruned 32k draft vocabulary misses up to 30–67% of the derivative's next-token mass (Russian Vikhr 0.39, Romanian RoLlama 0.30, Thai 0.67). Out-of-vocab mass predicts EAGLE-3 per-token loss (ρ −0.36, p 0.001); KL does not (ρ −0.08). (b) *Behavioural shift* (DPO/IPO tests, role-play, odd LoRAs): high KL; DFlash is more KL-sensitive (ρ −0.34). | A6 covariates × length-controlled pairs |
| F4 | **Acceptance-length retention is a misleading metric for derivatives.** 4 of the 5 worst Llama AL retentions are output-length artifacts (6–33-token answers). RoLlama has AL retention 1.135 but per-token retention 0.84; RestoreKV has 2.14 from looping. | EXP-ATL-005 anomalies |
| F5 | **Bank training gives a uniform +0.14–0.15 AL to every target, including the parent, but no derivative-specific benefit.** FS ≈ MVD ≈ PO-D ≈ PO-T (fixed panel, full budget; λ = 0 ≈ λ > 0). On the degraded tail of the 50-target matrix (partial), FS − controls ≈ 0 and the worst case (daxplain, 0.67) stays broken under every arm. | EXP-ATL-009/010 (operator re-derived 009); partial full matrix |

**Implication.** The strongest motivation is not "derivatives break drafters" (mostly false for feature-conditioned drafters). It is
"**a predictable minority of derivatives break them, for diagnosable reasons, and no generic training fixes those**."
A bank-level method (FollowSpec) cannot work by construction: it cannot anticipate a specific unseen derivative's shift. A method must use the
derivative itself.

## 2. Literature position (read 2026-10-07)

- Per-target drafter adaptation exists: **EDA** (arXiv 2603.09527: shared/private experts, self-regenerated data, 3 Qwen2.5 domain fine-tunes,
  standalone drafters); **OmniDraft** (2507.02659: online LoRA, cross-vocabulary); **OSD** (2310.07177); **EvoSpec** (2605.27390: verification-guided
  online LoRA plus dynamic vocabulary, Qwen3-8B/EAGLE-2); **vLLM RFC #52038** (per-domain LoRA on DFlash drafters for multi-LoRA serving).
- Data-free drafter data via Magpie is shown to work: **Training Domain Draft Models** (2503.07807): offline > online by 11–25%; synthetic Magpie gives 80–93%
  of real-query performance.
- Vocabulary: **FR-Spec**, **VocabTrim** (2506.22694), **SpecVocab** (2602.13836), **DynaSpec** (2510.13847), **NanoSpec** (2605.26444). Static pruned
  vocabularies "miss locally important long-tail tokens".
- Robust architectures: **H-Spec** (2609.24197, zero-shot transfer to fine-tuned targets), **FlexSpec** (2601.00644).
- PEFT drafting must stay cheap: **"Accepted Prefixes Are Not All You Need"** (2607.12422): a full-backbone PEFT drafter gives no speedup.

**Gap.** Every adaptation paper assumes adaptation is needed and studies 1–3 self-chosen domain fine-tunes, mostly with standalone drafters.
None measures *which* real-world derivatives need it, why, or how to decide cheaply. None separates vocabulary failure from behavioural failure.

## 3. Proposed method: TRIAGE-then-REPAIR (working name *SpecMend*)

For a newly deployed derivative D of base B with released drafter d_B (EAGLE-3 or DFlash):

1. **Self-elicit.** Magpie-generate N queries from D itself and D's responses (no user data; reuse our A3/FIX-5 pipeline with forbidden-file dedup).
2. **Triage (cheap).** On about 32 self-elicited prompts: (a) measure first-position acceptance of d_B on D vs d_B on B (one short vLLM cell each);
   (b) out-of-draft-vocab mass of D's outputs (A6 code). Flag D if predicted retention < τ. Classify the mechanism as vocabulary if OOV-mass shift
   is high, else behavioural. *Validated on the full 174-derivative census*: AUROC of the probe against the full measurement, and compute saved by
   skipping the ~80% that need nothing.
3. **Repair flagged derivatives only, matched to mechanism.**
   - Behavioural: short self-distillation of the drafter on D's self-elicited data with D's online features (our B5/B6 trainer, single target,
     a few hundred steps), initialised from the bank-trained drafter (F5's uniform +0.15).
   - Vocabulary: re-select the draft vocabulary from D's self-elicited token frequencies (same size, so no extra drafter cost), then train only the new head rows plus the
     same short distillation. Training is required: the drafter head is not aligned with the target head (median row cosine 0.055, linear R² 0.28;
     measured tonight). A training-free row graft is ruled out.
4. **Deploy** the repair as a small delta beside D's adapter (multi-LoRA serving story; vLLM RFC #52038 shows demand).

**Claims to test.** (i) The probe predicts full-census degradation (AUROC); (ii) repair recovers most of the per-token loss on flagged derivatives at
minutes of A40 cost; (iii) self-elicited data ≈ in-domain data and > generic data (EDA-style) for repair; (iv) bank training alone (FS/MVD) does not
repair the tail (we already have this); (v) vocabulary re-selection is necessary for language-shift derivatives.

**Why reviewers may find it worthwhile.** Ecosystem-scale evidence (174 public derivatives, two drafter families, pinned engine) that no prior work has. A
correction to the field's metric practice (F4). A decision procedure practitioners can use. A cheap repair that targets mechanisms we identified.
**Honest risk.** The repair components individually resemble EDA/Magpie/FR-Spec. Novelty rests on the census, triage and mechanism matching.
If repair does not clearly beat generic-data adaptation, the paper is an analysis paper with a modest method.

## 4. Alternatives considered

- **B. Language-shift only** (vocabulary re-selection for localization derivatives): cleanest mechanism, but few cases in the census (about 6 Llama + 4 Qwen3)
  and direct competition from dynamic-vocabulary methods.
- **C. Adapter-aware drafter** (feed the drafter the LoRA branch's own activations, free in multi-LoRA kernels; train on the 60-target bank): most novel,
  but needs vLLM kernel changes and probably more than 60 adapters to generalise. Not feasible by Monday.
- **D. Pure analysis paper** (census + F1–F5 + FollowSpec negative result): safest fallback; all evidence exists.

## 5. Plan (deadline Mon 23:59 AoE)

| When | What | Owner |
| --- | --- | --- |
| Thu 08:00 | Owner decides; record D-40 (framing) | owner |
| Thu 08:00–14:00 | codex: single-derivative repair stage (Magpie training split for any atlas derivative → responses → single-target short train from Frozen or bank init → export) + vocabulary re-selection tool; tests | codex |
| Thu 14:00–22:00 | **Pilot / go-no-go** on 5 tail derivatives (daxplain, Vikhr-R, tanliboy dpo-orca, natsumura storytelling, metacog toy-meta) × {self-elicited, generic-data} × {Frozen init, bank init}; frozen K4 harness on held-out A3 prompts | operator runs |
| Thu 22:00 | **Go** if repair recovers ≥ 50% of the lost first-position acceptance on ≥ 4/5 and beats generic data; otherwise switch to D | owner |
| Fri | Full tail (Llama EAGLE-3 ~17, DFlash if B10 trains, Qwen3 language tail) + probe validation on the census + ablations; ICE for training | all |
| Sat | Wall-clock speedups (A9, dedicated H200s), figures, ledger | operator |
| Sun–Mon | Writing (census sections already evidenced) | owner + agents |
