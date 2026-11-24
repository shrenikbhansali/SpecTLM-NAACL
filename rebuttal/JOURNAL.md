# Rebuttal journal (append-only)

## 2026-11-24T14:19:15-05:00 — codex-1 — kickoff and E1/E10
Owner authorized the supplied rebuttal handoff. Read AGENTS.md, MASTER0–4, handoff, submitted paper and actual reviews. Board claimed and pushed in 539b1f1. Build branch codex/REBUTTAL; frozen 6da2e42 worktree and run-* tags created immediately. Existing unrelated dirty files preserved; no historical outputs modified.

Commands/results:
- `pdftotext -layout` for both supplied PDFs; extracts in rebuttal/source_text; input SHA-256 manifest committed.
- Queried all five heck nodes via SSH with GSSAPIAuthentication=yes. All 40 A40s occupied; none allocated to this campaign. No queue running. GPU shortage question sent to owner; no slots assumed available.
- `.venv-atlas-031-clean/bin/python` and `.venv-transport/bin/python`: actual torch imports succeed; vLLM0.31 metadata matches original timing configs. Full `pip freeze` saved in E10.
- `python -m unittest discover -s rebuttal/tests -p test_crossover.py`: first failed because implementation absent (tests first), then all four passed.
- `python -m rebuttal.crossover --workspace /home/heck2/sbhansali8/ReFit --output /home/heck2/sbhansali8/ReFit/rebuttal/E1`: 12 groups, 156 quantities; original effects and CIs reproduced to 1e-14. Source files hashed. 0 GPU-hours.

Decisions/findings: all new code/output under rebuttal/. Workspace/cache relocated; old launch paths must be remapped in new manifests, not edited in historical artifacts. Existing queue memory-only guard could admit a 100%-busy GPU at 983 MiB; add opt-in utilization/process guard before queueing. EDA paper/code disagree on gates; pending owner response to code-vs-paper and missing PCA/quantile choices; implement independent prerequisites meanwhile. E1 interaction is standard d-b-c+a and not an extra contribution beyond averaged main effects. SPEED multilingual languages are vi, es, ar, fr, th (plus en), so E8 can use the explicit five-language mix.

## 2026-11-24 14:28 ET — codex-1 — implementation and live occupancy
Implemented opt-in queue utilization/process admission and in-memory historical-path remapping; defaults unchanged. Added decoder_head_lora and complete-epoch scratch batching with one uninterrupted cosine horizon. Tests written first and observed failing imports, then passed. Native pinned trainer has no pytest; installed pytest8.3.5 into an isolated rebuttal/test-tools directory, without changing pinned envs. Default-shell regression attempt:43 pass/1 import failure due to its older transformers; actual pinned-trainer run with isolated test tools:47 passed, including existing family repair, continuation, queue regressions and new EDA algebra tests.

EDA port: code-first as specified; one shared + one private expert gives an additive SwiGLU, so concatenating MLP weights represents the same function without modifying vLLM. FP64 forward/input-gradient equivalence tested; real vLLM loading/acceptance remains unverified. PCA128/90th-percentile selection settings will be explicitly documented as port choices, frozen before evaluation. No baseline chosen by poor performance.

Fresh occupancy14:24: one transient free slot srv3:0; swebster36 13 GPUs, adokme3 12, swoo81 8, jdu333 4, own account2. Own srv3:2/srv5:4 jobs are amazidea continual.cli; left untouched. Snapshot recorded. All13 required existing training-data/checkpoint paths located in asset_inventory.json. Nemotron interface seeds1–2 exist in REV2_E8; whole-LoRA Nemotron seeds1–2 still needed. Canonical queue log will be resumed with old-root paths remapped in memory; no historical outputs rewritten.
