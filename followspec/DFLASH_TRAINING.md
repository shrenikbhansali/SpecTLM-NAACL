# B10 implementation status

The DFlash extension is under acceptance and is not a production training path.
`install_follow_spec_dflash` wraps the pinned native forward and backbone. The
base pass replays the child's random anchor draw, then restores the RNG state
after that draw. Both passes must return identical indices and masks. Native
block attention, KL, decay and checkpoint keys are preserved. The delta uses
child top-k probabilities normalized within that set and averages over all
native valid masked positions; per-position diagnostics are logged separately.
Its base-feature branch is detached only inside delta, preserving gradients
from the separate native base loss.

DFlash uses raw sequences. The pinned native training CLI applies `shift_batch`
to EAGLE-3 only. `prepare_block_sample` therefore preserves each raw token,
feature, label and mask. With `sample_from_anchor=False`, target logits at an
anchored block index come from the previous sequence position; the anchor
itself has zero loss. Explicit child/base projections follow that same rule.
Use `build_manifest(..., sequence_layout='dflash_raw')` for DFlash. It counts
raw sequence tokens; the dataset rejects a transform that shifts them. Legacy
EAGLE manifests keep shifted accounting. Never mix these units in a comparison.

`load_presets(algorithm='dflash')` selects the released Llama DFlash checkpoint,
its block size10, native512 anchors, gamma4 and native fixed exponential decay.
All four arms retain the same AdamW/LR/8192-token batch/seed controls. The common
`train_eagle3` entry point dispatches from the explicit config algorithm; it
refuses DFlash with EAGLE-layout or offline manifests. `overfit_acceptance
--algorithm dflash` uses exactly64 bounded responses and the same native
defaults; its before/after probes replay identical anchor RNG draws. Production
remains blocked until the overfit and native export acceptance checks pass.

`load_presets(family='qwen3')` selects the released Qwen3 EAGLE-3 initialization
and retains every other starting setting. The bounded overfit entry point
accepts `--family qwen3` and checks the target and verifier architecture family.
Qwen3 response inputs must use non-thinking rendering; the B10 bounded input
bundle explicitly verifies the empty `<think>…</think>` prefix on all64 queries.
Neither family presets nor CPU plumbing tests establish B10(a)–(g) GPU acceptance.

Teacher top-k extraction now selects in the original bf16/fp16 representation
before casting the selected values to float32; base values are gathered before
casting too. Float64 inputs retain float32-before-top-k behavior. This removes
a5120×128256 float32 temporary at the native512-anchor layout. The pinned A40
check compared values and indices exactly on random bf16/fp16, tied and all-zero
inputs; all passed. It changes no loss formula, anchor count or optimizer.
