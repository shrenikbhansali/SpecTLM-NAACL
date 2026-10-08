### EXP-ATL-019 — P4 D48 DFlash interface versus full repair

**Landed:** 2026-10-08.

**Status:** pilot; in progress, not certified.

**What / why.** Test whether interface repair transfers to a second drafter architecture.

**New.** Single-target B10 nativeDFlash repair behind new flag, fc/full matched2048-token batches and64anchors with memory flags;256selfexamples,target R1Llama/Nemotron.

**Artifacts.** `artifacts/P4_D48_20261008_1505/`; configs, publication receipts, logs, per-prompt records, native exports and pending analyses.

**Config + results.** Pinned native261a82d, codeef0b0db; nativeKL gamma4 fixed-exp-decay, AdamW2e-5. Bothn5/2step A40 smokes pass (peak28.36/37.81GiB); frozen6da2e42 DFlashK10 export checks dispatched. Planned50/150/300 exports, SPEED128/MATH64 pairedCIs. No scientific result yet.

**Caveats.** B10historical8192/512anchor recipe requiredH200; this is explicit smaller A40pilot. Full-vocab verifier head remainsfrozen and omittedfromexport, consistentnativeDFlash. InheritedconverterBOS/EOSmetadatawarnings retained. Cross-architectureeffectnotyetestablished.
