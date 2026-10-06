# A2 proposal: pool freeze (needs owner D-04 before freezing)

Prepared by claude-ops, 2026-10-06 (ET). Evidence: `notes/A2.md`; per-model filter results
`$WS/artifacts/A2_queue_20261005/{llama,qwen3}_filter_summary.csv`; B1 final drafts
`$WS/artifacts/atlas/B1_<base>_finaldraft_retry_20261005/`.

## What was done
Every staged candidate (Llama 132 = 100 sampled + all 39 bank adapters; Qwen3 118 = 100 + all 25) went through the
FIX-1 filter on the pinned engine (vLLM 0.31.0, EAGLE-3 K = 4, fresh compile, A40): vLLM loadability, PPL on the shared
SPEED-128 reference ≤ 2× base, and 0/10 degenerate answers (D-16). Base references: Llama PPL 7.461, Qwen3 8.529.
Every extreme or crash-type rejection was triaged (journal): one rsLoRA adapter is broken (checked against HF PEFT);
two Qwen3 LoRAs carry non-standard modules (`model.unembed_tokens`, full embed/lm_head weights without modules_to_save).

## Result (cutoffs as drafted in §5.7; D-04 pending)

| | Llama | Qwen3 | §5.7 requirement |
| --- | --- | --- | --- |
| Sampled atlas derivatives accepted | **87 / 100** | **88 / 100** | ≥ 60 Llama, ≥ 40 Qwen3 ✓ |
| … of which test pool (post-cutoff, author-disjoint) | **50** | **46** | ≥ 30 each ✓ |
| … of which pre-cutoff atlas | 30 | 35 | — |
| … of which bank adapters in the sample | 7 | 7 | — |
| Bank (all staged pre-cutoff LoRA adapters) accepted | 34 / 39 | 23 / 25 | target 30–60 |
| Bank after dedup (cos > 0.95) | **33** | **21** | Llama ✓; Qwen3 below target |
| Test–bank pairs with cos > 0.9 | 0 | 0 | none allowed ✓ |

Accepted atlas types: Llama: abliterated 22, full fine-tune 20, LoRA 18, RL-tuned 12, FP8 6, merge 3, other 3, AWQ 2, GPTQ 1.
Qwen3: RL-tuned 15, full fine-tune 14, LoRA 14, abliterated 14, other 11, FP8 9, AWQ 5, GPTQ 5, merge 1.

## Proposed freeze rules (owner to confirm or change)
1. **D-04 cutoffs as drafted** (Llama bank < 2025-07-01; Qwen3 bank < 2026-01-01). Both test pools clear 30.
2. **Dedup:** for each bank pair above 0.95, keep the adapter with more Hub downloads (ties: earlier upload). Pairs:
   `Yaxin1992/llama3-8b-summary-tulu-setting` vs `Yaxin1992/llama3.1-8b-dpo-7000-tulu-setting` (0.997);
   `Hanqix/GCM-Qwen3-8B-MMLU` vs `Hanqix/Qwen3-8B_GCM_MMLU_lora_model` (1.000);
   `Hanqix/GCM-Qwen3-8B-TriviaQA` vs `Hanqix/Qwen3-8B_GCM_TriviaQA_lora_model` (1.000).
3. **Freeze artifact:** `pool_manifest_<base>.csv` with columns model_id, revision, type, pool, license, filter run ID,
   PPL ratio, plus a sha256 recorded in §13; no later edits (replacements get a new manifest and a §13 entry).

## Observations for the owner (no action taken)
- **Engine-capability exclusions are systematic:** GPTQ with desc_act=True, bitsandbytes/NF4, torchao INT4, AMD MXFP4,
  and non-causal-LM architectures (a reward model, a guard model) cannot load on the pinned engine. The quantized strata
  therefore cover FP8, AWQ and static-order GPTQ only, which belongs in Limitations.
- **The Llama test pool has no quantized derivatives** (all quantized Llama derivatives predate the cutoff), so
  quantization effects on held-out derivatives can be studied only on Qwen3.
- **Qwen3 bank = 21 after dedup**, below the 30–60 target; relevant only to M6 (FollowSpec on Qwen3).
- **Magpie refusals (§1 item M)** may shrink own-domain workloads for safety-tuned derivatives at A3; decide before A3.
