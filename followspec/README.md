# B3 mixture acceptance

`mixture.py` writes exact concatenated PEFT factors with scaling one. It never
loads a base model. CPU tests cover algebra, differing ranks/modules/dtypes,
rsLoRA and configured vLLM rank caps.

`verify_mixture.py` is the remaining real-model acceptance driver. It has two
phases, which must run in separate processes to release model memory. Both
refuse real execution if the root or historical pause marker exists. Dry runs
print provenance and never load a model or create an output directory.

```sh
python -m followspec.verify_mixture --phase logits \
  --base meta-llama/Llama-3.1-8B-Instruct --revision BASE_SHA \
  --adapters /path/a /path/b /path/c --prompts /path/16prompts.jsonl \
  --max-lora-rank CAP --atol RECORDED_ATOL --rtol RECORDED_RTOL \
  --output /path/new-logits-artifact --dry-run
```

After the pause is lifted, remove `--dry-run` in a compatible Transformers +
PEFT environment. Tolerances are mandatory because MASTER says bf16 tolerance
without a numerical threshold. Record them before measuring. The driver checks
all three one-hot choices, zero scale, and three seeded random mixtures at
scales 0.5, 1, 1.5 on the full next-token vocabulary at each of 16 prompts.
It reports maximum absolute and relative errors, with per-prompt records.
Direct dense merging accumulates original source updates in float32 and casts
the final weights to bf16. Original base weights are restored bit-for-bit.

Run the same arguments with `--phase vllm` and a fresh output directory using
the isolated **vLLM 0.31.0** environment. This phase loads one mixture through
LoRARequest and generates four tokens for each prompt. This is a loadability
smoke test; it does not measure speculative acceptance length.

The real phases have **not run** while paused. Ten CPU tests cover the mixture
and acceptance helper logic, but do not establish real PEFT/vLLM integration.
Both real phases must pass before merge/review.
