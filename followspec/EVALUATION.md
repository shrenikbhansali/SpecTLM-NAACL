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

## Production M3-to-M4 handoff (FIX-9)

Once all twelve runs in a `followspec.training_jobs` stage complete, use:

```bash
python -m followspec.evaluation_jobs --training M3_JOB_STAGE \
  --targets TARGET_SPEC.json --python /path/to/pinned-vllm/bin/python \
  --code-repo CLEAN_TAGGED_MAIN_CHECKOUT --output NEW_M4_STAGE
```

`TARGET_SPEC.json` has a `targets` list in the B7 format above, including an
explicit `model_id: "base"` entry. Full-weight derivatives may additionally
supply `snapshot`; LoRA derivatives must supply `adapter` and `max_lora_rank`.
All workload files must contain exact `rendered_token_ids`. Base workload labels
must cover the derivative labels so parent-retention cells exist. Record own-domain
unavailability in the input spec; never silently remove a derivative based on its
results. Use the frozen test pool and separately identified ledger children.

The handoff checks actual training configs, seeds, pins, completed budgets/steps,
memory flags and nonempty native exports before writing any output. It records
checkpoint hashes. It emits `jobs.jsonl`, `index_k4.json` (all four trained arms
and Frozen), and `index_k2_k8.json` (FS and Frozen only, per M4). All cells use
exact input tokens, greedy seed 0, 512 new tokens, batch 8, memory utilization
0.70 and a fresh compile directory, matching the sprint's atlas cell settings.
Both sides of every LoRA pair enable LoRA with the same rank capacity. H200
training permission is never included in these evaluation jobs.

Run both actual cell and launcher preflights, then dispatch on A40s. A nonempty
export is only a planning prerequisite: its first real vLLM cell still has to
establish loadability. Pass the completed K4 index to B7 aggregation. K2/8 contain
only FS/Frozen and must stay separate from the complete-arm Gate 3 aggregator.
The owner still chooses the primary workload and makes the Gate 3 call; emitting
jobs or reporting numerical criteria does not make that decision. The stage
records NumPy/SciPy versions for the CPU planning/analysis environment.
