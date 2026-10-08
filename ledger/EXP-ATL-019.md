### EXP-ATL-019 — P4 D48 DFlash interface versus full repair

**Landed:** 2026-10-08.

**Status:** pilot; in progress, not certified.

**What / why.** Test whether interface repair transfers to a second drafter architecture.

**New.** Single-target B10 nativeDFlash repair behind new flag, fc/full matched2048-token batches and64anchors with memory flags;256selfexamples,target R1Llama/Nemotron.

**Artifacts.** `artifacts/P4_D48_20261008_1505/`; configs, publication receipts, logs, per-prompt records, native exports and pending analyses.

**Config + results.** Pinned native261a82d, codeef0b0db; nativeKL gamma4 fixed-exp-decay, AdamW2e-5. Bothn5/2step A40 smokes pass (peak28.36/37.81GiB); frozen6da2e42 DFlashK10 export checks dispatched. Planned50/150/300 exports, SPEED128/MATH64 pairedCIs. No scientific result yet.

**Caveats.** B10historical8192/512anchor recipe requiredH200; this is explicit smaller A40pilot. Full-vocab verifier head remainsfrozen and omittedfromexport, consistentnativeDFlash. InheritedconverterBOS/EOSmetadatawarnings retained. Cross-architectureeffectnotyetestablished.

### 2026-10-08T15:54:44.534927-04:00 — completed24-cell pilot
[Fullreport](../reports/P4-DFlash-repair-20261008.md),4nativeA40runs,24frozen6da2e42/vLLM0.31/K10cells. SPEED128at300steps:R1fcΔp1+.0686[.0608,.0767],full+.1003[.0918,.1086],τ2.2246/2.3129; Nemofc+.0681[.0587,.0779],full+.0970[.0861,.1080],τ2.2380/2.3552. MATH64positivebothscopes/targets; all50/150/300cellsandnullτNemo50reported. Directpairedfull-minus-fcCIspositiveat300onbothworkloads. Costs0.29–0.43GPUh incldata, singleseed. Source `artifacts/D48_analysis_20261008_1528/snapshot-20261008_154917/`,10kpairedbootstrap,matchedconfigchecksPASS.
