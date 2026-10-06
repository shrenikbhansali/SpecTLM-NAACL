# B8 paired covariates

Use the pinned vLLM0.31.0 A10 cell on the derivative's own64 B4 evaluation
prompts as the generation source. Add `--capture-prompt-token-ids` to B2
`atlas.run_cell`. This optional flag saves the actual engine context tokens;
all historical defaults and metrics are unchanged. Keep the same rendered
prompt file for matched A00/A10. A6 preparation checks the prompt hash and
derivative revision and rejects A00 generations substituted for A10.

```bash
python -m atlas.prepare_covariates --cell ARTIFACTS/A10_CELL --output ARTIFACTS/NEW_SEQUENCES
.venv-covariates/bin/python -m atlas.covariates \
  --base LOCAL_BASE_SNAPSHOT --base-revision BASE_SHA \
  --drafter LOCAL_EAGLE3_SNAPSHOT --drafter-revision DRAFTER_SHA \
  --child LOCAL_CHILD_SNAPSHOT --derivative-id CHILD_ID --derivative-revision CHILD_SHA \
  --sequences ARTIFACTS/NEW_SEQUENCES/sequences.jsonl --output ARTIFACTS/NEW_COVARIATES
```

Use `--adapter LOCAL_ADAPTER` instead of `--child` for LoRA. Base/self uses
neither flag and `--derivative-id base`; it consumes the same saved child
sequences. All inputs are pinned local snapshots; the launcher must assign a
free A40. Prepend the selected environment's bin directory to PATH. No large
campaign is launched by these instructions: the operator schedules A6. Active
pause markers block real execution; `--dry-run` prints a read-only plan.

Offline passes are paired bf16/eager Transformers on identical token IDs,
with backend versions recorded. They are covariates, not replacement vLLM
acceptance measurements. LoRA preserves the same unmerged PEFT computation;
weight norms use exact low-rank update algebra. Dense targets compare actual
weight tensors. Weight-only AWQ/GPTQ checkpoints are decoded to their effective
weights in memory without exporting models. AWQ uses native nibble order;
GPTQ is restricted to the pinned engine's symmetric/static4/8bit layouts.
Native compressed-tensors decompression keeps activation QDQ hooks enabled.
Other layouts fail explicitly; do not relabel them as dense targets. A config
with bitsandbytes metadata in an adapter repository is still loaded as a PEFT
adapter on the pinned base, matching its native generation path.

All modules with base `.weight` parameters contribute to relative norms,
including unchanged modules. Extra quantization scale parameters do not enter
the weight-update norm. The EAGLE3 taps use checkpoint layer IDs or pinned
vLLM's default `[2,n//2,n-3]`, interpreted as embedding-inclusive HF hidden
states before final normalization. The vocabulary mapping is validated from
both `t2d` and `d2t`. Positions predicting generated answer tokens are scored;
prompt-only positions are excluded. KL is child||base; feature displacement
is mean tokenwise relative L2 and cosine distance. Token counts accompany
averages, with per-prompt records retained. A single diagnostic run does not
estimate run-to-run uncertainty.

Base/self must have zero weight, KL, feature, LM-head and outside-vocabulary
**mass-shift** covariates. Absolute outside-vocabulary mass is retained and
need not be zero for the base. This distinction is required by its definition.
Chat-template identity is computed from actual snapshot templates, with base
inheritance explicit for adapters lacking a template. Loading unsupported or
mismatched identities, masks and lengths fails instead of silently truncating.

A bounded acceptance check can use `--acceptance-smoke` (at most10 prompts).
`prepare_covariates --filter-run FIX1_CELL --acceptance-smoke` reuses exact
native A2 general-set generations for smoke checks only. Such data can never
pass the production64-own-prompt gate. Decode and inspect five samples and
their assistant masks for every new data path before downstream use.

Outputs are new directories with config, per-prompt metrics, weight covariates,
results/runtime, quantization backend details where applicable, and a pilot
ledger draft. The operator assigns a ledger ID and verifies acceptance.
