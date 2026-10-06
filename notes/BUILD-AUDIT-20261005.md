# Build and run-readiness audit — 2026-10-05T22:00:57-04:00

codex-1; requested by the owner. Audited main bdfe287 and all task branches, MASTER §§0–4/7/13, Gate 1 and daily reports, operator handoff, journals, actual run records and live GPUs. This is a builder audit, not a gate decision or a replacement for operator reports.

## Current state

No active experiment pause in the repo, its ancestors or the historical live launch root. Archived marker SHA matches the authorization record. **No sprint GPU job or B1 curator is running.** At 21:57 ET, 33/40 A40s were free on heck-srv1–5 (2/8/8/7/8); occupied GPUs were left alone. Shared /home/heck2 has **1.5 TiB free, 99% used**. Shared H100/H200 cluster access remains undocumented; dedicated H200s remain reserved for A9.

| Work | Landed on main? | Evidence and remaining work |
| --- | --- | --- |
| B2 atlas harness | Yes; operator marked done | vLLM0.31.0 lock, 14 tests, six golden cells; operator verification in notes/B2.md |
| W1 paper skeleton | Yes; operator marked done | Both anonymous ACL builds passed; method 2 pages, atlas 1 |
| O1 orchestration | Yes; operator marked done | ops launch/status tooling, 8 recorded tests |
| A1 engine checks | Results/docs landed; done | 71 included GPU cells; independent recomputation in this audit passes. Gate 1 recommends PASS; owner D-08 remains pending |
| B1 curation | No; codex/B1 | 100 sampled snapshots per base staged. Format/architecture checks, bank staging and complete similarity tables remain. CSV parsing bug fixed on branch cb8dc16, 9 tests pass |
| B3 mixtures | No; codex/B3 | One-hot/zero checks and vLLM generation pass; three bf16 mixture comparisons fail. Owner numerical-acceptance decision unresolved |
| B4 workloads | No; codex/B4 | Resolved SPEED128 and general20k prepared with zero hash overlap. Magpie real generation, five-derivative samples and global split audit remain |
| B6 trainer | No; codex/B6 | 19 CPU tests and native loss-function composition check pass. Full native model equivalence, 64-sample fit and checkpoint B2 acceptance remain; B5 data absent |
| B11 EAGLE3.1 | No; codex/B11 | Architecture/checker only; recipe and licensed regenerated-data provenance unresolved |
| FIX-1 | No code/branch yet | A2 loadability/perplexity/coherence evaluator needed; spec in notes/FIX-1.md |
| B5/B7/B8/B9/B10/B12/B13 | Not built | B7 can start from accepted B2; others have the dependencies listed on the board |

## Results checked against artifacts

- A1: independently read all **71 ×128** per-prompt records, checked unique golden IDs/hash, clean commit, engine version, accepted/proposed counts and bounds, per-prompt AL, and re-derived aggregate AL. **Zero discrepancies.** The initial audit used an incorrect key (`per_step_proposed`); the stored schema is `per_step_drafted`. Its KeyErrors were audit-script errors, preserved separately; corrected validation is `artifacts/STATUS_audit_20261005_2200/A1_corrected.json`.
- EAGLE-3 base, GSM8K128, K4, max128: fresh-compile mean **3.053985**, SD **0.004580**, range **0.012338**, n=20 runs. At max512: mean **3.105030**, SD **0.002914**, range **0.008592**, n=20. Shared-cache n=20 is identical at **3.061797**. These measured differences support separate reporting by cache policy; they do not quantify every child's noise.
- Historical child: mean of three A10 seeds minus fresh-compile A00 mean is **−0.249112**, close to historical three-seed **−0.2476**. Each child seed has only one A1 run. B2 seed0 AL **2.874685** versus A1 seed0 **2.855434** differs by **0.019251**. Logged cell configs differ only in output path and commit; source SHA matches. This exceeds the base's measured 128-token range **0.012338**. Child-specific fresh-compile repeats are needed before explaining the gap as compile variation or assigning the base SD to A10.
- B1: schema, counts, author disjointness and staged revision/path/file-size checks pass for **200/200 sampled snapshots**. This audit did not rehash 2.23 TB; original staging performed hash checks before its completion events. Llama: 6,992 inspected +217 errors=7,209 discovered; all 217 are gated-without-access. Qwen3: 4,849+28=4,877; 27 gated errors and one HTTP429 (`vistralis/Qwen3-8B-INT8`). Gated errors should become explicit exclusions in the complete list; retry the rate-limit failure. Current sample is not a fully reconciled discovery ledger.
- Draft bank counts: **39 Llama /25 Qwen3** in complete inspected lists, but **7 each** in sampled100. Stage all eligible bank adapters and compute full bank/bank plus bank/test update-cosine checks. Qwen3 is below the stated 30–60 target before further filtering; no cutoff change was made.
- B4: **128 unique SPEED prompts**, **20,000 unique general prompts**, **1,136 unique full-release SPEED turns**, zero normalized-text training/SPEED overlap, all rechecked. Reconstruction includes newly accessible HLE. Use `B4_public_resolved_20261005`; old `B4_public_20261005` remains invalid and preserved.

## Defects and documentation corrections

1. B1 format filtering treats file extensions as loadable format evidence, admitting MLX/OpenVINO/TurboMind snapshots. Zebra hybrids advertise ordinary Llama config fields despite nonstandard architecture; these fields alone are insufficient. Confirm layout/architecture from pinned metadata/weight keys, exclude inappropriate entries, regenerate a new draft and fill sampled slots. `sovthpaw/OmniSenter-Base-16B` has Qwen3 model_type and 36 layers in the staged config; its name/byte size alone does not prove an architecture mismatch. Likewise MLX bf16 needs actual layout inspection rather than automatic rejection by repo name.
2. Newly reproduced B1 reader defects: scalar target_modules `all-linear` crashed JSON parsing; large Hub file inventories exceeded CSV's default field limit. Wrote failing tests first (2 failed/5 passed), fixed typed serialization and legacy parsing/field capacity, then **9 passed**. Logs `artifacts/build_logs/B1_csv_{before,after}_20261005_2200.log`; fix is **cb8dc16**, unmerged with B1.
3. **B3 proposed operator rule would still FAIL existing evidence:** mixture max absolute errors **0.3125/0.375/0.3125**, while the single-adapter control is **0.28125**. All fp32 cases are <1e-4, but that does not pass bf16 acceptance. Do not describe adopting the proposed control bound as unblocking M1. A defensible revised validation protocol is an owner decision; keep all existing failures.
4. Gate/daily counts: analysis contains **75 directories =71 included +4 excluded**, whereas prose says 74 runs. Distinguish total launch attempts if a separate registry count is intended.
5. Gate report assigns base SD ~0.0046 to individual child A10 runs and explains B2's higher child value by compile variation. That attribution is unverified without child repeats; report it as a hypothesis. Base/shared-cache observations remain valid.
6. MASTER §1 and daily draft contain stale “B1 downloads running” / “Codex idle” state. Own B1/B4 rows and this audit are current; operator-owned §1/report text was not overwritten. Codex resumed this audit at 21:55 ET.
7. **HF token authorization is already explicit:** owner said “Just use the token with write access, and change the AGENTS.md accordingly.” It is cited in notes/B1.md at16:50 and recorded in AGENTS rule9/ff2ef3c. Only the operator's §13 bookkeeping remains; no repeated user confirmation is needed. Reads/downloads only, no Hub mutations.
8. B4's code still hard-requires H100/H200 for every real invocation. Owner already authorized available heck-srv1–5 GPUs and small acceptance runs, so add a bounded A40 acceptance-smoke path with explicit output limits/provenance before five-derivative testing; production generation placement stays separate. The current CLI is not ready to run directly on those A40s. Adapter/tokenizer provenance validation and bounded context/memory configuration also need review before real smoke use.

## Next work and run order

1. **Builder:** finish B1 format/architecture corrections, explicit access exclusions, one retry, all-bank staging, full cosine tables and spot checks. Preserve existing artifacts; create a corrected draft, then full acceptance → merge/review.
2. **Builder:** FIX-1 is a new P0 dependency of A2; implement its tests first, then base/known-child/broken-input smoke. Define perplexity reference/scoring identically for base and child; thresholds beyond MASTER's 2× and 10-prompt checks need owner decisions. It precedes any P1 work.
3. **Builder:** complete B4 bounded Magpie smoke on five pinned derivatives, inspect ten prompts each, validate disjoint training/evaluation seeds and global hash overlap, then merge/review. Full per-pool generation is operator A3.
4. **Operator:** once B1/FIX-1/B4 are verified, propose/freeze A2 pools and run A3; A4/A7 follow A3 and recorded predictions. A5's accepted harness is ready, but its proposed 45-child library/cache policy still awaits owner selection.
5. **Method path:** resolve B3's numerical acceptance → M1; build B5 paired data capture → M2; finish B6 real native/overfit/export checks → M3. D-06 and cluster placement remain prerequisites for full training.
6. **Independent CPU build:** B7 can start now because B2 is done; B12 follows B7. B8 follows accepted B1. Keep the owner's critical-path ordering and FIX priority.

## Owner decisions still open

Gate 1 D-08 (PASS recommended); compile-cache policy and how to use measured noise; DFlash replication; D-04 cutoffs; D-05 predictions before sweeps/training; D-06 method defaults; B3 numerical validation; A5 child set; shared H100/H200 host/account/partition and capacity. License-policy expansion is optional: known-license exclusions need not block repairs under the current policy. Existing token and pause authorizations are resolved.

## Handoff

Audit complete; no new GPU jobs or sweeps launched. B1 remains in progress and unmerged; cb8dc16 fixes its newly found parser failures, with 9 tests passing. Other unresolved checks above remain real blockers. Raw audit JSONs: `artifacts/STATUS_audit_20261005_2200/`. Next builder work is B1 corrections, then FIX-1/B4 acceptance; operator should reconcile §1/daily/Gate1 prose using the findings above without changing recorded run artifacts or gate decisions.
