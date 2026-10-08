### EXP-ATL-020 — P6 D48 A40 cold and warm timing

**Landed:** 2026-10-08.

**Status:** pilot; in progress, not certified.

**What / why.** Measure real inference speedups against reused drafter and no speculation, including startup costs and repeated-run noise.

**New.** Fivearms reused/fc300/full300/oracle/no-spec; batch8 SPEED128 plus fixedhashselected32prompt batch1;3freshprocessreplicates each with coldpanel and3warmpanels.

**Artifacts.** `artifacts/P6_D48_20261008_1500/`; configs, publication receipts, logs, per-prompt records, native exports and pending analyses.

**Config + results.** Timingextension215fb44 imports/hashes frozen6da2e42 promptloader, identicalvLLM0.31.0 engine settings/greedy512, A40 only; acceptance numbers remain frozen-run_cell. Reused/no-spec n8smokes passed;30timingcells published. Numbers pending paired analysis.

**Caveats.** Cold means firstpanel after engine warmup; startupseparate. Prefixcacheoff, freshcompilation percell. A40s sharedcluster; placementandconcurrentloads retained. Batch8 CIs resample batches, notduplicate per-prompt batchtimes; report repeatvariation separately. Compareoutputtokens/lengths and generationmismatch rather than assumeequalwork.

### 2026-10-08T16:18:50.189668-04:00 — codex-1 — complete A40 timing matrix
All30cells complete,3freshprocesses perarm/batch,3warmpasses perprocess. Independent raw timers, prompt pairing, output counts and exactfrozenloader/engine/A40 assertions pass. Report reports/P6-A40-timing-20261008.md; source artifacts/P6_final_20261008_1615 with timing/economics/outputaudit hashes and inspectedfigure. Batch8warm speedupvsnone: reused1.072[.996,1.151],fc1.216[1.086,1.365],full1.243[1.106,1.407],oracle1.381[1.186,1.633],n128. Batch1n32:1.281/1.601/1.666/2.051. Repairvsreused1.134/1.159 batch8,1.250/1.301 batch1. Startupinclusivefc/fullbatch8 null. Wholeanswersmostlydiffer acrossfreshprocesses, includingnospec:15/256exactbatch8,2/64batch1; firsttokens255/256 and64/64same. No bitwiseequivalenceclaim; lengths/token-throughputreported. Costamortizationconditionalonthisquerymix:fc/full~7586/6332queriesvsreusedbatch8,759/638batch1,pairedCIreport. Successfuldata+traincost.465/.452GPUh; excludessearch/evaluation; oracletrainingcostunknown. Allremainpilot. Commands: finish_v2.py ranthreeindependentCPUanalyses; plot.py; visuallyinspectedPNG.
