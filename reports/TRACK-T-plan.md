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
