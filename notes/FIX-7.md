# FIX-7 journal

## 2026-10-06T17:00:45-04:00 — codex-1 — Claim

Read AGENTS.md, MASTER §§0–4, B5 and D-27/D-28/D-33/D-35, sites/README.md. Claimed FIX-7 before implementation. CPU tests and planning only; no GPU launches, no environment or pause-marker changes (marker absent). Protocol files 02_METHODS_AND_PROTOCOLS.md and 03_ALL_EXPERIMENTS.md are absent in this checkout.

`git pull --rebase origin main` in shared checkout failed: .git/FETCH_HEAD read-only. Created isolated writable clone with `git clone --no-hardlinks /home/heck2/sbhansali8/SpecTLM .worktrees/build-FIX7-20261006`, set origin to the same GitHub remote, and switched to codex/FIX-7. Pull in the clone failed DNS resolution for github.com; continue local implementation and investigate available GitHub connector for publication. Shared row mirrored for visibility.

Verified both shortfall runs: **prompts.jsonl is absent**, contrary to the initial expectation. Must use their existing partial_queries.jsonl without mutating source artifacts; planner will resolve the requested prompts.jsonl path only after validating explicit shortfall evidence.

## 2026-10-06T17:03:36-04:00 — codex-1 — Tests first and implementation

`python3 -m pytest followspec/tests/test_magpie_shortfalls.py -q`: **18 failed** before implementation (missing explicit allocator input/helper), retained in /tmp/FIX7_tests_first.txt; will archive with acceptance. Implemented explicit shortfall evidence passed by response planner to allocator. Need is computed from eligible-bank D-27 allocation; only mixtures can use D-35, bank still needs 500 for MVD. Same target seed/general-sampling/own-shuffle order. Requested prompts.jsonl maps may resolve to immutable partial_queries.jsonl only with proven D-23 exhaustion; input hashes include actual partial file, config and results. Requested generation count remains 500 for every run.

Targeted command: `python3 -m pytest followspec/tests/test_magpie_shortfalls.py followspec/tests/test_production.py followspec/tests/test_production_integration.py followspec/tests/test_bank_eligibility.py -q` → **42 passed in 35.47s**. Initial full collection failed because system Python lacks compressed_tensors (same documented FIX-6 dependency split); preserved /tmp/FIX7_full_suite.txt. Run system suite excluding native CT, and native CT separately in existing pinned interpreter read-only, with PYTHONDONTWRITEBYTECODE=1; no vLLM environment mutation. GitHub connector reads succeed, allowing remote publication despite shell DNS failure.

## 2026-10-06T17:06:37-04:00 — codex-1 — Real CPU planning acceptance

Fresh combined map: `artifacts/FIX7_acceptance_20261006/combined_prompt_paths.json`: 30 bank entries copied from the requested original bank map + all 30 admitted mixtures mapped to their requested retry1/runs/<id>/prompts.jsonl. Full exact argv: `artifacts/FIX7_acceptance_20261006/planning_candidate_command.json`; invoked system `python3 -m followspec.production responses` with the requested admission2, validation_general512, all_existing_eval_paths exclusions plus SPEED, and clean tagged checkout `.worktrees/FIX7-planning-candidate-20261006` (232df22). Output `artifacts/FIX7_acceptance_20261006/planning_candidate`: **exit 0**, 121 planned GPU response jobs (60 child + 60 paired base + 1 parent base), 61 CPU render commands. All 30 bank + 30 mixtures retained. FS/MVD child counts 30,000 each; parents 10,000 each. Both assignment and results record r1-03 count364/need250 and r1-06 count388/need250 with decision D-35. No GPU work launched.

Inspected five raw decoded prompts per shortfall in `five_samples_per_shortfall.json`; examples include desert size, concert artist, meditation, maximum-of-list coding and Unix commands. Embedded-answer prompts remain per D-23. Loss masks are unavailable at this planning stage (no response tokens generated), recorded explicitly; downstream B5 rendering/generation retains existing mask checks.

System CPU suite (excluding native CT only) initially **260 passed, 1 expected failure** (`test_engine_matches_committed_pin`, vLLM absent), /tmp/FIX7_cpu_suite.txt; native CT separately **1 passed**, /tmp/FIX7_native_ct.txt. Added regressions for existing prompts.jsonl shortfall output and preserved exact500/eligibility/mixture-bound/validation/forbidden/row-split checks.

GitHub connector recovered remote main f75d250 (operator FIX-8 update). Imported exact remote blobs/tree/unsigned commit with SHA verification using /tmp/FIX7_import_remote.py, then rebased; only claim-row context conflicted, resolved by preserving remote MASTER verbatim except own FIX-7 row. Connector publication is necessary because shell GitHub DNS remains unavailable; shared .git remains untouched.
