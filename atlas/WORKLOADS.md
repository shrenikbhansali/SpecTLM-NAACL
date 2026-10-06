# Workloads (B4)

Use the pinned B4 public-source manifest and `atlas.workloads build-public`
to create 128 stratified SPEED evaluation queries and 20,000 Alpaca training
queries. The public SPEED parquet contains placeholders: reconstruct every
original source with `atlas.reconstruct_speed` first, including gated HLE.
The builder rejects unresolved placeholders. Source licenses and hashes are
recorded in the manifest. Do not redistribute SPEED data.

The validated local public artifact is
`artifacts/B4_public_resolved_20261005`. The earlier
`artifacts/B4_public_20261005` is INVALID and retained for audit.

`python -m atlas.generate_magpie --help` lists required pinned pool,
target, tokenizer and revision arguments. Use each derivative's own chat
template when available and its inherited base template otherwise. The
generator checks B1 tokenizer and adapter hashes. It generates raw user
queries, using published Magpie sampling, length 10–1000, exact/MinHash
deduplication and language annotation. Qwen3 uses non-thinking mode.
Configs report upstream recipe and deviations. No semantic quality filter
is implied; inspect refusals, repeated candidate text and answer-like text.

Generate evaluation first (64 queries/derivative), then training (500/bank
child) with a different seed. Pass **all** already created evaluation sets
and the complete `all_speed_forbidden.jsonl` to training `--forbidden-files`.
Evaluation must exclude `general20000.jsonl`. Once all paths exist, run:

```bash
python -m atlas.workloads audit --training GENERAL TRAIN1 TRAIN2 --evaluation ALL_SPEED EVAL1 EVAL2
```

Expand these lists to every file in the campaign. Audit failure blocks
training; separate seeds alone do not prevent leakage. The audit hashes
NFKC-normalized, case-folded, whitespace-collapsed raw queries. Original
query hashes survive rendering. MinHash duplicate rates are in each
filter report; forbidden removals are reported separately.

Before B2 evaluation, render each raw evaluation workload using the selected
derivative's pinned local tokenizer/template:

```bash
python -m atlas.workloads render-evaluation --input RAW_JSONL --tokenizer LOCAL_SNAPSHOT --tokenizer-revision COMMIT_SHA --family llama --output NEW_DIRECTORY
```

Use the resulting **same** `prompts.jsonl` for paired A00/A10 (and A01/A11)
cells. Use `--family qwen3` for Qwen3. Generation prompts disable thinking.
Do not render twice or send training queries through this command: B5
constructs the full training conversation and assistant-only mask.

Run production Magpie on H100/H200 through the operator. The explicit
`--acceptance-smoke` allows A40 builder checks only: at most 10 queries and
240 candidates per invocation, marked `acceptance_only=true` in rows and
config. Never feed these smoke files to training. The builder's ten
acceptance paths live in `artifacts/B4_smoke_20261005`; production pool
generation and frozen manifests remain A2/A3 work. Active pause markers
block GPU generation; dry runs remain available. Every real cell needs a
fresh `VLLM_CACHE_ROOT` and a new output directory.

For B2/A4 generation of rendered workloads, pass `--use-prompt-token-ids` so
the engine receives the saved rendered IDs exactly (text retokenization adds
a second BOS for Llama). Add `--capture-prompt-token-ids` for B8/A6. Both
paired cells use the same prompt file and input mode. For LoRA A10, enable
LoRA support on A00 too with `--enable-lora` and the same max rank.
