### EXP-ATL-002
**Gate 1 (A1): engine smoke cells, compile-dependent noise floor, known-child drift on vLLM 0.31.0**

**Landed:** 2026-10-05 17:56–18:29 ET · NAACL sprint, Day 1 (A1 / Gate 1) · **Status:** pilot

**What / why.** Gate 1 asks whether the pinned engine runs EAGLE-3 (including LoRA targets), EAGLE-v1 and DFlash on
the Llama base, and whether repeat runs agree. A1 also re-estimates the noise floor on the new engine (20 base A00
replicates) and re-measures the ledger's known drifted child for all three seeds.

**New in this experiment.** First noise-floor estimate on vLLM 0.31.0, and the first test of how vLLM's compile cache
affects run-to-run variation: replicates sharing a cache vs a fresh compile per run, at 128 and at 512 new tokens.
First 3-seed child drift on the new engine; first DFlash replicates on the same engine as EAGLE.

**Artifacts.** One directory per run, `/home/heck2/sbhansali8/SpecTLM/artifacts/A1-llama-*/` (launcher `config.json`,
`launch_script.sh`, `launch.log`, `exit_code`, and harness output in `cell/`: config.json, per_prompt.jsonl, results.json).
Aggregated: `/home/heck2/sbhansali8/SpecTLM/artifacts/A1_gate1_analysis_20261005.json` (produced by `ops/a1_analyze.py`).
Wave definitions: `ops/waves/A1_wave1.sh`, `A1_retry1.sh`, `A1_retry2_eaglev1.sh`, `A1_wave2_freshcompile.sh`, `A1_wave3.sh`.
Paths verified to resolve 2026-10-05 18:31 ET.

**Config.**

| Setting | Value |
| --- | --- |
| Engine / lock | vLLM 0.31.0, `atlas/env/requirements.lock` sha256 deb579cd2b5e2bd95524ef136cc7230d56e83c10ca6b77d7ec1a200cf10c5a08 |
| Code | tag `run-A1-20261005` = main b37e85a (clean), worktree `/home/heck2/sbhansali8/SpecTLM-runs/run-A1-20261005` |
| Target / drafters | as EXP-ATL-001 (same pinned revisions) |
| Children | EXP-MTH-018 cell D (= EXP-MTH-002 math all-token, LR 2e-4), window 3, seeds 0/1/2: `cache_big/spectlm_a40_iclr_20260809/artifacts/l31-math-s{0,1,2}-drift-full-a1/adapters/window_003`; merged s0 = `$WS/artifacts/B2_merge_20261005/model` |
| Prompts | 128 GSM8K prompts, sha256 e3657029… (as EXP-ATL-001) |
| Decoding | greedy, seed 0, K = 4, batch 1, max_model_len 4096, gpu-mem 0.70; max_new_tokens 128 (512 in wave 3a) |
| Compile cache | wave 1 and retries: shared default `~/.cache/vllm`; wave 2 and 3: fresh per run (`VLLM_CACHE_ROOT=<run>/vllm_cache`) |
| Hardware | 1× A40 per cell on heck-srv1/2/3/4/5 (shared nodes) |

**Results.** Macro AL, n = 128 prompts per cell; 71 cells included, all passing §8.4 validation.

Base A00 replicates (EAGLE-3):

| Set | n | Mean | SD | Range | Pairwise \|diff\| p95 | Distinct values | Values |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Shared compile, 128 tok | 20 | 3.061797 | 0 | 0 | 0 | 1 | 20 × 3.061797 |
| Fresh compile, 128 tok | 20 | 3.053985 | 0.004580 | 0.012338 | 0.011733 | 6 | 3× 3.049459, 5× 3.050064, 4× 3.051874, 5× 3.057798, 2× 3.061358, 1× 3.061797 |
| Fresh compile, 512 tok | 20 | 3.105030 | 0.002910 | 0.008592 | 0.008400 | 7 | 8× 3.102709, 4× 3.104402, 2× 3.105006, 1× 3.105085, 2× 3.106355, 2× 3.111104, 1× 3.111301 |

Other drafters (base, 128 tok): EAGLE-v1 2.5907 (n = 1; run `A1-llama-eagle-k4-s0-202610051810`); DFlash K = 4:
3.4127 (wave 1) and 5 fresh-compile replicates 3.3951, 3.4113, 3.4127, 3.4127, 3.4132 (range across 6 cells 0.0181).

Known child, A10 (LoRA) and drift:

| Seed | A10 | Drift vs shared A00 (3.0618) | Drift vs fresh A00 mean (3.0540) | Ledger EXP-MTH-018 (0.17.1) |
| --- | --- | --- | --- | --- |
| 0 | 2.8554 | −0.2064 | −0.1986 | −0.1998 |
| 1 | 2.8037 | −0.2581 | −0.2503 | −0.2470 |
| 2 | 2.7555 | −0.3063 | −0.2985 | −0.2961 |
| Mean (sd, n = 3) | 2.8049 | −0.2569 (0.0500) | −0.2491 (0.0500) | −0.2476 |

LoRA vs merged (s0): 2.8554 vs 2.8580, diff −0.0026.

Timing (generation s / output tok/s, A40 batch 1): EAGLE-3 base 194 s / 80.4; 512 tok 286 s / 82.4; EAGLE-v1 260 s / 60.0;
DFlash 175 s / 89.3; child LoRA 179 s / 66.0; child merged 164 s / 75.2 (full table in reports/GATE-1.md).

**Caveats.** Within one compiled graph the engine is deterministic, so the shared-cache replicates measure nothing;
the fresh-compile sets are the relevant floor, and the outcome distribution is discrete (6–7 values in 20 runs), so
SD and range from n = 20 are coarse. Noise measured on GSM8K only. One A10 cell per seed (each also a single compile
draw); the child cells used the shared cache. EAGLE-v1 n = 1. DFlash K options other than 4 untested. Shared nodes,
so timing is indicative only. Excluded runs: `A1-llama-eagle3-k4-s0-202610051757-r01` (operator-started duplicate on a
busy GPU, aborted, `OPERATOR_NOTE.txt`), `A1-llama-eagle-k4-s0-202610051805` and
`A1-llama-eagle3-k4-s0-202610051806-mth018d-lora-s0` (HF 429 at engine init), `A1-llama-eagle-k4-s0-202610051807`
(offline cache lacked EAGLE-v1 weights); all re-run with identical settings.

**Addendum (2026-10-05 22:11 ET, wave 4; revision after codex-1 audit).** 10 more runs, fresh compile per run, settings as
wave 1: child s0 LoRA × 5 (`A1-llama-eagle3-k4-s0-2026100522xx-mth018d-lora-s0-fresh-r01…r05`) = 2.851340, 2.860999,
2.866934, 2.867170, 2.872315 (mean 2.86375, SD 0.00801, range 0.02098); child s0 merged × 5 (`…-mth018d-merged-s0-fresh-r01…r05`)
= 2.865450, 2.866550, 2.868753, 2.868753, 2.871856 (mean 2.86827, SD 0.00246, range 0.00641). Seed-0 drift vs fresh A00
mean: −0.1902; LoRA − merged (fresh means): −0.0045. Aggregate: `$WS/artifacts/A1_gate1_analysis_20261005_v2.json`
(81 included cells). **Caveat added:** LoRA-target cells vary more across compiles than the base (SD 0.0080 vs 0.0046), so
the base floor understates single-cell A10 noise for adapters. The B2 s0 LoRA value (2.8747) is 0.0024 above the
5-repeat range. The original entry's run total ("74") should read 75 for waves 1–3.
