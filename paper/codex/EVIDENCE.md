# Claim-to-source map

Paths below are relative to the research repository root. Machine-readable files retain full precision, uncertainty, sample counts, source paths, and hashes. All measurements remain pilot. The paper uses rounded values; no missing outcome was fabricated.

| Paper content | Source | Interpretation |
|---|---|---|
| Abstract; Table 1 R1 three-seed SPEED; 59.9%/71.7% recovery | `artifacts/D51_reports_20261009_1627/snapshot-20261009_192136/results.json`, records target=0/budget=16000, focal official | Paired seed/query bootstrap; official release's own reuse denominator |
| Table 1 Nemotron; robustness table | Same D51 JSON, target=1; focal official/production | Nemotron single seed; no oracle recovery |
| Full MATH-500 and independent/dedicated controls | `artifacts/D52_analysis_20261010_0020/math500/results.json` | 500 queries, seed 0; MATH-64 overlaps |
| SPEED independent 1B / dedicated baselines | `artifacts/D50_final_20261009_1451/results.json` | Frozen raw-recomputed records; K=4 |
| Figure 4 and timing appendix | `artifacts/D52_analysis_20261010_0020/timing-r1/snapshot-20261010_001805/results.json`; corresponding `timing-nemo/snapshot-20261010_001811/results.json` | Warm panel time, 3 processes × 3 repeats; fresh target-only controls |
| Measured repair cost | `reports/P3-primary-official-20261010.md`; `artifacts/D52_analysis_20261010_0020/consolidated/cost.md` | Seed 0, target response generation + training; no claim about unobserved dedicated-model cost |
| Figure 2 population retention and filter counts | `reports/P1-typed-population-20261008.md`; `artifacts/P1_typed_20261008_1515/analysis-v3/results.json` | 21 eligible post-trained checkpoints; checkpoint/query hierarchical bootstrap; not the archived 174-model population |
| Fixed-prefix feature/policy effects | `reports/P2-crossover-20261008.md`; `artifacts/P2_crossover_20261008_0348/full64/report/results.json` | HF diagnostic on 64 sequences per target/origin, not online p1 |
| Figure 3; component/source/budget tables | D50 JSON above | RedHat initialization; source and step budgets explicit; nulls retained in appendix |
| DFlash extension | `reports/P4-DFlash-repair-20261008.md`; `artifacts/D48_analysis_20261008_1528/snapshot-20261008_154917/results.json` | 256 examples, 300 steps, single seed, K=10 |
| Probe results | `reports/P5-triage-pilot-20261008.md`, final query+checkpoint uncertainty addendum | 16/112 disjoint query split; retrospective, no held-out-checkpoint claim |
| Nemotron reasoning toggle | `reports/P2-nemotron-toggle-20261008.md` | Same weights, documented system toggle; matched raw queries |
| Training objective and parameter scope | `followspec/family_repair.py`; training configs/parameters under `artifacts/FIX24_20261009_1420/` | Native KL/TTT3; fc only or full draft scope; frozen target and embeddings |
| Generic training queries | `artifacts/P3_D49_20261008_1800/selection.json`; `artifacts/B4_public_resolved_20261005/manifest.json` | Alpaca instruction/input fields, pinned revision, CC BY-NC 4.0; original answers discarded |
| Bibliography | `sources/bibliography-metadata.json` plus primary Alpaca and EAGLE 3.1 pages | Titles/authors/years checked against original arXiv metadata; primary-source citations |

The appendix's per-depth table is re-derived by `additional_tables.py`, independently of the project metric modules. It checks raw accepted/drafted counts, target-rendered prompt hashes, A40, frozen code, engine, K, batch, and greedy settings. Its p1, tau, and mean-length values match the existing focal summaries within 1e-10. The source raw-file hashes and conditional-depth intervals are in `data/raw-verification.json`.

The portable source ZIP excludes experiment data and local absolute paths. This repository folder retains the full audit trail for the owner.
