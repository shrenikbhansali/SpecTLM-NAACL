# EXP-ATL-011 — Track T phase1 target-conditioned failure hunt

**Landed:** 2026-10-07, Track T / D-40.

**Status:** pilot; partial2/72cells, no decision.

**What / why:** Test18public lineage, reasoning-distillation and RL checkpoints against their official base targets with EAGLE-3 and DFlash. Owner motivation rule requires≥20%per-token acceptance loss for both drafter families on≥2independent realistic publicmodels with a plausible mechanism.

**New in this experiment:** Each target uses its own chat template; A00 and A10 get identical rendered IDs. No adapters; full-weight local snapshots. Report all18 outcomes, per-position conditional acceptance,τ and outputlengths.

**Artifacts:** `artifacts/T1_models_20261007/manifest.jsonl`, `artifacts/T1_canonical_20261007_2347/index.json`, `artifacts/T1_cells_20261007_2350`; [initial partial](../artifacts/T1_cells_20261007_2350/partial-2-1791431750961148283/results.json).

**Config + results:** Frozen harness6da2e42; vLLM0.31.0, A40, seed0 greedy, batch8,512outputtokens, freshcompile. EAGLE3K4; DFlashLlamaK10/QwenK16. Shared SPEED128,128prompts/model. First complete pair (not a class result):

| Model | Drafter | n | Position1 A10/A00 [95%prompt CI] | τ A00→A10 | Median outputlength A00→A10 |
| --- | --- | ---: | --- | --- | --- |
| meta-llama/Llama-3.1-8B | EAGLE-3 K4 |128|1.2158 [1.1619,1.2782]|2.7913→3.7814|285.5→512.0|

**Caveats:** Partialmatrix, one seed, fixed promptpanel; promptbootstrap2000draws does not measure run-to-run uncertainty. This first checkpoint improves acceptance and does not meet the failure threshold; DFlash pair pending. Own-template post-training comparisons include template/trajectory effects even with identical paired inputIDs. DeepSeek AutoTokenizer whitespace bug repaired before any affected GPUlaunch; original malformed renders retained. Unknown/custom license labels in the supplied18model manifest remain flagged, not silently treated as standard. No quality or speedup claim, no owner framing decision.

## 2026-10-08T00:08:07-04:00 — Eligibility audit update

Two supplied OpenLearnLM checkpoints declare Qwen2/hidden3584/layers28 despite qwen3_8b repository names. Their8unlaunched pairedcells held as structurallyincompatible;16models/64cellsremaineligible, all18retained in originalplan. [Audit](../artifacts/T1_cells_20261007_2350/model_metadata_audit.json), [holds](../artifacts/T1_cells_20261007_2350/exclusions.json). This is inputvalidity, not acceptance degradation. Sixmanifestentries lacklicense metadata and3arecustom/other; labels remain visible.

## 2026-10-08T01:16:40-04:00 — codex-1 — T1 interim signal and quality caveats

T1 independent raw snapshot now53/64eligiblecells, 26pairedresults: `artifacts/T1_cells_20261007_2350/partial-53-1791436372870569621/results.json`. Reasoning targets show a useful exploratory signal: DeepSeek-R1-Distill-Llama p1retention EAGLE3=.725,DFlash=.735; NemotronNano8B=.696/.708, n128each. Tau retention .765/.606 and .733/.577 respectively; median outputs lengthen (DeepSeek199.5→512 EAGLE,175.5→512 DFlash; Nemotron222→402.5/415), so report p1 alongside length. No new gate or framing decision. QwenR1 weaker loss(.858/.810); TuluDPO/RLVR around.80–.84; pretrainedLlama improves(.1.216/1.158); all nulls retained.

Quality diagnostic `artifacts/T1_quality_20261008_0116/check.py` applies already-approved repeated4gram coverage>.5 to raw IDs, not a new exclusion: DeepSeekDistill/Nemotron0/128 flagged each family. Late luckeciano4461 checkpoint is collapsed:107/128(EAGLE),105/128(DFlash) repetitive, firstfive mostly token1980 repeated; its nearzero acceptance should not be sold as realistic useful-target drift. It remains in the ledger/data. DeepSeek saved completion strings contain known tokenizer whitespace artifacts; redecoded raw token IDs with native BPE tokenizer to new `deepseek-five-redecoded.json`, preserving originals. Five reasoning samples/family read; coherent-looking reasoning but factual errors remain (including movie facts), so no task-quality claim. Token-ID acceptance unchanged.

## 2026-10-08T01:26:55-04:00 — codex-1 — T1 completion / Handoff

Phase1 complete64/64eligiblecells,16models,32pairs,n128 each. Final independent raw report `artifacts/T1_cells_20261007_2350/report/`; full readable table [reports/T1-phase1-20261008.md](../reports/T1-phase1-20261008.md). All new runs remain pilot. Reasoning models DeepSeekDistillLlama/Nemotron show27–30%p1loss forbothfamilies, no repetition flags; quality/length caveats retained. Final SwallowQwen: p1retention EAGLE.836[.801,.875],DFlash.711[.689,.735], tau.855/.566, medianoutput384/387→512. Earlier `.1.216` typo means1.216 pretrainedLlama EAGLE. No gate or owner framing decision changed.

Handoff: T1 rowreview, no further T1jobs scheduled. Queue3546069 continues I1(100/180) and small I3–I5pilots on designated TrackI nodes. Full M4 report already complete. Raw T1reporter may remain alive in its harmless watch loop; optionalthinking-mode/H4not launched. Next ownercheckpoint reviews this alongside Q1/repair findings; no need to wait to finish currently authorized pilots.
