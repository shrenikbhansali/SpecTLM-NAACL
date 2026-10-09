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

### 2026-10-08T17:07:08.644981-04:00 — codex-1 — self4k timing extension / live Handoff
ExtendedD48P6fromcompleted256timingtofinalself4kseed0exports (1315steps), toconnectlargerrecoverypointwithactualspeedandcost. artifacts/P6_D48_self4k_20261008_1707/launch.py clonesexacttested215fb44timingprotocol, sameoriginalSPEED128/fixedbatch1-32IDs,3freshprocesses/arm,1first+3warm panels; all5armsrepeatedincludingfreshreused/oracle/no-speccontrols,30jobs. Queuestagedir+diskguardscheckedby publish_common; samecanonicalqueue4129996, nosecondqueue. AllowedlivefreeA40srv2:0–3/srv3/srv4/srv5:1–7, queuechecksoccupancy. Noacceptancenumbersfromtimingpath; separatefrozen24self-scalingcellsevidence. Timing256reportretained; no claim4kbeatsgenericwhilegenericpending.
CPUfinalizer55329 atsame stage waits30/30thenreusesindependenttiming/economics/outputidentityaudits, writesfinal-report.md/analysis-complete.json; itdoesnoteditrepoorchoosescientificthresholds. Economicschargesactual4kassemblygeneration4.7997GPUh+training; nonpositivesavingshandledasundefined/unbounded, nooptimisticspeedassertion. First256timing30/30complete remains reports/P6-A40-timing-20261008.md andEXP020. Next: inspectnewtimingoutputs/errors,reportallnulls/lengths/outputidentityandcostfrontier,returnP6toreviewafter30finish.

### 2026-10-08T18:07:58.130837-04:00 — codex-1 — D49 dedicated recipe cost estimate
What/why: add a clearly labelled recipe-scale A40 cost projection for economics; no oracle training measurement or rerun. New: published EAGLE-3 paper plus pinned SafeAILab/EAGLE cb7e0841fe0c206c6ed74a197ad5e2a1f13f5a2b source; data nominal532k plus unspecified OpenThoughts math subset (646k upper scenario), code default40epochs/cap2048, upstreamTTT7 versus localTTT3. Artifacts: artifacts/P6_D49_recipe_estimate_20261008_1800 with saved primary sources, hashes, estimate.py/json and plot.py. Report: reports/P6-dedicated-cost-estimate-20261008.md and inspected PDF/PNG figure.
Config/results: three measured full-self4k A40 runs yield median778.6 input tokens/s, range730.3–819.3, including online capture/startup/export. Projection N×epochs×mean_length/rate/3600;1/10 epochs are sensitivity assumptions,40 public code default (not known oracle budget), length557 local observed vs2048 cap scenario. At40epochs train-only range4,229–18,879A40GPUh; generation proxy adds291–353. Actual released checkpoint epochs/data/lengths/system timings unknown; do not claim a measured oracle bill or exact repair-cost ratio. Per-repair measured costs preserved alongside separate assumption panel. Status estimate/pilot; nulls/uncertainty unchanged. Commands: estimate.py, plot.py; checked source assertions and visually inspected PNG. No new downloads of models or GPU launches for this estimate.

### 2026-10-09T02:17:12.583259-04:00 — codex-1 — D50 E6 fixed-K cost model and new16k timing

New: 30 fresh generic16k timing cells (reused/fc/full/oracle/no-spec, b1/b8, 3 processes, 1first+3warm passes); canonical queue, same timing extension and frozen prompt input. Artifacts `artifacts/P3_D50_20261009_0200/E6-timing`; 6/30 complete at first fit. Earlier two30-cell campaigns calibrate fixed-K4 seconds/token = nonnegative intercept + step/tau, 2000 paired process/query-batch draws including acceptance uncertainty; generic16k held out of fitting. Report [provisional cost model](../reports/P6-D50-cost-model-20261009.md). SPEED128 b8 predictions fc1.260[1.105,1.433],full1.308[1.132,1.510] token-throughput ratio; these are predictions, not measured speedups. b1n32 predictions1.719/1.817. UnseenK disallowed, MATH/Nemotron/official drafter uncalibrated; oracle slope unidentified. CI excludes model misspecification, validation pending. Build tests8/8; direct rawcounter identities and identical rendered IDs checked including batch1subset. Status pilot.

### 2026-10-09T02:28:13.739308-04:00 — codex-1 — completed self4k timing report published

Published [self4k real timing](../reports/P6-self4k-timing-20261009.md), all30cells previouslycompleteOct8T18:13. Warmb8SPEED128 fc1.233[1.096,1.394],full1.286[1.137,1.468] panel-time speedupvsnone; token ratios1.226/1.280. b1n32fc1.634[1.535,1.736],full1.750[1.652,1.850].3processes×3warmpasses,10000pairedprocess/batchbootstrap. Startupinclusiveb8 nulls retained; exactoutputmismatches reported. Generation+trainfc5.398/full5.555GPUh,conditionalbreak-even vsnoneb8~51318/44770queries;notdeploymentforecast. D50 generic16k timing separatelyrunning, notmixedwithself4k.

### 2026-10-09T02:49:25.853194-04:00 — D50 held-out timing validation (pilot)

Earlier 60 timing cells fit fixed-K4 cost model; new16k timing28/30 complete in `artifacts/P3_D50_20261009_0200/cost-model/snapshot-20261009_023512`. Batch8 SPEED n128, 3 processes ×3 warm repeats: token-throughput ratios fc1.274 [1.116,1.446], full1.317 [1.140,1.523], reused1.074 [0.999,1.151]; paired process/batch bootstrap2000. Predicted absolute TPS residuals −0.6%fc/−0.2%full. This validates one target, architecture, K and workload condition; no cross-K or independent-drafter generalization. New16k cells excluded from fitting; complete batch1 and actual independent1B timings pending. [Report](../reports/P6-D50-cost-model-20261009.md).

### 2026-10-09T02:53:08.585653-04:00 — D50 complete16k timings and economic validation (pilot)

All30cells completed: five arms×batch1/8×3processes; each1first+3warm passes. A40/vLLM0.31/frozen prompt loader, greedy512, identical SPEED IDs. Paired10000 process/query-batch bootstrap, n128 atbatch8 andfixed32atbatch1. Warm panel-time speedup fc/full: batch8 1.274[1.125,1.447]/1.306[1.140,1.515], batch1 1.724[1.626,1.821]/1.807[1.683,1.929]. Batch8 startup-inclusive fc1.061[.979,1.147], full1.081[.989,1.185] remain nulls. Data+train costs10.907/11.175GPUh; break-even assumptions and all outputs/length differences reported. Held-out TPS prediction errors within1.5% at both batches; fit excludes new16k cells. [Report](../reports/P6-generic16k-timing-20261009.md), [fixedK cost conversion](../reports/P6-D50-cost-model-20261009.md). Final source `artifacts/P3_D50_20261009_0200/E6-timing/analysis-complete.json`. Independent1B timing comparison still running.

### 2026-10-09T02:58:00.528094-04:00 — codex-1 — independent1B batch8 cost comparison (pilot)

| Batch | Arm | Reference | n queries / processes | Warm panel speedup [95% CI] | Warm token throughput ratio | Cold panel speedup | Cold including startup |
|---:|---|---|---|---|---:|---:|---:|
| 8 | independent | none | 128 / 3 | 1.108 [1.087,1.131] | 1.114 | 1.105 | 1.054 |
| 8 | independent | reused | 128 / 3 | 1.033 [0.967,1.104] | 1.037 | 1.034 | 1.113 |
| 8 | independent | fc | 128 / 3 | 0.870 [0.768,0.981] | 0.874 | 0.873 | 0.994 |
| 8 | independent | full | 128 / 3 | 0.848 [0.733,0.968] | 0.845 | 0.850 | 0.975 |
| 8 | independent | oracle | 128 / 3 | 0.770 [0.656,0.893] | 0.771 | 0.773 | 0.916 |

Only batch8 complete: n128,3processes×3warm repeats, paired10000process/query-batch bootstrap. Warm1B vsno-spec1.108[1.087,1.131]; vsreused1.033[.967,1.104] is null. Independent/fc panel ratio.870[.768,.981] and independent/full.848[.733,.968] indicate repairs complete this panel faster despite competitive independent acceptance. Costs include runtime only here; data/training amortization and startup differ. Hosts were not randomized; output lengths/IDs differ, raw token-normalized and startup CI inJSON. No claim of broad superiority from this one target/panel. Batch1 timings still active. Source`artifacts/P3_D50_20261009_0200/E3-timing/analysis/snapshot-20261009_025720/results.json`.

### 2026-10-09T03:04:30.591409-04:00 — codex-1 — independent1B timing complete (pilot)

| Batch | Arm | Reference | n queries / processes | Warm panel speedup [95% CI] | Warm token throughput ratio | Cold panel speedup | Cold including startup |
|---:|---|---|---|---|---:|---:|---:|
| 8 | independent | none | 128 / 3 | 1.108 [1.087,1.131] | 1.114 | 1.105 | 1.054 |
| 8 | independent | reused | 128 / 3 | 1.033 [0.967,1.104] | 1.037 | 1.034 | 1.113 |
| 8 | independent | fc | 128 / 3 | 0.870 [0.768,0.981] | 0.874 | 0.873 | 0.994 |
| 8 | independent | full | 128 / 3 | 0.848 [0.733,0.968] | 0.845 | 0.850 | 0.975 |
| 8 | independent | oracle | 128 / 3 | 0.770 [0.656,0.893] | 0.771 | 0.773 | 0.916 |
| 1 | independent | none | 32 / 3 | 1.267 [1.203,1.334] | 1.269 | 1.263 | 1.172 |
| 1 | independent | reused | 32 / 3 | 0.981 [0.945,1.024] | 0.979 | 0.979 | 1.031 |
| 1 | independent | fc | 32 / 3 | 0.735 [0.702,0.773] | 0.728 | 0.734 | 0.842 |
| 1 | independent | full | 32 / 3 | 0.701 [0.663,0.749] | 0.697 | 0.701 | 0.810 |
| 1 | independent | oracle | 32 / 3 | 0.618 [0.575,0.674] | 0.617 | 0.618 | 0.744 |

All36 timing cells (six independent plus30shared controls); source`/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/E3-timing/analysis/snapshot-20261009_030417/results.json`. Threeprocesses×3warm repeats, A40, greedy512, paired10000process/query-batch bootstrap, n128/b8 and32/b1. Cold/startup intervals, per-process values, output lengths and mismatches in JSON. Exact same rendered IDs; no acceptance derived from timing. Available hosts were not randomized; different greedy outputs remain documented. Nulls retained.
