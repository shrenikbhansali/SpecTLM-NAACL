# Gate report (draft): Fri Oct 9 18:00 ET freeze — method + final experiment list

Drafted by claude-ops at 2026-10-09 ~11:30 ET for the owner's freeze decision. All results are **pilot** (ledger status unchanged).
Engine: frozen harness 6da2e42, vLLM 0.31.0, A40, EAGLE-3 K4, greedy, 512 tokens.
Workloads: target-rendered SPEED-128 / MATH-64 (MATH-500 where noted). Intervals are 95% paired bootstraps over queries (and seeds where stated). τ includes the bonus token; zero-step prompts are excluded pairwise (D-32).
Every number below was recomputed by the operator from raw `per_prompt.jsonl`, or taken from codex's raw-counter analysis snapshots listed under each table.

## 1. Evidence by paper claim

**C1 — Off-lineage post-training breaks family drafters; on-policy RL does not.**

| Population | EAGLE-3 p1 retention | DFlash p1 retention | Source |
|---|---|---|---|
| R1-Distill-Llama-8B (SPEED) | .725 | .735 | [T1](T1-phase1-20261008.md) |
| Nemotron-Nano-8B (SPEED) | .696 | .708 | T1 |
| Direct-child on-policy RL, 4 ckpts | .986 [.969, 1.001] | .990 [.978, 1.006] | [P1](P1-typed-population-20261008.md) |
| Sibling SFT + teacher distillation, 5 ckpts | .898 [.800, .975] | .862 [.786, .927] | P1 |

Robustness to which drafter checkpoint is reused (E1): the official yuhuili EAGLE-3 has τ 1.764 on R1 and 1.763 on Nemotron, about the same as production reuse (1.730 / 1.824). It breaks the same way.

**C2 — Interface-first repair (re-fit `fc`; or full warm start) recovers most of the dedicated-drafter gain without the original training data.**
R1-Distill: reuse τ 1.730 → oracle 2.848 on SPEED; reuse 1.948 → oracle 3.904 on MATH-64.

| Arm (generic 16k, one epoch) | SPEED τ | SPEED gap recovery | MATH-64 recovery | Source |
|---|---|---|---|---|
| fc, 3 seeds | 2.300 | **50.9% [48.9, 53.0]** | 36.3% [34.4, 38.4] | [D49 3-seed](P3-scaling-D49-20261009.md) |
| full, 3 seeds | 2.466 | **65.8% [63.4, 68.2]** | 48.3% [46.4, 50.2] | same |
| full, + 2nd epoch (E5a), seed 0 | 2.480 | 67.1% | 50.4% | Δτ vs 1 epoch +0.022 [+0.001, +0.043] SPEED, +0.045 [+0.011, +0.081] MATH |

- Seed spread is ≤ 0.6 points, much smaller than the query-level interval.
- MATH-500 (n = 500): fc 35.0%, full 48.0%; Δp1 vs reuse +0.201 [.197, .205] / +0.243 [.239, .248]. MATH-64 is a subset of MATH-500.

Second target (E7), Nemotron, 16k one epoch, single seed. There is no oracle for Nemotron, so gains are given against reuse:
- full: SPEED τ 1.824 → 2.424, Δp1 +0.184 [+0.172, +0.196]; MATH τ 1.960 → 2.819, Δp1 +0.234 [+0.223, +0.244].
- fc: SPEED τ 2.315, MATH τ 2.591.

Data scaling, as SPEED recovery for fc / full:

| Repair data | fc | full |
|---|---|---|
| 256 examples | 35.6% | 45.0% |
| 4k | ~44% | ~57% |
| 16k | 50.9% | 65.8% |

**C3 — It is the warm start, not just the data.** Training the same drafter from scratch on the same 16k data (E4) ends **below reuse**: SPEED τ 1.519, MATH 1.672.
Paired against warm-start full: Δτ −0.940 [−0.996, −0.883] on SPEED and −1.217 [−1.260, −1.175] on MATH.

**C4 — Wall-clock speedups (A40, warm, against no speculation, 16k checkpoints; [E6](P6-generic16k-timing-20261009.md)).**

| | reuse | fc | full | oracle |
|---|---|---|---|---|
| batch 1 (n 32 × 3 processes) | 1.29× | 1.72× [1.63, 1.82] | 1.81× [1.68, 1.93] | 2.05× [1.87, 2.23] |
| batch 8 (n 128 × 3) | 1.07× | 1.27× [1.13, 1.45] | 1.31× [1.14, 1.52] | 1.44× [1.24, 1.69] |

The fixed-K cost model was fitted on earlier timings only. On the held-out 16k cells its predicted speedups are within 1.5% of the measured ones ([cost model](P6-D50-cost-model-20261009.md)).

**C5 — Cheaper and faster than the alternatives.**
- Repair cost is measured at 10.9 / 11.2 A40 GPUh (fc / full), including generating the 16k responses.
- The dedicated drafter's public-recipe cost is an *estimate*: 397–825 GPUh at 1 epoch, 1,348–5,073 at 10 epochs, 4,520–19,232 at the 40-epoch public default ([P6 estimate](P6-dedicated-cost-estimate-20261008.md)).
- Independent Llama-3.2-1B drafter (E3): acceptance is competitive, but it is slower. R1 SPEED τ 2.441 and MATH 3.019 (MATH-500: 2.966, versus full 2.858). Warm speedup over no speculation is only 1.27× at batch 1 and 1.11× at batch 8. Its time per panel relative to full repair is 0.70 [0.66, 0.75] at batch 1 and 0.85 [0.73, 0.97] at batch 8, meaning repair finishes the same panel faster ([report](P6-independent1B-timing-20261009.md)).
- n-gram (E2): τ 1.49–1.70; the suffix baseline is unavailable (its dependency is not installed in the pinned environment).

**Nulls to report.**
- TTT4 vs TTT3 at 4k (E5b): Δτ −0.007 [−0.028, +0.013] SPEED full; −0.020 [−0.039, −0.004] MATH full.
- Decoder-LoRA alone is weak (9.6% recovery at 256 examples).
- Affine calibration is null.
- Self-elicited prompts are no better than generic prompts.

## 2. Not usable / pending

- **FIX-24 (blocking for any official-repair claim).** The trainer gives the official drafter a random frozen embedding, so every `E1-official-*-4k-*` repair cell and the snapshot contrasts `official_vs_production_*` (Δτ ≈ −0.8 to −1.0) reflect the bug, not the drafter. They are retained and must not be reported. Official *reuse* is valid. The fix plus rerun takes about 1 h; codex has not claimed it.
- **E5c 64k:** not launched. Started now it would end ~22:30 Fri. E5a shows a second pass adds only ~2 points, so more data is the remaining lever on the 34-point gap to the oracle. Disclose the Alpaca + Dolly source mix.
- E1 at 16k is conditional on official 4k ≥ production 4k, which is undecidable until FIX-24 lands.
- The independent 1B is not timed on Nemotron, and Nemotron repairs are not timed at all.

## 3. Recommended freeze (operator recommendation; owner/delegate decides)

1. **Method:** interface-first repair, with fc and full warm start as the two operating points. The main table uses one epoch on generic 16k with 3 seeds on R1, and 16k single-seed on Nemotron. The 2nd epoch goes in as an ablation row.
2. **Baselines in the main table:** reuse, dedicated oracle (R1), from-scratch on the same data, independent 1B (τ *and* wall-clock), n-gram.
3. **Drafter checkpoint:** keep production RedHat as primary. Add official yuhuili *reuse* as a robustness row. Include official repair only if the FIX-24 rerun is valid and strong (D-50: the strongest version).
4. **Appendix:** TTT4 null, DFlash repair (P4), component matrix, FollowSpec / Track I, triage (P5), MATH-500.
5. **Still to run before the writing freeze:** FIX-24 plus the official 4k rerun (~1 h). Optionally E5c 64k (overnight). Optionally Nemotron timing for fc/full/reuse/none and 1B, b1/b8 (~1 h on idle GPUs), so the second main case has measured speedups.

## 4. Risks for the write-up

- Lead with wall-clock, not τ. The 1B independent drafter matches full repair on τ (and beats it on MATH) but is 30% slower at batch 1.
- Batch-8 gains are compressed (1.27–1.31×), and startup-inclusive batch-8 intervals include 1.
- Timing hosts are shared and not randomized. Greedy outputs differ across arms and processes; this is audited and reported, not certified.
- Repair data comes from development-panel source choices (generic over self-elicited), so these are not untouched confirmation results.

### 2026-10-09T14:18:33.480034-04:00 — FIX-24 INVALIDATION

**INVALID (FIX-24): all historical `E1-official-t{0,1}-4k-{fc,full}` training/evaluation cells and every `official_vs_production_*` contrast derived from them.** The trainer used a random frozen embedding, not the target embedding. These numbers must not describe official-drafter repair or enter paper tables. Official reuse and production repair remain valid. Artifacts and old statements are retained as history; this notice supersedes their interpretation. Complete run manifest: `artifacts/FIX24_20261009_1420/invalid-runs.json`. The earlier conversion note claiming the native trainer used target embeddings was false; loaded-state parity only proved the vLLM path. Corrected runs will use new directories. Old D50 publication/analysis watchers stopped to prevent propagation.

### 2026-10-09T15:14:14-04:00 — claude-ops — addendum: FIX-24 fixed; official drafter now the stronger candidate

The corrected official yuhuili repairs **beat production at matched data**. Nemotron 4k final: fc SPEED τ 2.336 vs 2.252, MATH 2.601 vs 2.483.
R1 official at 25% of 4k is already ≥ production at 100%. The conditional official 16k on R1 is expected to fire (~2.5 h of training plus evals, so it lands ~19:30–20:30).
Per D-50 ("use the strongest version"), the freeze should keep **both drafter checkpoints** in the list and choose the primary checkpoint for the main table only after official 16k lands.
Production 16k already has 3 seeds; official 16k will have one. If official becomes primary, run seeds 1–2 overnight (~2.5 h each, parallel).
Unchanged reuse is equally broken for both (1.76 vs 1.73), so the motivation does not depend on the choice.

### 2026-10-09T18:09:29-04:00 — claude-ops — freeze recorded (D-52)

R1 official 16k seed 0 (operator-paired against the same drafter's reuse; production = D49 seed 0):

| Panel | Arm | official τ / Δτ | production τ / Δτ | Δ difference [95% CI] | gap recovery off / prod |
|---|---|---|---|---|---|
| SPEED | fc | 2.403 / +0.639 | 2.294 / +0.564 | +0.075 [+0.038, +0.113] | 58.9% / 50.5% |
| SPEED | full | 2.536 / +0.772 | 2.459 / +0.728 | +0.044 [+0.015, +0.074] | 71.2% / 65.2% |
| MATH-64 | fc | 2.833 / +0.910 | 2.651 / +0.703 | +0.207 [+0.155, +0.256] | 45.9% / 35.9% |
| MATH-64 | full | 3.006 / +1.083 | 2.888 / +0.941 | +0.142 [+0.103, +0.180] | 54.6% / 48.1% |

Official leads in 16/16 comparisons, so it is primary under D-51, conditional on seeds 1–2. Full decision and the remaining run list: MASTER §13 D-52.

### 2026-10-09T19:20:58-04:00 — claude-ops — D-52 condition met: official primary confirmed (3 seeds)

R1 16k, 3 seeds per drafter. Δτ = repaired − same-drafter reuse; joint seed+query bootstrap. Operator raw recomputation.

| Panel | Arm | official Δτ (per seed) | production Δτ (per seed) | difference [95% CI] | gap recovery official / production |
|---|---|---|---|---|---|
| SPEED | fc | .639 / .645 / .666 | .564 / .573 / .571 | +0.081 [+0.047, +0.118] | 60.0% / 50.9% |
| SPEED | full | .772 / .781 / .781 | .728 / .737 / .741 | +0.043 [+0.012, +0.076] | **71.8%** / 65.8% |
| MATH-64 | fc | .910 / .883 / .889 | .703 / .714 / .714 | +0.184 [+0.132, +0.228] | 45.1% / 36.3% |
| MATH-64 | full | 1.083 / 1.070 / 1.071 | .941 / .943 / .950 | +0.130 [+0.087, +0.171] | 54.2% / 48.3% |

Official full per-seed SPEED recovery: 71.2 / 72.0 / 72.0%.

Official-drafter timing (D-52 follow-ups; fresh same-session none/oracle/independent controls). Operator point estimates of warm panel speedup vs no speculation (mean of 3 processes); codex's paired-bootstrap analysis to follow:

| | official reuse | official fc16k | official full16k | oracle | independent 1B |
|---|---|---|---|---|---|
| R1, batch 1 | 1.31× | 1.74× | **1.83×** | 2.05× | 1.26× |
| R1, batch 8 | 1.07× | 1.27× | 1.29× | 1.41× | 1.11× |
| Nemotron, batch 1 | 1.29× | 1.69× | **1.80×** | – | 1.37× |
| Nemotron, batch 8 | 1.13× | 1.39× | 1.42× | – | 1.24× |

MATH-500 (n=500) official: fc 2.773, full 2.969 (production 2.611 / 2.858; independent 2.966; oracle 3.842). Official reuse is still running.
