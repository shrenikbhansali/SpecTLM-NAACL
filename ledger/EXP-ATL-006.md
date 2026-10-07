### EXP-ATL-006 — D-38 reduced-budget method pilot: four arms vs Frozen on a fixed held-out panel (K = 4, seed 0)

**Landed:** 2026-10-07 · NAACL sprint, FollowSpec feasibility (D-37/D-38).

**Status:** pilot (exploratory; single training seed; not a Gate 3 certification).

**What / why.** Owner-requested quick directional check: does FollowSpec (FS) beat the released Frozen EAGLE-3 drafter and the matched controls
(MVD, PO-D, PO-T) on held-out derivatives, before full-budget training finishes?

**New in this experiment.** All four arms were trained for 250 matched optimizer steps (1,991,138 tokens each, D-36 subdivision, same presets, initialization and data
order; FIX-14). Fixed 10-target panel (base + 9 held-out test derivatives; 2 per type by seeded hash, fixed 01:24:58 before launch; FIX-15).
Two of 190 evaluation cells (FS A01/A11 on heck-srv2:4/7) failed at engine start because another user's jobs took the GPU memory ("No available memory for the
cache blocks"). They were re-run unchanged except for output path and tag (exit 0). The report was produced by an operator script that calls the same
`followspec.pilot_report.summarize` on the stage index with those two run_dirs substituted (stage files untouched; all input hashes recorded).

**Artifacts:** `$WS/artifacts/M3_pilot_D38_20261007/` (finalized/, training/runs/m3-d38-*-s0, watch/stage-1791364858988590960,
retry1/, report_retry1/{make_report.py, config.json, results.json}).

**Config + results.** vLLM 0.31.0, greedy, K = 4, batch 8, 512 new tokens, fresh compile, pairwise D-32 zero-step handling. Gain = paired difference
in macro acceptance length (bonus token included) between the FS-trained drafter and the comparator on the derivative's prompts (A11 vs A11/A10).
CIs bootstrap over the 9 fixed targets, conditional on one training seed.

| Workload | Comparison | n | Median gain (AL) [95% CI over targets] | Mean | Win rate |
| --- | --- | ---: | --- | ---: | ---: |
| general | FS − Frozen | 9 | +0.1047 [+0.0952, +0.1389] | +0.1135 | 1.00 |
| general | FS − MVD | 9 | +0.0079 [-0.0156, +0.0260] | +0.0043 | 0.56 |
| general | FS − PO-D | 9 | -0.0040 [-0.0156, +0.0258] | +0.0004 | 0.44 |
| general | FS − PO-T | 9 | -0.0098 [-0.0239, +0.0346] | +0.0003 | 0.44 |
| own | FS − Frozen | 9 | +0.0947 [+0.0838, +0.1378] | +0.1091 | 1.00 |
| own | FS − MVD | 9 | +0.0059 [-0.0215, +0.0485] | +0.0031 | 0.56 |
| own | FS − PO-D | 9 | +0.0132 [-0.0521, +0.0480] | +0.0061 | 0.56 |
| own | FS − PO-T | 9 | +0.0056 [-0.0298, +0.0445] | +0.0046 | 0.56 |

Parent (base model on its own prompts) relative AL change vs Frozen:
- general: FS +2.7%, MVD +3.8%, PO-D +3.3%, PO-T +3.8%
- own: FS +3.3%, MVD +3.7%, PO-D +3.4%, PO-T +3.6%

Per-target values are in results.json (`per_target`). Every trained arm gains over Frozen on every target, by about +0.08 to +0.18 AL.

**Observations (descriptive; interpretation is the owner's).**
1. FS − Frozen is positive on 9/9 targets in both workloads (median ≈ +0.10 AL, ≈ 3% of base AL ≈ 3.0).
2. FS − {MVD, PO-D, PO-T} medians lie within ±0.013 AL, every CI includes 0, and win rates are 0.44–0.56. At this budget and n, the arms are not
   distinguishable from each other. The gain over Frozen is shared by all trained arms.
3. Parent AL rises under every arm (+2.7% to +3.8%); FS is the smallest in both workloads.
4. Noise context: the fresh-compile SD for one cell is 0.0029 (base) / 0.0080 (LoRA) (EXP-ATL-002). The FS-vs-control differences are of the same order as cell-level noise.

**Caveats.** 250 of 1,294 planned steps (~19% of budget); one seed; 9 targets (2 per type, not representative); native validation recorded
separately; the full-budget seed-0 runs are still training (≈ 21:00 finish) and may differ.

**Mandatory fields:** prediction reference EXP-ATL-000 §6.3 items 6–8 (not evaluated here); code 6da2e42 (run-FIX15-pilot-eval-20261007) plus
operator report script; engine lock deb579cd…; seed 0; n = 9 targets × 2 workloads; status pilot.
