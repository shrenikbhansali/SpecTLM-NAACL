### EXP-ATL-001
**B2 golden acceptance cells on the pinned vLLM 0.31.0 harness**

**Landed:** 2026-10-05 17:39–17:49 ET · NAACL sprint, Day 1 (B2) · **Status:** pilot (run by codex-1; entry drafted by claude-ops)

**What / why.** The sprint moves all atlas measurement to a newly pinned engine (vLLM 0.31.0) and a new harness
(`atlas/run_cell.py`). These six cells check that the harness reproduces the ledger's golden measurements on that
engine before any sweep uses it (MASTER §7 B2 acceptance (a)–(e)).

**New in this experiment.** Replication of EXP-MTH-021 (EAGLE-3 / EAGLE-v1 base) and EXP-MTH-018 cell D seed 0 (child
drift) on a new engine (0.31.0 vs 0.17.1) and a new harness with per-request detailed spec-decode counters. First
same-engine DFlash cell (EXP-MTH-022 used SGLang).

**Artifacts.** `/home/heck2/sbhansali8/SpecTLM/artifacts/B2_acceptance_20261005/{base_retry2,repeat,lora_retry2,merged,eagle_retry1,dflash_retry1}/`
(config.json, per_prompt.jsonl, results.json); checker report `…/acceptance_report.json`; merge provenance
`/home/heck2/sbhansali8/SpecTLM/artifacts/B2_merge_20261005/`. Paths verified to resolve 2026-10-05 18:31 ET.

**Config.**

| Setting | Value |
| --- | --- |
| Engine | vLLM 0.31.0, lock `atlas/env/requirements.lock` (sha256 deb579cd…) |
| Code | commit 97a9a999 (clean) |
| Target | meta-llama/Llama-3.1-8B-Instruct @0e9e39f249a16976918f6564b8830bc894c89659 |
| Drafters | EAGLE-3 RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3 @f4fa34a8; EAGLE-v1 yuhuili/EAGLE-LLaMA3.1-Instruct-8B @d0e4a208; DFlash z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat @d3af30de (block size 10) |
| Child | `cache_big/spectlm_a40_iclr_20260809/artifacts/l31-math-s0-drift-full-a1/adapters/window_003` (LoRA r 8, alpha 16, q/v; adapter sha256 e67734a3…); merged via CPU PEFT safe_merge |
| Prompts | 128 GSM8K eval prompts of EXP-MTH-021, sha256 e365702983e4e1c5d640c6100a9b3ca46e16bc285520a237101137d0bab99ea7 |
| Decoding | greedy (temperature 0), seed 0, K = 4, max_new_tokens 128, batch 1, max_model_len 4096, gpu-mem 0.70, prefix caching off, LoRA enabled (max rank 64) in every cell |
| Compile cache | separate per cell (fresh compile) |
| Hardware | 1× A40 per cell, heck-srv2 |

**Results.** Macro acceptance length (1 + accepted/steps per prompt, mean over prompts), n = 128 prompts each.

| Cell | Macro AL | Prompt-bootstrap 95% CI | Generation s | Cell total s |
| --- | --- | --- | --- | --- |
| base (EAGLE-3) | 3.0495 | [2.9984, 3.0981] | 194.5 | 363.5 |
| repeat (EAGLE-3) | 3.0578 | [3.0080, 3.1053] | 193.9 | 327.1 |
| child s0, LoRA | 2.8747 | [2.8197, 2.9287] | 183.6 | 366.3 |
| child s0, merged | 2.8729 | [2.8194, 2.9262] | 164.2 | 287.0 |
| EAGLE-v1 base | 2.5906 | [2.5450, 2.6374] | 260.4 | 429.5 |
| DFlash base, K = 4 | 3.3951 | [3.3349, 3.4508] | 175.5 | 344.7 |

Derived: repeat diff 0.0083; child drift −0.1748 (ledger seed 0: −0.1998); LoRA − merged +0.0018; base vs ledger
3.0559: −0.0064. Prompt-bootstrap CIs describe prompt variation, not run-to-run noise (see EXP-ATL-002).

**Caveats.** Single seed of the child; every cell is a single draw from the compile-outcome distribution (EXP-ATL-002
shows base A00 takes values 3.0495–3.0618 across fresh compiles, and 3.0495 is the lowest of them. This pair's drift
(−0.175) is therefore a single-draw estimate; EXP-ATL-002's seed-0 drift against the 20-replicate A00 is −0.199 to −0.206). Several earlier attempts failed on an AutoConfig incompatibility and a missing `ninja` on PATH; they are
preserved as `*_retry*`/failed directories and excluded. Timing on a shared node.

**Erratum (2026-10-05T23:21 ET, claude-ops).** The Config row "LoRA enabled (max rank 64) in every cell" is incorrect: the harness sets
`enable_lora=bool(adapter)`, so only the child-LoRA cell ran with LoRA enabled. `max_lora_rank` is recorded in every config
but is inert without an adapter. Values and artifacts are unchanged. (Found by codex-1, notes/B8.md 23:11.)
