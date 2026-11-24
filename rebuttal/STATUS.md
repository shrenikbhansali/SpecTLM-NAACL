# Rebuttal status

### 2026-11-24T14:48:13-05:00 — codex-1 — owner jobs preempted; reproduction running
Finished: E1 independent raw crossover reduction (12 groups, n64 each); E10 environment audit; eight existing LoRA checkpoint ablations; EDA additive-expert export implementation and unit tests. Cancelled four own competing GPU workloads and six dispatcher workers, with before/after evidence in cancellation_20261124_1444.
Running: one canonical queue PID590758, seven remaining exact reference reproductions; three raw-counter checks already pass (R1 full/dedicated SPEED, Nemotron full SPEED). New training is staged but gated on complete reference checks.
GPU-hours: 0.6080 completed reproduction GPU-hours, including failed startup attempts; active cells not included. E1/E10 each0; E2/E4 implementation CPU-only so far.
Capacity: eight live-admitted A40 slots; no guaranteed reservation horizon. Owner is requesting dedicated capacity. Previously only three were available; scratch10-epoch plans are staged under that contingency but have not launched.
Needs a decision: none for cancellation or baseline restoration. Before starting scratch, reconcile actual available capacity with the plan's 10/20-epoch rule and enforce Nov28noon stop.
Deviations: exact original MATH500 used for paper-anchor reproduction; new rebuttal comparisons remain first128. Broken old HF cache paths restored to new directories with original SHA256 verification. First R1 reuse run used a converted native checkpoint; retain it as a superseded pilot and use exact released files for reproduction.

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
