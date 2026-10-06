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
Do not feed the current EAGLE online dataset's shifted-length budget directly
to DFlash: a raw-layout manifest, sampler accounting, trainer configuration and
released-checkpoint acceptance are still required.

`load_presets(family='qwen3')` selects the released Qwen3 EAGLE-3 initialization
and retains every other starting setting. The bounded overfit entry point
accepts `--family qwen3` and checks the target and verifier architecture family.
Qwen3 response inputs must use non-thinking rendering; the B10 bounded input
bundle explicitly verifies the empty `<think>…</think>` prefix on all64 queries.
Neither family presets nor CPU plumbing tests establish B10(a)–(g) GPU acceptance.
