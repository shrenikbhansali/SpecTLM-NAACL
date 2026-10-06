# Deterministic exhibits (B12)

`python -m paper.exhibits --catalog` lists every MASTER §11.3 figure,
table and appendix family for both framings. No framing is chosen by the
renderer. Supply an explicit JSON list of exhibit specifications:

```json
[{"id":"atlas_figure2","source":"paired_cells.csv","x":"A00","y":"A10","series":"type","xlabel":"A00","ylabel":"A10","synthetic":false}]
```

Each CSV row must have `run_ids` (a JSON list of nonempty run IDs) or one
`run_id`. Retain all contributing source IDs in aggregate rows, including
controls and training seeds. The renderer never fits predictors, selects
models, chooses favorable workloads, or turns an unsupported statistical
choice into a default. Atlas Table2 requires the separately specified and
validated cross-validation results. Proposition1 curves must be supplied
with their input-source run IDs. Uncertainty bounds, where appropriate,
come from the aggregate's explicit `low` and `high` columns; the renderer
does not manufacture intervals from pooled observations.

Use `x`, `y`, optional `series`, optional `panel`, and optionally both `low`
and `high`. `points` and `line` support numeric or categorical x axes.
`distribution` draws per-group boxes (quartiles; whiskers1.5×IQR), records
all computed box values and every contributing source row. Transport data
require `diagnostic=true` per row and visibly carry the diagnostic label.
Tables specify `columns`. Numeric table cells become LaTeX macros in an
accompanying `.numbers.tex`; include this file before the `.tex` table.
B13 will consolidate and verify these definitions against source aggregates.

```bash
python -m paper.exhibits --manifest EXHIBITS.json --output paper/figures/NEW_VERSION
```

Each exhibit gets PDF, PNG, a source CSV copy and JSON sidecar; tables also
get TeX and macro definitions. Sidecars retain source-file hash, source run
IDs, original row values, any derived box statistics, rendering-code hash,
commit and package versions. Axes ticks/legend labels are display metadata,
not empirical claims. Tables display six significant digits while full
source values remain in the sidecar. Output directories must be new;
previous artifacts are never overwritten.

PDF dates are suppressed, fonts/styles are fixed, and PNG metadata is
constant. Byte-identical reproduction assumes the pinned rendering stack
in `paper/analysis-requirements.txt`; regenerated code/inputs legitimately
change the provenance sidecar. Run the operator check twice on identical
inputs and compare all output files. Synthetic acceptance inputs must set
`synthetic=true`, are visibly labeled, and belong under `artifacts/`, never
in a paper results directory. Missing provenance and nonfinite values fail.
