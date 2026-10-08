### EXP-ATL-021 — P1 typed frozen checkpoint population

**Landed:** 2026-10-08.

**Status:** pilot descriptive synthesis; no certification.

**What / why.** Describe family-drafter retention by checkpoint lineage and documented training history without treating composite recipes as pure RL or pure distillation.

**New.** Semantic card inventory for 201 records; frozen matched results for 25 checkpoints; checkpoint-level hierarchical uncertainty and explicit unknown/quality exclusions.

**Artifacts.** [Report](../reports/P1-typed-population-20261008.md); `artifacts/P1_typed_20261008_1515/typed-v2.json` and `analysis-v3/`; original pinned cards, raw outputs and SHA256 provenance retained.

**Config + results.** Frozen6da2e42/vLLM0.31.0/A40, EAGLE K4/DFlash native K, greedy batch8/max512, paired derivative-rendered IDs. 66 complete pairs:25 checkpoints ×two drafters ×SPEED128, plus8 ×two ×MATH64. Four architecture-incompatible pairs excluded; pretrained and collapsed controls reported separately. Primary21 checkpoints/58pairs. Direct on-policy RL SPEED m4: p1 retention EAGLE .986 [.969,1.001], DFlash .990 [.978,1.006]. Direct teacher-distillation m2 MATH: EAGLE1.012 [.994,1.031] (null loss), DFlash .879 [.851,.905]. Full tables include all types/nulls. 5,000 checkpoint/paired-prompt bootstrap draws.

**Caveats.** Convenience sample, correlated lineages and mixed recipes; no causal recipe comparison. Forty-five histories unknown across the full card inventory; weaker tag/series evidence marked. Archived174-model numbers separately typed but not promoted to frozen-paper evidence. Historical failed analysis versions preserved; canonical retry overlay included in v3.
