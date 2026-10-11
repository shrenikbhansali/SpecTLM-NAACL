# REV4 journal

### 2026-10-11T02:35-04:00 — claude-ops — plan and paper edit
Owner (direct, ~02:25): remove release promises; run all remaining experiments we want → D-56.
- Paper: removed "per-model results will be released with the paper" (App. F census); no other release/code promises remain
  (grep for releas/available/will be/github). Rebuilt: 14 pp, content ends p. 8, no overfull boxes.
- Plan: reports/REV4-plan-20261011.md (Y1–Y10). Board rows REV4-P0/P1/P2 added as ready for codex.
- State at planning: canonical queue (owner method-M1, log artifacts/M2_D28_20261006/response_queue.log) polling; no pause marker;
  heck-srv2/3 GPUs idle, srv1 all 8 hold ~44 GB at 0% util, srv4 partially occupied; /home/heck2 324 GiB free (~348 GB), just below
  the 350 GB floor → Codex must reclaim D-47 regenerable caches before launching.
- Inputs confirmed: z-lab/Qwen3-8B-DFlash-b16 in census CSV (R1-0528-Qwen3 DFlash retention .81 [.79,.84]); E5c generic64k data exist.
Next: Codex claims REV4 rows and dispatches; claude-ops verifies P0 results ~14:00 ET and folds strong results into paper/claude_final.
