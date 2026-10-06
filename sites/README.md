# Sites and repository protocol

> **Status 2026-10-06: ICE is down until Thu Oct 8 (D-19). All agents and jobs run on heck until then; see MASTER §3.2.
> `codex-ice` starts only when ICE returns; until then codex-1 builds the A40 paths (FIX-3, B5, B6 GPU acceptance).**

**Repository.** `origin = https://github.com/shrenikbhansali/SpecTLM-NAACL` (private). One `main` branch is the single
source of truth for code, MASTER.md, notes/, ledger/ and reports/ on every site (owner decision 2026-10-05: one main plus
per-site config; no long-lived site branches).

**Sites.** `heck` = heck-srv1–5 A40s (atlas inference, covariates, filters) + heck-srv6 4×H200 (A9 timing only).
`ice` = Slurm H100/H200 cluster (M2 data generation, all training, evaluation of trained drafters; MASTER §8.2).
Site-specific values live only in `sites/<site>.env`. Code must not hard-code site paths (existing `ops/waves/*` scripts are
heck run records and carry heck paths).

**Git rules (all agents, all sites).**
1. `git pull --rebase origin main` before editing MASTER.md, notes/, ledger/ or reports/; commit small; push right after.
2. Work branches: `codex/<TASK-ID>`, `claude/fix-<id>`; push them. Merge to main only after acceptance tests pass, then push main.
3. Runs start from pushed tags `run-<TASK>-<YYYYMMDD>` on main (`git tag … && git push origin --tags`), via a detached worktree.
4. Never commit artifacts, model weights, environments, tokens or `ops/runs.jsonl` (see .gitignore).
5. Agent identity per commit: `git -c user.name=<agent> -c user.email=<agent>@localhost commit …`; never `git config` in a shared clone.

**Environments.** Each site builds its own env from `atlas/env/requirements.lock` (same vLLM 0.31.0, D-08). Record the lock
sha256 and the GPU type in every run. **Never mix GPU types within one comparison** (A00 vs A10, arm vs arm, seeds of one
arm): acceptance and timing can differ by hardware.

**Artifacts across sites.** Each site keeps `$WS/artifacts/<run_id>/`. Ledger "Artifacts" fields name the site,
e.g. `ice:$WS/artifacts/<run_id>`. Small run outputs (config.json, per_prompt.jsonl, results.json, logs; not checkpoints
or features) are copied to heck `$WS/artifacts/ice/<run_id>/` for operator validation and figures; the operator checks
that every cited path resolves.

**First steps on ICE (owner).** `git clone https://github.com/shrenikbhansali/SpecTLM-NAACL.git`; fill `sites/ice.env`;
build the env with `python atlas/env/build.py --prefix $WS/.venv-atlas-031-clean --lock-output <new dir>` and compare its
freeze to `atlas/env/requirements.lock`; stage the pinned models into `$HF_HOME`; run one B2 golden cell on H100/H200 as a
site smoke test (its numbers are a new-hardware reference, not comparable to A40 cells).

**Agents per site (owner, 2026-10-05).** `codex-1` (heck) builds as before. `codex-ice` (ICE) is the builder **and** the
operator for ICE-placed work, because no Claude Code session runs on ICE: site bring-up, the Slurm launcher, the GPU parts of
B5/B6/B10/B11, and M2, M3, M4 (trained-drafter evaluation), M5–M7. It claims only those rows (Agent column may stay `codex`;
the claim names `codex-ice`). claude-ops (heck) keeps §1, A-tasks and verification: ICE tasks go to `review`, and
claude-ops sets `done` after checking the synced outputs (MASTER §0.3).
