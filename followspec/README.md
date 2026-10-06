# FollowSpec EAGLE-3 builder state

Backend source is pinned by `backend.lock.json`; `requirements.lock` records
`.venv-followspec-clean`; `online-requirements.lock` records the A40 online
acceptance environment `.venv-transport`. Both passed pip check. Native loss imports
resolve to the pinned source. The historical and B2 evaluation environments
were not modified.

The owner approved normalizing p_child within the selected top-k set on
2026-10-05 (MASTER D-11). `delta.py` implements that centered variance. Selected
raw logits are mathematically equivalent to log probabilities here: each
log-normalizer is a per-prefix constant that centering removes. Only the delta
base branch is detached; the beta-weighted native base anchor keeps gradients.

`eagle3_extension.py` installs paired forwards on the native model, gathering
only selected logits at every TTT step. No model parameter names or export
methods change. Child/native, base/native, delta and per-step terms are logged
separately. Default behavior requires explicit child/base projected targets;
using a shared verifier head requires positive evidence in the B5 manifest.

`paired_data.py` defines the B5/B6 boundary: each safetensors sample has shared
input_ids/loss_mask and paired auxiliary/final hidden states, plus projected
target logits when needed. The native one-token shift is applied to both sides.
Native packing is reused; truncation and scoring across document boundaries
are rejected. Native default uniform noise (0.05) uses the same draw for both
feature tensors to preserve the paired difference. Native model master weights
stay float32; training autocast is bf16.

All four JSON presets must resolve to the same initialization revision, exact
token budget and optimizer-step count before training. `configs.py` rejects
unintended differences. Null fields are deliberate blockers, not guessed values.
Training data manifests require per-sample target IDs, hashes, split, length,
feature file SHA, allowed bank/mixture targets, forbidden evaluation hashes,
and B5 feature/decoded-mask acceptance evidence. Acceptance-only token manifests
have been exercised; full matched production manifests are still B5 work.
For online capture, see [ONLINE_TRAINING.md](ONLINE_TRAINING.md).

The operator launch command is:

```sh
python -m followspec.train_eagle3 \
  --configs /resolved/FS.json /resolved/MVD.json /resolved/PO-D.json /resolved/PO-T.json \
  --arm FS --seed 0 --manifest /audited/B5/manifest.json \
  --base-snapshot /pinned/local/llama-snapshot \
  --output /new/artifact/path --dry-run
```

`--dry-run` prints the resolved plan without model loading or output creation.
Real execution checks pause markers, backend revision, code cleanliness, data
acceptance, actual token count and actual packed step count. It delegates
optimization/checkpointing to native Trainer, preserves checkpoints, and logs
config, source sample records, metrics, results/failures and a ledger draft.
Use torchrun for distributed execution only after the single-process acceptance
path is validated. No large training run has been launched by this builder.

**B6 native acceptance passed and was independently reproduced by the operator.**
The core plus artifact ownership regressions has46 tests. A refused retry into
an existing output directory leaves every artifact unchanged; new-run errors
are recorded only after that launch acquires its output directory.
Native fixed-batch λ0 composition has absolute error0.0. The released drafter
overfit64 real bank responses in three native optimizer steps: loss12.5937 to
9.7890, frozen teacher and finite drafter gradients, unchanged state keys.
The native exported checkpoint produced a valid five-prompt B2 cell on pinned
vLLM0.31.0. See `notes/B6.md` and `artifacts/B6_acceptance_20261006` for evidence.

The overfit test used8192 padded tokens but only5249 actual sequence tokens.
Peak allocation42.44GiB and a recovered allocator warning leave tight A40
headroom; check full batches and longer responses before production. The test
used one bank adapter and one acceptance seed, not the complete mixture/data
recipe. B5 production budgets, mixture validation and owner defaults remain
separate requirements. No production M3 run has been launched.

# B3 mixture acceptance

`mixture.py` writes exact concatenated PEFT factors with scaling one. It never
loads a base model. CPU tests cover algebra, differing ranks/modules/dtypes,
rsLoRA and configured vLLM rank caps.

`verify_mixture.py` is the original real-model acceptance driver. It has two
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

Both real phases ran after the pause was lifted. The original bf16 mixed-vs-dense
checks failed (maximum errors0.3125/0.375/0.3125), while one-hot/zero were exact
and native vLLM generation passed. Those failures remain in the original artifacts.

MASTER D-20 now authorizes fp32 maximum absolute error strictly below1e-4 on
all seven16-prompt cases plus vLLM multi-LoRA loadability. Apply that recorded
rule with `python -m followspec.mixture_decision --evidence-root ORIGINAL_ROOT
--output NEW_REPORT`. It recomputes the threshold from every per-prompt record,
checks source pins/hashes and case completeness, and reports the original bf16
failure beside the new decision. It never rewrites or relabels old artifacts.
The fp32 diagnostic command is `python -m followspec.diagnose_rounding
--launch-record ORIGINAL_ROOT/launch.json --float32-only --output NEW_FP32_RUN`;
use a fresh path for the operator's independent reproduction. Twelve CPU tests
cover the builder, driver and D-20 checker. No throughput claim follows from
these numerical/loadability checks.
