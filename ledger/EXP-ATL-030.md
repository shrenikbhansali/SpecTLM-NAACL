### EXP-ATL-030 — REV5 three-hour secondary analyses

**Landed:** 2026-10-12, codex-1.

**Status:** pilot; CPU analysis complete. Optional enlarged long panel is prepared but not launched.

**What/why:** owner requests strongest feasible evidence within three hours after two new draft reviews. Quantify continuous drift versus acceptance, deployment amortization from measured costs/timers, and longer-response repair versus the existing short-response recipe.

**New:** family/method-stratified checkpoint-bootstrap correlations for141 atlas checkpoints and a separate17-checkpoint T1 cohort; raw-timer amortization; paired raw-counter E9 long-data versus short16k comparison. No new acceptance cells, training or changed engine.

**Artifacts:** `artifacts/REV5_cpu_20261012_1430/{config.json,results.json,report.md,drift-models.csv}`; `artifacts/REV5_longdata_20261012_1425/{config.json,analyze.py,results.json}`; `reports/REV5-three-hour-evidence-20261012.md`; `notes/REV5.md`. Tested code `a3ebdaa`.

**Config/results:**10,000 checkpoint or paired process/query bootstrap draws, with units explicitly separated. Llama/DFlash KLρ−.336[−.534,−.116],n80; other family/method KL intervals include zero. R1 full measured11.127GPUh amortizes against reuse after13,582[12,774,14,503] SPEED or11,706[11,374,12,058] MATH requests, batch1,n128,3processes,3warm passes. E9 full R1 long4k minus short16k Δτ+.070[−.026,+.178],mixed20k+.025[−.057,+.115],n32,one seed,cap8192. Complete nulls/results/sources are retained in the report.

**Caveats:** archived drift diagnostics use different context distributions for atlas/T1 and are observational, not an independently identified causal mechanism. Checkpoint-bootstrap drift CIs condition on per-model estimates. Tulu KL uses shared-vocabulary conditioning; collapsed RL sensitivities explicitly labelled. Amortization uses fixed observed seed0 costs and capped warm workloads; no dedicated-cost estimate or deployment forecast. E9 packing, sample count and optimizer steps differ across data recipes. Seven larger acceptance jobs are only planned: free349.7GB is below350GB floor; no number claimed from them.

**Next:** Claude/owner may integrate evidence; no paper files modified. When headroom returns, canonical queue publication and independent raw reduction of prepared128-query long panel, if it still fits the owner window. No scientific promotion.

### 2026-10-12T14:37:16.547025-04:00 — owner-authorized cleanup and long128 publication
Deleted32 invalid original FIX24 official4k trainable-weight files only,30.401GB, with manifest/inventory: reports/REV5-checkpoint-cleanup-20261012.md. Scientific raw records retained. Seven supplementary long128 acceptance cells now published to canonical dispatcher; no completed numbers yet. All available servers occupied at live check, so they are queued, not running. CPU completion reducer will report every result with paired intervals.
