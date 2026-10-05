# Pinned atlas harness (B2)

Use the isolated environment built by `python atlas/env/build.py --prefix <new-path> --lock-output <new-path>`.
The source pin is `atlas/env/engine.json`; the resolved freeze is committed only after installation and dependency checks pass. Never run in the historical vLLM 0.17.1 environment.

`python -m atlas.run_cell --target MODEL --target-revision SHA --drafter MODEL --drafter-revision SHA --method eagle3 --K 4 --prompts prompts.jsonl --output /absolute/WS/artifacts/UNIQUE_RUN --dry-run` prints the configuration without creating artifacts. Remove `--dry-run` only after the owner removes the experiment pause marker. Existing output directories are refused.

Prompts are JSONL with unique `prompt_id` and already-rendered `prompt` strings. They are passed directly to `LLM.generate`, matching the historical GSM8K path. Do not double-apply chat templates. Qwen3 workloads must be rendered in non-thinking mode by the workload builder. Default generation length is 512, as specified in MASTER; the old script default was 128, so golden comparisons must explicitly match the historical artifact's setting.

An adapter cell additionally takes `--adapter /pinned/local/path --adapter-revision PROVENANCE_ID`; every adapter file is hashed. Full model and drafter revisions must be 40-character SHA pins. Batch size is logged and must match across controls. The engine gets explicit target LoRA requests.

## Metrics

Acceptance length is `1 + sum(accepted_draft_tokens) / speculative_steps` per prompt, then an unweighted mean over prompts. The bonus convention matches the old `tlm_sd.metrics.acceptance_length`. Missing counters fail; zero-step outputs are not silently interpreted as acceptance 1. Ordered raw accepted and proposed counts are retained.

`per_position_acceptance` preserves the historical unconditional rate. `per_position_conditional_acceptance` conditions on previous positions being accepted and the current position being proposed. Undefined denominators are null. Detailed per-request counters replace the old single-request global-counter subtraction, enabling correct macro aggregation at batch sizes greater than one.

Timing separates engine startup, generation, and total cell wall time; batch wall time is not presented as each prompt's latency. No warmup runs are inserted. This differs from the historical harness, which warmed two prompts and then ran an extra full batch for throughput. Dedicated wall-clock comparisons remain operator task A9.

## Operator acceptance

Use precisely the 128 GSM8K prompts from EXP-MTH-021 and the narrow LR 2e-4 final child linked by EXP-MTH-018 to EXP-MTH-002. The latter is **not** the LR 1e-5 child in the EXP-MTH-018 new artifact list. Preserve the same max-token setting across old/new and A00/A10 cells.

Collect base, identical repeat, child LoRA, same child merged, EAGLE-v1, and DFlash cells. Then run `python -m atlas.check_acceptance --base DIR --repeat DIR --lora DIR --merged DIR --eagle DIR --dflash DIR --golden-prompts FILE --report NEW_JSON`.

The checker reports the historical base (3.0559), repeat difference versus 0.0138, signed child drift versus -0.248, LoRA/merge parity versus the observed repeat difference, and all timings. It does not invent a numeric tolerance for “similar size”; the operator must review that phrase in MASTER. DFlash's trained block size is read from the model config and saved alongside configured K; the pinned engine validates supported settings.

Source contracts were checked against upstream vLLM v0.31.0 `outputs.py`, `v1/metrics/stats.py`, `engine/arg_utils.py`, `config/speculative.py`, and `config/observability.py` at https://github.com/vllm-project/vllm/tree/v0.31.0/vllm . This is not GPU validation.
