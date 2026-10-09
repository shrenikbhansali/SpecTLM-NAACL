### EXP-ATL-024 — D50 final repair controls E1–E7

**Landed:** 2026-10-09T02:17:12.583259-04:00.

**Status:** pilot, in progress; no certification.

**What / why.** Test family initialization, training-free and independent baselines, matched-budget scratch, further training and Nemotron scaling under owner D50.

**New.** E1 pinned official family drafter plus fc/full generic4k; E2 ngram K4/8 lookupmax3/5 and suffix only if available; E3 Llama1B K4/6; E4 scratch generic16k; E5 resumed second epoch and TTT4 generic4k; E7 Nemotron generic16k. E6 timing and cost conversion are in EXP-ATL-020.

**Artifacts.** `artifacts/P3_D50_20261009_0200/`; `run-P3-D50-20261009` tag at3cb2cd1 exists before worktree creation. Official model record/license/tensor-conversion proofs, smoke gates, all publication receipts, launch alerts and controller logs retained.

**Config + results.** Acceptance uses unmodified frozen6da2e42 loop and aggregate, vLLM0.31.0,A40,greedy512,b8,seed0,SPEED128/MATH64,paired identical derivative-rendered IDs. E2/E3 new opt-in proposal config adapter3cb2cd1 has27passing acceptance/build tests including unchanged frozen loop identities; smoke gates precede full cells. Official revision ada412b672e293d682423de84a095447bf38a637,Apache2; all15 converted tensors equal source exactly; actual frozen parity check gates repair. Suffix unavailable (arctic_inference absent); no environment modification. Completed paper-sized new-cell results pending. Existing generic16k3seeds complete, separately reported EXP018.

**Caveats.** Conditional extensions (official16k,64k) await evidence. Scratch randomizes trainable fc/layer/head/norm; verifier embedding and vocabulary mapping remain fixed. Second epoch restores final weights/Adam moments, extends cosine horizon from4477to8967 and records LR transition; first epoch retains its original shorter schedule, missing RNGstate means seeded restart, not uninterrupted2epochs. ngram tau conditions on actual proposal steps; proposal coverage/zero-step counts must be reported. Compare paired p1/tau with n and CIs, include nulls. Data masks and dedup gate every new path, trainable-only intermediates/shared shards, queue350GB/runtime250GB guard.
