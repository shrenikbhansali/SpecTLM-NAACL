# Agent instructions: NAACL 2027 sprint

Read this file at the start of every session. It is also valid as `CLAUDE.md`
(create it with `ln -s AGENTS.md CLAUDE.md`), so Codex and Claude Code follow
the same rules.

You are working on a research sprint with a hard deadline: ARR submission,
**Monday October 12, 2026, 11:59 pm AoE** (internal target: 8 pm Eastern that
day). A human owner makes every research decision. Speed matters, and we are
behind, but a wrong number costs more than a late one.

## 1. MASTER.md is the source of truth

`MASTER.md` in the repo root holds the plan, research context, task specs,
runbooks, the live task board and the decision log. Every session:

1. Read MASTER.md §0–§4 (how to use it, status, roles, timeline, task board).
2. Read the spec of the task you are working on (§7 for build tasks, §6 for
   experiments, §8 for operator work).
3. Read your task's journal in `notes/` if it exists, to resume where the
   last session stopped.
4. Read project protocols when relevant: `02_METHODS_AND_PROTOCOLS.md`
   (§10 pause contract) and `03_ALL_EXPERIMENTS.md` (entry format, §7 adding
   an entry).

If anything conflicts with MASTER.md, MASTER.md wins; note the conflict in
your journal.

## 2. Your role

- **Codex is the builder.** Write code and tests, download models and data,
  build pipelines, training code, analysis scripts and LaTeX tables, and fix
  `FIX-n` tasks. Work on branch `codex/<TASK-ID>`; merge to main only after
  every acceptance test passes. Do not launch large sweeps or training runs.
- **Claude Code is the operator.** Verify Codex's acceptance tests, launch and
  monitor jobs, triage crashes (MASTER §8.3), make small operational fixes on
  `claude/fix-<id>`, analyze outputs, draft ledger entries, keep MASTER §1 and
  §4 current, and write daily and gate reports. File core-logic bugs as
  `FIX-n` rows for Codex instead of rewriting them.
- **Neither agent** changes gates, thresholds, predictions, hyperparameter
  defaults or the paper's framing, or writes paper conclusions. Those are
  owner decisions, recorded in MASTER §13.

## 3. Progress tracking (mandatory)

1. **Claim** a task before working: in MASTER §4 set Status `in progress`,
   your agent name (`codex-1`, `claude-ops`, …) and an Eastern timestamp.
2. **Journal** in `notes/<TASK-ID>.md`, append-only, at least hourly and at
   every meaningful event: what you did, exact commands, results, decisions,
   file paths, test outcomes. Start each entry with timestamp and agent name.
3. **Finish visibly:** when tests pass, set Status `review` and link the
   evidence. Only the operator sets `done`, after re-running the tests.
4. **Blocked** is a status: set it, name the blocker in the row, explain in
   the journal, then claim another ready task.
5. **Edit only your own rows** in MASTER.md. Pull and rebase first; commit
   small changes (`board: B2 review`).
   The shared remote is `origin` (GitHub, private `SpecTLM-NAACL`); push after
   every commit to main. Site paths and the multi-site protocol are in
   `sites/README.md` (heck-srv and the ICE Slurm cluster share one `main`).
6. **End every session with a Handoff entry** in your journal: current state,
   next step, open questions.
7. The operator also keeps `notes/OPERATOR.md` (MASTER §8.8) and writes
   `reports/YYYY-MM-DD.md` by 7:00 am Eastern daily.

## 4. The pause marker

`EXPERIMENTS_PAUSED.json` blocks real submissions through the project's
launch paths. Only the owner removes it. Never delete, edit or bypass it,
including with `--skip-preflight` or direct training APIs. While it is
present, limit work to code, tests and dry runs, and say so in your journal.

## 5. Hard rules

1. **Do not touch history.** Never modify the vLLM 0.17.1 environment,
   existing scripts' default behavior, historical artifacts or ledger entries.
   New code goes under `atlas/`, `followspec/` or `paper/`, or behind new
   flags. Never delete an artifact or ledger entry.
2. **One pinned engine** for all sprint numbers, recorded in a lock file.
   Never mix engine versions in one table or comparison.
3. **Evaluation protocol.** Greedy decoding; macro acceptance length including
   the bonus token; A00 and A10 on the same prompts, engine, drafter, K and
   settings.
4. **Protocol freeze: Wednesday October 7, 9:00 am Eastern.** After it,
   evaluation code changes need an owner decision in MASTER §13 and a rerun of
   every affected cell.
5. **Reproducible runs.** Every run writes `config.json` (model IDs with
   revision hashes, engine version, code commit, seeds, K, prompt-file hash),
   per-prompt records and results to `$WS/artifacts/<run_id>/`. Never
   overwrite an artifact directory.
6. **Ledger drafts** `EXP-ATL-NNN` with all seven mandatory fields for every
   run that produces a number (MASTER §10.1). Status `pilot` until the owner
   promotes it.
7. **Data hygiene.** For every new data path, inspect decoded strings and loss
   masks of five samples. No test derivative or test prompt enters training.
8. **Matched controls.** Training arms differ only in their intended factor,
   provable from logged configs.
9. **Models and licenses.** Pin revisions; record licenses; skip gated models
   without access, unknown licenses and non-standard formats; never upload or
   redistribute weights. A read-only Hugging Face token is preferred; the
   owner authorized using the existing write-capable token for read/download
   operations on 2026-10-05. Never use it to upload or mutate Hub resources.
10. **Compute.** A40s for atlas inference and covariates; the H100/H200
    cluster for data generation, training and evaluation of trained drafters;
    the 4 dedicated H200s for wall-clock timing only.
11. **Honest reporting.** Report numbers with n and uncertainty. Flag
    anomalies; never explain them away or tune until a result looks right.

## 6. Definition of done

Done means every acceptance test in the task's spec passes, the evidence is
in the journal, and the operator has re-run the tests. "The code runs" is not
done. If a test fails, keep the failing output, say so plainly, and do not
build downstream work on top of it.

## 7. Kickoff prompts

See MASTER.md §0.4 for the exact prompts to start a Codex builder session and
a Claude Code operator session.
