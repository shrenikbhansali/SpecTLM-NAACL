# Online EAGLE3 training on heck

MASTER §3.2 / D-19 places method work on A40s while ICE is unavailable.
The implementation uses one frozen base model, one resident bank adapter and
online child/base capture. Response-token files remain on disk; dense paired
features do not. Run one training process per A40 with data-loader workers0.

The B6 core includes the native trainer and accepted token reader/provider.
The rendering CLI, matched response controls, arm-set assembler and full data
recipe below are separate B5 work, currently on codex/B5 and unmerged.
Production requires B5/B6 operator
verification, the final pool/recipe decisions and matched arm manifests. B3's
mixture validation is unresolved; the current bank provider refuses mixtures.

## Inputs and audit

1. Generate raw training queries with B4, including full SPEED/evaluation
   exclusion checks. Accepted bank-candidate generation is allowed before the
   final cutoff under D-19. Only the operator launches production jobs.
2. Render each child's queries once with `followspec.render_inputs`. Pass its
   `prompts.jsonl` as `--rendered-inputs` to both child and PO-D response jobs.
   Keep generation seed, LoRA capacity, engine, hardware and sampling settings
   matched. This matters when the child's chat template differs from the base.
3. `followspec.generate_responses --allow-a40-production` retains the specified
   512-token limit, temperature0.6 and top-p0.95. The separate acceptance mode
   caps responses at64 tokens, marks all outputs acceptance-only, and cannot
   feed production training.
4. Build arm source-reference manifests with `followspec.token_data`. Every
   source has config/results/records hashes. FS and PO-T reuse identical token
   records; PO-D has base-generated responses on the same rendered prompts.
   Counts distinguish shifted sequence tokens from assistant loss tokens.
   Unequal arm budgets are rejected. No trimming/resampling policy is inferred.
5. Before resolving presets, audit actual counts, native sampler steps, parent
   share, per-child Magpie/general quotas, forbidden prompt hashes, train/val
   disjointness, and five decoded samples/masks per arm. Set audit status only
   with evidence. The assembler deliberately leaves `data_acceptance_passed`
   false and `optimizer_steps` null until these requirements are satisfied.

The adapter registry maps bank IDs to `kind: bank`, pinned `revision`, local
`path` and `files_sha256`. B1 staging and accepted A2 outputs establish the bank
identity. The provider hashes every newly selected adapter, unloads the old
adapter and freezes all target parameters, including after PEFT base-context
restoration. Loader failures abort the step rather than returning old features.

## Operator launch shape

Use a clean, immutable checkout and a new artifact directory. Resolve all four
presets together: same initialization revision, token budget, optimizer steps,
seed set, optimizer and native batch size. The committed draft presets leave
unknown values null. Check the dry run before a real invocation:

```sh
python -m followspec.configs --configs FS.json MVD.json PO-D.json PO-T.json
python -m followspec.train_eagle3 \
  --configs FS.json MVD.json PO-D.json PO-T.json --arm FS \
  --manifest /absolute/path/to/FS/manifest.json \
  --base-snapshot /absolute/path/to/pinned/base/snapshot \
  --drafter-snapshot /absolute/path/to/pinned/drafter/snapshot \
  --allow-a40-production --seed 0 --output /absolute/path/to/new/run --dry-run
```

After the launch requirements pass, the operator uses the same command without
`--dry-run`. Use the pinned native backend in `backend.lock.json`; the acceptance
environment and exact package versions are recorded with each run. Production
uses native attention/TTT/batching and fused KL. The small fixed-batch acceptance
uses explicit eager attention and is labeled separately. Its memory footprint
does not establish full-batch training capacity.

`training_metrics.rank*.jsonl` contains separate child, base, delta and combined
loss terms. Config, source hashes, per-prompt references, final results and a
ledger draft stay with the run. Native checkpoints preserve the architecture
and state-dict names. Every exported checkpoint still needs B2 inference
validation on pinned vLLM0.31.0; an overfit result is no transfer claim.

## Bounded acceptance commands

`followspec.tests.native_eagle_online_check` checks λ0 composition and backward
on five responses from the released checkpoint. `followspec.overfit_acceptance`
requires exactly64 distinct training responses, each at most64 new tokens,
acceptance-only source provenance, and a recorded five-sample mask audit. It
runs three fixed overfit epochs, retaining native8192 batching and the starting
loss/optimizer controls. Its before/after probe reuses training data with no
feature noise. These are builder acceptance runs, separate from M3.

Every launch/capture/forward honors the active pause marker. Failed runs and
source artifacts remain intact; retries use new directories.


D-26's longer pre-M3 check uses `followspec.overfit_acceptance --epochs 30`
with the same audited64-example inputs. It is exactly30 optimizer steps on
one native batch; default acceptance remains3 steps and production remains
one epoch. The earlier3-step run used8.6GB for its checkpoints, so budget
roughly86GB for30 checkpoints. Preserve every run/checkpoint; use a fresh
output directory. This check still does not establish capacity on long or
fully occupied batches.
