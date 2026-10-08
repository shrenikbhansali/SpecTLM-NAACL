### EXP-ATL-016 — P3 single-target EAGLE-3 repair pilot

**Landed:** 2026-10-08.

**Status:** pilot; D-45 initial generic data experiment; no winner promotion or paper conclusion.

**What / why.** Measure how much target-specific native drafter repair recovers, with family-drafter initialization, before the D-46 component/self-elicited matrix.

**New.** Three targets ×fc-only/fc+LoRA/full warm-start ×50/200steps ×SPEED128/MATH64:36 valid evaluation cells. Additional scratch two cells invalid as scratch controls due to an HF initialization-guard bug; retained and excluded. All variants use the same target-specific520 generic prompts/responses and batch/schedule recipe. Native TTT objective unchanged.

**Artifacts.** [Report](../reports/P3-generic-pilot-20261008.md); independent raw counter analysis `artifacts/P3_generic_report_20261008_0352/{analyze.py,results.json}`; source `artifacts/P3_repair_20261008_0305/`. Pinned revisions, response/audit/prompt/file hashes and parameter proofs in every config/export.

**Config + results.** Single seed0; native trainer261a82d, code1e88bb2, TTT3 KL, AdamW2e-5,2048token batch ceiling. All acceptance uses frozen6da2e42/vLLM0.31.0/A40/K4/greedy/512tokens/batch8 and identical derivative-rendered tokens. Paired10,000prompt bootstrap. R1 SPEED,n128: fc200 Δp1+.1417[.1301,.1523],τ2.1014 vs1.7302,Δτ+.3712[.3389,.4008]; full200 Δp1+.1772[.1648,.1890],τ2.2395,Δτ+.5092[.4742,.5428]. Owner fixed τ-gap recovery33.2%/45.5%, data+train0.438/0.437A40GPUh. Nemotron full200 Δp1+.1532[.1418,.1645]; R1Qwen full200+.0541[.0464,.0617],n128. All36 estimates, MATHn64, per-depth/lengths and nulls in report/JSON.

**Caveats.** Generic public prompts, not self-elicited; distinguish old fc_lora(fullfc+all7decoderprojectionLoRA) from D46 low-rank-fc and decoder q/v+MLP proxies. No run-to-run CI or speedup claim. Incomplete reasoning traces and teacher factual errors retained. Per-repair cost charges successful data generation in full but excludes evaluation, failed Magpie trials and engineering overhead. Dedicated oracle cost/data unknown. Scratch invalidation recorded, fixed with regression and native smoke, replacement separately tagged. Component mechanism verdict provisional; affine/RMS and decoder controls pending. No promotion of earlier FollowSpec negative results.
