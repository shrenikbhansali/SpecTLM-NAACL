### EXP-ATL-024 — D50 final repair controls E1–E7

**Landed:** 2026-10-09T02:17:12.583259-04:00.

**Status:** pilot, in progress; no certification.

**What / why.** Test family initialization, training-free and independent baselines, matched-budget scratch, further training and Nemotron scaling under owner D50.

**New.** E1 pinned official family drafter plus fc/full generic4k; E2 ngram K4/8 lookupmax3/5 and suffix only if available; E3 Llama1B K4/6; E4 scratch generic16k; E5 resumed second epoch and TTT4 generic4k; E7 Nemotron generic16k. E6 timing and cost conversion are in EXP-ATL-020.

**Artifacts.** `artifacts/P3_D50_20261009_0200/`; `run-P3-D50-20261009` tag at3cb2cd1 exists before worktree creation. Official model record/license/tensor-conversion proofs, smoke gates, all publication receipts, launch alerts and controller logs retained.

**Config + results.** Acceptance uses unmodified frozen6da2e42 loop and aggregate, vLLM0.31.0,A40,greedy512,b8,seed0,SPEED128/MATH64,paired identical derivative-rendered IDs. E2/E3 new opt-in proposal config adapter3cb2cd1 has27passing acceptance/build tests including unchanged frozen loop identities; smoke gates precede full cells. Official revision ada412b672e293d682423de84a095447bf38a637,Apache2; all15 converted tensors equal source exactly; actual frozen parity check gates repair. Suffix unavailable (arctic_inference absent); no environment modification. Completed paper-sized new-cell results pending. Existing generic16k3seeds complete, separately reported EXP018.

**Caveats.** Conditional extensions (official16k,64k) await evidence. Scratch randomizes trainable fc/layer/head/norm; verifier embedding and vocabulary mapping remain fixed. Second epoch restores final weights/Adam moments, extends cosine horizon from4477to8967 and records LR transition; first epoch retains its original shorter schedule, missing RNGstate means seeded restart, not uninterrupted2epochs. ngram tau conditions on actual proposal steps; proposal coverage/zero-step counts must be reported. Compare paired p1/tau with n and CIs, include nulls. Data masks and dedup gate every new path, trainable-only intermediates/shared shards, queue350GB/runtime250GB guard.

### 2026-10-09T02:36:45.800831-04:00 — codex-1 — D50 independent raw snapshot

26 completed cells independently re-derived with frozenengine/A40/prompt-pair/counter assertions; 6 currently indexed cells pending. Pilot source `/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/analysis/snapshot-20261009_023645/results.json`, readable table `/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/analysis/snapshot-20261009_023645/report.md`; 10000pairedquery CIs, nulls/per-depth/lengths/coverage/costs retained. This does not certify a gate or select a framing.

### 2026-10-09T02:56:24.997613-04:00 — codex-1 — fullMATH500 flagship extension queued

D50 explicitly permits fullMATH500 if cheap. Staged all500 from the existing pinned MIT PRM800K source, verified source hash, all500 already excluded from training, exact token-ID identity for previous64; maxprompt761, no truncation. Read allfive decoded prompts (including original Asymptote text); no answers or training masks. Five cells: production reuse, generic16k seed0fc/full, dedicated oracle, independent1B K4. Frozen6da2e42; explicit D50 adapter only for independent1B. Reused existing tagged worktrees, no new worktree needed.

Initial mixed-source preflight correctly failed independent adapter import under frozen checkout; no GPU jobs published then. Retried separate frozen4/adapter1 preflight groups under their correct source, allpassed; preserved failed preflight. Queue/stage checks in both publications, no overwrite or duplicate. `prioritize_pending_v4.py` retains owner E1 and required small baselines ahead of optional500cells, only reorders pending jobs. Finalizer PID433465, `math500/finish.py`, independently reconstructs allfive cells with paired10000query CIs, writes immutable snapshot plus notes/EXP024. No fullMATH500 result yet; original64 is a subset, not independent replication.
