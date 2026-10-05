# FollowSpec EAGLE-3 builder state

Backend source is pinned by `backend.lock.json`; `requirements.lock` records
`.venv-followspec-clean`. The environment passed pip check. Native loss imports
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
and B5 feature/decoded-mask acceptance evidence. No real B5 manifest exists yet.

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

**Not ready for review.** Nineteen CPU tests passed. The native full-model
fixed-batch equivalence, 64-sample overfit and exported-checkpoint B2 run still
need execution. The training launcher and feature dataset are unverified on
real B5 data. Checkpoint state-key preservation in a toy fixture is not proof
of vLLM loadability. The pause has now been lifted by the owner; resume these
checks after the higher-priority B2/B3 acceptance work and B5 data are ready.
