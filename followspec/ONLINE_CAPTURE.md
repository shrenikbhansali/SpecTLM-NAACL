# Online paired targets on the A40s

Owner decision D-19 places method generation and training on the heck A40s
while ICE is unavailable. Use `--allow-a40-production` with
`atlas.generate_magpie` or `followspec.generate_responses`. Without that
flag, the previous H100/H200 production guard remains. Magpie production
still requests 500 training or 64 evaluation queries; `--acceptance-smoke`
still produces diagnostic data which production training must reject.
Pause checks apply in both modes. Use a fresh `VLLM_CACHE_ROOT` and output
directory for each generation cell.

`python -m followspec.generate_responses --help` describes the response
entry point. It requires pinned local base/tokenizer snapshots, raw training
queries, forbidden evaluation files, and (for a child) the staged B1 manifest,
download records and successful A2 filter directory. It permits only base
or bank LoRA targets. Generation uses vLLM 0.31.0, temperature 0.6, top-p
0.95, and 512 new tokens; the five-prompt acceptance mode caps responses at
64 tokens. Each request has a recorded independent deterministic seed.
Rendering happens once; exact engine prompt/response IDs produce the
assistant mask. No re-tokenized answer or evaluation prompt is admitted.

Response artifacts retain config, per-prompt records, results and a pilot
ledger draft. Their `training_ready` field stays false: B5 still must
assemble the four arm manifests, enforce the owner-selected budgets and
parent share, audit all train/evaluation files, and inspect decoded masks.
Mixture generation remains dependent on B3's unresolved numerical
acceptance. This helper does not authorize a training run.

`OnlinePairCapture(model, tap_indices, draft_token_ids)` freezes one target
instance and exposes the B6 raw tensor contract. `model` may be a PEFT
wrapper. Each call accepts one complete sequence and its contiguous
assistant mask, then runs the base and child on those exact IDs. The base
pass temporarily disables the adapter; the context restores it even on
failure. Supply the drafter's actual tap indices and its ordered target
vocabulary IDs (`arange(len(d2t)) + d2t`), never infer a smaller vocabulary.

The returned fields are `input_ids`, `loss_mask`, `hidden_states`,
`base_hidden_states`, `verifier_last_hidden_states`,
`base_verifier_last_hidden_states`, `child_target_logits`, and
`base_target_logits`. Hidden taps are unshifted; final states are captured
before the target's final norm. Labels use each pass's actual LM head,
projected into draft-vocabulary order. B6's `shift_paired` and native
collator consume this contract. Target passes run under `no_grad`, so the
drafter can save the resulting ordinary tensors for backward. Target
parameters never get gradients. No feature tensors are written to disk.

Call capture in the main training process (`num_workers=0`), outside
distributed wrapping of the drafter. Keep the frozen target separate from
the drafter's optimizer and `.train()` calls. A trainer may switch the
active registered bank adapter between samples, but must not switch it
during capture. Each process owns its target. Do not keep all bank adapters
resident by default; B5/B6's loader must bound its adapter cache.

`route_arm` requires base-generated responses for PO-D, child-generated
responses for FS/MVD/PO-T, and base-generated parent-share records. PO-T
and PO-D request `feature_target='base'`; this reuses the exact base-pass
outputs for both sides. FS and MVD request child features. This routing
does not choose mixture ratios, token counts, optimizer steps or budgets.

Storage: three Llama taps × 4096 × bf16 × two passes = 49,152 bytes/token,
or 1.47 TB at 30M tokens before final states and labels. Online capture
stores only response token records; feature memory lasts for the batch.
It trades repeated target forward computation for storage. FIX-3's small
native check reports peak GPU memory, but does not prove that B6's full
8192-token training batch fits: B6's native overfit/export acceptance must
measure that separately without silently changing the matched defaults.
