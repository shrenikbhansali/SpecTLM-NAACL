# Online EAGLE3 training on heck

MASTER §3.2 / D-19 places method work on A40s while ICE is unavailable.
The implementation uses one frozen base model, one resident bank adapter and
online child/base capture. Response-token files remain on disk; dense paired
features do not. Run one training process per A40 with data-loader workers0.

B5 provides rendering, matched response controls, arm manifests and the online
feature provider; B6 provides the native trainer. Bounded bank and mixture
checks establish the implementation, while M1/M2 must produce the admitted
mixture registry and complete production corpora. Production requires B5/B6
operator verification and audited, matched arm manifests. B3's
mixture builder passed D-20. Mixtures need immutable source/file provenance and
the shared-training-general perplexity check before production admission.

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
   The owner approved paired response trimming on 2026-10-06. Before assembly,
   run `python -m followspec.paired_responses --child-run CHILD --base-run BASE
   --child-id BANK_ID --output NEW_DIRECTORY`. It verifies exact shared prompts
   and generation controls, then writes child/base reference lists and a log
   of every pair (including zero trims). Both lists retain the shorter response
   prefix, keep every prompt token, and refer to unchanged original files.
   Use child references for FS/PO-T; base references for PO-D. MVD bank sources
   can use the same policy, but its overall quotas still need the approved recipe.
   The loader recomputes each retained length from both hash-pinned originals;
   hand-edited lengths or changed peers are rejected. All four arm totals must
   still match; pairing does not infer MVD resampling or a final token budget.
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


## Mixture inputs after D-20

Add each B3 mixture as `kind: mixture`, its local `path`, `source_ids` (two or
three registry bank IDs in concatenation order), SHA256 of all three files
(`adapter_config.json`, `adapter_model.safetensors`, `mixture_manifest.json`),
and `revision` equal to the mixture-manifest SHA256. This content revision is
local provenance, not a Hub commit. The provider checks the original sources,
weights, scale and rank cap; nested mixtures and test targets are refused.
MVD always refuses a mixture target.

Use `--target-registry REGISTRY.json` with `followspec.render_inputs`,
`followspec.generate_responses`, or `atlas.generate_magpie` for a local mixture.
Mixtures inherit the pinned base tokenizer/template. Generate paired base
responses using the same rendered inputs, prompt target, registry and rank cap.
The ordinary public-bank flags and their defaults remain unchanged.

Production registry entries require an `admission` object naming a report
folder and the SHA256 of its config/results. Build the report with
`python -m followspec.mixture_targets --registry REGISTRY --mixture-id ID
--mixture-filter-run RUN --bank-filter-runs BANK_RUNS.json
--pool-manifest FROZEN_POOL.csv --output NEW_REPORT`.
`BANK_RUNS.json` maps every frozen bank ID to its corresponding filter run.
Run the existing `atlas.filter_pool` on one shared128-query reference selected
from the B4 public **training general** pool for the bank and each mixture.
Its `--adapter`/`--adapter-revision` inputs support local mixtures. The A2
SPEED reference cannot stand in for this training-general check. Admission
recomputes PPL from all per-prompt records and requires mixture PPL no higher
than the worst real bank child's; all reference tokens, model pins and scoring
controls must match. A changed report, source, or failed bound is rejected.

Only bounded acceptance paths may use an explicitly `acceptance_only: true`
mixture before this PPL step. They remain acceptance-only in generated data;
the production trainer refuses them. `FrozenAdapterBank(...,
allow_acceptance=True)` is reserved for those bounded native tests. It does
not change the production launch default.

The bounded `followspec.tests.native_trim_check --mixture-id ID` mode checks
five mixture examples in FS/PO-T/PO-D, fresh child/base features on three
examples, exact zero-update equality, and mixture → bank → mixture restoration.
It validates the three paired manifests with `validate_paired_arms`; it makes
no MVD mixture or four-arm budget claim. The default bank check still requires
all four arms. Both modes require the recorded decoded-string/mask audit and
immutable source hashes before loading a GPU model.

Before resolving M3 presets, run the CPU-only native sampler audit:

```sh
python -m followspec.audit_batches \
  --manifests FS.json MVD.json PO-D.json PO-T.json --replicas 1 \
  --output /absolute/path/to/new/batch-audit
```

It rechecks source hashes and paired views, rejects cross-arm train/validation
leakage, verifies every sample appears exactly once per epoch across all ranks,
and requires identical actual token budgets and optimizer steps across all arms
and preset seeds. Long samples are rejected before the sampler can truncate them.
The output records every batch's sample indices. It changes no presets, quotas,
source files or acceptance flags. `--acceptance-smoke` permits only at most64
acceptance-only records per arm for builder checks; its output cannot establish
production readiness. A failing audit requires explicit data assembly changes;
it never silently drops, repeats or truncates samples to make counts match.

D-26's longer pre-M3 check uses `followspec.overfit_acceptance --epochs 30`
with the same audited64-example inputs. It is exactly30 optimizer steps on
one native batch; default acceptance remains3 steps and production remains
one epoch. The earlier3-step run used8.6GB for its checkpoints, so budget
roughly86GB for30 checkpoints. Preserve every run/checkpoint; use a fresh
output directory. This check still does not establish capacity on long or
fully occupied batches.

The separate full-response capacity check uses
`generate_responses --acceptance-smoke --acceptance-limit 64 --capacity-smoke`.
It still requires exactly64 distinct training queries and marks every response
acceptance-only, but uses the production512-token response cap. These records
cannot enter M2 production manifests. Inspect the first5 decoded strings and
masks and record the normal audit before running
`overfit_acceptance --capacity-smoke` with those sources. This mode runs one
native epoch with at most8 optimizer steps and at most65536 actual sequence
tokens, retaining the8192 batch, released initialization, noise, optimizer and
loss settings. It requires at least one response reaching512 tokens. The
ordinary5/64-query generation cap remains64 response tokens, the default
overfit remains3 epochs, and D-26 remains30 steps. Capacity results record
actual tokens in each batch as well as padding; they do not certify every
possible production prompt length or mixture rank. No sweeps are launched.

The optional `--release-grad-before-forward` flag (trainer and bounded overfit
checker) clears previous-step gradients before the next training forward. The
pinned native Trainer normally clears them after that forward; it does not
accumulate gradients. This changes tensor lifetime only: native backward,
clipping, optimizer and scheduler stay unchanged. Evaluation retains the final
training gradients for acceptance inspection. Record the flag and use the same
setting across all matched arms. Original default is unchanged.
