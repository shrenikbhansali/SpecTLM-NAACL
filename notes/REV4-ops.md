# REV4 operations journal (claude-ops)

### 2026-10-12T00:57-04:00 — claude-ops — collision recovery, REV4-R1 rerun, 64k fold-in
State at 00:42: no Codex agent activity since 16:09 (watchers alive); canonical queue idle since 23:57; no pause marker; disk 349 GiB.
- Failures since 21:50 were all vLLM startup collisions with other users' processes (free 4–27 GiB < 31.09 GiB required;
  Y10-t0-data-3: "No available memory for the cache blocks"). Other users hold srv1 (adokme3, 6 days), srv2/srv3/srv5 (aavsian3).
- Published immutable collision retries (same command; tag/output only), mirroring REV4_collision_retry_20261011_1553:
  artifacts/REV4_collision_retry_20261012_0046 (5 Y6 jobs) and _0048 (full timing r0, second collision on srv4:4).
  Script: scratchpad ops_retry_20261012.py / ops_retry_next.py using followspec.review_followup.publish (preflight + lock).
  rev4_results watcher accepted the replacements (reduced the 64k full SPEED cell at 00:54).
- REV4-R1: published 6 timing jobs (Nemotron none/reuse, MATH-500 first 128, b1, r0–r2) in artifacts/OPS_REV4R1_rerun_20261012_0046
  (not a replacement: original r2 exit 0 but disturbed). Reduce with followspec.rev2_timing_analysis when complete.
- 64k official results (seed 0): SPEED full 2.622 (gap 79.1%), interface 2.484 (66.4%); MATH-500 3.067 / 2.874 → paper §6.4, Fig. 4.
- Y10 NOT restarted (operator decision under owner delegation): needs 16 data jobs + manual five-sample gate + 8 long-context
  trainings on the untested SDPA path + evals; with ≤3 free A40s it cannot land before the Mon 16:00 writing freeze, and E9
  (long Alpaca data) was null. Owner can override.
Next: watch Y6 64k timing (fc r0/r2, full r0 retry2/r2) and REV4-R1; fold 64k speedup and R1 cell into the paper when reduced.

### 2026-10-12T03:20-04:00 — claude-ops — retries complete; 64k timing; REV4-R1 last process
- Collision watcher (scratchpad ops_autoretry.py) finished 03:14: Y6 64k timing all 6 processes succeeded (full r0 on attempt 6).
  REV4-R1: 5/6 processes succeeded; reuse-r1 hit the 6-attempt cap (all collisions on srv4:5/srv4:6, jdu333 cycling jobs);
  relaunched watcher with cap 12 → OPS-REV4R1-Y1-t1-reuse-math128-b1-r1-a7 published 03:15 (srv2/srv4:4–7 free now).
- Y6 64k timing (watcher reduction 20261012_031342): full/none 1.905x [1.802,2.007], full/reuse 1.426x → paper §6.4.
- ANOMALY: Y6 64k fc timing original r1 (REV4-Y6-…-fc-speed128-timing-b1-r1, srv4:7, 21:50–23:38) 1.058x vs 1.804/1.798x;
  fc/none 1.459x [1.07,1.87]. Not used in the paper; no rerun queued (interface 64k speed not needed for the story).

### 2026-10-12T05:00-04:00 — claude-ops — REV4-R1 complete
All six processes succeeded (reuse-r1 on attempt 7, srv4:4). Reduced with followspec.rev2_timing_analysis (same reducer as Y1):
artifacts/OPS_REV4R1_rerun_20261012_0046/analysis-plan.json → analysis_20261012_0500/results.json.
Nemotron reuse/none, MATH-500 first 128, b1: 1.296x [1.218,1.383]; process ratios 1.291/1.370/1.232 (wider spread than usual,
shared-node contention); cold 1.268x. Consistent with the undisturbed original processes (1.310/1.313). Paper updated (Table 2,
App. D); 32-prompt stand-in removed. REV4-R1 → review.

### 2026-10-12T13:55-04:00 — claude-ops — final paper pass; correction
- CORRECTION: my 00:57 entry attributed all Y10 data failures to GPU collisions. Codex's audit (4538e47) and the logs show 12 of 16
  failed with "query shortfall" (generator length filter rejected 1–5 of 500 questions; e.g. REV4-Y10-t1-data-0: 496/500) and 4
  with engine-startup memory failures. Decision unchanged (Y10 not restarted for the submission).
- No new results since REV4-R1 (05:00). paper/claude_final finalized for submission (see paper README "Final pass").
