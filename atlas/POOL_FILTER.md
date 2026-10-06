# Pool coherence filter (FIX-1 / operator A2)

Use the pinned vLLM 0.31.0 environment. First prepare one shared reference:

```bash
python -m atlas.filter_pool --prepare-reference --prompts SPEED128_RAW_JSONL --base-snapshot PINNED_LOCAL_BASE --base-id BASE_ID --base-revision BASE_SHA --output NEW_REFERENCE_DIRECTORY
```

PPL is teacher-forced fixed general-prompt text, excluding each first token,
with global token weighting. References explicitly retain the first 2048
tokens; truncation and score masks are recorded. Generation uses the base
chat template, retains the last 2048 tokens when needed, disables Qwen
thinking, and generates at most 128 greedy tokens on the first ten prompts.
All derivatives use identical reference token IDs. This is a coherence
diagnostic; it does not check factual accuracy or create training data.

Run the base once, then one process per staged derivative with `--baseline`
pointing to that successful base directory. Use `--pool`, `--downloads`,
`--derivative-id`, `--reference`, pinned base and drafter arguments, and a
new `--output` path. `python -m atlas.filter_pool --help` lists all options.
For the EXP-MTH-018 acceptance child, `--adapter` and `--adapter-revision`
record local file hashes and its provenance ID. All runs use EAGLE-3/K4,
max model length4096, max LoRA rank128, and fresh per-cell compilation.
Set a sufficient explicit rank cap consistently for base and derivatives.
Production jobs belong to the operator; pause preflight remains mandatory.

The owner approved `--repetition-threshold 0.5` on October5 (notes/FIX-1.md).
Flag an answer if it is empty, immediately ends, or one repeated4gram covers
strictly more than50% of its generated token positions. Overlapping token
positions count only once; the4gram must occur at least twice. Accept only
if PPL≤2×base and zero of ten answers are flagged. No threshold is silently
inferred when the option is absent: metrics are written, accepted is null.

Saved runs with a pending threshold can be finalized without inference:

```bash
python -m atlas.finalize_filter --run SOURCE_RUN --repetition-threshold 0.5 --decision 'Owner approval, notes/FIX-1.md' --output NEW_DECISION_DIRECTORY
```

This validates recorded logprobs, recomputes repetition from token IDs, checks
the matched baseline and writes derived results with source-file hashes.
Original artifacts remain unchanged. Each GPU/derived run has a pilot ledger
draft for operator assignment. Inspect failure phase and error for rejected
inputs; do not interpret infrastructure failures as scientific exclusions
without operator triage.
