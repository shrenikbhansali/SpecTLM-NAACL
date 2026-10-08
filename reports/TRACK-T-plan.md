# Track T: find a robust failure mode for target-conditioned drafters (EAGLE-3, DFlash)

Owner direction 2026-10-07 23:xx ET (D-40). Server: **heck** (validated A40 atlas harness; acceptance comparisons stay on A40s).
**ICE is unavailable (D-41):** Track T shares heck with Track I (proposed: Track T on heck-srv1 + heck-srv3). H4 runs only as A40-feasible training.

## Why the current census is not enough
Public derivatives *of the official Instruct model* rarely break target-conditioned drafters. Median per-token retention is ≈ 0.99–1.00, and the tail
is language-localization tunes, three DPO/IPO tests and odd LoRAs (EXP-ATL-005/007, `artifacts/ATLAS_lencontrolled_20261007`). DFlash is more fragile at
deep block positions (position 10: 5/87 Llama derivatives < 0.6 vs 1/87 for EAGLE-3), but its median is ≈ 1.0.

## Hypotheses (ranked by expected effect × realism), all testable with public checkpoints
| ID | Shift | Why it should break the drafter | Public checkpoints (verified on the Hub 2026-10-07) |
| --- | --- | --- | --- |
| H1 | **Lineage**: same pretrained base, *different post-training* (not a derivative of the drafter's target) | Drafters exist only for the official Instruct model, yet the most-used models in a family often come from the base via other post-training. Hidden-state geometry and style diverge | Tülu-3 ladder from Llama-3.1-8B: `allenai/Llama-3.1-Tulu-3-8B-SFT` → `-DPO` → `Llama-3.1-Tulu-3-8B` (RLVR); `NousResearch/Hermes-3-Llama-3.1-8B` (522k downloads); `meta-llama/Llama-3.1-8B` (pretrained); `Qwen/Qwen3-8B-Base` |
| H2 | **Reasoning distillation / long chain-of-thought** | Output style and length change drastically; drafters were trained on short chat | `deepseek-ai/DeepSeek-R1-Distill-Llama-8B` (190k downloads), `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B` (673k), `nvidia/Llama-3.1-Nemotron-Nano-8B-v1`; Qwen3-8B thinking vs non-thinking mode (same weights) |
| H3 | **RL drift** (policy moves with RL steps) | On-policy RL sharpens and shifts the distribution; drafters go stale (important for RL-rollout acceleration) | Step ladders: `shufanshen/Qwen3-8B-GRPO-DeepMath-{50,150}-steps`; `luckeciano/Llama-3.1-8B-Instruct-GRPO-Base-v2_{2886,4461}`; `OpenLearnLM/deepseek_qwen3_8b_{think_reward,nothink}_grpo_step_300`; `etiennebamas/qwen3-8b-classic-grpo-step-250`; `zztheaven/Llama-3.1-8B-Instruct-Open-R1-GRPO`; `tokyotech-llm/Qwen3-Swallow-8B-RL-v0.2` |
| H4 | **Heavy/continued training** (controlled) | Larger, longer updates move the representation further | Our own: high-rank LoRA or A40-feasible fine-tunes with increasing steps/LR on one domain (heck A40s; extends the D-39 code/math SFT panel, where step-200 LoRA SFT barely degraded the drafter) |
| H5 | **Language localization** (already observed) | Pruned draft vocabulary misses the language's tokens | Vikhr (ru), WiroAI (tr), RoLlama (ro), Thai/Cantonese/Japanese Qwen3 tunes (in the census) |

## Protocol (phase 1, tonight → Thu noon)
- Same frozen harness as the atlas (vLLM 0.31.0, greedy, batch 8, 512 tokens, fresh compile, exact rendered prompts, D-22 matched settings).
- Drafters: EAGLE-3 K = 4 and DFlash native K (10 Llama / 16 Qwen3) for both bases.
- Workloads: the shared general set (SPEED-derived, 128) rendered with each model's own chat template (D-30 fallback to the base template).
  Add GSM8K/MATH-style prompts for H2/H3 if the general set is short on reasoning.
- A00 = official Instruct (or Qwen3-8B) + drafter on the same raw queries.
- Metrics: **per-position conditional acceptance** (position 1 = length-robust headline), τ, output length, and wall-clock on the dedicated H200s for
  the strongest cases (A9 rules).

## Decision rule for "robust failure mode" (Thu ~14:00)
Adopt a shift as the paper's motivation if it gives **≥ 20% per-token acceptance loss** (position 1, or the mean over positions) **for both drafter
families**, on **≥ 2 independent public models** of a **common, realistic class**, with a plausible mechanism (covariates). Otherwise report the
robustness finding (census) as the motivation for Track I.

## Owners
- codex-1 (heck): stage, filter, render and cells for the H1–H3 list (reuse B1/A2/A3/A4 code); record licenses (AGENTS rule 9).
- claude-ops (heck): downloads tonight, launch and verify, per-position analysis, ledger.
- ICE: unavailable (D-41). Track I also runs on heck (heck-srv4 + heck-srv2:0–3).

## Phase 1b (owner, 2026-10-08 ~01:45): is the reasoning-distillation failure real, novel and significant? (exploratory)

T1 interim (operator re-derived, n = 128 prompts per pair): position-1 retention for EAGLE-3 / DFlash is R1-Distill-Llama-8B .75 / .72,
Nemotron-Nano-8B .77 / .75, R1-0528-Qwen3-8B .86 / .80, Tülu-3 DPO/RLVR .78–.81 / .82; GRPO from the drafter's own target (Qwen3 50–250 steps)
≈ 1.0. Context: drafters trained on chat data are known to lose acceptance on reasoning traces (practitioner reports; arXiv 2509.04474,
2604.14682). RL's Razor (arXiv 2509.04259, ICLR 2026) shows on-policy RL stays KL-close to the base, whereas SFT can drift far. A dedicated EAGLE-3
exists for R1-Distill-Llama-8B (`yuhuili/EAGLE3-DeepSeek-R1-Distill-LLaMA-8B`), but none was found for R1-0528-Qwen3-8B, Nemotron-Nano-8B or
Hermes-3, and no DFlash drafter exists for any R1 distill.

Three checks decide whether this can carry the paper:

| Check | Question | Probe | Reading |
| --- | --- | --- | --- |
| **C1 domain vs model** | Is the loss caused by reasoning *text* (known) or by the derivative's *model shift* (more novel)? | (a) Teacher-forced on R1-Distill's and Nemotron's own A10 traces: per-position top-1 agreement of the EAGLE-3 drafter (fed the target's own taps) with (i) the derivative and (ii) Llama-3.1-8B-Instruct, on the same token contexts; same on Instruct's own A00 outputs as the reference. (b) vLLM cells: Qwen3-8B thinking vs non-thinking with its own EAGLE-3/DFlash drafters on identical raw queries. | Agreement vs Instruct also drops on reasoning text, or the thinking-mode drop is large → mostly a domain effect. Agreement vs Instruct stays high on reasoning text while agreement vs the derivative drops → model shift |
| **C2 oracle** | How much does a dedicated drafter recover? | R1-Distill-Llama-8B + `yuhuili/EAGLE3-DeepSeek-R1-Distill-LLaMA-8B` (pinned, license recorded) on the same T1-rendered prompts, EAGLE-3 K4, beside the Instruct-drafter A10 and the Instruct A00 | Sets the reference any cheap repair must approach; its training cost (model card) sets the economics |
| **C3 RL vs distillation** | Does "on-policy RL keeps drafters, distillation breaks them" hold beyond short runs, and does it track KL? | Add 2–4 longer or larger-drift RL checkpoints from the same base (prefer step ladders; check architecture compatibility first). Use the Tülu-3 SFT → DPO → RLVR ladder as a within-lineage series. Compute child‖base KL (atlas.covariates) for every T1 model and plot position-1 retention vs KL together with the atlas | RL points at low KL with high retention and distillation at high KL with low retention → supports the RL's Razor framing. Mixed → report as is |

Outcomes map to directions for the owner: model shift plus RL/distillation contrast → strong motivation for repair of target-conditioned
drafters on distilled derivatives (with C2 as the reference). Mostly domain → population paper with "what post-training breaks speculators" as the
headline and repair as a measured baseline.
