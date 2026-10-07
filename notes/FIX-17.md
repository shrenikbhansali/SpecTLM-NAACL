# FIX-17: D-39 matched lambda ablation

## 2026-10-07T13:54:44.818801-04:00 — codex-1 — Claim and acceptance specification

Owner approved the prior exploration proposal. Build three additional FS runs lambda0/.03/.3 with unchanged D-38 data, order, seed0, 250steps,1991138tokens, initialization and optimizer. Reuse lambda.1 and controls. Keep all outcomes, use unchanged frozen evaluation6da2e42. No pause marker observed in active project paths. AGENTS builder-only restriction overridden by MASTER2.2/direct owner operational authorization.

Acceptance tests first: (a) defaults still reject changed lambda; explicit D-39 option admits only approved grid with matching config metadata, rejects missing/mismatched approval; (b) configs/manifests and resolved training plans differ only in lambda and provenance, all source hashes verified; (c) three unique FS-only jobs, no repeated controls, exact seed/budget/memory flags; (d) actual trainer and launcher dry runs pass, existing CPU regression suite passes; (e) checkpoint continuation requires sealed complete training budget and uses unchanged frozen evaluation code, distinct output paths, all variants retained. Commands/results appended below.

## 2026-10-07T14:03:47.149450-04:00 — codex-1 — Implementation and CPU checks

Tests written first:11 expected failures plus watcher import failure retained in /tmp/FIX17-tests-first.log and /tmp/FIX17-watch-first.log. Implemented explicit D-39 lambda guard (unchanged default), sealed pilot-stage cloning with only FS delta_lambda changed, three new FS jobs and original control job references. Controller loads evaluation/statistical modules from immutable6da2e42, verifies full checkpoint budget, reuses byte-identical control exports, preflights cells, and handles one documented collision retry. All302 followspec/ops tests passed (then15 targeted after identical-export-path reuse fix). Original evaluation code unchanged. Actual staged preflight follows before merge/launch.

## 2026-10-07T14:06:19.475934-04:00 — codex-1 — Review / launch readiness

Merged79a13ed and tagged run-FIX17-lambda-20261007. 303 CPU tests pass: python -m pytest followspec/tests ops/tests -q. Actual followspec.lambda_ablation source=D38training output=artifacts/M5_D39_20261007: three FS-only new jobs, each250steps/1991138tokens, same original manifests/order/masks. Six actual trainer/launcher dry runs pass; frozen-controller --once validates152 reused Frozen/control cells and waits for three complete sealed checkpoints. Evidence preflight/results.json, tests.log, watch_preflight/events.jsonl. Existing masks are unchanged, so no new data path. Worker code path .worktrees/codex-FIX17 is clean and pinned79a13ed; leave that checkout immutable. No atlas/run_cell, evaluation_jobs, or statistics changes. Ready to append three jobs to existing dispatcher; original full-budget controller continues.

## 2026-10-07T14:17:37.426274-04:00 — codex-1 — Three lambda jobs running

Allthree jobs launched14:08 on heck-srv3 GPUs1/4/5: m5-d39-l000-fs-s0, m5-d39-l003-fs-s0, m5-d39-l030-fs-s0. At14:17 first6–7trainingrecords perrun, finite/no failures. Prelaunch attempts14:07 were correctly refused because execution checkout still named codex/FIX-17; no training artifacts had been created. Detached same clean79a13ed to merged run-FIX17-lambda-20261007 tag, restarted sole dispatcher using identical argv/canonicallog. Current sole dispatcher3029674 (execsession13281); fullbudgetcontroller2981571 unchanged; lambda controller3028651 (execsession30202), output artifacts/M5_D39_20261007/watch. Dispatcherrestart/submission evidence retained. Existing full-budget comparison continues.
