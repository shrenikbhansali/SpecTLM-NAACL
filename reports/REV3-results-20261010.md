# REV3 — additional ReFit results

Owner D55. All results remain pilot; this evidence document is separate from `paper/claude_final`. Every outcome, including nulls and regressions, is retained. The owner and claude-ops select material for the paper.

## X5 — DFlash16k (P0, Sun Oct11 08:00 ET)

**Status, Saturday 15:40 ET:** all eight native DFlash trainings completed successfully. Evaluation and timing continue; 30/86 total jobs were complete at 15:38, with no failures observed. Preliminary batch-8 Nemotron speedups over no speculation are 1.557 [1.470, 1.641] for interface and 1.623 [1.528, 1.712] for full (95% paired CIs, n=128, three processes). Repair-versus-reuse comparisons await the reuse controls. The live tables below contain the current independently reduced results.

**Training.** Released `z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat`, revision `d3af30def9601abdd10810aba220d692f0e803f0`, MIT license recorded from the pinned model card. R1-Distill-Llama and Nemotron-Nano use their exact already-audited16k Alpaca/512 response files; no regeneration, selection or truncation. Interface/full, R1seeds0–2 and Nemotronseed0, one epoch. Existing native DFlash fused-KL objective, gamma4/fixed-exponential position weighting, up to64 anchors per2048-token packed batch; gradient checkpointing and saved-tensor offload preserve the established memory path. The teacher/embeddings/output projection stay frozen as in B10. The interface trains83,886,080 parameters; full trains1,048,626,432. Final-only shared-shard exports avoid a duplicate native checkpoint copy; this opt-in persistence change does not alter updates. Disk floor350decimalGB.

**Evaluation.** Frozen harness `6da2e4265c0398ec0de5affaf23b0bd1df0be445`, vLLM0.31.0, A40, native DFlashK10, greedy, batch8. All arms share the main table's target-rendered SPEED128/MATH500 IDs and the existing MATH32 IDs at8192-token ceiling. Three-seed R1 groups are required before reporting aggregate repair estimates; Nemotron is seed0. Independent raw-counter analysis provides p1, macroτ including bonus, per-depth conditional acceptance, generated lengths, paired seed/query bootstrap95%CIs and source hashes.

**Timing.** SPEED128, all128 prompts at both batch1 and batch8, three independent processes×three warm passes. Compare none/reuse/interface/full, using seed0 repair exports. Cold panel and startup-inclusive timing remain separate. This is a new opt-in DFlash method in the timing wrapper; acceptance code remains frozen. Output mismatches and lengths are retained. Complete plan:8trainings+30acceptance cells+48timing processes=86jobs.

**Dedicated-reference search.** No compatible public dedicated R1-Distill-Llama-8B DFlash checkpoint was found in the62-model [z-lab catalog](https://huggingface.co/z-lab/models) or the Hub-wide DFlash search on2026-10-10. The similarly named [R1-Distill PARO release](https://huggingface.co/z-lab/DeepSeek-R1-Distill-Llama-8B-PARO) is a quantized full target (`LlamaForCausalLM`, `paroquant`), not a DFlash drafter; Alpamayo-R1-10B is also a different target. No reference result or oracle-gap recovery is invented. [Archived catalog, pinned card/config and search](../artifacts/REV3_X5_hub_audit_20261010_1405/summary.json). This records what the searches found, not a claim that no private or unlisted checkpoint exists.

### Census retention beside EAGLE-3

Existing focused SPEED128 pairedA00/A10 census, n128queries per row,95%paired-query bootstrap CIs, independently recomputed in REV2. Both families here use their released production family drafters; EAGLE-3 is not the separately selected official repair initialization. These are within-drafter p1 retention ratios, not cross-methodτ comparisons.

| Target | EAGLE-3 p1 retention [95% CI] | DFlash p1 retention [95% CI] | n |
|---|---|---|---:|
| R1-Distill-Llama | .725 [.690,.763] | .735 [.705,.768] |128|
| Nemotron-Nano | .696 [.672,.721] | .708 [.688,.729] |128|

[Model-level census CSV, exact checkpoint pins, counts and raw-source hashes](REV2-evidence-20261010/census.csv); [full census composition table](REV2-evidence-20261010/census-table.md).

**Reproduction.** [Training plan](../artifacts/REV3_X5_20261010_1410/plan.json), [reuse/timing-control plan](../artifacts/REV3_X5_20261010_1410/control-plan.json), [journal](../notes/REV3.md). Training/timing tag `run-REV3-X5-20261010-1410` /`b65eeed`; every acceptance job uses the separate frozen6da checkout.46 targeted regression tests passed before publication; subsequent watcher checks passed as well. Final-model evaluations and timing are automatically appended on completed exports.

<!-- REV3 X5 LIVE BEGIN -->
### X5 live independently reduced results

Updated 2026-10-10T15:37:48.651948-04:00; pilot. Completed30/86planned final jobs; failed=[]. Three-seed R1 groups required before showing a combined estimate.

| Target | Arm | Panel | n/seeds | Reuse τ | Repair τ [95% CI] | Δτ [95% CI] | p1 [95% CI] | Δp1 [95% CI] |
|---|---|---|---:|---:|---|---|---|---|

SPEED128 timing, seed0 exports, three processes × three warm passes. All128 prompts at both batch sizes. Cold/startup and output-token differences remain in source JSON.
| Experiment | Target | Batch | Arm / reference | n/processes | Warm panel speedup [95% CI] | Warm token ratio [95% CI] | Cold+startup [95% CI] |
|---|---|---:|---|---:|---|---|---|
| X5 | 0 | 8 | reuse / none | 128/3 | 1.227 [1.175,1.276] | 1.223 [1.166,1.275] | 0.980 [0.935,1.035] |
| X5 | 1 | 8 | fc / none | 128/3 | 1.557 [1.470,1.641] | 1.575 [1.480,1.672] | 1.107 [1.049,1.166] |
| X5 | 1 | 8 | full / none | 128/3 | 1.623 [1.528,1.712] | 1.650 [1.546,1.748] | 1.149 [1.091,1.206] |

| Target | Scope | Seed | Native steps | Measured training GPUh | Peak allocated GiB |
|---|---|---:|---:|---:|---:|
| 0 | fc | 0 | 4488 | 1.281 | 28.36 |
| 0 | full | 0 | 4488 | 1.494 | 38.24 |
| 0 | fc | 1 | 4480 | 1.264 | 28.36 |
| 0 | full | 1 | 4480 | 1.495 | 38.24 |
| 0 | fc | 2 | 4491 | 1.262 | 28.36 |
| 0 | full | 2 | 4491 | 1.483 | 38.24 |
| 1 | fc | 0 | 2636 | 0.818 | 28.36 |
| 1 | full | 0 | 2636 | 0.926 | 38.24 |

[Raw counts, paired seed/query CIs, per-depth acceptance, lengths and hashes](../artifacts/REV3_X5_live_analysis_20261010_1420/20261010_153748_043005/acceptance.json); [timing intervals and source files](../artifacts/REV3_X5_live_analysis_20261010_1420/20261010_153748_043005/timing/results.json); [completion evidence](../artifacts/REV3_X5_live_analysis_20261010_1420/20261010_153748_043005/progress.json).
<!-- REV3 X5 LIVE END -->
