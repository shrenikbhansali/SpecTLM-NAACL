### EXP-ATL-018 — P3 D48 data scaling, seeds and generality

**Landed:** 2026-10-08.

**Status:** pilot; in progress, not certified.

**What / why.** Test whether more self-elicited data closes the remaining dedicated-drafter gap and whether fc/full repair generalizes.

**New.** Self-elicited1k/4k nested sets, generic4k, quarter/half/final one-epoch exports; two additional seeds per256/300step arm; Nemotron,R1Qwen,GRPO150,Hermes3 controls.

**Artifacts.** `artifacts/P3_D48_20261008_1455/`; configs, publication receipts, logs, per-prompt records, native exports and pending analyses.

**Config + results.** Native261a82d, EAGLE3 K4 frozen6da2e42/vLLM0.31.0/A40 evaluation on held-out SPEED128+MATH64. Data generation9jobs dispatched; seeds and generality publishing after exact five-sample audits. New compact storage native2steps/frozen8prompt checks pass bothfc/full;21 storage/family tests pass. No D48 scientific result yet.

**Caveats.** 3seeds at256budget reuse D46 seed0; best-scale seed extension waits scaling evidence. Oversampled4×1100selfqueryshards will be globally deduplicated and deterministically selected; allunused/rejectedrecords retained. Generation512tokens caps reasoning; errors/incompleteanswers retained. Hermes3 explicitly selected by prior EAGLE retention. Paired CIs and full null/regression reporting pending.
