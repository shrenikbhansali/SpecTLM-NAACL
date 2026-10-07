# FIX-17: D-39 matched lambda ablation

## 2026-10-07T13:54:44.818801-04:00 — codex-1 — Claim and acceptance specification

Owner approved the prior exploration proposal. Build three additional FS runs lambda0/.03/.3 with unchanged D-38 data, order, seed0, 250steps,1991138tokens, initialization and optimizer. Reuse lambda.1 and controls. Keep all outcomes, use unchanged frozen evaluation6da2e42. No pause marker observed in active project paths. AGENTS builder-only restriction overridden by MASTER2.2/direct owner operational authorization.

Acceptance tests first: (a) defaults still reject changed lambda; explicit D-39 option admits only approved grid with matching config metadata, rejects missing/mismatched approval; (b) configs/manifests and resolved training plans differ only in lambda and provenance, all source hashes verified; (c) three unique FS-only jobs, no repeated controls, exact seed/budget/memory flags; (d) actual trainer and launcher dry runs pass, existing CPU regression suite passes; (e) checkpoint continuation requires sealed complete training budget and uses unchanged frozen evaluation code, distinct output paths, all variants retained. Commands/results appended below.

## 2026-10-07T14:03:47.149450-04:00 — codex-1 — Implementation and CPU checks

Tests written first:11 expected failures plus watcher import failure retained in /tmp/FIX17-tests-first.log and /tmp/FIX17-watch-first.log. Implemented explicit D-39 lambda guard (unchanged default), sealed pilot-stage cloning with only FS delta_lambda changed, three new FS jobs and original control job references. Controller loads evaluation/statistical modules from immutable6da2e42, verifies full checkpoint budget, reuses byte-identical control exports, preflights cells, and handles one documented collision retry. All302 followspec/ops tests passed (then15 targeted after identical-export-path reuse fix). Original evaluation code unchanged. Actual staged preflight follows before merge/launch.
