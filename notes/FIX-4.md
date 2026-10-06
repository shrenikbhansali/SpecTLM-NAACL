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

## 2026-10-06T02:58:48-04:00 — codex-1 — Claim

Claimed FIX-4 ahead of P1 B10; owner method priority. Read D-27, §5.4–5.5, B5/B6 specs, ONLINE_TRAINING and filed FIX-4 request. Existing B3/B5 operator done; B6 D-26 acceptance passed, review. Build CPU planner/orchestrator under followspec, branch codex/FIX-4; operator launches production GPU jobs. Tests first for deterministic sampling/rank limits, shared training-only filter reference, admitted≥20/≤30 and≤2rounds, prompt allocation/disjointness/50:50/parent25%, exact generation flags, D-21 pair integrity, logged tail matching, native batch audit and readiness fail-closed. No pause marker; B10 OOM preserved, no production launch.

## 2026-10-06T03:22:19-04:00 — codex-1 — Planner, assembly and real-bank compatibility

Branch f461298 pushed, unmerged;97 followspec CPU tests PASS (`artifacts/build_logs/FIX4_full_views_20261006.log`). Tests first: FIX4_before (missing planner), FIX4_assembly_before (missing assembler), FIX4_adapter_views_before (missing bank-view helper); all preserved. Pure contract tests and a CPU end-to-end fixture exercise paired originals, all4 arms,25% parent/50:50 child ratios, source tampering, real B5 dataset views, native-audit interface, mask-review hashes and final config resolution. Fixture uses a stand-in sampler/tokenizer and does not claim GPU or production-corpus acceptance. Exact native sampler and launcher dry runs still required. One initial planner test was terminated (own pytest PID943185) because an unnecessarily repeated hash-set construction was slow; precomputed that set, retry passed.

Implementation: followspec.production CLI stages prepare/materialize/admit/mixture-prompts/responses/render-local/assemble/finalize, docs PRODUCTION_DATA.md. Two candidate rounds frozen before scores; no third round. Explicit operator validation-query input (subset of general20000), disjoint parent/child general partition, shared general reuse across child targets, no within-target repeats. Per-target integer rounding can drop one final query to make halves exact, logged. Fixed eight-record ordering blocks (6 children,2 parents) allow suffix-only matching while retaining ratios. Largest common token prefix that passes every native seed is selected; no feasible prefix is a recorded failure, no resampling/threshold relaxation. Parent order stays shared across arms. All GPU work is emitted as argv-based ops/queue jobs with fresh compile; none launched.

Real CPU preparation PASS on all33 frozen bank entries (`artifacts/FIX4_planner_acceptance_20261006/plan`), immutable e80d648, seed0,rankcap256,60 frozen candidate definitions,128 training-general references. Commands and PIDs in launch.json/materialize_launch.json. First CPU materialization failed on third candidate; first2 outputs and failure log preserved. Two Hiranmai49 bank adapters include saved `lm_head.base_layer.weight`, which strict B3 refuses. Read-only full tensor check (`artifacts/FIX4_saved_heads_20261006`) found159176 differing values each, maxabs2.9802322387695312e-8; they are NOT exact base copies. An attempted exact-copy-only test was abandoned before code implementation; failing output FIX4_saved_head_before retained.

Pinned local vLLM0.31.0 source supplies the actual fix: LoRAModel.from_lora_tensors explicitly skips is_base_embedding_weights, exactly `.embed_tokens.base_layer.weight` and `.lm_head.base_layer.weight` (lora/lora_model.py139; lora/utils.py223). PEFT loads these into its base_layer, so original files would contaminate the shared base in online capture. New explicit materialization-only factor views retain all LoRA factors bitwise and adapter config bytes; omit only the two vLLM-skipped suffixes; record original hashes/keys/pin; reject any other extra tensor. Registry uses views for B3 mixtures and PEFT capture; vLLM generation continues to use original pinned adapters with the same effective factors. B3 strict default is unchanged. Next: rerun actual round1 materialization from f461298, verify real pinned vLLM loader equivalence and PEFT base restoration, then end-to-end native CPU audit and launch-command validation before merge.

No active pause markers. Reserved methodGPU6/7 remain free. Referenced legacy protocol files are absent under this checkout's documented paths; MASTER pause/ledger contracts apply. No research cutoffs changed.
