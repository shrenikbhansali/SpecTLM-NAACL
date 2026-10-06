# FIX-7 journal

## 2026-10-06T17:00:45-04:00 — codex-1 — Claim

Read AGENTS.md, MASTER §§0–4, B5 and D-27/D-28/D-33/D-35, sites/README.md. Claimed FIX-7 before implementation. CPU tests and planning only; no GPU launches, no environment or pause-marker changes (marker absent). Protocol files 02_METHODS_AND_PROTOCOLS.md and 03_ALL_EXPERIMENTS.md are absent in this checkout.

`git pull --rebase origin main` in shared checkout failed: .git/FETCH_HEAD read-only. Created isolated writable clone with `git clone --no-hardlinks /home/heck2/sbhansali8/SpecTLM .worktrees/build-FIX7-20261006`, set origin to the same GitHub remote, and switched to codex/FIX-7. Pull in the clone failed DNS resolution for github.com; continue local implementation and investigate available GitHub connector for publication. Shared row mirrored for visibility.

Verified both shortfall runs: **prompts.jsonl is absent**, contrary to the initial expectation. Must use their existing partial_queries.jsonl without mutating source artifacts; planner will resolve the requested prompts.jsonl path only after validating explicit shortfall evidence.

## 2026-10-06T17:03:36-04:00 — codex-1 — Tests first and implementation

`python3 -m pytest followspec/tests/test_magpie_shortfalls.py -q`: **18 failed** before implementation (missing explicit allocator input/helper), retained in /tmp/FIX7_tests_first.txt; will archive with acceptance. Implemented explicit shortfall evidence passed by response planner to allocator. Need is computed from eligible-bank D-27 allocation; only mixtures can use D-35, bank still needs 500 for MVD. Same target seed/general-sampling/own-shuffle order. Requested prompts.jsonl maps may resolve to immutable partial_queries.jsonl only with proven D-23 exhaustion; input hashes include actual partial file, config and results. Requested generation count remains 500 for every run.

Targeted command: `python3 -m pytest followspec/tests/test_magpie_shortfalls.py followspec/tests/test_production.py followspec/tests/test_production_integration.py followspec/tests/test_bank_eligibility.py -q` → **42 passed in 35.47s**. Initial full collection failed because system Python lacks compressed_tensors (same documented FIX-6 dependency split); preserved /tmp/FIX7_full_suite.txt. Run system suite excluding native CT, and native CT separately in existing pinned interpreter read-only, with PYTHONDONTWRITEBYTECODE=1; no vLLM environment mutation. GitHub connector reads succeed, allowing remote publication despite shell DNS failure.
