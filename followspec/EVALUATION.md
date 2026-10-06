# Held-out evaluation (B7)

`python -m followspec.evaluate plan --input SPEC.json --output PLAN.json
--artifact-root NEW_ROOT` creates a list of commands; it never submits jobs.
The operator runs those commands through preflight on the authorized cluster.
Each command has a fresh per-cell `VLLM_CACHE_ROOT` and immutable output path.
Never run training-bank targets through this held-out driver.

The spec has `base_id`, pinned `base_revision`, `K` (2/4/8), `checkpoints`
and `targets`. A checkpoint contains `arm` (FS/MVD/PO-D/PO-T/Frozen), training
`seed`, `model_id`, pinned `revision`, and optional `method` (eagle3).
A target contains `model_id`, pinned `revision`, `pool` (test/base), optional
local `adapter`, and `workloads` mapping each label to a B4-rendered JSONL.
Include an explicit base target for parent-retention evidence. Use the same
workload labels in parent and held-out evaluation. Checkpoint file hashes
are captured by B2 for local exports.

Pair A00/A10 and A01/A11 on the same rendered prompt file, generation seed
and settings. Each training arm needs three matched training seeds;
`evaluation_seed` defaults to 0 and is separate from the training seed.
Repeat the same Frozen checkpoint for each seed slot. Copies of its results
are not independent training runs; parent TOST pairs trained seeds against
their frozen controls. Its degrees of freedom are training seeds minus one.

After the operator completes and validates the cells, pass the plan (with
actual `run_dir`s and run IDs) as the aggregation index:

```bash
python -m followspec.evaluate aggregate --input COMPLETED_INDEX.json --output NEW_REPORT_DIRECTORY
```

The loader recomputes macro acceptance length, including bonus tokens,
from B2 per-step accepted/drafted counters. It rejects incomplete matrices,
duplicate IDs, inconsistent checkpoints or targets, unmatched prompts and
settings, failed/dirty cells, or an engine other than the pinned vLLM 0.31.0.
Results include per-seed CSV, per-derivative seed-averaged A00/A01/A10/A11,
FS-minus-control median/mean gain, a 10,000-resample paired derivative
bootstrap interval for the median, win rate, and worst-decile retention
(mean of the lowest ceil(10% of n) ratios A11/A00).

Parent TOST applies the fixed 2% relative margin to paired training-seed
acceptance changes; it reports both one-sided p values and the 90% interval.
The report lists numerical criteria separately for every K/workload, along
with n and source run IDs. It does not select the most favorable group or
decide paper framing. The owner must specify the primary Gate 3 comparison
and review `GATE-3.md`; the operator publishes it to `reports/GATE-3.md`.

Every aggregate carries an input-index hash, code commit and source run IDs.
Synthetic acceptance fixtures are tests only, never paper evidence.
