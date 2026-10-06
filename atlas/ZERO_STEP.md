# D-32 zero-step observations

A request with no speculative verify step has undefined acceptance length.
The cell harness saves its completion, empty per-step arrays, zero totals and
`zero_step: true`. Its acceptance length, acceptance rate and position rates
are JSON null. Missing engine metrics or inconsistent histograms still fail.
Normal requests retain their existing metric values and add `zero_step: false`.

`results.json` reports `n_total`, `n_zero_step`, and `n` (the number entering
the macro). Thus `n + n_zero_step = n_total`. An all-zero cell completes with
`n = 0`, null macro and null interval; it cannot estimate a comparison.
The original config `n` continues to count all requested prompts. Historical
all-valid cells without the new fields remain readable.

Never subtract or divide independent cell macros when zero-step prompts differ.
For an atlas pair, run:

```
python -m atlas.paired_cells --parent A00_DIR --child A10_DIR --output NEW_PAIR_DIR
```

It reconstructs every metric from counters, checks settings, drafter and prompt
identity, and computes both means over the same nonzero-step prompt IDs. It
writes paired counts, excluded IDs, the difference and retention, source hashes
and a pilot ledger draft. No shared valid prompt means the comparison is
undefined: the command refuses it. Include the paired count and excluded count
per derivative in operator tables. Cell-level intervals describe their own
valid subsets and are not intervals for the paired difference.

The held-out `followspec.evaluate` loader retains every prompt, including zero
observations. A00/A10 and A01/A11 use their respective pairwise intersections;
FS/control gains, A11/A00 retention and trained/frozen parent TOST each use the
intersection of the two cells in that comparison. Seed averaging and derivative
bootstrap settings are unchanged. Per-derivative CSV rows retain each pair's
values, counts and excluded IDs per seed; summary.json also records comparison
and parent-retention exclusions. The displayed A11 and A00 columns belong to
their respective target-shift pairs, so their quotient need not equal retention
when the valid subsets differ; use `pairing_retention` to reproduce that ratio.
An empty intersection blocks the report, rather than silently dropping a
held-out derivative. No zero-step observation is assigned a fabricated AL=1.

Re-run failed A4/A7 cells into new paths from a fresh tagged main checkout.
Preserve the original failures. Existing successful cells need no numerical
rerun: the counter formulas and nonzero means are unchanged. The original B2
golden checker still requires 128 valid observations; that gate is not relaxed.
