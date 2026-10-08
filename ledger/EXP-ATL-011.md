# EXP-ATL-011 — Track T phase1 target-conditioned failure hunt

**Landed:** 2026-10-07, Track T / D-40.

**Status:** pilot; partial2/72cells, no decision.

**What / why:** Test18public lineage, reasoning-distillation and RL checkpoints against their official base targets with EAGLE-3 and DFlash. Owner motivation rule requires≥20%per-token acceptance loss for both drafter families on≥2independent realistic publicmodels with a plausible mechanism.

**New in this experiment:** Each target uses its own chat template; A00 and A10 get identical rendered IDs. No adapters; full-weight local snapshots. Report all18 outcomes, per-position conditional acceptance,τ and outputlengths.

**Artifacts:** `artifacts/T1_models_20261007/manifest.jsonl`, `artifacts/T1_canonical_20261007_2347/index.json`, `artifacts/T1_cells_20261007_2350`; [initial partial](../artifacts/T1_cells_20261007_2350/partial-2-1791431750961148283/results.json).

**Config + results:** Frozen harness6da2e42; vLLM0.31.0, A40, seed0 greedy, batch8,512outputtokens, freshcompile. EAGLE3K4; DFlashLlamaK10/QwenK16. Shared SPEED128,128prompts/model. First complete pair (not a class result):

| Model | Drafter | n | Position1 A10/A00 [95%prompt CI] | τ A00→A10 | Median outputlength A00→A10 |
| --- | --- | ---: | --- | --- | --- |
| meta-llama/Llama-3.1-8B | EAGLE-3 K4 |128|1.2158 [1.1619,1.2782]|2.7913→3.7814|285.5→512.0|

**Caveats:** Partialmatrix, one seed, fixed promptpanel; promptbootstrap2000draws does not measure run-to-run uncertainty. This first checkpoint improves acceptance and does not meet the failure threshold; DFlash pair pending. Own-template post-training comparisons include template/trajectory effects even with identical paired inputIDs. DeepSeek AutoTokenizer whitespace bug repaired before any affected GPUlaunch; original malformed renders retained. Unknown/custom license labels in the supplied18model manifest remain flagged, not silently treated as standard. No quality or speedup claim, no owner framing decision.

## 2026-10-08T00:08:07-04:00 — Eligibility audit update

Two supplied OpenLearnLM checkpoints declare Qwen2/hidden3584/layers28 despite qwen3_8b repository names. Their8unlaunched pairedcells held as structurallyincompatible;16models/64cellsremaineligible, all18retained in originalplan. [Audit](../artifacts/T1_cells_20261007_2350/model_metadata_audit.json), [holds](../artifacts/T1_cells_20261007_2350/exclusions.json). This is inputvalidity, not acceptance degradation. Sixmanifestentries lacklicense metadata and3arecustom/other; labels remain visible.
