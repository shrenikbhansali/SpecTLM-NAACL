### EXP-ATL-016 — P3 single-target EAGLE-3 repair pilot

**Landed:** 2026-10-08.

**Status:** pilot; D-45 initial generic data experiment; no winner promotion or paper conclusion.

**What / why.** Measure how much target-specific native drafter repair recovers, with family-drafter initialization, before the D-46 component/self-elicited matrix.

**New.** Three targets ×fc-only/fc+LoRA/full warm-start ×50/200steps ×SPEED128/MATH64:36 valid evaluation cells. Additional scratch two cells invalid as scratch controls due to an HF initialization-guard bug; retained and excluded. All variants use the same target-specific520 generic prompts/responses and batch/schedule recipe. Native TTT objective unchanged.

**Artifacts.** [Report](../reports/P3-generic-pilot-20261008.md); independent raw counter analysis `artifacts/P3_generic_report_20261008_0352/{analyze.py,results.json}`; source `artifacts/P3_repair_20261008_0305/`. Pinned revisions, response/audit/prompt/file hashes and parameter proofs in every config/export.

**Config + results.** Single seed0; native trainer261a82d, code1e88bb2, TTT3 KL, AdamW2e-5,2048token batch ceiling. All acceptance uses frozen6da2e42/vLLM0.31.0/A40/K4/greedy/512tokens/batch8 and identical derivative-rendered tokens. Paired10,000prompt bootstrap. R1 SPEED,n128: fc200 Δp1+.1417[.1301,.1523],τ2.1014 vs1.7302,Δτ+.3712[.3389,.4008]; full200 Δp1+.1772[.1648,.1890],τ2.2395,Δτ+.5092[.4742,.5428]. Owner fixed τ-gap recovery33.2%/45.5%, data+train0.438/0.437A40GPUh. Nemotron full200 Δp1+.1532[.1418,.1645]; R1Qwen full200+.0541[.0464,.0617],n128. All36 estimates, MATHn64, per-depth/lengths and nulls in report/JSON.

**Caveats.** Generic public prompts, not self-elicited; distinguish old fc_lora(fullfc+all7decoderprojectionLoRA) from D46 low-rank-fc and decoder q/v+MLP proxies. No run-to-run CI or speedup claim. Incomplete reasoning traces and teacher factual errors retained. Per-repair cost charges successful data generation in full but excludes evaluation, failed Magpie trials and engineering overhead. Dedicated oracle cost/data unknown. Scratch invalidation recorded, fixed with regression and native smoke, replacement separately tagged. Component mechanism verdict provisional; affine/RMS and decoder controls pending. No promotion of earlier FollowSpec negative results.

**D46 completion addendum (2026-10-08T14:36:29.421597-04:00; pilot).** Seven matched300step training runs,50/150/300exports plus RMS-only calibration:44frozen cells complete. [Report](../reports/P3-self-elicited-pilot-20261008.md). R1 SPEEDn128: fc300Δp1+.1533[.1417,.1645],τ2.1272,35.5%pairedoraclegap; full300+.1760[.1647,.1863],τ2.2435,45.9%gap;0.465/0.452A40GPUh including successfulself-data. MATHn64gains+.1404/+.1616. Lowrank/decoder-only weaker; RMSτnull; corrected scratchτ1.2078. All44pairedestimates, lengths/depths and trainingmatchaudit saved under artifacts/P3_D46_20261008_0335/report. Single seed; no isolatedreal-speedupclaim.

### 2026-10-08T16:48:43.111084-04:00 — codex-1 — optional head control complete
D46idle-GPUhead-only control complete6/6frozencells afternative2step/frozen8smokes. Onlylm_head.weight(131072000parameters) trained; matchedfcdata/batches/nativeobjective/optimizer fields pass. Step300SPEEDΔp1+.0623[.0539,.0707],τ1.8560,oracle-gap11.2%[9.3,13.1]; MATH+.0581[.0514,.0651],τ2.0792,gap6.7%[5.9,7.6]. Directhead-minus-fcp1−.0910[−.1006,−.0814]SPEED/−.0823[−.0938,−.0700]MATH. Cost.349GPUh incldata, singletrainingseed. All50/150/300budgetsreported in reports/P3-head-control-20261008.md; source artifacts/P3_head_optional_20261008_1618/snapshot-20261008_163453; rawindependentanalysis/matchedtrainingPASS. Scopeextendscomponentpilotwithoutchangingframingorretuninghead.
