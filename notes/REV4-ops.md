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
