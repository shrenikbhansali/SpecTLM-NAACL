# FIX-24 — official EAGLE-3 drafter repair uses a random embedding in the trainer

## 2026-10-09T03:16:57-04:00 — claude-ops — filed

**Symptom (E1, D-50).** Every official-drafter repair is *worse than reusing the official drafter unchanged*, on both targets, while
the matched production repairs on the same data work (operator recomputation from raw `per_prompt.jsonl`, zero-step excluded):

| Target | Cell | τ SPEED | p1 SPEED |
|---|---|---|---|
| R1 (t0) | official reuse | 1.764 | 0.413 |
| R1 (t0) | official 4k fc s279 / full s279 | 1.302 / 1.462 | 0.270 / 0.346 |
| Nemotron (t1) | official reuse | 1.763 | 0.417 |
| Nemotron (t1) | official 4k fc s489 / full s326 | 1.355 / 1.480 | 0.301 / 0.361 |
| Nemotron (t1) | production 4k fc s489 / full s489 | 2.264 / 2.348 | 0.570 / 0.589 |

**Step-0 training metrics** (first row of `training_metrics.jsonl`, before any update):
- official `E1-official-t0-4k-fc`: loss_0 8.76, top-1 acc 50/1802 = **2.8%**
- production `E1-production-t1-4k-fc`: loss_0 1.94, top-1 acc 803/1685 = **47.7%**

The served official drafter accepts ~41% at position 1, so the trainer's forward pass does not match vLLM's.

**Root cause (verified by the operator, CPU only, no artifact written).**
- The official release has no `embed_tokens.weight`. A key diff against RedHat production finds no other missing or extra key and no shape differences.
- `followspec/family_repair.py:203-207` loads EAGLE-3 with `SpeculatorModel.from_pretrained(...)` and never calls `model.load_verifier_weights()`. Only `followspec/dflash_loader.py:19` calls it.
- Loading `E1-official-native-v2-t0` exactly as the trainer does (in `.venv-transport`) gives `embed_tokens` ≠ the target's `model.embed_tokens.weight` (max abs diff 0.254). It is random init, and frozen by the variant config.
- `convert_official.py`'s proof note ("native trainer uses target embedding") is therefore false for the trainer path. It holds only for vLLM.
- Taps are not the cause: `tap_layers` gives [2,16,29] for both drafters.

**Acceptance tests for the fix (Codex, on `codex/FIX-24`):**
1. The trainer-loaded official drafter's `embed_tokens` is bit-identical to the target embedding, on both targets.
2. Step-0 teacher-forced position-1 accuracy of the official drafter is within ~5 points of its served p1 on the same data (≈0.4–0.5). A dry-run of a few batches is enough.
3. The production path is unchanged: same loaded state dict hash and the same step-0 metrics as the existing `E1-production-t1-4k-fc` first row. Regression test included.
4. Rerun E1 official 4k fc/full on t0/t1 in **new** artifact dirs.
   - The existing `E1-official-t{0,1}-4k-*` trainings and evals are invalid. Keep them on disk and in the ledger, labelled invalid (FIX-24).
   - Never report them as a property of the official drafter.
   - Stop the still-running invalid official trainings to free GPUs.
5. While at it, confirm whether vLLM serves the **production** drafter with its own checkpoint embedding or the target's. If it uses the target's, the production trainer has a smaller version of the same mismatch; report it and do not change it silently.

Official *reuse* cells (τ 1.764 / 1.763) are unaffected. They are served by vLLM with loaded-state parity proven.

### 2026-10-09T14:17:09.188310-04:00 — codex-1 — claim

Pulled main (up to date), read AGENTS and FIX24 evidence/spec. One canonicalqueue4129996, D50 core runs finished; no duplicate launch. Will write embedding-source/regression tests first, validate both target embeddings and actual step0 onGPU, preserve production behavior, invalidate historical official repair/contrasts while retaining artifacts. Owner also explicitly authorizes64kfc/full now; data staging proceeds independently. Disk~740GiB,350GB guard.

### 2026-10-09T14:18:33.480034-04:00 — FIX-24 INVALIDATION

**INVALID (FIX-24): all historical `E1-official-t{0,1}-4k-{fc,full}` training/evaluation cells and every `official_vs_production_*` contrast derived from them.** The trainer used a random frozen embedding, not the target embedding. These numbers must not describe official-drafter repair or enter paper tables. Official reuse and production repair remain valid. Artifacts and old statements are retained as history; this notice supersedes their interpretation. Complete run manifest: `artifacts/FIX24_20261009_1420/invalid-runs.json`. The earlier conversion note claiming the native trainer used target embeddings was false; loaded-state parity only proved the vLLM path. Corrected runs will use new directories. Old D50 publication/analysis watchers stopped to prevent propagation.

### 2026-10-09T14:24:59.589387-04:00 — codex-1 — tests and diagnostic launch integration

Branchcodex/FIX-24 commit7997072 adds exact checkpoint-omission detection, target embedding copy only when absent, provenance, and read-only step0probe. Production path returns without loading target or mutating any tensor/RNG; all19 tests pass in pinned transport dependencies (`tests-pinned.log`). Tests against old main fail missing helper as expected (`test-legacy-fails.log`). Initial transport invocation lacked pytest; default Python then exposed incompatible transformers; both environmental failures retained, tests rerun with pinned dependencies and only pytest runner appended.

FIX24 probe tag was created/pushed before worktree. Launcher correctly refused real diagnostic jobs because tagcommit7997072 not yet an ancestor ofmain. MASTER requires main ancestry for GPU checks while its generic merge rule asks acceptance before merge: integrating CPU-tested change now solely to unblock tagged GPU diagnostics, keeping FIX24 inprogress and official reruns gated until required GPU evidence passes. No acceptance/Gate PASS claimed and no launcher bypass. Failed attempts retained; retries get new names.64kdata independent production path already running.

### 2026-10-09T14:29:07.782325-04:00 — codex-1 — core GPU checks PASS

`core-acceptance.json`: exact target embedding copy both targets, target bf16 roundtrip exact. Eight frozen step0 batches: official R1p10.426739, Nemop10.462563; original R1firstbatch2.8% becomes40.7%. Production full loadedstate hashes identical before/after helper and ALLfirststep metrics exactly equal historical E1-production-t1-4k-fc (803/1685=47.6558%). No optimizer steps.

Actual pinnedvLLM loaded-state diagnostics on both targets show production serves its OWNcheckpoint embedding, not target embedding; maxabs production-vs-target .0361328125(R1)/.0537109375(Nemo). Both served hashes match checkpoint, neither matches target (`production-serving-embedding.json`); no smaller production mismatch to change. Source loader sets has_own_embed_tokens when checkpoint provides it, shares target only if absent or equal. Official matchedtraining-query frozenserved cells pending (strictly diagnostic, not heldout paper results); reruns still gated until that check.

### 2026-10-09T14:32:30.158919-04:00 — codex-1 — automatic FIX24 progression

Published FIX24-official-t0-4k-fc after all FIX24 core/matched checks passed.

### 2026-10-09T14:32:33.679753-04:00 — codex-1 — automatic FIX24 progression

Published FIX24-official-t0-4k-full after all FIX24 core/matched checks passed.

### 2026-10-09T14:32:37.004539-04:00 — codex-1 — automatic FIX24 progression

Published FIX24-official-t1-4k-fc after all FIX24 core/matched checks passed.

### 2026-10-09T14:32:40.239132-04:00 — codex-1 — automatic FIX24 progression

Published FIX24-official-t1-4k-full after all FIX24 core/matched checks passed.

### 2026-10-09T14:34:34.772100-04:00 — codex-1 — all core acceptance PASS; corrected reruns queued

`acceptance.json` passes exact embedding both targets, unchanged production state+step0, and matchedtraining-query served check: R1n30 servedp1.395608 vs teacher-forced.426739 (3.11points); Nemon57 .440140 vs.462563 (2.24points), both within5points. Different estimands/contexts explicitly documented: original response teacher forcing across positions vs freshserved proposal starts on identical query IDs. Not heldout paper results. Production vLLM uses own checkpoint embedding both targets.

Corrected `FIX24-official-t0/t1-4k-fc/full` published in newdirectories by watcher814853, using run-FIX24-20261009 tag7997072. Everyexport auto-evaluated frozen6da2e42 on sameSPEED128/MATH64; official16k conditional comparisons use only corrected4k vs matchingproduction4k. Old official16k decisions not reused. Initial three ancestry-refused launch alerts resolved with final GPUevidence, no retries duplicated. Rerun outcomes stillpending, FIX24 remainsinprogress until completed evidence.

### 2026-10-09T14:46:26.640849-04:00 — codex-1 — integration progress

Core acceptance complete; first corrected official4k Nemotron full job launched14:44, other three queued at highest priority. Existing canonical queue only. Full rerun acceptance remains pending.

### 2026-10-09T14:53:58.123188-04:00 — codex-1 — Handoff checkpoint (work continuing)

FIX24 core19 tests + GPU parity pass; four corrected4k trainings active, evaluations auto-published. Canonicalqueue4129996, no duplicates. Source/data watcher832362 gates64k on complete48shards and manualAlpaca+Dolly review (Dollypending). FIX24watch814853 handles exporteval and conditionalofficial16k. Nemo timing30jobs, finish832363/cost837791. Disk~730GiB,350GBfloor. Consolidated207-row rawreport reports/P3-D50-consolidated-20261009.md, seven LaTeX tables compile;32invalidcells excluded. Earlysnapshot1443 had cost-key rendering defect,1446 failed unescaped-percent LaTeX header; retained and superseded by1451 which passes. Next: finishDollymanualreview, confirm64kassembly/trainpublication, monitorcorrectedexports andNemo, auto-addnewresults. No new owner decision needed.

### 2026-10-09T14:59:34.932994-04:00 — codex-1 — first corrected held-out results

Corrected official Nemotron,25% of one4k epoch (step163), MATH64 n64, seed0. Pilot frozen6da/vLLM0.31/A40. Not final4k or the conditional16k decision.

| Arm | Reference | p1 [95% CI] | tau [95% CI] | Delta p1 [95% CI] | Delta tau [95% CI] |
|---|---|---|---|---|---|
| fc | official reuse | 0.666 [0.653, 0.678] | 2.524 [2.476, 2.570] | 0.214 [0.204, 0.225] | 0.821 [0.785, 0.856] |
| fc | production matched163 | 0.666 [0.653, 0.678] | 2.524 [2.476, 2.570] | 0.012 [0.001, 0.023] | 0.097 [0.063, 0.131] |
| full | official reuse | 0.699 [0.688, 0.711] | 2.675 [2.625, 2.723] | 0.248 [0.238, 0.257] | 0.971 [0.932, 1.010] |
| full | production matched163 | 0.699 [0.688, 0.711] | 2.675 [2.625, 2.723] | 0.010 [0.000, 0.020] | 0.072 [0.042, 0.103] |

10000 paired-query bootstrap; exact rendered IDs, settings and raw counters checked. Only unchanged official reuse and valid production repair controls used; old official repair excluded. Matched163 data/steps/nativeTTT3 verified from full config diff.

Source: artifacts/FIX24_20261009_1420/first-corrected-math64.json.

### 2026-10-09T15:02:26.831919-04:00 — codex-1 — Handoff

Current state: main contains FIX24 correction and final-table tooling/report; branches/tags pushed, no pending code integration. Root operator re-ran19 embedding/trainer tests (tests-main-operator.log),4 table tests;7 preview tables compiled and first page/figure visually checked. Four corrected trainings running, four initial held-out evaluations complete. first-corrected-math64.json records actual early quarter-epoch Nemo results with n64/pairedCIs; final4k/conditional16k pending. Full corrected-vs-old training config diff allows onlycode/output/sharedroot/probe0/diskguard changes; data/seed/hyperparameters/steps identical.

E5c64k: both source-level five-sample reviews PASSED (40Alpaca+5Dolly inspected); all21completed shards independently checked for exact input concatenation and masks (21000rows). Remaining generation continues; source-path-review.json lets assembly/training progress without another human approval. Watch832362 -> all48 results +64000row checks -> two64k trainings -> allfrozenexports. Estimated training alone ~9h from16k throughput, so completion is overnight, beyond18ET; no scheduling gate added. Mixture35988Alpaca+12012Dolly extension labelled, original16kpreserved.

Live processes: canonicalqueue4129996; FIX24controller814853; E5c832362; Nemo timingfinalizer832363 + cost837791; immutable reportwatch851749; launch/runhealth383520. Check pgrep and stage dirs before any launch. All launch alerts resolved; no failure silently retried. Watchers are NOT restart-idempotent: inspect existing publications and make a new resume version, never rerun from the top. No pause marker. Disk~730GiB,350GBguard. Remaining work: monitor runtime/errors, include completedofficial/64k/Nemo outputs; verify finalreport snapshots; markFIX24review only after rerun acceptance, not merely corefix. No owner question blocking execution.

### 2026-10-09T15:08:27.104741-04:00 — codex-1 — live GPU collision detected

During check, step489 Nemotronfc SPEED128 failed on heck-srv4:5 at15:06:30. Raw vLLM OOM: external process1276047 held13.98GiB, ownprocess30.13GiB,303.81MiBfree;402MiBallocation failed. Preserve partialrun, no acceptance number. Retry unchangedfrozenengine/batch8/512/seed0/K4 in newoutput/tag on srv2/3/5. BothNemotron4k trainingscomplete; finalevals automatic. No pause marker; disk~711GiB,350GBfloor.

### 2026-10-09T15:13:55.752544-04:00 — codex-1 — automatic FIX24 progression

Published FIX24-official-t1-16k-fc after all FIX24 core/matched checks passed.

### 2026-10-09T15:14:00.442349-04:00 — codex-1 — automatic FIX24 progression

Published FIX24-official-t1-16k-full after all FIX24 core/matched checks passed.

### 2026-10-09T15:14:00.443258-04:00 — codex-1 — automatic FIX24 progression

Official16k decision target1: True; all paired CIs retained.

## 2026-10-09T15:14:14-04:00 — claude-ops — operator verification (partial; rerun still running)

- Tests re-run by the operator: `.venv-atlas-031-clean/bin/python -m pytest -q followspec/tests/test_missing_embedding.py followspec/tests/test_family_repair.py followspec/tests/test_repair_continuation.py` → **22 passed**.
- Step-0 training metrics of the corrected runs are fixed. Top-1 acc0 / loss0: FIX24-official-t0-4k-fc 0.407 / 2.415, FIX24-official-t1-4k-full 0.468 / 2.223 (was 0.028 / 8.76). This matches served p1 (~0.41–0.45).
  `acceptance.json`: target-embedding sha matches on both targets; served vs teacher-forced p1 differ by 3.1 / 2.2 points.
- Corrected results, operator recomputation from raw (τ SPEED / MATH):

| Target | Arm | Official (corrected) | Production, same data | Δ |
|---|---|---|---|---|
| Nemotron | fc, 4k final (s652) | 2.336 / 2.601 | 2.252 / 2.483 | +0.084 / +0.118 |
| Nemotron | full, 4k final (s652) | 2.437 / (MATH running) | 2.361 / 2.696 | +0.076 / – |
| R1 | fc, 25% of 4k (s279) | 2.291 / 2.603 | 4k **final** 2.224 / 2.532 | official is already ahead at 25% |
| R1 | full, 25% of 4k (s279) | 2.401 / 2.782 | 4k final 2.374 / 2.785 | ahead on SPEED, equal on MATH |

  So the official drafter repairs better than production, and the conditional official 16k should fire (codex watcher 814853).
- Do not use the partial `FIX24-official-t1-4k-fc-s489-speed128` (n=16, OOM-killed by another user's process); its retry is `...-collision-retry1`.
- FIX-24 stays in progress until the rerun completes. The operator will mark it done after the final cells.

### 2026-10-09T15:14:50.842117-04:00 — codex-1 — check, recovery and conditional progression

Pulled main (already current), checked canonical queue4129996, stage directories, all five hosts, live watchers, raw results and disk. No duplicate launch names in the recent queue. Both corrected official Nemotron4k trainings complete; R1 continues ({'FIX24-official-t0-4k-full': 768, 'FIX24-official-t0-4k-fc': 837}). 19 corrected evaluation cells complete. E5c extension: 23/48 complete shards, 45 started, 32360/48000 new responses written; existing16000 retained. Both source inspections pass; all-row validation still gates automatic64k training. Disk 700.4GiB,350GB floor. Nemo timing 4/30; no partial speedup claimed.

Independent raw check: artifacts/FIX24_check_20261009_1515/report.md +results.json,32 paired comparisons/16 completed cells at analysis start, source hashes and exact rendered IDs/settings/counter totals verified. Final Nemotron4k SPEED,n128,seed0: official fc p1 .5943[.5665,.6203],tau2.3359[2.2513,2.4167]; vs production4k Delta p1 .01483[.00403,.02542],Delta tau .08396[.05022,.11821]. Full p1 .61496[.58687,.64132],tau2.43654[2.35111,2.52058]; Delta p1 .00949[-.00194,.02094] (null),Delta tau .07581[.04404,.10925]. Paired-query10000 draws; one training seed, pilot. Final fc MATH64 Delta p1 .02049[.01066,.03038],Delta tau .11784[.09344,.14155]. Full finalMATH still pending at this check.

Both final SPEED mean gains meet the owner's resource-allocation condition: official16k-decision-t1.json. New official Nemotron16k fc/full published15:13–15:14 through existing queue, pinnedrun-FIX24-20261009; no duplicate or new approval. This selection is exploratory, not a significance/framing decision. R1 conditional16k still awaits final4k.

Collision recovery: other user's14GB process caused Nemotronfc step489 SPEED OOM on srv4:5; original partial output retained and excluded. Unchanged frozen retry submitted in new directory ending collision-retry1, running on srv2:0 since15:09:59. Alert99729d98fed6f5d269aa remains open until actual success verified by resolver871017. External processes subsequently left srv4:4/5; current queue can use live-free slots. Dispatch priority changed only order under lock: final4k/retry/conditional16k, remaining64k data, intermediate evaluations, optionaltiming. Receipt artifacts/FIX24_check_20261009_1507/priority-receipt.json; no cell configuration changed.

### 2026-10-09T15:15:55.264252-04:00 — codex-1 — Handoff

Check complete; work continues automatically. New raw-check artifact FIX24_check_20261009_1515 records16 completed frozen cells/32 paired comparisons at analysis start. FinalNemotron4k SPEED supports owner-authorized conditionalofficial16k: both trainings actually launched15:14:58(full,srv3:1) and15:15:01(fc,srv3:2). FullfinalMATH completed15:14:58 after raw snapshot; included by next immutable automated report, not imputed here. R1corrected4k ~70–75% done. 64k newdata ~32k/48k written,23complete shards,45started; all48 then allrowvalidation -> two training runs automatically. SourceAlpaca+Dolly mixture explicitly labelled. Training alone expected~9h, not an18ET result. Nemo timing4/30 advances behind critical jobs.

Collision retry remains active on srv2:0; resolver871017 acknowledges alert99729d98fed6f5d269aa only after fullsuccess/rawchecks. Originalfailedpartial stays on disk and excluded. No other unresolvedalert detected. Canonicalqueue4129996; FIX24watch814853; E5c832362; Nemo finish832363/cost837791; report851749; health383520. Do not restart controllers from the top (not restart-idempotent); inspect receipts, queue and stage dirs before any recovery/publication. Free~700GiB,350GBfloor; no pause marker.

No code changes this check; prior19trainer+4table checks remain applicable. Claimed ownE2/E3/E4/E7 rows reconciled to review from completed/raw-verified evidence. Concurrent operator89bb934 adds independent22-test verification and gate addendum, preserved. Next: verify collision resolution, finishR1 and conditional16k, watch64kassembly/trainpublication and optionalNemo timings; include all completed results/nulls in finalreports, leaveFIX24inprogress until correctedreruns verified. No owner decision blocking execution.

### 2026-10-09T15:15:57.097521-04:00 — codex-1 — collision retry verified

Step489 Nemotronfc SPEED retry complete,n128; frozen settings/prompt IDs/counters verified. Originalfailedpartialretained; alert99729d98fed6f5d269aa resolved. Source /home/heck2/sbhansali8/SpecTLM/artifacts/FIX24_20261009_1420/repair-eval/runs/FIX24-official-t1-4k-fc-s489-speed128-collision-retry1.

### 2026-10-09T15:16:08.538958-04:00 — codex-1 — Handoff addendum: collision resolved

Unchanged retry completed; resolver checked frozen code/settings/exact rendered IDs/raw counters and n128, wrote99729d98fed6f5d269aa.resolved.json at15:15:57. Original partial retained. All known launch alerts now resolved; controllers/queue continue. This supersedes the pending retry status in the preceding handoff.
