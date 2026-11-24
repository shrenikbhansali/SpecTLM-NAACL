# Rebuttal status

### 2026-11-24T14:11:37.162068-05:00 — codex-1 — kickoff
Finished: read AGENTS/MASTER0–4, supplied experiment handoff and reviews; extracted submitted PDF for reading. Pulled main (up to date).
Running: hardware/env/path inventory; raw E1 reproduction; no GPU jobs launched yet.
GPU-hours: 0 for new rebuttal experiments.
Needs a decision: none yet; source-code/spec ambiguities will be recorded before dependent jobs.
Deviations: workspace renamed SpecTLM→ReFit and HFcache→caches/huggingface. Existing path-migration edits are uncommitted; preserve them and old artifacts. Historical CLEANUP-1 interrupted before deletion; cleanup is deferred during rebuttal.

## First-hour checklist (in progress)
- Available A40s and reservation horizon: querying live nodes. Authentication needs GSSAPI enabled; initial -F /dev/null attempt failed, normal GSSAPI SSH succeeds.
- Data/checkpoint/config/log paths: indexing existing records and validating moved paths.
- Interaction: existing P2 report states d-b-c+a, paired 10,000 resamples; verify implementation and raw records next.
- Engine: paper pinned vLLM0.31.0; probing current pinned envs rather than default shell Python.
- SPEED multilingual languages: inspect exact evaluation rows.
- Dataset downloads: owner authorized listed plan execution; public license checks required before use. If licenses or access block a listed source, report and proceed elsewhere.
- GPU priority: apply plan defaults/cuts once live count is known; no reservation beyond the current live-free view is assumed.
