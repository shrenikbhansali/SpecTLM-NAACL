# Gate 1 — Engine (due Mon Oct 5, 11 pm ET)

Prepared by claude-ops, 2026-10-05 18:40 ET. Evidence: `notes/A1.md`, `notes/B2.md`,
`$WS/artifacts/A1_gate1_analysis_20261005.json` (every cell, recomputed from raw per-prompt counters),
ledger drafts `ledger/EXP-ATL-001.md` (B2 golden cells) and `ledger/EXP-ATL-002.md` (A1).
`$WS = /home/heck2/sbhansali8/SpecTLM`.

## Recommendation

**PASS (mechanical application of the §3.1 rule).** The pinned engine runs EAGLE-3 with LoRA targets, DFlash and
EAGLE-v1 on the Llama base, and repeat runs agree within the ledger noise floor. Lock the engine below for all sprint
numbers. The owner records the outcome as §13 D-08.

Two protocol questions need an owner decision before the A4/A7 sweeps (see "Decisions needed"): how cells handle the
vLLM compile cache, and which noise floor the atlas uses.

## Engine and lock

| Item | Value |
| --- | --- |
| Engine | vLLM **0.31.0** (latest stable on PyPI at build time), torch 2.13.0 (cu130), transformers 5.17.0, flashinfer-python 0.7.0.post1 |
| Lock file | `atlas/env/requirements.lock`, sha256 `deb579cd2b5e2bd95524ef136cc7230d56e83c10ca6b77d7ec1a200cf10c5a08`; source pin `atlas/env/engine.json` |
| Environment | `$WS/.venv-atlas-031-clean` (isolated; historical vLLM 0.17.1 env untouched) |
| Harness | `atlas/run_cell.py` (B2, done 17:54 after operator re-run); A1 ran from tag `run-A1-20261005` (main b37e85a), clean |
| Hardware | NVIDIA A40 46 GB, driver 610.57.04; heck-srv1–5, one GPU per cell, batch 1 |
| Models (pinned) | target meta-llama/Llama-3.1-8B-Instruct @0e9e39f2; EAGLE-3 RedHatAI/…speculator.eagle3 @f4fa34a8; EAGLE-v1 yuhuili/EAGLE-LLaMA3.1-Instruct-8B @d0e4a208; DFlash z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat @d3af30de |
| Protocol | 128 GSM8K prompts of EXP-MTH-021 (sha256 e3657029…, pre-templated); K = 4; greedy, seed 0; **max_new_tokens 128 to match the ledger's golden cells** (the historical scripts default to 128; verified from per-prompt completion lengths); gpu-mem 0.70; max_model_len 4096 |

## Gate 1 checks

| Check (§3.1, §6.1 A1, §7 B2) | Result | Verdict |
| --- | --- | --- |
| EAGLE-3 runs, base | 3.0540 mean of 20 fresh-compile replicates (range 3.0495–3.0618); ledger (vLLM 0.17.1) 3.0559 | pass |
| EAGLE-3 with LoRA targets | child LoRA cells run for 3 seeds (below) | pass |
| EAGLE-v1 runs | 2.5907 (A1), 2.5906 (B2); ledger 2.5951 | pass |
| DFlash runs | 3.3951–3.4132 over 6 cells (5 fresh-compile + 1 wave-1) at K = 4 (trained block size 10); B2's cell 3.3951 | pass. Other K options were not tested (see caveats) |
| Repeat runs agree | identical within one compiled graph (20/20 bit-identical); across fresh compiles range 0.0123 < ledger floor 0.0138 | pass |
| LoRA = merged within noise | child s0: LoRA 2.8554 vs merged 2.8580, diff −0.0026 (B2: 2.8747 vs 2.8729, diff +0.0018); fresh-compile pairwise p95 = 0.0117 | pass |
| Known child's drift negative, near −0.248 | mean −0.257 over 3 seeds (ledger −0.248); per seed within 0.011 of the ledger (table below) | pass |

### Known child (EXP-MTH-018 cell D = EXP-MTH-002 math all-token LR 2e-4, window 3), A10 − A00

| Seed | A10 (LoRA) | Drift vs shared-compile A00 3.0618 | Drift vs fresh-compile A00 mean 3.0540 | Ledger (0.17.1) |
| --- | --- | --- | --- | --- |
| 0 | 2.8554 | −0.2064 | −0.1986 | −0.1998 |
| 1 | 2.8037 | −0.2581 | −0.2503 | −0.2470 |
| 2 | 2.7555 | −0.3063 | −0.2985 | −0.2961 |
| **Mean (sd)** | | **−0.2569 (0.050)** | **−0.2491 (0.050)** | **−0.2476** |

One A10 cell per seed; each A10 value has between-compile uncertainty of about ±0.006 (SD 0.0046). B2's own s0
LoRA cell (separate compile) gave 2.8747 (drift −0.175 against its base 3.0495). That B2 pair is two single
draws from the compile distribution; the 3-seed comparison above uses the 20-replicate A00.

## Noise floor (new engine)

| Replicate set (base A00, EAGLE-3, K = 4) | n | Mean | SD | Range | Pairwise \|diff\| median / p95 | Distinct values |
| --- | --- | --- | --- | --- | --- | --- |
| Shared compile cache (wave 1) | 20 | 3.06180 | 0 | 0 | 0 / 0 | 1 |
| **Fresh compile per run, 128 tok** (wave 2) | 20 | 3.05398 | 0.00458 | **0.01234** | 0.00592 / **0.01173** | 6 |
| **Fresh compile per run, 512 tok** (wave 3) | 20 | 3.10503 | 0.00291 | **0.00859** | 0.00195 / 0.00840 | 7 |
| DFlash, 5 fresh-compile + 1 wave-1 cell, 128 tok | 6 | 3.4096 | — | 0.0181 | — | 5 |
| Ledger EXP-MTH-031 (vLLM 0.17.1) | 89 | — | — | — | median spread 0.0138 | — |

**Finding (observation for the owner).** Within one compiled graph the engine is deterministic: 20 replicates on 3
nodes and 20 GPUs are bit-identical (all loaded one cached AOT-compiled graph from `~/.cache/vllm`). Each fresh
compile lands on one of a few discrete outcomes (6 values over 20 runs at 128 tokens). The low end, 3.049459, and
3.057798 are exactly B2's base and repeat, which each compiled fresh. Model blobs are byte-identical across the two HF
caches used, which rules out weights. So run-to-run variation on this engine comes from compilation, and a floor
measured on a shared cache (0) would understate the variation between cells that compile separately.

## Timing (A40, batch 1, shared nodes; not A9-grade)

| Cell type | n | Macro AL | Generation s | Output tok/s | Startup s | Cell total s | Tokens/prompt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EAGLE-3 base, shared compile | 20 | 3.0618 | 193.4 | 80.8 (80.5–80.9) | 74 | 267 | 122.1 |
| EAGLE-3 base, fresh compile | 20 | 3.0540 | 194.4 | 80.4 (80.2–80.6) | 121 | 316 | 122.0 |
| EAGLE-3 base, fresh, 512 tok | 20 | 3.1050 | 286.0 | 82.4 (81.7–83.0) | 151 | 438 | 184.0 |
| EAGLE-v1 base | 1 | 2.5907 | 259.9 | 60.0 | 104 | 365 | 121.9 |
| DFlash base | 6 | 3.4096 | 175.4 | 89.3 (88.6–89.7) | 134 | 310 | 122.4 |
| Child LoRA (s0–s2) | 3 | 2.8049 | 179.4 | 66.0 (64.8–67.2) | 145 | 325 | 92.6 |
| Child merged (s0) | 1 | 2.8580 | 164.3 | 75.2 | 114 | 279 | 96.5 |

Observation: the same child served as LoRA ran at 67.2 tok/s against 75.2 merged, with nearly equal acceptance
(2.855 / 2.858), which is LoRA serving overhead. Fresh compilation adds ~50 s of startup per cell. No target-only
(no-speculation) baseline was run; speedups are A9's job on the dedicated H200s.

## Decisions needed (owner)

1. **D-08 Gate 1 outcome.** Recommended: **pass**; lock vLLM 0.31.0 with `atlas/env/requirements.lock` (sha256 deb579cd…).
2. **Compile-cache policy for the atlas (A4, A5, A7).** Options:
   (a) **fresh compile per cell** (`VLLM_CACHE_ROOT=<run>/vllm_cache`): each cell is an independent draw; the noise
   floor is the between-compile distribution above; ~50 s more startup per cell;
   (b) shared compile cache: base replicates are deterministic, but different targets (LoRA vs merged, other
   architectures or quantizations) compile their own graphs, so A00 vs A10 still carries between-compile variation
   while the replicates hide it.
   **Recommended default: (a).** It matches how the noise floor is measured.
3. **Noise floor used for atlas comparisons.** Recommended: at the atlas length (512 tokens), use the fresh-compile
   values: SD 0.0029, range 0.0086 (n = 20). Keep the ledger's 0.0138 for comparisons against historical 128-token cells.
   The 512-token estimate is on GSM8K only; noise on other workloads is unmeasured. Option: repeat 5 fresh-compile
   base cells on the SPEED-Bench general set once B4 lands.
4. **DFlash noise and K.** DFlash's range across 6 cells (0.018) exceeds EAGLE-3's. Recommended: A7 runs DFlash
   cells with replicates (≥3 per cell) or reports against the DFlash range. B2 tested only K = 4. vLLM's accepted K
   values for DFlash and the native setting (block size 10) still need a run; proposed as the first A7 smoke cell.

## Caveats

- One target family and one workload (GSM8K, 128 prompts) at 128 tokens for the golden checks. The 512-token floor
  is one extra measurement, not the atlas workloads.
- EAGLE-v1 n = 1 in A1 (plus B2's cell, which agrees to 1e-4). DFlash K options untested.
- Child A10 cells ran on the shared default compile cache; the drift is reported against both A00 estimates.
- Launch incidents (no effect on included numbers; details in `notes/A1.md`): a duplicate replicate started by the
  operator on a busy GPU (aborted, excluded, marked with `OPERATOR_NOTE.txt`); two cells failed on HF 429 rate
  limits and one on a missing cached weight file, all re-run under identical settings (retry run IDs in the journal).
- Timing is from shared A40 nodes (other users' jobs on heck-srv1), not exclusive GPUs.
- Validation (§8.4): all 71 included cells: config complete with pinned revisions, engine 0.31.0, clean tagged commit,
  128/128 golden prompt IDs, every per-prompt AL in [1, K+1], macro recomputed from raw counters equal to results.json.
