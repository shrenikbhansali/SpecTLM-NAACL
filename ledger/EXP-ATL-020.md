### EXP-ATL-020 — P6 D48 A40 cold and warm timing

**Landed:** 2026-10-08.

**Status:** pilot; in progress, not certified.

**What / why.** Measure real inference speedups against reused drafter and no speculation, including startup costs and repeated-run noise.

**New.** Fivearms reused/fc300/full300/oracle/no-spec; batch8 SPEED128 plus fixedhashselected32prompt batch1;3freshprocessreplicates each with coldpanel and3warmpanels.

**Artifacts.** `artifacts/P6_D48_20261008_1500/`; configs, publication receipts, logs, per-prompt records, native exports and pending analyses.

**Config + results.** Timingextension215fb44 imports/hashes frozen6da2e42 promptloader, identicalvLLM0.31.0 engine settings/greedy512, A40 only; acceptance numbers remain frozen-run_cell. Reused/no-spec n8smokes passed;30timingcells published. Numbers pending paired analysis.

**Caveats.** Cold means firstpanel after engine warmup; startupseparate. Prefixcacheoff, freshcompilation percell. A40s sharedcluster; placementandconcurrentloads retained. Batch8 CIs resample batches, notduplicate per-prompt batchtimes; report repeatvariation separately. Compareoutputtokens/lengths and generationmismatch rather than assumeequalwork.
