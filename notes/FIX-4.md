# FIX-4 — M1/M2 production assembler (filed by claude-ops)

## 2026-10-06T02:37-04:00 — claude-ops — Filed

The B5/B6 pieces pass, but M1/M2 production involves ~10 manual stages (followspec/ONLINE_TRAINING.md) and needed recipe choices that are now
fixed by **§13 D-27** (owner-delegated). Please build one orchestrator (CPU planning + launcher-ready job files; operator launches GPU jobs via
`ops/launch.py`/`ops/queue.py`, fresh compile, HF_HUB_OFFLINE) that:
1. samples mixture candidates (§5.4, fixed seed) and emits atlas.filter_pool jobs for the 33 bank + candidates on a shared 128-query
   **training-general** reference, then runs `followspec.mixture_targets` admission (2 rounds max; ≥ 20 needed);
2. assigns per-target prompts per D-27 (MVD 1,000/bank child; FS round(33,000/n)/target; 50:50 Magpie:general; disjoint seeded general split;
   parent share 25% base-on-general);
3. emits generation job lists (child responses, base responses for PO-D and parent share) with `--allow-a40-production`;
4. runs paired trimming (D-21), builds FS/MVD/PO-D/PO-T manifests, and applies D-27(6)'s logged tail truncation to equalize tokens/steps;
5. runs `followspec.audit_batches` and the 5-sample decoded/mask audits; writes a single readiness report.
Inputs ready: frozen pools `atlas/pools/`; bank Magpie training prompts are coming from A3 phase 2 (operator, 500 per bank child).
