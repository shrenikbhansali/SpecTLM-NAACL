# Paper numbers and ledger tracing

Use `python -m paper.verify_numbers generate --manifest MANIFEST.json --output NEW_DIR`
to create `numbers.tex` and `numbers.trace.json`. Generation never overwrites an
existing directory. The operator installs reviewed, real outputs into
`paper/numbers.tex` and its accompanying trace, then includes that file from the
shared preamble. The current skeleton intentionally contains no empirical values.

A manifest has an explicit `synthetic` boolean, `numbers`, optional `exhibits`,
`runs`, and `results`. Paths are absolute or relative to the manifest directory.
For example (replace every illustrative path with a real reviewed source):

```json
{
  "synthetic": false,
  "numbers": [{"macro":"ResultMedianGain", "source":"aggregate.csv",
    "where":{"arm":"FS","workload":"own"}, "column":"median_gain", "format":".3f"}],
  "exhibits": ["figures/method_table2/method_table2.json"],
  "runs": {"RUN_ID": {"artifact":"../artifacts/RUN_ID", "ledger":"../ledger/EXP-ATL-NNN.md"}},
  "results": ["results.tex", "analysis.tex", "appendix_results.tex"]
}
```

Each selector must identify exactly one CSV data row. A row must contain `run_id`
or a JSON list in `run_ids`, retaining every contributing source. No aggregate
is recomputed by choosing a new estimator: the checker verifies transcription
from the explicit aggregate cell. B12 table sidecars import all table macros;
values are independently reread from the original CSV and checked against the
sidecar, including run IDs and file hash. Consolidate those macros here instead
of also loading the exhibit's separate `.numbers.tex` file.

Each run mapping requires an existing artifact with parseable `config.json` and
`results.json`, no failure marker, and an assigned EXP-ATL Markdown ledger entry
with all required fields. The ledger must cite that exact artifact path in
backticks; brace lists such as `/path/{base,child}/` are supported. Relative ledger
artifact paths resolve against the manifest directory. `invalid` and `superseded`
entries fail. Pilot and diagnostic entries can be checked during drafting;
`--require-paper-grade` additionally enforces owner promotion before final use.
The checker never promotes entries or judges scientific validity.

```bash
python -m paper.verify_numbers verify --manifest MANIFEST.json --output NEW_DIR --report NEW_REPORT.json
python -m paper.verify_numbers verify --manifest MANIFEST.json --output NEW_DIR --require-paper-grade
```

Verification exits nonzero on a changed number, extra/missing/duplicate macro,
changed CSV (even below rounding precision), changed sidecar, ledger or run
config/results, missing provenance, or hard-coded number in a selected result
source. Result `input`/`include` files are followed recursively. Citation/reference
IDs, layout paths and comments are excluded from the numeric scan; visible
percentages, sample sizes and literal numbers in prose/math/tables are flagged.
Definitions/overrides inside results and undefined `Result*`/`Exhibit*` macros
are rejected. This is a conservative source lint, not a full TeX interpreter;
list every result-bearing file explicitly, and review the reported scan coverage.
Regenerate a new bundle after a legitimate source or ledger change.

Synthetic tests require `--allow-synthetic`, remain visibly labeled and belong
under `artifacts/`, never in the submission. Empty skeleton verification provides
no empirical evidence. Do not fabricate macros to populate an empty draft.
