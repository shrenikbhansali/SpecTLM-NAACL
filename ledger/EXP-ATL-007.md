### EXP-ATL-007 — A6 covariates vs atlas retention (descriptive Spearman)

**Landed:** 2026-10-07 · NAACL sprint, atlas A6.

**Status:** pilot (descriptive; no model selection; prediction evaluation is an owner step).

**What / why.** Relate per-derivative covariates (B8 `atlas.covariates`: child‖base KL on the child's own generations, EAGLE-3 tap feature displacement,
relative weight-update norm, LM-head change, outside-drafter-vocabulary mass shift) to matched retention from EXP-ATL-005.

**New in this experiment.** Operator analysis script only (`$WS/artifacts/A6_analysis_20261007/analyze.py`). Joins A6 cell results (125 original + 18 OOM
retries) to EXP-ATL-005 per_derivative.json by (base, model_id). Two targets per covariate: signed retention, and −|log retention|
(closeness to 1, i.e. magnitude of change in either direction).

**Artifacts:** `$WS/artifacts/A6_analysis_20261007/` (analyze.py, results.json).

**Config + results.** n = 80 Llama, 61 Qwen3 derivatives with covariates. Missing: 15 loader gaps (FIX-8, mostly FP8/quantized), osiris (broken adapter),
and general-only derivatives (no own-domain prompts, so no A6 sequences). Spearman ρ (p):

| Group | KL: ρ(ret) / ρ(−\|log ret\|) | Deep-tap rel L2 | Weight rel norm | LM-head change | OOV-mass shift |
| --- | --- | --- | --- | --- | --- |
| EAGLE-3 K4 Llama | +0.02 / **−0.77** | +0.19 / **−0.76** | +0.17 / −0.28 (p 0.012) | +0.28 / −0.38 | +0.02 / +0.03 |
| EAGLE-3 K4 Qwen3 | +0.30 / **−0.69** | +0.34 / **−0.71** | +0.04 / −0.29 (p 0.023) | +0.13 / −0.38 | +0.16 / −0.27 |
| DFlash K10 Llama | −0.01 / **−0.69** | +0.17 / **−0.67** | +0.21 / −0.31 | +0.26 / −0.45 | 0.00 / −0.08 |
| DFlash K16 Qwen3 | +0.20 / **−0.60** | +0.25 / **−0.62** | +0.05 / −0.18 (p 0.16) | −0.09 / −0.25 | +0.01 / −0.31 |

Bold: p < 1e-4. Full table with p-values in results.json.

**Observations (descriptive).** KL and feature displacement track the *magnitude* of retention change far more strongly than the weight-update norm does,
for both drafters and both bases. Their association with *signed* retention is weak, because large changes occur in both directions (EXP-ATL-005: increases with
short or looping outputs). OOV-mass shift shows little association on Llama.

**Caveats.** Correlational; KL/features are computed on the child's own generations, which share the length/degeneracy confound flagged in EXP-ATL-005.
Covariate coverage is not random (quantized models are under-represented). Multiple comparisons are uncorrected. Single covariate run per derivative.

**Mandatory fields:** predictions EXP-ATL-000 §6.3 items 4–5 (not evaluated here); inputs EXP-ATL-005 + A6 cells (paths in script); engine pins as A4/A7;
bf16 eager Transformers for covariates (.venv-covariates); n above; status pilot.
