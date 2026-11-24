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
