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

### 2026-10-09T03:32:58.240096-04:00 — codex-1 — fullMATH500 flagship extension (pilot)

# D50 acceptance update (pilot)

5 complete cells; 0 currently published/planned cells pending. More repair checkpoints become eligible as training exports appear.

| Target | Variant | Panel | K | n/zero-step | p1 | delta p1 [95% CI] | tau | Recovery |
|---|---|---|---:|---|---:|---|---:|---:|
| 0 | MATH500-reused / sNA | math500 | 4 | 500/0 | 0.495 | +0.000 [+0.000,+0.000] | 1.949 | 0.0% |
| 0 | MATH500-fc / s4477 | math500 | 4 | 500/0 | 0.696 | +0.201 [+0.197,+0.205] | 2.611 | 35.0% |
| 0 | MATH500-full / s4477 | math500 | 4 | 500/0 | 0.738 | +0.243 [+0.239,+0.248] | 2.858 | 48.0% |
| 0 | MATH500-oracle / sNA | math500 | 4 | 500/0 | 0.872 | +0.377 [+0.372,+0.382] | 3.842 | 100.0% |
| 0 | MATH500-independent / sNA | math500 | 4 | 500/0 | 0.709 | +0.214 [+0.209,+0.220] | 2.966 | 53.7% |

All arms reported, including nulls. Primary p1 and macro tau independently recomputed from frozen raw counters. Full per-depth, lengths, paired CIs, coverage, matched-control differences and costs in results.json. Different K/method comparisons are descriptive; no automatic best-arm selection or benchmark certification.

Source: `/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/math500/snapshot-20261009_033258/results.json`. All500 excluded from training since original math64 reservation; fixed original-source order, same target-rendered IDs for all arms. Greedy512, A40, frozen6da2e42 (explicit D50 mapping adapter for independent1B), paired10000query bootstrap, n500 each. No claim of output quality or full solution accuracy; original64 overlaps this500, so they are not independent replications.

### 2026-10-09T03:37:04.395432-04:00 — codex-1 — D50 independent raw snapshot

90 completed cells independently re-derived with frozenengine/A40/prompt-pair/counter assertions; 8 currently indexed cells pending. Pilot source `/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/analysis/snapshot-20261009_033704/results.json`, readable table `/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/analysis/snapshot-20261009_033704/report.md`; 10000pairedquery CIs, nulls/per-depth/lengths/coverage/costs retained. This does not certify a gate or select a framing.

### 2026-10-09T04:37:07.044096-04:00 — codex-1 — D50 independent raw snapshot

111 completed cells independently re-derived with frozenengine/A40/prompt-pair/counter assertions; 3 currently indexed cells pending. Pilot source `/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/analysis/snapshot-20261009_043706/results.json`, readable table `/home/heck2/sbhansali8/SpecTLM/artifacts/P3_D50_20261009_0200/analysis/snapshot-20261009_043706/report.md`; 10000pairedquery CIs, nulls/per-depth/lengths/coverage/costs retained. This does not certify a gate or select a framing.

### 2026-10-09T14:18:33.480034-04:00 — FIX-24 INVALIDATION

**INVALID (FIX-24): all historical `E1-official-t{0,1}-4k-{fc,full}` training/evaluation cells and every `official_vs_production_*` contrast derived from them.** The trainer used a random frozen embedding, not the target embedding. These numbers must not describe official-drafter repair or enter paper tables. Official reuse and production repair remain valid. Artifacts and old statements are retained as history; this notice supersedes their interpretation. Complete run manifest: `artifacts/FIX24_20261009_1420/invalid-runs.json`. The earlier conversion note claiming the native trainer used target embeddings was false; loaded-state parity only proved the vLLM path. Corrected runs will use new directories. Old D50 publication/analysis watchers stopped to prevent propagation.

### 2026-10-09T14:53:39.454090-04:00 — codex-1 — consolidated raw tables and authorized E5c

Pilot:207 recomputed rows,32 FIX24-invalid cells excluded; source artifacts/D50_final_20261009_1451/results.json, report reports/P3-D50-consolidated-20261009.md, compiled LaTeX and fragments included. Raw counters, prompt hashes and exact renderedIDs verified. 10000pairedquery / three-seed hierarchical CIs. Paired TTT4/self-vs-generic/second-epoch/scratch/decoder/RMS contrasts retained, including nulls. Existing16k results unchanged. E5c64k explicitly authorized by owner now: existing16000 +35988Alpaca +12012Dolly, pinned licenses in stage source-provenance.json; source-mixture change labelled. Generation running; training/evaluation gated, no64k number yet. Corrected official4k four runs active; old invalid cells retained on disk.

### 2026-10-09T14:56:35.707543-04:00 — codex-1 — E5c source data inspection passed

Fully read five Dolly decoded prompts/responses and masks in data36/manual-five-decoded.txt, in addition to fortyAlpaca samples already inspected. SingleBOS, exact concatenation, prompt0/answer1 masks pass. Dolly3/5hit512 reasoning cap; unsupported factual guesses and arithmetic/season errors retained and documented, no quality certification or selective filtering. source-path-review.json binds first-five hashes for both sources. All48jobs use samepinnedpipeline; transportshards are not separateformattingpaths. Assembly/training now requires only all48generation completions plus full64000-row structural/dedup/eval-exclusion check; no remaining manual-approval dependency.

### 2026-10-09T14:56:06.427826-04:00 — codex-1 — automatic raw update

Pilot update: 207 raw-recomputed rows,32 FIX24-invalid cells excluded; 0 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_145606/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T15:06:50.856527-04:00 — codex-1 — automatic raw update

Pilot update: 216 raw-recomputed rows,32 FIX24-invalid cells excluded; 8 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_150650/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T15:17:49.320414-04:00 — codex-1 — automatic raw update

Pilot update: 227 raw-recomputed rows,32 FIX24-invalid cells excluded; 20 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_151749/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T15:28:45.428369-04:00 — codex-1 — automatic raw update

Pilot update: 232 raw-recomputed rows,32 FIX24-invalid cells excluded; 25 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_152845/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T15:39:29.593071-04:00 — codex-1 — automatic raw update

Pilot update: 239 raw-recomputed rows,32 FIX24-invalid cells excluded; 32 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_153929/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T15:50:14.017730-04:00 — codex-1 — automatic raw update

Pilot update: 243 raw-recomputed rows,32 FIX24-invalid cells excluded; 36 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_155014/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T16:00:58.985388-04:00 — codex-1 — automatic raw update

Pilot update: 245 raw-recomputed rows,32 FIX24-invalid cells excluded; 38 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_160058/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T16:11:43.853928-04:00 — codex-1 — automatic raw update

Pilot update: 247 raw-recomputed rows,32 FIX24-invalid cells excluded; 42 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_161143/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T16:22:30.963850-04:00 — codex-1 — automatic raw update

Pilot update: 250 raw-recomputed rows,32 FIX24-invalid cells excluded; 45 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_162230/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T16:33:17.274455-04:00 — codex-1 — automatic raw update

Pilot update: 255 raw-recomputed rows,32 FIX24-invalid cells excluded; 50 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_163317/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T16:44:03.418034-04:00 — codex-1 — automatic raw update

Pilot update: 258 raw-recomputed rows,32 FIX24-invalid cells excluded; 53 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_164403/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T16:54:50.267139-04:00 — codex-1 — automatic raw update

Pilot update: 259 raw-recomputed rows,32 FIX24-invalid cells excluded; 54 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_165450/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T17:05:37.077494-04:00 — codex-1 — automatic raw update

Pilot update: 263 raw-recomputed rows,32 FIX24-invalid cells excluded; 58 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_170537/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T17:31:24.498626-04:00 — codex-1 — automatic raw update

Pilot update: 264 raw-recomputed rows,32 FIX24-invalid cells excluded; 59 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_173124/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T17:42:11.774243-04:00 — codex-1 — automatic raw update

Pilot update: 267 raw-recomputed rows,32 FIX24-invalid cells excluded; 62 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_174211/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T18:03:59.660105-04:00 — codex-1 — automatic raw update

Pilot update: 268 raw-recomputed rows,32 FIX24-invalid cells excluded; 63 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_180359/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T18:14:47.544064-04:00 — codex-1 — automatic raw update

Pilot update: 271 raw-recomputed rows,32 FIX24-invalid cells excluded; 66 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_181447/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T18:32:35.880028-04:00 — codex-1 — automatic raw update

Pilot update: 272 raw-recomputed rows,32 FIX24-invalid cells excluded; 67 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_183235/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T18:43:24.944253-04:00 — codex-1 — automatic raw update

Pilot update: 273 raw-recomputed rows,32 FIX24-invalid cells excluded; 68 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_184324/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T18:57:13.590239-04:00 — codex-1 — automatic raw update

Pilot update: 274 raw-recomputed rows,32 FIX24-invalid cells excluded; 69 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_185713/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T19:08:02.647171-04:00 — codex-1 — automatic raw update

Pilot update: 275 raw-recomputed rows,32 FIX24-invalid cells excluded; 70 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_190802/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T20:46:53.728352-04:00 — codex-1 — automatic raw update

Pilot update: 276 raw-recomputed rows,32 FIX24-invalid cells excluded; 71 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_204653/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T20:57:42.662102-04:00 — codex-1 — automatic raw update

Pilot update: 277 raw-recomputed rows,32 FIX24-invalid cells excluded; 72 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_205742/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T21:39:32.225310-04:00 — codex-1 — automatic raw update

Pilot update: 278 raw-recomputed rows,32 FIX24-invalid cells excluded; 73 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_213932/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T21:50:21.291803-04:00 — codex-1 — automatic raw update

Pilot update: 279 raw-recomputed rows,32 FIX24-invalid cells excluded; 74 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_215021/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T23:04:11.646831-04:00 — codex-1 — automatic raw update

Pilot update: 280 raw-recomputed rows,32 FIX24-invalid cells excluded; 75 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_230411/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.

### 2026-10-09T23:15:01.735057-04:00 — codex-1 — automatic raw update

Pilot update: 281 raw-recomputed rows,32 FIX24-invalid cells excluded; 76 new completion sources observed. Immutable report /home/heck2/sbhansali8/SpecTLM/artifacts/D50_final_watch_20261009_1454/snapshot-20261009_231501/report.md and LaTeX/CSV/scaling figure. No pending result imputed; source-mixture caveat and nulls retained.
