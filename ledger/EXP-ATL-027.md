### EXP-ATL-027 — REV2 scaled location controls and extended serving workloads

**Landed:**2026-10-10, codex-1; owner D54, reports/REV2-plan-20261010.md.

**Status:**pilot, in progress. CPU evidence complete/compiled; new GPU jobs running or queued. No paper edits or promotion.

**What / why.** Test matched-capacity adaptation at the main16k budget, cross-family repair, longer response coverage, realistic MATH timing, whole-drafter LoRA, scratch scaling and training-resource cost. Supply reproducible per-checkpoint census evidence and distinguish fixed-prefix diagnostics from online acceptance.

**New.** E8 twenty trainings: R1/Nemotron3seeds,50,331,648-parameter dense interface versus q+o,1,228,800-parameter interface-r75 versus decoder-r16; reuse existing interface seeds. E9 long4k and short16k+long4k repairs; E12 Qwen16k; E14 missingMATH500 arms/seeds; E10 repeated MATH/8k timing; E11 b16/b32; E17 whole-LoRA r16/r343; E13 scratch64k; E16 synchronized200-step profiles; optional E15 vocabulary support. E18 static EAGLE trees are infeasible in pinned engine; field/source audit retained.

**Artifacts.** `artifacts/REV2_E8_20261010_0425`, `REV2_data_20261010_0430`, `REV2_panels_20261010_0430_v2`, `REV2_E10a_20261010_0430`, `REV2_E10b_20261010_0430`, `REV2_P1_20261010_0437`, `REV2_E11_20261010_0437`, `REV2_E12_controls_20261010_0445`. Plans, job specs and cell/launcher dry runs retained. CPU: `REV2_A1_20261010_0445`, `REV2_A2_20261010_0440`, `REV2_A4_20261010_0445`, `REV2_diagnostics_20261010_0445`. [Results document](../reports/REV2-results-20261010.md), [census CSV](../reports/REV2-evidence-20261010/census.csv), journal notes/REV2.md; source followspec/rev2_*.py. Tags run-REV2-train-20261010-0425/62cecc1 and run-REV2-profile-20261010-0437/5cdfae9.

**Config + results.** Frozen6da2e42/vLLM0.31/A40 primary acceptance, target-rendered IDs shared across arms; greedyK4/b8, held-out SPEED128/MATH64/MATH500. Long caps supplementary; timing uses3independent processes×3warm passes, cold/startup separate. Training native TTT3/FIX24/official initialization except specified Qwen family; compact final-only/shared shards,350GB floor. At04:44,237job specs published,27launched; no new acceptance numbers claimed. CPU independent recomputation reproduces all414 historical/focused checkpoint-method-workload retention estimates to1e−8. Historical174=87Llama+87Qwen;42unknown histories. Equal-checkpoint,10,000 hierarchical/paired-query CIs. Official16k repairs improve τ in all11 SPEED domains on both targets with positive pointwise95% intervals (R1 three seeds,Nemo one); no simultaneous-family claim. R1 full short-response16k gap recovery on matchedMATH32:53.5%[50.2,57.0] at512,51.8%[49.3,54.6] at2048,39.2%[32.0,45.7] at8192. OOV on fixed R1 child text: parent5.96%,child6.03%,paired difference+.07pp[−.06,+.20],n64.

**Caveats.** Every outcome retained; incomplete cells are pending, not assigned provisional acceptance. Same prompts need not yield numerically identical greedy trajectories, so lengths and token throughput are recorded. Historical census commits are preserved and FIX23-audited, not relabeled as fresh6da2e42runs. Compound/card-unknown training histories remain explicit. Native TTT propagates predicted hidden states but shifted ground-truth lexical IDs; no objective modification or claim of sampled-token rollout. Dedicated cost remains scenario projection including generation, not measured oracle training cost. Five decoded samples/masks gate each new data path before training. Initial system-tokenizer render failure and empty stage retained; rerender with pinned environment succeeded in a new directory. One canonical exclusive-owner queue, duplicate checks before publication; priority changes do not restart jobs.33 targeted regression tests pass using pinned training dependencies.

## 2026-10-10T05:53:20.444268-04:00 — codex-1 — First frozen export check

Nemotron interface-LoRA r75 seed1 MATH64 completed with launcher exit0, frozen6da2e42/vLLM0.31/A40. Rawτ exactlymatches archived2.5182419374007345. Paired query bootstrap10kdraws: Δτ+.8149168[.7816735,.8474012], p1 .6644656[.6532646,.6756369], Δp1+.2128366[.2042235,.2215466], n64/one seed. Evidence artifacts/REV2_first_export_check_20261010_0552/proof.json; labeled partialseedgroup, not the planned3seed location contrast. This is the first end-to-end newtrain/export/frozen-eval success. All comparisons/nulls remain in the full matrix.

## 2026-10-10T06:07:21.192668-04:00 — codex-1 — Supplementary long-prefix analysis

Added tested raw prefix-bin reconstruction from frozen REV1MATH32 cap8192 counters; initial target token accounted, terminal step excluded and0/1terminal residual validated for all192records. Matched reuse/fc/full queries perbin, pairedbootstrap10k. Full gain atprefix2048–4095: R1Δτ+.321[.105,.555],n14; Nemo+.490[.413,.567],n9; beyond4096R1n6intervalcrosseszero,Nemon2retained. Source artifacts/REV2_A4c_20261010_0608/results.json and portable prefix-bins.md. No newGPUjob or evaluation-engine change; this is supplementary analysis, not causal context-length attribution.39pinned tests PASS.

## 2026-10-10T06:14:21.525914-04:00 — codex-1 — First complete E8 matched group and hourly health

Nemotron MATH64 dense50M3seeds: interfaceτ2.71249,decoderq+o2.70453; Δτ+.00796[−.01748,+.03318],Δp1+.00725[−.00057,+.01531],n64/3seeds,all512tokens,noexcludedqueries. Null location contrast retained; no equivalent-performance claim. Source artifacts/REV2_live_analysis_20261010_0550/20261010_061318_285942/E8/results.json. All training-config checks pass.37 successful jobs/no failures at06:14; R1nine trainings~3291–4272/4477steps. Hourly SSH nvidia-smi allfivehosts: eligible27slots in training/generation/evaluation/compile transitions; srv1/srv5:0 still other-user allocated; excluded srv2:4–7 untouched.480decimalGB available; canonicalqueue4129996 alone. LongR1data3968/4000, Nemo3424/4000, Qwen7224/16000 at last count. All five-sample audits already complete, seal gates remain active.

### 2026-10-10T06:19:08.861075-04:00 — E9 R1 corpus and training handoff

R1long4k sealed,4000rows/3530565answer tokens,7.014GPUh; mixed20k sealed,manualsamplematchesPASS;4trainingjobs published through canonicalqueue. Sources artifacts/REV2_followups_20261010_0500/sealed-t0 andtraining-t0/plan.json. No E9performance number yet. E8matched Nemotron dense50MSPEED Δτ+.023[-.006,.052],n128/3seeds, null retained.

### 2026-10-10T12:53:07.693553-04:00 — Midday independent results and E9 recovery

Completed E8/E10/E11/E12/E14/E16 raw tables: artifacts/REV2_live_analysis_20261010_0550/20261010_124623_480893; full narrative/CI/n/sources in reports/REV2-results-20261010.md middaysection. Qwenfull Δτ+.377[.335,.415]SPEED128,+.473[.456,.491]MATH500,one seed. LongMATH32warmfull/no-spec R11.767[1.437,2.272],Nemo1.634[1.371,2.020],3processes. E8three-seedτlocationcontrasts null inall8groups,seed0R1MATH500favorsdecoder. EightE9 first-backwardOOMattempts preserved, retries use2304packing perD54,fullsequencesunchanged; newtag d6f6502. No E9performance number claimed.

## 2026-10-10T13:43:34.228374-04:00 — codex-1 — Completion ping REV2-P2

8/8 mandatory jobs completed successfully; required raw counter/timing/resource analyses are present. Board moved to review, numbers remain pilot. Completion evidence: artifacts/REV2_live_analysis_20261010_1255/progress-20261010_134334_228395.json. Nulls retained; paper unchanged.
