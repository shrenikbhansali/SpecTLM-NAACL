# MASTER: NAACL 2027 sprint — derivative atlas + FollowSpec

Single source of truth for the sprint. Plan, research context, task specs,
runbooks, progress tracking and decisions all live here. If anything elsewhere
disagrees with this file, this file wins; flag the conflict in your journal.

Deadline: **ARR submission, Monday October 12, 2026, 11:59 pm AoE**
(= Tuesday October 13, 7:59 am Eastern). Internal target: submit by
**8 pm Eastern on Monday October 12**. All times below are Eastern (ET).

---

## 0. How to use this document

### 0.1 Who reads what

| Reader | Read every session | Read when relevant |
| --- | --- | --- |
| Owner (human) | §1 Status, §4 Task board, §13 Decision log, latest `reports/` | Everything else |
| Codex (builder) | `AGENTS.md`, §1, §2, §4, the spec of the task you claim in §7 | §5 research context, §6 experiments, §9 verification |
| Claude Code (operator) | `AGENTS.md`, §1–§4, §8 runbook, `notes/OPERATOR.md` | §6, §9, §10, §11 |

### 0.2 Files in the repo root

| Path | Purpose | Who writes |
| --- | --- | --- |
| `MASTER.md` | This plan and the live task board | Owner; agents edit only their task rows, §1 (operator) and §13 (operator records owner decisions) |
| `AGENTS.md` (and `CLAUDE.md` → symlink) | Standing rules for every agent | Owner |
| `notes/<TASK-ID>.md` | Append-only journal per task | The agent working that task |
| `notes/OPERATOR.md` | Claude Code's running state: jobs, queue, open incidents | Claude Code |
| `reports/YYYY-MM-DD.md` | Daily report for the owner, ready by 7:00 am ET | Claude Code |
| `reports/GATE-<n>.md` | Gate evidence reports | Claude Code |
| `$WS/artifacts/<run_id>/` | Every run's config, per-prompt records, results (per site; never in git) | The job itself |
| `sites/` (`README.md`, `heck.env`, `ice.env`) | Repository protocol, per-site paths and launchers (heck-srv, ICE) | Operator; owner fills `ice.env` |
| Ledger (`docs/research/experiments/`, `03_ALL_EXPERIMENTS.md`) | Formal record, `EXP-ATL-NNN` entries | Claude Code drafts; owner promotes |

### 0.3 Update rules (progress tracking)

1. **Claim before you work.** Set your task's row in §4 to `in progress`, put
   your agent name (`codex-1`, `claude-ops`, …) and an ET timestamp.
2. **Journal as you go.** Append to `notes/<TASK-ID>.md` at least every hour
   and at every meaningful event: what you tried, what happened, decisions,
   commands, file paths, test results. Never rewrite past entries.
3. **Finish visibly.** When acceptance tests pass, set the row to `review`
   with an evidence link (journal anchor, test output, artifact path). The
   operator re-runs the tests and sets `done`.
4. **Blocked is a status.** Set `blocked`, say on what in the row, and write
   the details in your journal. Then claim another ready task.
5. **Edit only your own rows.** Pull and rebase before editing `MASTER.md`;
   commit small changes with messages like `board: B2 review`.
6. **End every session with a handoff entry** in your journal: state, next
   step, open questions, so a fresh session can resume without you.

### 0.4 Kickoff prompts

**Codex (start as many parallel sessions as the plan allows):**

> Read AGENTS.md, then MASTER.md sections 0–4. Pick the highest-priority task
> in §4 whose Agent is `codex`, Status is `todo`, and dependencies are `done`.
> Claim it in §4, read its spec in §7, and keep a journal in
> notes/<TASK-ID>.md as described in §0.3. Build until every acceptance test
> passes, merge to main, set the row to `review` with evidence, then claim the
> next ready Codex task. Keep going until no Codex task is ready; then write a
> handoff entry in your journal and stop.

**Claude Code (one operator session at a time):**

> You are the sprint operator. Read AGENTS.md, then all of MASTER.md, then
> notes/OPERATOR.md and the latest reports/. Follow the operator loop in §8:
> keep §1 and §4 current, verify tasks in `review` by re-running their
> acceptance tests, launch jobs whose dependencies are met, monitor them,
> triage failures by the runbook, draft ledger entries, and write the daily
> report by 7:00 am ET and gate reports when due. Record your state in
> notes/OPERATOR.md before every pause so the next operator session can
> resume. Never change evaluation code after the protocol freeze without an
> owner decision in §13.

---

## 1. Status at a glance

*Operator updates this section at least three times a day.*

| Field | Value |
| --- | --- |
| Last updated | 2026-10-06 00:01 ET (claude-ops) |
| Sprint day | Day 1 of 8 (Mon Oct 5) |
| Next gate | Gate 1 **PASSED** (§13 D-08, vLLM 0.31.0; fresh compile per cell D-14). Next: Gate 2 (verification, Wed noon). Per D-15, downstream work starts as soon as dependencies pass |
| Paper framing | Undecided until Gate 3 (Thu Oct 8, 6 pm ET) |
| Experiment pause marker | **Lifted 17:32 ET** by codex-1 on owner authorization (§13 D-12) |
| Jobs running | A1 wave 4: 10 fresh-compile child repeats (claude-ops, 22:05, A40 heck-srv2/5), testing the Gate 1 child-noise attribution. B1 staging finished ~20:40 (200/200). codex-1 active again from 21:55 (audit, B1 fixes) |
| Blockers | **ICE down until Thu Oct 8 (D-19): all work on heck A40s (§3.2).** Method path on A40s needs FIX-3 (A40 production path + online capture), B5, B6 GPU acceptance, and owner decisions D-04/D-05/D-06 and B3 validation. B11 recipe/data gaps |
| Owner action needed | (L) **A00/A10 engine-setting mismatch (decide before Wed 9 am protocol freeze):** `atlas/run_cell.py` enables LoRA only when an adapter is given, so base A00 cells run with LoRA off and LoRA-derivative A10 cells with LoRA on (compiled graphs differ). AGENTS rule 3 asks for identical settings. Measured effect so far is small (child s0 LoRA vs merged fresh means −0.0045, ≈1.2 SE) but untested directly. Options: (a) add a `--enable-lora` flag (default unchanged) and run A00 with LoRA enabled whenever its A10 is a LoRA cell; (b) keep as is and state it. Operator recommends (a); it needs codex-1 (eval code) before the freeze. (Operator error: B2 verification and EXP-ATL-001 had claimed LoRA was on everywhere; errata added.) (M) **Magpie degenerate outputs (before A3):** in B4's smoke, `INSAIT-Institute/Llama3.1-8B-MixAT` returned the refusal "Sorry, I can't do that." for 64/80 query generations, and other outputs embed an assistant answer in the user turn; filters don't catch these. Decide how A3 treats such derivatives (e.g., general-set-only evaluation for derivatives whose own-domain workload falls below 64 valid prompts, vs keep and flag). notes/B4.md. (H) **Dedicated H200s (heck-srv6) are fully occupied by another user** (`aavsian3`, 8 processes, ~131 GB per GPU at 22:39); A9 (Fri) needs exclusive use. (G1) Gate 1 follow-ups (reports/GATE-1.md): choose the atlas noise floor (base 512-tok fresh-compile SD 0.0029 / range 0.0086, n=20; LoRA A10 cells vary more, SD 0.0080, n=5, so replicate LoRA cells or use type-specific floors) and DFlash replication in A7. (1) **B3 bf16 validation (blocks M1 mixtures):** mixture vs directly merged weights in bf16 differ by up to 0.3125/0.375/0.3125 in logits, failing codex-1's pre-set atol 0.125; in fp32 all cases match within 9.1e-5. A single real adapter vs its own bf16 merge already differs by 0.28125. **Correction (22:08):** the rule the operator suggested earlier (mixture error ≤ single-adapter control) would still **fail** this evidence (0.3125 and 0.375 > 0.28125), so it does not unblock M1. The operator withdraws it as a default and proposes none chosen after seeing results. A revised validation protocol is the owner's decision. Evidence: notes/B3.md, notes/BUILD-AUDIT-20261005.md item 3. (2) **Shared storage `/home/heck2`: 1.5 TB free (99%) at 22:00** after B1 staged both sampled pools (~2.2 TB); B1 bank staging and B5 feature capture still need space (B5 needs a storage estimate before running). (3) **ICE** is down until Oct 8 (D-19); repo ready to clone then (`sites/README.md`). Optional: allow the heck-srv6 H200s for M3 training until ICE returns (currently occupied by another user). (4) Home quota resolved at 17:37 (7.38 of 15.36 GB). **codex-1: point `PIP_CACHE_DIR` at /home/heck2 for env builds.** (5) ARR registrations. (6) Confirm §13 D-04 cutoffs |

---

## 2. Mission and roles

### 2.1 Mission

Submit a strong ARR long paper by October 12. Run two tracks in parallel:

- **Atlas track:** measure how frozen state-of-the-art drafters (EAGLE-3,
  DFlash) lose acceptance on dozens of real public derivatives (fine-tunes,
  adapters, merges, quantized variants) of Llama-3.1-8B-Instruct and Qwen3-8B,
  separating target shift from workload shift.
- **Method track:** train one drafter against a distribution of derivatives
  (FollowSpec) and test zero-shot transfer to held-out derivatives against
  matched controls.

Gate 3 (Thursday) picks the framing: a **method paper** if FollowSpec beats
all controls on held-out derivatives, otherwise an **atlas paper**. Both share
data and opening sections, so nothing is wasted.

Be ambitious: compute is plentiful (40 A40s, 4 dedicated H200s, a shared
cluster of hundreds of H100s/H200s). The binding constraints are serial
dependencies and correctness, not GPUs.

### 2.2 Roles

| Role | Does | Never does |
| --- | --- | --- |
| **Owner** (human) | Lifts the pause; makes every research decision and gate call; writes and approves paper text; promotes ledger entries; submits | — |
| **Codex** (builder) | Writes code and tests; downloads models and datasets; builds pipelines, training code, analysis scripts, LaTeX tables; fixes bugs filed as FIX tasks | Launches large sweeps or training jobs; changes gates, predictions or framing; edits evaluation code after the freeze without a §13 decision |
| **Claude Code** (operator) | Verifies Codex's acceptance tests; launches and monitors jobs; triages crashes; makes small operational fixes; analyzes outputs; drafts ledger entries; maintains §1, §4 and `notes/OPERATOR.md`; writes daily and gate reports; regenerates figures; helps draft paper text when asked | Rewrites core logic (files a FIX task for Codex instead); makes research decisions; interprets beyond what the numbers show |

**Handoffs between agents** happen only through §4 and the journals: the
operator files `FIX-n` rows assigned to `codex` with a link to the failing
run; Codex claims them like any task. Codex works on branches
`codex/<TASK-ID>` and merges to main only after its tests pass. The operator
runs jobs from main only, on a tagged commit recorded in each run's config.

---

## 3. Timeline (Mon Oct 5 – Mon Oct 12)

| Day | Date | Codex (build) | Claude Code (operate) | Owner | Gate / exit |
| --- | --- | --- | --- | --- | --- |
| 1 | Mon Oct 5 | B1 pools, B2 harness, B3 mixtures, B4 workloads, B6 training scaffold, W1 LaTeX skeleton | O1 orchestration and monitoring; env lock; download monitoring; run Gate 1 smoke cells as B2 lands | Lift pause; ARR registration; cluster booking; confirm cutoffs (D-04) | **Gate 1 (engine)** by 11 pm |
| 2 | Tue Oct 6 | B5 data generation, B6 complete, B7 eval driver, B8 covariates | Golden cells and noise floor; launch atlas EAGLE-3 sweeps (A4); launch bank data generation (M2) once B5 verified | Freeze pools and splits; record predictions before sweeps (D-05) | Sweeps and data generation running |
| 3 | Wed Oct 7 | B9 transport, B10 DFlash and Qwen3 paths, B11 EAGLE 3.1 pipeline, B12 figure scripts | **Protocol freeze 9 am**; Gate 2 checks; launch M3 training (12 runs); DFlash sweeps (A7); covariates (A6) | Review Gate 2 | **Gate 2 (verification)** by noon |
| 4 | Thu Oct 8 | B13 number checker; FIX tasks | Held-out evaluation M4; Gate 3 report by 6 pm; launch P1 runs (M5–M7); transport subset (A8) | **Gate 3 decision**; start shared paper sections | **Gate 3 (framing)** by 8 pm |
| 5 | Fri Oct 9 | LaTeX tables, appendix tables; FIX tasks | P1 evaluation; wall-clock timing on dedicated H200s (A9); figures v1; ledger drafts | Write results sections | All P0 results final |
| 6 | Sat Oct 10 | Lints; FIX tasks only | **Hard freeze 12:00**: bug reruns only; regenerate all figures from ledger | Complete draft | **Gate 4 (freeze)** |
| 7 | Sun Oct 11 | Format and anonymity lint | Number checker over the draft; final figures | Self-review against §11.5; anonymize; appendix; checklist | Submission-ready PDF |
| 8 | Mon Oct 12 | — | Final checks | Final read; **submit by 8 pm** | Submission ID |

### 3.1 Gates

- **Gate 1 — engine (Mon 11 pm).** Pass if the pinned vLLM runs EAGLE-3 with
  LoRA targets, DFlash, and EAGLE-v1 on the Llama base, and repeat runs agree.
  Fail fallback: EAGLE-3 on the known-good 0.17.1 harness for main tables;
  DFlash on its own engine in separate tables; never mixed.
- **Gate 2 — verification (Wed noon).** Pass if every check in §9 passes for
  every pipeline feeding P0 results. A failure blocks only the affected jobs.
- **Gate 3 — framing (Thu 8 pm).** Method framing if FollowSpec's median
  per-derivative gain over each of the three comparison arms (data-matched
  parent-only, text-matched parent-labeled, multi-version distillation) has a
  bootstrap 95% interval excluding zero on the held-out Llama pool, and parent
  retention passes TOST at a 2% margin. Otherwise atlas framing; redirect P1
  compute to atlas DFlash, transport and Qwen3 cells.
- **Gate 4 — freeze (Sat noon).** No new experiments; reruns only for bugs.
  If only P0 atlas results are solid, consider a 4-page short paper.

### 3.2 Heck-only operation until ICE returns (Thu Oct 8) — owner decision D-19

The ICE cluster is down until Thursday October 8. Until then **every job runs on heck** (§8.2 placement is overridden;
`sites/README.md`). Everything runs on A40s, so both tracks stay on one GPU type, which keeps comparisons clean (never
mix GPU types). The dedicated H200s (heck-srv6) stay A9-only unless the owner reallocates them; they are occupied by
another user as of Oct 5.

**Priority order on the A40s (method critical path first, atlas in parallel):**
1. **Method data path, in the background as early as possible.** B5 on A40s: Magpie training prompts for every accepted
   bank adapter (500 each) and on-policy child responses with vLLM multi-LoRA (§5.4 settings). Response generation is
   cheap: an 8B model at batch ≫ 1 on one A40. It can start for all A2-accepted bank-candidate adapters plus the base
   before D-04 is final; the cutoff only drops children, and generated data is reusable. Mixture children follow once
   the B3 validation rule is decided.
2. **Feature capture online, not offline.** Paired child + base EAGLE-3 tap features take ~48 KB per token (3 taps ×
   4096 × bf16 × 2 passes), ≈1.5 TB per arm at 30M tokens and ≈6 TB for four arms; `/home/heck2` has ~2 TB free. Bank
   children are LoRAs of the base, so one weight copy serves both passes by toggling the adapter; this fits an A40
   (16 GB weights + drafter + activations). B5/B6 should train with online capture (B5 step 3).
3. **M3 training on A40s** (4 arms × 3 seeds, one A40 each), once B5/B6 pass and D-04/D-05/D-06 are decided; then M4 on
   A40s. Budget estimates go in the journals before launch.
4. **Atlas track in parallel on the remaining A40s:** A2 freeze → A3 → A4/A7 sweeps; A5 when its child set is chosen.
5. **Default A40 split** (operator adjusts by queue state): heck-srv2 + heck-srv3 for the method track; heck-srv5,
   heck-srv1:6–7 and any freed GPUs for the atlas. Other users hold heck-srv1:0–5 and heck-srv4.

Gate 3 (Thu) stands. If M3/M4 cannot finish in time on A40s, the §3.1 rule applies to whatever exists; the owner decides.

---

## 4. Task board (live)

Status values: `todo` · `in progress` · `blocked` · `review` · `done` ·
`dropped`. Priority: P0 must ship, P1 should ship, P2 only after Gate 3.

| ID | Task | Pri | Agent | Depends on | Due | Status | Claimed by / updated | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | Derivative pool curation, both bases | P0 | codex | — | Mon | done | codex-1 / 2026-10-05T22:42:51-04:00 | [journal](notes/B1.md); finaldraft_retry acceptance both bases;18 tests; 200 sampled + all64 bank adapters staged; full cosine matrices; merged556e955; operator re-run PASS (23 tests, both validators, independent checks) with A2 notes ([B1 journal](notes/B1.md)) |
| B2 | Atlas cell harness on pinned vLLM | P0 | codex | — | Mon | done | codex-1 / 2026-10-05T17:50:31-04:00 | [journal](notes/B2.md); [six-cell acceptance](artifacts/B2_acceptance_20261005/acceptance_report.json); merged 8651954; 14 tests pass; operator re-run PASS with notes ([B2 journal](notes/B2.md)) |
| B3 | LoRA-mixture builder | P0 | codex | — | Mon | blocked | codex-1 / 2026-10-05T17:50:31-04:00 | [journal](notes/B3.md); bf16 logit acceptance fails; fp32 diagnostics <1e-4; vLLM 16-prompt smoke passes |
| B4 | Workload builder (SPEED-Bench + Magpie prompts) | P0 | codex | — | Mon | done | codex-1 / 2026-10-05T22:34:14-04:00 | [journal](notes/B4.md); [smoke acceptance](artifacts/B4_smoke_20261005/acceptance.json); 11 tests, five derivatives × two splits, zero leakage; merged 592c919; A3 production pending; operator re-run PASS (11 tests; leakage 0) with A3 flags ([B4 journal](notes/B4.md)) |
| B5 | On-policy data generation + feature capture pipeline | P0 | codex | B3, B4 | Tue | todo | | |
| B6 | FollowSpec trainer: arms, losses, configs (EAGLE-3) | P0 | codex | — | Tue | in progress | codex-1 / 2026-10-05T17:50:31-04:00 | [journal](notes/B6.md); 19 CPU tests and native loss composition pass; real overfit/export pending B5 |
| B7 | Held-out evaluation driver + Gate 3 report generator | P0 | codex | B2 | Tue | done | codex-1 / 2026-10-05T22:38:52-04:00 | [journal](notes/B7.md); [synthetic acceptance](artifacts/B7_acceptance_20261005/acceptance.json); 9 tests, 94% coverage across200 trials; merged ec802a4; operator re-run PASS (9 tests; coverage 0.967, noisy-twice 0.953) ([B7 journal](notes/B7.md)) |
| B8 | Covariates pipeline | P0 | codex | B1 | Tue | review | codex-1 / 2026-10-05T23:34:01-04:00 | [journal](notes/B8.md); [acceptance](artifacts/B8_acceptance_final_20261005/acceptance.json);22 CPU tests; native dense/LoRA/AWQ/CT/GPTQ checks pass; code1ab1661 merged; FIX-2 token-input integration before production |
| B9 | Transport-cell scorer | P1 | codex | B2 | Wed | in progress | codex-1 / 2026-10-06T00:02:12-04:00 | [journal](notes/B9.md);10 tests and full Eagle3 5-prompt smoke pass; n10 subset fixed, jobs not started; resume after P0 FIX-3 |
| B10 | DFlash and Qwen3 training paths | P1 | codex | B5, B6 | Wed | todo | | |
| B11 | EAGLE 3.1 baseline training pipeline | P1 | codex | — | Wed | blocked | codex-1 / 2026-10-05T17:50:31-04:00 | [journal](notes/B11.md); recipe/license gaps remain; pause lifted; 8 checker tests pass |
| B12 | Analysis and figure scripts | P0 | codex | B7 | Wed | done | codex-1 / 2026-10-05T22:50:05-04:00 | [journal](notes/B12.md); [acceptance](artifacts/B12_acceptance_20261005/acceptance.json); 6 tests,18 exhibit families byte-identical twice; merged054561a; operator re-run PASS (8 tests; 86 files byte-identical; cross-session identical except code_commit) ([B12 journal](notes/B12.md)) |
| B13 | Number-to-ledger checker for the draft | P0 | codex | B12 | Thu | review | codex-1 / 2026-10-05T23:28:03-04:00 | [journal](notes/B13.md); [acceptance](artifacts/B13_acceptance_20261005/acceptance.json);12 combined tests; actual-ledger valid bundle passes and altered macro caught; code9173385 merged |
| W1 | ACL/ARR LaTeX skeleton, both framings | P0 | codex | — | Mon | done | codex-1 / 2026-10-05T17:08:24-04:00 | [acceptance](notes/W1.md); both latexmk builds pass (2/1 pages); operator re-run PASS ([W1 journal](notes/W1.md)) |
| O1 | Orchestration, monitoring, env lock | P0 | claude-ops | — | Mon | done | claude-ops / 2026-10-05T16:43-04:00 | [journal](notes/O1.md); `ops/` (status.sh, launch.py, 8 tests pass); lock = atlas/env/requirements.lock |
| A1 | Gate 1 smoke cells + timing | P0 | claude-ops | B2 | Mon | done | claude-ops / 2026-10-05T17:54-04:00 | [journal](notes/A1.md); [GATE-1](reports/GATE-1.md); ledger EXP-ATL-001/002; 71 cells validated |
| A2 | Freeze pools and splits (manifests) | P0 | claude-ops | B1 | Tue | in progress | claude-ops / 2026-10-05T22:45-04:00 | [journal](notes/A2.md) |
| A3 | Build workloads for every pool derivative | P0 | claude-ops | B4, A2 | Tue | todo | | |
| A4 | Atlas EAGLE-3 sweep, both bases, K = 2/4/8 | P0 | claude-ops | A1, A3 | Wed | todo | | |
| A5 | Ledger children re-measured (dose-response) | P0 | claude-ops | A1 | Tue | todo | | |
| A6 | Covariates for every derivative | P0 | claude-ops | B8, A2 | Wed | todo | | |
| A7 | Atlas DFlash sweep, both bases | P0 | claude-ops | A1, A3 | Wed | todo | | |
| A8 | Transport decomposition, ~20 derivatives | P1 | claude-ops | B9 | Thu | todo | | |
| A9 | Wall-clock speedups, dedicated H200s | P1 | claude-ops | A4 | Fri | todo | | |
| M1 | Bank manifest + sampled mixtures | P0 | claude-ops | A2, B3 | Tue | todo | | |
| M2 | Bank data generation (all arms' data) | P0 | claude-ops | B5, M1 | Tue | todo | | |
| M3 | Train four arms × 3 seeds (Llama, EAGLE-3) | P0 | claude-ops | B6, M2 | Wed | todo | | |
| M4 | Held-out evaluation + Gate 3 report | P0 | claude-ops | B7, M3, A4 | Thu | todo | | |
| M5 | Ablations: λ = 0, bank only, s_max = 1, λ sweep | P1 | claude-ops | M3 | Fri | todo | | |
| M6 | FollowSpec on DFlash and on Qwen3-8B | P1 | claude-ops | B10 | Fri | todo | | |
| M7 | EAGLE 3.1 baseline, then FollowSpec on it | P1 | claude-ops | B11 | Fri | todo | | |
| M8 | Delta-KD objective; online adaptation curves | P2 | claude-ops | Gate 3 | Fri | todo | | |
| G1–G4 | Gate reports (`reports/GATE-n.md`) | P0 | claude-ops | see §3.1 | §3 | in progress | claude-ops / 2026-10-05T18:32-04:00 | G1: [reports/GATE-1.md](reports/GATE-1.md) (18:32, revised 22:11) → **PASS** (D-08) |
| R1 | Daily reports (`reports/YYYY-MM-DD.md`) | P0 | claude-ops | — | daily 7 am | todo | | |

*Add `FIX-n` rows below as needed (Agent `codex`, Depends on the failing run).*

| ID | Task | Pri | Agent | Depends on | Due | Status | Claimed by / updated | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FIX-1 | A2 filter script: vLLM loadability + coherence per derivative (no B task covers it; spec in notes/FIX-1.md) | P0 | codex | B1, B2 | Tue am | done | codex-1 / 2026-10-05T22:41:55-04:00 | [journal](notes/FIX-1.md); [acceptance](artifacts/FIX-1_acceptance_20261005/acceptance.json); approved50% criterion, base/child/broken pass;19 tests; merged880e68e; operator re-run PASS (48 tests) ([FIX-1 journal](notes/FIX-1.md)) |
| FIX-2 | Exact rendered token input and explicit matched LoRA setting in B2 | P0 | codex | B2, B4 | now | done | codex-1 / 2026-10-05T23:51:05-04:00 | [journal](notes/FIX-2.md); [acceptance](artifacts/FIX-2_rendered_retry_20261005/acceptance.json);34 tests + paired5-prompt GPU checks pass; code898f0c7 merged; operator re-run PASS (71 tests; checker; single BOS 10/10) ([FIX-2 journal](notes/FIX-2.md)) |
| FIX-3 | A40 production path for B4/B5 (D-19): allow full Magpie and response generation on A40s (currently H100/H200-only for production, notes/BUILD-AUDIT item 8) and implement online paired feature capture for B5/B6 training (§3.2 storage estimate) | P0 | codex | B4, B6 | Tue am | review | codex-1 / 2026-10-06T00:15:17-04:00 | [journal](notes/FIX-3.md); [acceptance](artifacts/FIX-3_online_final_20261006/check/results.json);29 tests, paired5-response GPU runs, exact fresh/zero online checks; merged8b70bc2; full B5/B6 integration next |

---

## 5. Research context (what agents need to know)

### 5.1 The paper

| | Method framing | Atlas framing |
| --- | --- | --- |
| Working title | FollowSpec: One Speculative Drafter for Every Fine-Tune of Its Base Model | When Does a Speculative Drafter Survive Its Target's Fine-Tuning? An Atlas of Public Derivatives |
| Chosen when | Gate 3 passes | Gate 3 fails or is inconclusive |
| Lead claim | A drafter trained once against many derivatives transfers to unseen ones, beyond controls that match its data | How much, when and why frozen drafters lose acceptance on real derivatives |

Research questions: (1) How much acceptance do frozen drafters lose on real
derivatives once target shift is separated from workload shift? (2) How does
the loss depend on speculation depth and drafter architecture? (3) Which
measurable derivative properties predict it? (4) How much of a derivative's
change does a frozen drafter inherit through its input features? (5) Can a
drafter trained against many derivatives transfer to unseen ones?

### 5.2 Definitions

- **Derivative**: any model built from a base: LoRA adapter, full fine-tune,
  merge, quantized variant, abliterated or RL-tuned model.
- **A00**: base target + frozen drafter, on the derivative's workload.
  **A10**: derivative target + frozen drafter, same workload.
  **A01 / A11**: base / derivative target with a trained drafter.
- **Target shift** = A10 − A00 (workload held fixed). **Workload shift** =
  A(base; derivative's workload) − A(base; general workload).
- **Retention** = A10 / A00.
- **Acceptance length**: macro mean accepted tokens per verification step,
  including the bonus token. Greedy decoding throughout.
- **K**: speculative tokens per step (chain drafting for EAGLE family).
- **Transport**: what a frozen drafter inherits by receiving the derivative's
  hidden states instead of the base's (see §6, A8).

### 5.3 Theory used in the paper

- **Proposition 1 (depth amplification).** With per-token acceptance b and K
  drafted tokens, E[L] = (1 − b^(K+1)) / (1 − b). The relative sensitivity
  ∂ ln E[L] / ∂b = 1/(1−b) − (K+1) b^K / (1 − b^(K+1)) rises monotonically with
  K. Example: b from 0.80 to 0.75 costs 9% of accepted length at K = 4 and 18%
  at K = 15. Prediction: relative loss from a derivative grows with K.
- **Proposition 2 (tracking bound).** Under speculative sampling, per-position
  acceptance is b(p, q) = Σ min(p, q) = 1 − TV(p, q). With Δp = p_child − p_base
  and Δq = q(h_child) − q(h_base) on the same prefix:
  ½‖Δp − Δq‖₁ − (1 − b_base) ≤ 1 − b_child ≤ (1 − b_base) + ½‖Δp − Δq‖₁.
  The tracking error ‖Δp − Δq‖ governs derivative acceptance when the base fit
  is good; FollowSpec's delta term targets it.

### 5.4 FollowSpec (the method)

A training recipe applied to a released drafter. Architecture and inference
are unchanged; the output is a drop-in checkpoint.

**Component 1, derivative-distribution training.** Train against many
targets: real bank children (pre-cutoff public LoRA adapters) plus sampled
LoRA mixtures:

    Δ_sampled = s · Σ_{i∈S} w_i · c_i · B_i A_i ,   w ~ Dirichlet(α),  s ~ U[0, s_max]

represented exactly as one adapter: B = [s w_1 c_1 B_1, …], A = [A_1; …],
rank Σ r_i (c_i = alpha_i / r_i, or alpha_i / sqrt(r_i) with rsLoRA). Data per
child: Magpie prompts generated by the child plus shared general prompts;
responses generated on-policy by the child; white-box targets from the child.
A share of steps uses the base model itself.

**Component 2, delta-consistency objective.** On identical token sequences,
with child and base target passes and drafter passes on child features h_c and
base features h_0:

    d(v)  = [log q(v|h_c) − stopgrad(log q(v|h_0))] − [log p_c(v) − log p_0(v)]
    d̄     = Σ_{v∈V_k} p_c(v) · d(v)
    L     = D(p_c ‖ q(h_c)) + β · D(p_0 ‖ q(h_0)) + λ · Σ_{v∈V_k} p_c(v) · (d(v) − d̄)²

D is the drafter's native training loss (EAGLE-3 train-time-test loss; DFlash
block loss). V_k is the child target's top-k tokens inside the drafter's
vocabulary. The centered term is the squared log-space distance to the
Delta-KD target q* ∝ q(h_0) · p_c / p_0. Apply it at every draft position of
the drafter's native unroll.

**Starting hyperparameters** (owner may change via §13):

| Setting | Default |
| --- | --- |
| Initialization | RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3 |
| Bank | All filtered pre-cutoff LoRA adapters (target 30–60); ledger children excluded |
| Mixtures | 30 sampled; \|S\| ∈ {2, 3}; α = 0.5; s_max = 1.5; discard any mixture whose perplexity on the shared general set exceeds the worst real bank child's |
| Samples per child | 1,000 (50% the child's Magpie prompts, 50% shared general prompts) |
| Parent share | 25% of training samples, on the base's own data |
| Generation | Max 512 new tokens; temperature 0.6, top-p 0.95 unless the released drafter's recipe specifies otherwise (record which) |
| Token budget | Identical across arms (about 30M training tokens per arm; record the exact count) |
| Optimizer | AdamW, LR 2e-5, cosine, 3% warmup, 1 epoch, bf16, speculators' default batch size |
| Loss weights | β = 1.0; λ = 0.1 (P1 sweep {0.03, 0.1, 0.3}); k = 32 |
| Seeds | 3 per arm |

### 5.5 Training arms (what each isolates)

All arms start from the same checkpoint and match tokens, steps, optimizer
and seeds. They differ only as listed.

| Arm | Targets and data | Isolates |
| --- | --- | --- |
| **FS** (FollowSpec) | Bank + mixtures, child data, λ = 0.1 | The method |
| **MVD** (multi-version distillation) | Bank only (more samples per child to match tokens), λ = 0 | Contribution of mixtures + delta term |
| **PO-D** (data-matched parent-only) | Same prompts as FS; responses, features and labels from the base | Target diversity versus prompt diversity |
| **PO-T** (text-matched parent-labeled) | Same child-generated responses as FS; features and labels from the base | Target features and labels versus response text |
| Frozen | The released drafter, untrained | Reference cells A00, A10 |

FS and the delta term need base-target features and distributions on
child-generated sequences, so data generation captures both passes.

### 5.6 Checkpoints

| Role | Model ID |
| --- | --- |
| Primary target | meta-llama/Llama-3.1-8B-Instruct |
| EAGLE-3 drafter | RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3 |
| DFlash drafter | z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat |
| EAGLE-v1 drafter (analysis only) | yuhuili/EAGLE-LLaMA3.1-Instruct-8B |
| Second target | Qwen/Qwen3-8B (non-thinking) |
| Qwen3 EAGLE-3 drafter | RedHatAI/Qwen3-8B-speculator.eagle3 |
| Qwen3 DFlash drafter | z-lab/Qwen3-8B-DFlash-b16 |

These match the ledger: EXP-MTH-021 used the same EAGLE-v1 and EAGLE-3,
EXP-MTH-022 the same DFlash. Pin every model to a revision hash.

### 5.7 Pools and splits

- **Pools.** At least 60 Llama and 40 Qwen3 derivatives after filtering,
  stratified across adapters, full fine-tunes, merges and quantized variants,
  plus abliterated and RL-tuned ones where available.
- **Cutoffs** (pending owner confirmation, §13 D-04): Llama bank = created
  before 2025-07-01; Qwen3 bank = created before 2026-01-01. Later uploads form
  the test pools, after removing any whose author also appears in the bank. A
  test pool must keep at least 30 derivatives; if not, propose a new cutoff.
- **Leakage.** A test derivative is excluded if its weight update has cosine
  similarity above 0.9 with any bank adapter; bank adapters above 0.95 with
  each other are deduplicated. Prompt sets for training and test are disjoint.
- **Ledger children** (the update library, about 50 Llama configs) are never
  in the bank; they are a controlled held-out set and the A5 dose-response.

### 5.8 Workloads

Every derivative is evaluated on (a) a fixed general set: 128 prompts from
SPEED-Bench's Qualitative split, and (b) its own domain: 64 Magpie prompts it
generates itself. Training prompts never overlap with either.

---

## 6. Experiment specs

### 6.1 Atlas track

| ID | What | Settings | Output | Success criterion |
| --- | --- | --- | --- | --- |
| A1 | Gate 1 smoke cells, timing, noise floor | EAGLE-3, EAGLE-v1, DFlash on the Llama base; 128 GSM8K prompts from EXP-MTH-021; K = 4; base A00 repeated 20 times | Engine lock, per-cell timings, noise floor | All drafters run; LoRA = merged within noise; known child's drift negative, near ledger's −0.248 |
| A2 | Freeze pools | Filters of B1 plus vLLM loadability and coherence (perplexity on the general set at most 2× base; no degenerate outputs on 10 prompts); deduplication; split | `pool_manifest_<base>.csv` with `pool` column, frozen and hashed | Counts meet §5.7 |
| A3 | Workloads per derivative | §5.8 | Prompt files, hashed | All derivatives covered |
| A4 | EAGLE-3 sweep | Both bases; every derivative; A00 and A10 at K = 2, 4, 8 on its own workload; base on the general set once per K | Atlas core table | Complete, no failed cells unexplained |
| A5 | Ledger children | Update-library configs; A00, A10 at K = 4 (K = 2, 8 for a subset) | Dose-response table | Matches ledger direction for documented children |
| A6 | Covariates | B8 on every derivative | Covariate table | Complete |
| A7 | DFlash sweep | Both bases; native block size, plus K = 4 if the engine allows | DFlash table | Complete or documented |
| A8 | Transport | B9 on ~20 derivatives spanning the loss range; validated against vLLM A00/A10 | Transport ratios | Offline cells track vLLM (see §9) |
| A9 | Wall-clock | 5 derivatives spanning the loss range; batch 1 and 8; target-only, frozen drafter, FS drafter; dedicated H200s only | Speedup table | Exclusive-GPU runs, 3 repeats each |

### 6.2 Method track

| ID | What | Settings | Output | Success criterion |
| --- | --- | --- | --- | --- |
| M1 | Bank and mixtures | Bank = pre-cutoff filtered adapters minus duplicates; 30 mixtures per §5.4 | `bank_manifest_llama.csv`, mixture adapters | Mixtures pass B3 tests and the perplexity filter |
| M2 | Data generation | B5 for every bank child, mixture and the base; both child and base passes on child sequences | Training shards per arm | §9 data-path checks pass |
| M3 | Train arms | FS, MVD, PO-D, PO-T × 3 seeds, §5.4 defaults | 12 checkpoints | Configs equal except intended fields; all load in vLLM |
| M4 | Held-out evaluation | Llama test pool + ledger children; A11 and A01 for all 12 checkpoints and frozen; K = 4 (K = 2, 8 for FS and frozen) | `reports/GATE-3.md` | Report complete; owner decides |
| M5 | Ablations | λ = 0 with mixtures; bank only with λ = 0.1; s_max = 1; λ ∈ {0.03, 0.3} | Component table | — |
| M6 | Generality | FS vs MVD vs PO-D on DFlash (Llama) and on EAGLE-3 (Qwen3) | Generality table | — |
| M7 | Strongest baseline | Train EAGLE 3.1 for Llama; then FS from it; evaluate as M4 | Baseline row | — |
| M8 | P2 extras | Delta-KD KL objective; online adaptation curves from frozen vs FS initialization | Appendix | Only after Gate 3 |

### 6.3 Predictions (owner records in §13 before A4 and M3 launch)

1. LoRA adapters keep median EAGLE-3 retention above 95% at K = 4; full
   fine-tunes keep less.
2. Relative loss grows with K at the rate Proposition 1 predicts.
3. DFlash loses more than EAGLE-3 in relative terms at its native block size.
4. Target KL and tap displacement predict loss better than weight-delta norm.
5. Mass outside the drafter vocabulary predicts EAGLE-3's loss on non-English
   derivatives, but not DFlash's.
6. FS beats PO-D on held-out derivatives, with most but not all of the gain
   already captured by MVD.
7. FS keeps parent acceptance within 2%.
8. FS's gains are largest where the frozen drafter lost most.

---

## 7. Build task specs (Codex)

Every spec has the same shape: goal, steps, outputs, acceptance tests, out of
scope. A task is done only when every acceptance test passes and the evidence
is in `notes/<TASK-ID>.md`. Put new code under `atlas/`, `followspec/` or
`paper/`; never change the default behavior of existing scripts.

### B1. Derivative pool curation (both bases)

**Goal.** Candidate lists and staged weights of public derivatives of
`meta-llama/Llama-3.1-8B-Instruct` and `Qwen/Qwen3-8B`.

**Steps.**
1. List derivatives through the Hub's base-model relations, per relation type:
   `base_model:adapter:<base>`, `base_model:finetune:<base>`,
   `base_model:merge:<base>`, `base_model:quantized:<base>`.
2. Record per candidate: `model_id`, `revision` (commit hash), `relation`,
   `created_at`, `author`, `license`, `downloads`, `gated`, file formats,
   `size_bytes`; for adapters `r`, `lora_alpha`, `use_rslora`, `target_modules`.
3. Tag `type`: lora_adapter, full_finetune, merge, quantized_fp8,
   quantized_awq, quantized_gptq, abliterated, rl_tuned (card mentions RL,
   GRPO, PPO or DPO), other.
4. Exclude gated without access, unknown or non-research licenses, GGUF-only,
   MLX-only, EXL2-only, other architectures, repos without weights.
5. Tokenizer check from tokenizer and config files only: `tokenizer_identical`
   (hash of `tokenizer.json` vs base) and `template_changed` (chat-template
   hash). Exclude non-identical tokenizers.
6. Stratified sample of about 100 candidates per base across types, preferring
   higher downloads within a stratum; keep the full list too.
7. Assign `pool` by the cutoffs in §5.7 and drop test candidates whose author
   is in the bank. Report counts per type and pool.
8. Download every sampled candidate's weights to shared storage with resume;
   log progress and total size. Adapters first, then quantized, then full
   fine-tunes.
9. For adapters, compute pairwise cosine similarity of flattened weight
   updates (BA per module, concatenated) and flag pairs above the §5.7
   thresholds.

**Outputs.** `atlas/curate_pool.py` + tests; `$WS/artifacts/atlas/candidates_<base>.csv`;
`$WS/artifacts/atlas/pool_draft_<base>.csv`; download log; similarity table.

**Acceptance tests.** Schema (every field, no duplicate IDs); counts sum
correctly; no author in both pools; 10 random rows per base listed with Hub
URLs in the journal for owner spot checks; download log shows every sampled
model present with matching revision.

**Out of scope.** Loadability and coherence filters (A2).

### B2. Atlas cell harness on a pinned vLLM

**Goal.** `atlas/run_cell.py`: measure one cell (target, drafter, K, prompt
set) on a newly pinned engine, for full-weight targets and base + LoRA.

**Steps.**
1. New environment with the latest stable vLLM, at least 0.22 if available
   (EAGLE 3.1 and DFlash), otherwise at least 0.20.1 (DFlash). Lock file
   committed. The 0.17.1 environment is untouched.
2. Inputs: target ID and revision, or base plus adapter path; drafter ID and
   method (`eagle3`, `eagle`, `dflash`); K; prompt file; seed; max new tokens
   (default 512); batch size.
3. Outputs per AGENTS.md rule 5: per-prompt accepted lengths and draft counts,
   per-position conditional acceptance, macro acceptance length including the
   bonus token, engine version, GPU type, wall-clock time.
4. Reuse metric definitions from `scripts/run_vllm_eval.py`; document any
   unavoidable difference.

**Acceptance tests.** On the Llama base with the 128 GSM8K prompts of
EXP-MTH-021, K = 4: (a) two repeats agree within the ledger's noise floor
(0.0138) or the difference is reported; (b) the narrow GSM8K LR 2e-4 child of
EXP-MTH-018 (adapter located via that entry's Artifacts) shows negative
A10 − A00 of similar size to −0.248; (c) the same child as LoRA and as merged
weights agree within the repeat difference; (d) EAGLE-v1 and DFlash each
produce valid cells; record DFlash's block size and K options; (e) per-cell
wall-clock time for each drafter. The 0.17.1 harness measured 3.0559 for
EAGLE-3 here; report the new value without correcting it.

### B3. LoRA-mixture builder

**Goal.** `followspec/mixture.py`: one PEFT adapter equal to s · Σ w_i c_i B_i A_i
(§5.4), loadable by vLLM multi-LoRA.

**Steps.** Concatenate factors as in §5.4 and save with scaling 1 (alpha =
new rank, rsLoRA off). Handle differing ranks, alphas, rsLoRA, dtypes and
target-module sets (union; missing modules contribute zero). Check the
engine's maximum LoRA rank and refuse mixtures that exceed it, reporting the
cap.

**Acceptance tests.** One-hot w with s = 1 reproduces the source adapter's
weight update and logits; s = 0 reproduces the base; three random mixtures of
three adapters (s ∈ {0.5, 1.0, 1.5}) match directly merged weights on 16
prompts within bf16 tolerance (report max absolute and relative differences);
one mixture generates through vLLM multi-LoRA.

### B4. Workload builder

**Goal.** Evaluation and training prompt sets per derivative.

**Steps.**
1. SPEED-Bench Qualitative split: obtain the official release, record source
   URL, version and file hash; sample 128 prompts stratified by category with
   a fixed seed.
2. Magpie generator: feed the derivative its chat template's user-turn prefix
   and let it write the user query; stop at end of turn. Use the published
   Magpie sampling settings and record them. Qwen3 runs in non-thinking mode.
3. Filter: length 10–1,000 characters; exact and near-duplicate removal
   (MinHash); record detected language.
4. Per derivative: 64 evaluation prompts. Per bank child: 500 training prompts
   from a different seed. Shared general training pool: 20,000 prompts from a
   public instruction dataset disjoint from SPEED-Bench (record which).

**Acceptance tests.** Hash check shows no overlap between any training and
evaluation prompt, or with SPEED-Bench; duplicate rate reported; 10 prompts
each from 5 derivatives pasted into the journal for spot checks.

### B5. On-policy data generation and feature capture

**Goal.** Training data for every arm in §5.5.

**Steps.**
1. Generate child responses with vLLM multi-LoRA for every bank child and
   mixture (settings §5.4); base responses for PO-D and the parent share.
2. Feature capture: run the base and the child target on each child-generated
   sequence; capture the drafter's tap hidden states (read layer IDs from the
   drafter config) and what the trainer needs for target distributions (final
   hidden states or top-k logits). PO-T uses the base pass on child sequences.
3. Decide online versus offline capture: online if speculators supports LoRA
   targets in that mode; otherwise offline, with a storage estimate written in
   the journal before any large run.
4. Write shards in the trainer's expected format, with a manifest per arm.

**Acceptance tests.** Decoded strings and assistant-only loss masks for five
samples per arm in the journal; captured features match a fresh forward pass
within tolerance on three samples; features with a scale-0 child equal the
base's exactly, and with a real child differ; per-arm token counts reported
and matched to §5.4.

### B6. FollowSpec trainer (EAGLE-3)

**Goal.** Train all arms in §5.5 from one code path.

**Steps.** Extend speculators' EAGLE-3 trainer (or SpecForge, if a better fit;
record the choice): multi-target dataset with per-sample target ID and paired
base features; arm presets as config files; the delta-consistency loss of
§5.4 at every train-time-test step; separate logging of each loss term;
checkpoint export loadable by vLLM.

**Acceptance tests.** (a) The delta term is zero when the drafter's shift
equals the target's exactly; (b) it is unchanged when a per-prefix constant is
added to either log-distribution; (c) no gradient flows through the
base-feature drafter pass inside the delta term; (d) λ = 0 reproduces the
stock trainer's loss on a fixed batch to 1e-6; (e) loss falls when
overfitting 64 samples; (f) a config-diff tool shows the four arm presets
differ only in their intended fields; (g) an exported checkpoint runs in B2.

### B7. Held-out evaluation driver and Gate 3 report

**Goal.** Schedule B2 cells for checkpoints × derivatives × K and aggregate.

**Steps.** Compute per derivative A01 and A11 (per seed and seed-averaged);
paired differences of FS against each arm; bootstrap 95% intervals over
derivatives (10,000 resamples); win rate; worst-decile retention; parent
retention TOST at 2%. Emit `reports/GATE-3.md` from a template, plus CSVs.

**Acceptance tests.** On synthetic data with a known effect, intervals cover
the truth at the nominal rate; the same checkpoint evaluated twice gives a
difference interval that includes zero.

### B8. Covariates

**Goal.** Per derivative: (1) relative weight-update norm per module type;
(2) KL(p_derivative ‖ p_base) averaged over tokens of the derivative's own
generations on its 64 evaluation prompts; (3) relative L2 and cosine
displacement of hidden states at the EAGLE-3 tap layers on the same
sequences; (4) relative LM-head change; (5) chat-template change; (6) the
derivative's probability mass outside EAGLE-3's draft vocabulary.

**Acceptance tests.** The base against itself gives zeros; a known ledger
child gives nonzero values; runtime per derivative reported.

### B9. Transport-cell scorer

**Goal.** Offline cells a(f, p) for features f and labels p in {base,
derivative}: first-position teacher-forced top-1 agreement, distribution
overlap Σ min(p, q), and forward KL, on sequences generated by the
derivative; per-position versions along the drafter's unroll. For DFlash,
swap the LM head as a third factor when the derivative changes it. Report
label shift, transport and transport ratio R (§5.2, proposal definitions).

**Acceptance tests.** Across at least 10 derivatives, the diagonal cells track
vLLM A00 and A10: Spearman correlation of at least 0.8, and the same sign of
A10 − A00 for at least 90% of derivatives. Hybrid cells are labeled
diagnostic in every output.

### B10. DFlash and Qwen3 training paths

**Goal.** Run M6. DFlash via speculators (0.5.0 or later,
`--speculator-type dflash`) or SpecForge, with the delta term at every masked
block position; Qwen3-8B with the RedHatAI EAGLE-3 drafter in non-thinking
mode. **Acceptance:** B6's tests (a)–(g) for each path.

### B11. EAGLE 3.1 baseline pipeline

**Goal.** Train an EAGLE 3.1 drafter for Llama-3.1-8B-Instruct with TorchSpec
or SpecForge on Open-PerfectBlend regenerated by the target (the SpecBundle
recipe), with FC normalization and post-norm. **Acceptance:** loads in the
pinned vLLM; base acceptance on SPEED-Bench Qualitative at K = 4 at least the
RedHatAI EAGLE-3's, or the shortfall reported.

### B12. Analysis and figure scripts

**Goal.** Deterministic scripts producing every exhibit in §11.3 from
artifacts and aggregate CSVs, into `paper/figures/` (PDF + PNG), each with a
JSON sidecar listing source run IDs. **Acceptance:** two regenerations are
byte-identical; every plotted number traces to a run ID.

### B13. Number-to-ledger checker

**Goal.** Every number in the paper is a LaTeX macro in `paper/numbers.tex`,
generated from aggregate CSVs. A checker in the style of
`scripts/verify_ttcl_paper.py` re-derives every macro and fails on mismatch,
and flags hard-coded numbers in results sections. **Acceptance:** a
deliberately altered number is caught.

### W1. LaTeX skeleton

**Goal.** Official ACL style files (acl-org/acl-style-files) in review
(anonymous) mode. Two main files, `paper/method/main.tex` and
`paper/atlas/main.tex`, sharing `paper/shared/` (introduction opening,
background, atlas setup), `paper/numbers.tex` and `paper/figures/`. Both
include a Limitations section. **Acceptance:** both compile cleanly with
latexmk; page counts reported.

---

## 8. Operator runbook (Claude Code)

### 8.1 Operator loop

Run this loop every 30–60 minutes while jobs are active, and at the start of
every session:

1. Pull main. Read §1, §4, `notes/OPERATOR.md`, and every journal updated
   since your last check.
2. **Verify reviews.** For each task in `review`, re-run its acceptance tests
   from a fresh checkout. Pass: set `done`. Fail: set `in progress`, write
   what failed in the task's journal, and assign it back.
3. **Launch.** Start every job whose dependencies are `done`, in the priority
   order of §8.2, unless the pause marker is present or a gate forbids it.
   Record run IDs in `notes/OPERATOR.md` and in the task's journal.
4. **Monitor.** Queue state, GPU utilization, log tails, throughput, disk use,
   ETA for each running job.
5. **Triage** anything failed or suspicious using §8.3.
6. **Collect.** Validate each finished run (§8.4), draft its ledger entry
   (§10.1), update the task's Evidence column and §1.
7. **Save state** in `notes/OPERATOR.md` before ending the loop.

### 8.2 Resource policy and priorities

- **Critical path first:** M1 → M2 → M3 → M4 (Gate 3 depends on it), then A4,
  A7, A6, A5, then P1 (M5, M6, M7, A8, A9), then P2.
- **Placement:** 40 A40s (site `heck`) for A1–A8 inference and covariates; the ICE
  cluster's H100/H200s (site `ice`) for M2 data generation, all training, and evaluation
  of trained drafters; the 4 dedicated H200s (heck-srv6) for A9 timing only, with no
  other jobs. Never mix GPU types within one comparison (`sites/README.md`).
- **Jobs are idempotent and resumable.** One run ID per job:
  `<task>-<base>-<drafter>-k<K>-s<seed>-<YYYYMMDDHHMM>`. Never overwrite an
  artifact directory; replicates get new IDs.
- **Book ahead.** If the cluster queue would delay the critical path, tell the
  owner in §1 "Owner action needed".

### 8.3 Failure triage

| Class | Symptoms | Action |
| --- | --- | --- |
| Infrastructure | Node loss, preemption, NCCL timeout, download or network errors | Retry automatically up to 2 times; then escalate in §1 |
| Out of memory | CUDA OOM | Reduce batch size or max tokens only if comparability is unaffected; for training arms apply the same change to all arms; record in the config and journal |
| Config or path | Missing file, wrong ID, bad flag | Fix the config, rerun, journal it |
| Code bug | Exception in project code, shape errors | Small obvious fixes (typo, import, path) on branch `claude/fix-<id>`, re-run tests, journal; anything touching core logic becomes a `FIX-n` row for Codex with run ID, logs and a minimal repro |
| Training divergence | NaN or exploding loss | Restart once from the last checkpoint with the same config; if it repeats, stop, file `FIX-n`, tell the owner |
| Silent anomaly | Acceptance outside [1, K+1]; identical results across conditions; base A00 drifting beyond the noise floor; implausible effect sizes | Stop downstream use, mark the run `suspect` in `notes/OPERATOR.md`, investigate, file `FIX-n`; never explain it away in a report |

After the protocol freeze (Wed 9 am), no change to evaluation code without an
owner decision recorded in §13.

### 8.4 Run validation (before any number is used)

- `config.json` complete: model IDs with revisions, engine version equal to
  the lock file, K, seed, prompt-file hash, code commit.
- Per-prompt record count equals the prompt count.
- Every acceptance length lies in [1, K + 1].
- Model revisions match the frozen manifests.
- No two runs claim the same cell unless marked as replicates.

### 8.5 Daily report (`reports/YYYY-MM-DD.md`, ready by 7:00 am ET)

1. **Status**: a copy of §1.
2. **Done since last report**: tasks moved to `done`, with evidence links.
3. **Runs**: launched, finished, failed (run IDs).
4. **Key numbers**: with n and intervals; no interpretation beyond them.
5. **Incidents and anomalies**: what happened, what was done.
6. **Decisions needed**: each with a recommended default.
7. **Today's critical path**: what must finish today for the next gate.
8. **Risks to the deadline**.

### 8.6 Gate reports (`reports/GATE-n.md`)

- **Gate 1:** engine version and lock; every A1 cell; timings; LoRA versus
  merged; noise floor; recommendation (pass, or fallback per §3.1).
- **Gate 2:** each §9 check with evidence, per pipeline; list of pipelines
  cleared for P0 use.
- **Gate 3:** the B7 output: per-arm tables, per-derivative paired
  differences with bootstrap intervals, win rates, parent TOST, ledger
  children results; the §3.1 decision rule applied mechanically; caveats.
- **Gate 4:** freeze inventory: final run list, ledger entries, regenerated
  figures, number-checker result.

### 8.7 Analysis duties

Using B12 scripts: retention distributions by derivative type and drafter;
relative loss against K with Proposition 1's prediction overlaid; regression
of target shift on the B8 covariates with cross-validated R²; transport
ratios; per-derivative FS gains. Label anything beyond the numbers as an
"observation for the owner".

### 8.8 `notes/OPERATOR.md` layout

Keep these headings, newest information first: **Now** (time, sprint day,
next gate); **Active jobs** (run ID, task, cluster, started, ETA, status);
**Queue** (ready to launch next); **Open incidents**; **Recently verified**;
**Handoff** (what the next operator session must do first).

---

## 9. Verification protocol

Several of the project's ten retractions traced to silent pipeline bugs, such
as the EXP-MTH-026 data-path defect. Every check below must pass before a
result is used. Codex writes the tests; the operator re-runs them; the owner
reviews them at Gate 2.

| Check | Requirement | Applies to |
| --- | --- | --- |
| Golden cells | Base A00 reproduced within the noise floor before any sweep; the EXP-MTH-018 narrow LR 2e-4 child reproduces its drift in sign and rough size | B2, A1, A4, A7 |
| Noise floor | Re-estimated on the pinned engine from 20 base A00 replicates | A1 |
| Data paths | Decoded strings and loss masks inspected for 5 samples per path | B4, B5, B6 |
| Mixture equals merged | Within bf16 tolerance on 16 prompts | B3, M1 |
| Feature capture | Captured features equal a fresh forward pass; scale-0 child equals base | B5 |
| Leakage | No test derivative above cosine 0.9 with any bank adapter; prompt sets disjoint | A2, M1, B4 |
| Matched configs | Arms differ only in intended fields, checked from logged configs | B6, M3 |
| Transport validity | Offline diagonal cells track vLLM (Spearman ≥ 0.8; same sign for ≥ 90%) | B9, A8 |
| Protocol freeze | Evaluation code frozen from Wed 9 am; changes need §13 approval and reruns | All evaluation |
| Traceability | Every paper number is a macro re-derived from CSVs by B13 | Paper |

---

## 10. Records

### 10.1 Ledger entries

Every run that produces a number gets a draft entry `EXP-ATL-NNN` in the
project ledger with all seven mandatory fields: **ID + title**; **Landed**
(ISO date and campaign); **Status** (`pilot` until the owner promotes it to
`paper-grade`; also `diagnostic`, `superseded`, `invalid`); **What / why**
(2–4 sentences); **New in this experiment**; **Artifacts** (a path that
resolves); **Config + results** (hyperparameter table and results table with
every seed and condition, effect sizes and uncertainty). Add **Caveats**, or
write "none known". Never delete an entry; superseded entries get a pointer.

### 10.2 Journals

`notes/<TASK-ID>.md`, append-only. Each entry starts with an ET timestamp and
the agent name, then: what was done, commands, results, decisions, next step.
Each session ends with a **Handoff** entry.

### 10.3 Git

Remote `origin` = `https://github.com/shrenikbhansali/SpecTLM-NAACL` (private), shared by every site (§13 D-18). One
`main` holds code, this file, notes, ledger and reports for all sites; site differences live only in `sites/<site>.env`
(protocol in `sites/README.md`). Pull with rebase before editing shared files and push right after committing. Codex
works on `codex/<TASK-ID>` and merges after tests pass; the operator's small fixes go on `claude/fix-<id>`; both push
their branches. Commit messages start with the task ID. Every run records the commit and the pushed `run-*` tag it ran from.

---

## 11. Paper

### 11.1 Outlines (8 pages of content; Limitations, ethics, references and appendices are outside the limit)

**Method framing**

| § | Section | Pages | Content |
| --- | --- | --- | --- |
| 1 | Introduction | 1.0 | Derivatives outnumber drafters; contributions |
| 2 | Background and theory | 1.0 | Feature-conditioned drafters; target versus workload shift; Propositions 1–2 |
| 3 | How frozen drafters fare | 1.25 | The atlas, compressed: losses by type, depth amplification, predictors |
| 4 | FollowSpec | 1.0 | Derivative-distribution training, mixtures, delta-consistency objective (Algorithm 1) |
| 5 | Experimental setup | 0.75 | Bank and temporal holdout, arms, metrics |
| 6 | Results | 1.5 | Held-out gains over arms, parent retention, ablations, second family |
| 7 | Analysis | 0.5 | Transport before and after training; which derivatives gain |
| 8 | Related work | 0.5 | Positioning |
| 9 | Conclusion | 0.25 | Takeaways |

**Atlas framing**

| § | Section | Pages | Content |
| --- | --- | --- | --- |
| 1 | Introduction | 1.0 | Problem, why now, contributions |
| 2 | Background and setup | 0.75 | Drafters, derivatives, the two shifts, four-cell measurement |
| 3 | The atlas | 1.0 | Pools, filters, workloads, drafters, metrics |
| 4 | How much do drafters lose? | 1.5 | Target shift by type, the tail, workload shift for contrast |
| 5 | Depth and architecture | 1.0 | Proposition 1; loss against K; EAGLE-3 vs DFlash vs EAGLE-v1 |
| 6 | What predicts the loss? | 1.0 | Covariates, regression, a practical retraining rule |
| 7 | How much do drafters inherit? | 0.75 | Proposition 2; transport ratios |
| 8 | Related work | 0.5 | Positioning |
| 9 | Conclusion | 0.25 | Takeaways; FollowSpec as future work |

Mandatory and appendix material: Limitations (one base family in the main
text if Qwen3 slips, greedy primary, public derivatives as a convenience
sample, acceptance as the main metric); ethics statement (licenses, no weight
redistribution); Appendix A derivative list with IDs, revisions, licenses,
types; B protocol and engine versions; C proofs; D per-derivative results and
ledger children; E (method framing) training details, arm configs, bank list.

### 11.2 Writing schedule

| Day | Writing work | Who |
| --- | --- | --- |
| Thu Oct 8 | Shared sections: introduction opening, background and theory, atlas setup | Owner; Claude Code drafts from §5 on request |
| Fri Oct 9 | Results and analysis sections from B12 exhibits | Owner with Claude Code |
| Sat Oct 10 | Complete draft; related work; limitations; ethics | Owner |
| Sun Oct 11 | Self-review (§11.5), anonymization, appendix, checklist, number checker | Owner; Claude Code runs B13 and lints |
| Mon Oct 12 | Final read; submit by 8 pm ET | Owner |

### 11.3 Exhibits

| Exhibit | Method framing | Atlas framing | Source tasks |
| --- | --- | --- | --- |
| Figure 1 | Frozen vs FS retention per held-out derivative | Retention distribution per drafter, by derivative type | A4, A7, M4 |
| Figure 2 | Atlas retention and depth (compressed) | A10 against A00 per derivative | A4, A7 |
| Figure 3 | Per-derivative FS gains over each arm | Relative loss against K, observed vs Proposition 1 | M4 / A4 |
| Figure 4 | Transport before and after FS | Transport ratio by derivative type | A8 |
| Table 1 | Arms and what each isolates | Pool composition by type | A2, M3 |
| Table 2 | Main results by arm, with parent retention | Predictor strength (cross-validated) | M4 / A6 |
| Appendix | Ablations (M5), generality (M6), EAGLE 3.1 (M7), speedups (A9), full per-derivative tables | Speedups (A9), per-derivative tables, ledger children (A5) | — |

### 11.4 ARR requirements and checklist

- [ ] Official ACL style, anonymous review mode, compiles without warnings
- [ ] At most 8 pages of content (4 for a short paper)
- [ ] Limitations section present (missing → desk reject)
- [ ] No names, affiliations, acknowledgements or identifying links; Spec-TLM findings described in the third person
- [ ] Every author has an OpenReview profile and completed ARR reviewer registration by Oct 12
- [x] Not under review elsewhere: the TTCL workshop paper (EXP-SUB-001) was never submitted or published
- [ ] Responsible NLP checklist: limitations (A1), risks (A2), licenses of every model and dataset (B)
- [ ] Research area: efficiency
- [ ] B13 checker passes; every number traced to a ledger entry
- [ ] Pre-registered predictions reported as made, including misses

### 11.5 Self-review: objections a strong reviewer will raise

| Objection | Where the paper answers it |
| --- | --- |
| "This is just data augmentation." | PO-D and PO-T hold prompts and response text fixed while removing target diversity; MVD and M5 ablations isolate mixtures and the delta term |
| "Per-child adaptation is cheap." | One-time FS cost against per-child costs (EDA reports 2.0 hours and 127 MB per child; Osprey 48 H100-hours per target) |
| "EAGLE 3.1 already made drafters robust." | M7 row, or a stated limitation if M7 slips |
| "Osprey already solved robustness." | Osprey addresses workload shift; the four cells separate it from target shift |
| "Fine-tunes barely hurt modern drafters." | The atlas reports the full distribution; Proposition 1 and the depth results |
| "Hand-picked fine-tunes." | Stratified public pools; temporal and uploader holdout; derivatives as the unit of analysis |
| "Acceptance is not speed." | A9 wall-clock on dedicated GPUs |
| "It hurts the base model." | Parent retention by TOST |

### 11.6 Claims to avoid

Not "first" to show fine-tuned targets degrade drafters (Hong et al., EDA,
FlexSpec); to adapt drafters to fine-tuned targets (EDA, Predibase Turbo
LoRA); a robust or reusable drafter (Osprey, EAGLE 3.1, OmniDraft);
version-agnostic drafting (FlexSpec); delta distillation (Delta-KD, OPD²); a
speculative-decoding benchmark (SPEED-Bench, Spec-Bench). Safe phrasing: "to
our knowledge, the first method that trains a feature-conditioned drafter for
zero-shot transfer across the derivatives of its base, evaluated on held-out
public derivatives with target shift separated from workload shift."

---

## 12. Risks

| Risk | Mitigation |
| --- | --- |
| Silent bug in agent-written code | §9 checks; operator re-runs every acceptance test; protocol freeze |
| Critical path (M1 → M4) slips past Thursday | Bank work starts Tuesday in parallel with the atlas; atlas framing as fallback |
| FS ties the controls | Atlas framing; report the tie honestly |
| Engine breaks EAGLE-3 + LoRA or DFlash | Gate 1 fallback to the 0.17.1 harness; never mix engines |
| Cluster queueing | Book allocation now; critical path first; seeds before extra arms |
| Storage for full fine-tunes and features | Stage each model once on shared storage; storage estimate before offline capture |
| Pools shrink after filters | Over-sample about 100 candidates per base |
| Atlas shows little loss | The tail and its predictors carry the atlas; method gains judged on derivatives that do lose |
| Offline transport fails validation | Move to appendix; propositions stand alone |
| Owner review becomes the bottleneck | Owner reviews gate reports and tests, not code |
| Writing squeezed | Shared sections start Thursday; hard freeze Saturday noon |
| Overclaiming | Claims fixed at the freeze; B13 checker; §11.6 |

---

## 13. Decision log

*Owner decisions only. The operator may record a decision the owner states,
citing where it was stated.*

| ID | Date | Decision | Status |
| --- | --- | --- | --- |
| D-01 | 2026-10-05 | Submit to the ARR October 2026 cycle; commit to NAACL 2027 | Decided |
| D-02 | 2026-10-05 | Run atlas and method tracks in parallel; Gate 3 chooses the framing by the §3.1 rule | Decided |
| D-03 | 2026-10-05 | Codex builds; Claude Code operates; owner decides | Decided |
| D-04 | — | Split cutoffs: Llama 2025-07-01, Qwen3 2026-01-01 (§5.7) | **Pending owner** |
| D-05 | — | Predictions in §6.3 recorded in the ledger before A4 and M3 launch | **Pending owner** |
| D-06 | — | FollowSpec starting hyperparameters (§5.4) accepted | **Pending owner** |
| D-07 | 2026-10-05 | The TTCL workshop paper (EXP-SUB-001) was never submitted or published; no conflict | Decided |
| D-08 | 2026-10-05 | **Gate 1 PASS**: engine locked to vLLM 0.31.0 (`atlas/env/requirements.lock`, sha256 deb579cd…) for all sprint numbers. Owner reply to codex-1 ~22:10 ET: "Approve PASS and fresh compilation per cell" (notes/B2.md, 22:11 entry); evidence reports/GATE-1.md. Entered by claude-ops | Decided |
| D-09 | — | Gate 2 outcome | Pending |
| D-10 | — | Gate 3 outcome and framing | Pending |
| D-11 | 2026-10-05 | Delta-consistency term (§5.4): renormalize the child's p_c within the top-k set V_k for both d̄ and the variance weights, so the term is invariant to additive log constants (§7 B6 test (b)). Owner reply to codex-1 in chat, "Normalize within top-k (recommended)", recorded in notes/B6.md at 17:18 ET; entered here by claude-ops. No other §5.4 default changes; D-06 is still pending | Decided |
| D-12 | 2026-10-05 | Lift the Sep 11 experiment pause for the NAACL sprint (small builder acceptance runs and operator jobs whose dependencies and preflight pass; no restart of historical campaigns). Owner message to codex-1: "if there are pause markers we can lift, lift them so we can begin running GPU jobs ... if the relevant code ... has been built". Recorded before removal in `notes/PAUSE-LIFT-20261005.json`; marker archived at `artifacts/pause_archive/20261005/`; marker absent from 17:32 ET. Entered here by claude-ops | Decided |
| D-13 | 2026-10-05 | Use the existing write-capable Hugging Face token for reads/downloads only; never upload or mutate Hub resources (AGENTS rule 9 amended). Owner to codex-1: "Just use the token with write access, and change the AGENTS.md accordingly" (cited in notes/B1.md 16:5x and notes/BUILD-AUDIT-20261005.md item 7; AGENTS.md commit ff2ef3c). Entered here by claude-ops | Decided |
| D-14 | 2026-10-05 | Atlas cells use a **fresh vLLM compile per cell** (`VLLM_CACHE_ROOT=<run>/vllm_cache`); child/derivative repeats are reported separately. Same owner reply as D-08. The noise-floor choice (GATE-1 decision 3) and DFlash replication (decision 4) remain open. Entered by claude-ops | Decided |
| D-15 | 2026-10-05 | Work as fast as possible: do not wait for gate calendar dates or another "continue"; advance as soon as dependency checks pass. Failed acceptance tests are not waived and thresholds are unchanged. Owner to codex-1 (notes/B2.md, 22:11 entry). Entered by claude-ops | Decided |
| D-16 | 2026-10-05 | A2 coherence filter (FIX-1) degeneracy criterion: flag an answer if it is empty, ends immediately, or one repeated 4-gram covers **strictly more than 50%** of its generated token positions (alongside MASTER's PPL ≤ 2× base and 10-prompt check). Owner reply to codex-1: "Approve the 50% repeated-4-gram criterion" (notes/FIX-1.md 22:39; proposed before outputs were inspected). Entered by claude-ops | Decided |
| D-17 | 2026-10-05 | Transport decomposition (B9/A8): label_shift = a(base features, child labels) − a(base, base); transport = a(child, child) − a(base, child); R = transport / (−label_shift), undefined when the denominator is 0. Owner approval to codex-1 (notes/B9.md 23:19). Entered by claude-ops | Decided |
| D-18 | 2026-10-05 | Repository on GitHub, private `shrenikbhansali/SpecTLM-NAACL`; **one `main` plus per-site config** (`sites/heck.env`, `sites/ice.env`), no long-lived site branches; the ICE Slurm cluster (H100/H200) is the training/data-generation site. Owner answers to claude-ops in chat (2026-10-05 23:53 ET). Entered by claude-ops | Decided |
| D-19 | 2026-10-06 | ICE is down until Thu Oct 8: all work runs on heck A40s until then, with the method data path (B5 generation, online feature capture, M2/M3 on A40s) prioritized and running in the background alongside the atlas track (§3.2). Owner instruction to claude-ops in chat (2026-10-06 00:01 ET). Entered by claude-ops | Decided |

---

## 14. References

### 14.1 Implementation

- vLLM LoRA × speculative decoding status: https://github.com/vllm-project/vllm/pull/55628
- Speculators, DFlash: https://docs.vllm.ai/projects/speculators/en/latest/user_guide/algorithms/dflash/
- Speculators, training DFlash: https://docs.vllm.ai/projects/speculators/en/stable/user_guide/tutorials/train_dflash_online/
- EAGLE repository: https://github.com/SafeAILab/EAGLE
- EAGLE 3.1 in vLLM: https://vllm.ai/blog/2026-05-26-eagle-3-1
- SpecForge SpecBundle EAGLE-3 for Llama-3.1-8B: https://huggingface.co/lmsys/SGLang-EAGLE3-Llama-3.1-8B-Instruct-SpecForge
- ARR call for papers: https://aclrollingreview.org/cfp · ARR dates: https://aclrollingreview.org/dates · NAACL 2027 call: https://2027.naacl.org/calls/main_conference_papers/

### 14.2 Papers for the writing phase

Give these to whoever drafts related work. Verify every citation and number
against its source before it enters the paper.

- Drafters and robustness: DFlash (https://arxiv.org/html/2602.06036v2); DSpark (https://arxiv.org/abs/2607.05147); Osprey (https://arxiv.org/abs/2609.09338); EAGLE 3.1 (blog above); Attention Drift (arXiv:2605.09992); KVShot (https://arxiv.org/pdf/2604.26412); SPEED-Bench (https://icml.cc/virtual/2026/poster/64011)
- Derivatives and adaptation: Hong et al., domain draft models (arXiv:2503.07807); EDA (https://arxiv.org/html/2603.09527); FlexSpec (https://arxiv.org/abs/2601.00644); OmniDraft (https://arxiv.org/html/2507.02659v1); Quantize the Target (https://arxiv.org/pdf/2607.04244); Draft-OPD (https://arxiv.org/pdf/2605.29343)
- Online and RL: Aurora (ICML 2026); OnlineSpec (ICML 2026); Test-Time Speculation (arXiv:2605.09329); DVI (https://arxiv.org/pdf/2510.05421); ReSpec (MLSys 2026); GrowMTP (https://arxiv.org/html/2609.16648v1); Online Draft Co-Training (https://arxiv.org/abs/2609.07108)
- Deltas and composition: Delta-KD (https://arxiv.org/abs/2509.14526v1); OPD² (https://huggingface.co/papers/2607.15161.md); Emulated fine-tuning (ICLR 2024); proxy-tuning (https://arxiv.org/abs/2401.08565v2); task arithmetic (arXiv:2212.04089); LoraHub (https://arxiv.org/pdf/2307.13269); ExPO (https://arxiv.org/abs/2404.16792v5)
- Systems and evaluation: Performance or Illusion? (MLSys 2026); S-LoRA (https://arxiv.org/pdf/2311.03285); SD² (AAAI 2026); LongSpec (ACL 2026); SpecExtend (Findings of ACL 2026)

### 14.3 Background

The full research proposal and literature grounding live in the owner's
"FollowSpec proposal" document; the Spec-TLM archive (`00_START_HERE.md`,
`02_METHODS_AND_PROTOCOLS.md`, `03_ALL_EXPERIMENTS.md`) holds the prior
evidence and protocols.
