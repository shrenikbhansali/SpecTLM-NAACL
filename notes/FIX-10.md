# FIX-10 — Immutable M2 response recovery

## 2026-10-06T17:47:50-04:00 — codex-1 — Claim

M2 parent response job target-019-base failed before generating records: engine reports availableKVcache -5.48GiB, CUDA graph memory delta -16.63GiB. Only this job failed; other same-engine/settings jobs succeed. Preserve original failure and first try identical controls in a new directory on a free slot. Need an immutable response-plan overlay so completed120other sources remain usable and assembly references the successful retry. Tests first; no data/seed/recipe changes, no overwrite, no waiver. Failed path artifacts/M2_D28_20261006/responses/runs/target-019-base; launcher M2-llama-method-data-k0-s20261006-202610061743-responses-response-019-base. Prior CPU assembly watcher correctly stopped on the failure. Original GPUqueuePID2187668 continues; do not duplicate it.

## 2026-10-06T17:50:25-04:00 — codex-1 — Root cause and recovery tests

Operator published8953842: an accidental second responsequeue started one duplicate job on heck-srv1:7 at17:43 while the canonical parent job was initializing there. Operator stopped their queue/job and preserved its unused artifacts. This explains the parent CUDA profiler seeing a -16.63GiB external memory change during graph capture. No settings/recipe change needed; retry original command in a new directory. Main push initially rejected due to this concurrent operator commit; fetched/merged without force (65760f4), preserving both agents records. Operator now acknowledges canonical queue ownership in FIX7 journal.

Tests first5missing-module failures in recovery_red.log; now5PASS. New response_recovery makes immutable overlay, updates both parent aliases, keeps successful/active paths, preserves exact generation argv except output, refuses unrelated/complete/changed sources, supports a later retry over an earlier overlay. Full regression running. Existing responsequeue remains active; assembly watcher stopped correctly.

## 2026-10-06T17:51:12-04:00 — codex-1 — Recovery acceptance PASS

Full `python3 -m pytest followspec/tests ops/tests -q`:208PASS in20.99s, artifacts/FIX7_integration_20261006/recovery_full_tests.log. Merge recovery helper now to unblock immediate unchanged parent retry; dispatcher exclusivity hardening follows. Canonical assembly must use new responses_retry1 overlay and ignore superseded failed source.

## 2026-10-06T17:53:26-04:00 — codex-1 — Dispatcher ownership hardening

Added opt-in `ops/queue.py --exclusive-owner` using a shared advisory lock keyed by owner. Test-first3missing-function failures, then18targeted testsPASS: a second process cannot acquire the same owner, distinct owners remain independent, closing owner releases lock. Existing invocation behavior unchanged unless flag used. AGENTS now requires this flag for all method-M1 dispatchers under owner authorization to adjust operational instructions. This prevents the observed duplicate-queue race; live GPU memory checks remain. Updated MASTER1 method status to prevent stale morning text from prompting duplicate launches. No scientific protocol/threshold changed.

Canonical retry overlay created from merged/tagged recoverycode ae6ddaa: artifacts/M2_D28_20261006/responses_retry1, one unchanged parent retry,120sources reused. Actual responseCLI and launcher dry runsPASS (response_retry1_preflight/results.json). Original failedparent source retained. Next resume the single canonical queue with effective job list/retryfirst, sharedownerlock and SAME launchlog; restart assembly watcher against overlay.

## 2026-10-06T17:53:40-04:00 — codex-1 — Full regression PASS

211 testsPASS in20.44s (recovery_lock_final_tests.log); default launcher/queue behavior preserved, new methodownerlock required by updatedAGENTS. Ready for review. Runtime retry remains operational M2 work, not a claim the corpus/Gate2 is complete.
