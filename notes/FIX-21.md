# FIX-21: complete matched D-39 K8 stress follow-up

## 2026-10-07T19:32:47.085974-04:00 — codex-1 — Claim / acceptance first

D-39 already authorizes K4/K8 comparisons consistently across arms. Existing secondary planner covers only FS/Frozen, so build a separate operational K8 plan for the full fixed six-condition code/math panel: 0.1 plus lambda0/.03/.3; reuse only identical K8 controls across variants. No target selection, training, seed repeats or evaluation implementation changes.

Acceptance: derive jobs from sealed K4 sources with only K, output identity and compile-cache path changed; prove reverse restoration of every other argument/record field. All four arms and Frozen present in each of four 70-cell indexes; exactly112unique K8jobs, no K4controls reused in K8pairing. Existingfrozen metrics validate per-prompt records and paired uncertainty, preserving all six correlated conditions. All cell/launcher dryruns pass; append to sole dispatcher after K4feasibility work. Each variant reports automatically when complete.

## 2026-10-07T19:36:45.105980-04:00 — codex-1 — CPU acceptance

Tests first (missingmodulefailure `/tmp/FIX21-first.log`). Operational derivation changes only K4→K8, run/output/cache identity, preserving complete original commands and source records. All four arms/Frozen and all4lambda indexes enforced; only identicalK8controljobs shared. Automaticreports call original frozen B7load_measurements/paired_values plus existingD39pairedprompt uncertainty; regressions retained. Added explicit comparison-target mismatch guard. `python -m pytest ops/tests followspec/tests -q`:328passed26.95s; additional diagnostic pairing/regression test:4targetedpass. Frozen metric/decoding files unchanged. Actual112-job preparation/preflight next; noGPUsubmittedyet.
