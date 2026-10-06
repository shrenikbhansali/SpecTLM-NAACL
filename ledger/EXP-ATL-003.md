### EXP-ATL-003
**DFlash K probe on vLLM 0.31.0 (Llama base, A7 prep)**

**Landed:** 2026-10-05 22:23–22:30 ET · NAACL sprint, Day 1 (A7 prep) · **Status:** pilot

**What / why.** B2/A1 tested DFlash only at K = 4. A7 must use the drafter's native block setting where the engine allows.
This probe records which K values vLLM 0.31.0 accepts for z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat (trained block
size 10) and the acceptance at each.

**New in this experiment.** First DFlash cells at K > 4 on the pinned engine (EXP-MTH-022 used SGLang with block 10).

**Artifacts.** `/home/heck2/sbhansali8/SpecTLM/artifacts/A7-llama-dflash-k{8,9,10}-s0-202610052223-kprobe/` (config.json, cell/).

**Config.** As EXP-ATL-002 (tag `run-A1-20261005`; vLLM 0.31.0; target @0e9e39f2; DFlash @d3af30de; GSM8K-128, sha256 e3657029…;
greedy, seed 0, max_new_tokens 128, batch 1, gpu-mem 0.70); fresh compile per run; K ∈ {8, 9, 10}; 1× A40 each (heck-srv3).

**Results.** n = 128 prompts per cell, one run per K.

| K | Macro AL | Generation s | Output tok/s |
| --- | --- | --- | --- |
| 8 | 4.0134 | 234 | 67.0 |
| 9 | 4.0738 | 238 | 65.9 |
| 10 | 4.0871 | 230 | 68.0 |
| 4 (EXP-ATL-002, 6 cells) | 3.3951–3.4132 | 175 | 89.3 |

**Caveats.** One run per K; DFlash between-compile range at K = 4 was 0.018 (n = 6), so the K = 9 vs 10 difference (0.013) is
within that range. One workload (GSM8K) at 128 tokens. Timing is from shared A40s, not A9-grade.
