# REV4 journal

### 2026-10-11T02:35-04:00 — claude-ops — plan and paper edit
Owner (direct, ~02:25): remove release promises; run all remaining experiments we want → D-56.
- Paper: removed "per-model results will be released with the paper" (App. F census); no other release/code promises remain
  (grep for releas/available/will be/github). Rebuilt: 14 pp, content ends p. 8, no overfull boxes.
- Plan: reports/REV4-plan-20261011.md (Y1–Y10). Board rows REV4-P0/P1/P2 added as ready for codex.
- State at planning: canonical queue (owner method-M1, log artifacts/M2_D28_20261006/response_queue.log) polling; no pause marker;
  heck-srv2/3 GPUs idle, srv1 all 8 hold ~44 GB at 0% util, srv4 partially occupied; /home/heck2 324 GiB free (~348 GB), just below
  the 350 GB floor → Codex must reclaim D-47 regenerable caches before launching.
- Inputs confirmed: z-lab/Qwen3-8B-DFlash-b16 in census CSV (R1-0528-Qwen3 DFlash retention .81 [.79,.84]); E5c generic64k data exist.
Next: Codex claims REV4 rows and dispatches; claude-ops verifies P0 results ~14:00 ET and folds strong results into paper/claude_final.

### 2026-10-11T02:32:15.314113-04:00 — codex-1 — Claim all REV4 levels
Read AGENTS/CLAUDE, MASTER0–4 and D51–56, complete REV4 plan/journal, established REV2/REV3 pipelines. All tasks authorized D56. One canonicalqueue4129996 remains. Disk below350GB; first reclaim only completed-launch vllm_cache directories under D47 with immutable manifest. No other outputs/weights deleted. P0 precedes P1 Y4/Y6/Y7/Y5/Y3b/Y8 with CPU Y9; Y10 after every P0/P1 job queued. No paper edits.

### 2026-10-11T02:41:54.236725-04:00 — codex-1 — D50 launch health
Free disk 395.0GB; new failures=[]; unresolved failures=[]. Each failure has an immutable alert file in /home/heck2/sbhansali8/SpecTLM/artifacts/REV4_launch_health_20261011_0250; explicit resolution records required. No failed job is silently retried or treated as running.

### 2026-10-11T02:48:44.978370-04:00 — codex-1 — P0/P1 publication and implementation
P0 all141jobs published,23launched with no observed failures. Ten initial tests passed. Stage artifacts/REV4_P0_20261011_0240, tagbc20893/run-REV4-P0-20261011-0240. All new thinking-mode evaluation renders manually inspected, five prompts per panel, explicit detailed-thinking-on system, original raw IDs preserved. Independent P0 watcher2326530; health2326531 in artifacts/REV4_logs_20261011_0250. P1 first12trainings plus14QwenDFlashcontrols queued in orderY4/Y6/Y7/Y5, stageREV4_P1_20261011_0255, code7faeef1/run-REV4-P1-native-20261011-0255; watcher2331616. All source data/audits reused. Actual production0.5k point is generic520 (not256), data-0-generic exactsubset reused; official run oneepoch perD56, oldproduction200steps labelled separately. QwenDFlash9b41424 MIT/ungated cachepresent; native configblock16,taps2/10/18/26/34, no trainerchange. TimingK16 addedopt-in with failingthenpassingtest; defaultK4unchanged. Twenty-six relevant tests pass including linear-map orientation, Procrustes/LS recovery, defaultsystemrender and explicit8192datacontext. Y3b/Y8/Y9 preparation next.
D47 cleanup manifest contains823finished-run vllm_cachepaths; serial18 and parallel805 reclaimed; no outputs/weights/ledger/envs removed. Disk reached~395GB. Global hf executable lacks hub module; existingpinnedcache made downloadunnecessary, no env modified. Hubmetadata/card/config archived at artifacts/REV4_Y4_hub_20261011_0240.

### 2026-10-11T02:56:45.902359-04:00 — codex-1 — Y9 complete; dependent stages
Y9 independently recomputed own-domain groups for163models/326rows; focused21 table42rows complete. Distillation pooled retention1.071 DFlash [0.907,1.262],1.141 EAGLE [0.924,1.449]; no reliable loss on this population/workload, reported plainly. Evidence artifacts/REV4_Y9_20261011_0300. Y3b8data shards andY8two fits queued; first ofeach running. New tests for audit gate/stable pending order failed before implementation then8pass. Followup code1ab0049 tagged/pushed run-REV4-followups-20261011-0310. One canonical queue; stable pending order P0, Y4/Y6/Y7/Y5/Y3b/Y8, Y10 last. No running jobs interrupted. Y8watch2336610.

### 2026-10-11T03:14:51.160880-04:00 — codex-1 — dependent pipelines and source validation
Y3b firstfive actually inspected (artifacts/REV4_Y3b_data_20261011_0300/early-five-decoded-masks.json), review manifest hashes exactsamples. Sealing/controller automatically transfers only identical inspected samples, then queues fc/full and frozen cells. Controller now uses.venv-transport tokenizer runtime (basePython transformers4.37 differs); CPUdataflowPIDs2347609/2347610/2347737. Y10queries ready: MIT MATH21a5633/GSM8K740312a;2000each, exacthashdedupall11024eval andAlpaca;no generation before110mandatoryP1jobs queued (2346258). Future mathsample review remains required. P1rawresults2348687, P1/P2completion2348688, D47cachemaintenance2348695 (finished direct-launch vllm_cacheonly, manifests first, trigger380GB).
NativeSDPA opt-in tests compare packedTTT3 eagerloss,metrics,gradients and pass;17memory/REV4 tests passed, subsequently13REV4 tests includingdispatchidentity/completion/cacheguards passed. Existingdefaults unchanged. Latestcodead451e3, tagrun-REV4-maintenance-20261011-0340. A temporary0320worktree tagged the previous commit during an overlappinggitoperation; unused for launches, superseded by verified0321; no tag rewritten.
Y9sourceaudit: historical423d3b6/f00992f generation commits retained, all41728rawrecords validate under6da2e42metricfunction; report distinguishes historical raw re-analysis from new frozen generation. No historical config relabelled. Y8 fit positions follow earlier calibration completion-prediction p-2 window excluding after-EOS; this is a paired feature fit, not a claim that every masked nativeTTTposition is identical.
Current25REV4 GPU jobs active (23timing,1data,1fit), no failures;~394GB free. AllP0/P1/P2 rows remain in progress pending GPU results.

### 2026-10-11T03:16:45.033992-04:00 — codex-1 — operational status
Daily report reports/2026-10-11.md written before07ET; ownboardrows updated, remaininprogress. Mathquerycontext audit passed4000queries pertarget withmaxprompt1559R1/1569Nemo, so4096responsefits8192budget. Firstfive renderedprompts inspected pertarget; these are prompts only, future response/mask review stillrequired. P0 timing processes remainhealthy. All commits pushed before launches; latestmain3fe9df3 plus thisdocumentationcommit.

### 2026-10-11T03:31:07.445685-04:00 — codex-1 — Handoff (background jobs continue)
All D56 levels remain **in progress**, not complete. No owner input is needed for ready stages. P0 all141 jobs queued;23 timing processes active, no P0 results yet. P1 first12train+14controls+8Y3bdata+2Y8fits queued; R1Y8 fit exit0, four frozen evals now also queued. Y9 CPU complete with full null/provenance reporting. Current24 activeGPUjobs,1 completedfit,0 failures,~390GB free. Third-party process occupied srv4:5 after fit released it; dispatcher correctly skips. srv1 all GPUs and srv5:0 remain allocated; srv2:4–7 are free but excluded by the owner's rule, untouched.

**Exact current source/automation:** main6575d97 (plus this documentation commit), branchcodex/REV4/build worktree `.worktrees/run-REV4-build-20261011-0235`. GPU runtime tags: P0bc20893/run-REV4-P0-20261011-0240; initialP1 7faeef1/run-REV4-P1-native-20261011-0255; Y3bdata/Y8fit ea57396/run-REV4-data-align-20261011-0300; Y3btraining/export f618e6f/run-REV4-data-flow-20261011-0321; futureY10 7e3cb52/run-REV4-math-20261011-0330. Some tag suffixes were planned labels rather than wall-clock times; configs/journal contain actual times. Tags pushed before runtimes. Do not launch a new queue.

Canonicalqueue4129996, owner method-M1/exclusive, dispatch `artifacts/FIX16_operations_20261007/dispatch.jsonl`, log `artifacts/M2_D28_20261006/response_queue.log`. P1exportwatch2331616; Y8exportwatch2336610; P0rawreport2353313; P1/P2rawreport2353314; completionping2353315; Y3bdataflow2347609; Y10prerequisitegate2346258; Y10dataflows2347610/2347737; health2326531; D47cachemaintainer2348695. All alive at03:28check. Logs in `artifacts/REV4_logs_20261011_0250`. Latest analysis roots `artifacts/REV4_P0_live_20261011_0322` and `artifacts/REV4_P1_live_20261011_0322`; completion proofs will appear in `artifacts/REV4_completion_20261011_0322`. Raw collectors use6575d97, independently check matched fc/full optimization configs; P0 posts immediately when141success/56timing/6acceptance contrasts complete. P1 requires110mandatoryjobs queued/completed and40acceptance/22timing contrasts; P2 requires16data/8train/24eval and24acceptance contrasts.

**Next operator actions:** monitor every hour and inspect failures immediately (launch health also alerts launch_failed). Y3b can complete autonomously: five decoded responses/masks already actually inspected and hashed; transfer requires exact sealed sample equality before training. Y10waits for everyP0/P1 downstream cell to be queued; CPU queries ready under `artifacts/REV4_Y10_queries_20261011_0315`, allcontextsfit8192. Once Y10responses appear, actually inspect five decoded responses/masks for **each target** and the mixed-data path, then write the expected review manifests `artifacts/REV4_Y10_data_20261011_0330/manual-review-t{0,1}-{math4k,mixed20k}.json`; review schema follows Y3b `manual-review-early-five.json`. The controller deliberately cannot fabricate that review. For mixed data it produces ten inspection samples (firstfive existingAlpaca + firstfive newmath); inspect allten before recording the mixed review. No repeated request for owner permission is needed. Long-mathSDPA native packedTTT3 equivalence tests pass; verify actual A40 memory on first math-training backwards. All other dependent exports/evals/rawreductions are automatic.

R1Y8fit evidence `artifacts/REV4_Y8_20261011_0305/REV4-Y8-t0-linearfit/results.json`:4000responses,1,875,707positions,0.507allocatedA40hours,31.14GiBpeak; exports have identical frozenbody hashes and target embedding exactness. Four evaluationjobs publication marker present. All new acceptance/timing uses6da2e42; historicalY9 generation commits are explicitly separate, validated41728rawrecords with frozenmetricfunction. Do not relabel old configs. No paper edits. Daily report `reports/2026-10-11.md` written ahead of07ET. Most recent targeted suite13PASS; nativeSDPA/memory suite17PASS earlier. Unrelated dirty notes/OPERATOR/P3/REV2/REV3 and oldledger/report files belong to other controllers; leave them alone.

### 2026-10-11T03:42:08.830319-04:00 — codex-1 — D50 launch health
Free disk 389.7GB; new failures=[]; unresolved failures=[]. Each failure has an immutable alert file in /home/heck2/sbhansali8/SpecTLM/artifacts/REV4_launch_health_20261011_0250; explicit resolution records required. No failed job is silently retried or treated as running.

### 2026-10-11T04:42:22.407134-04:00 — codex-1 — D50 launch health
Free disk 387.2GB; new failures=[]; unresolved failures=[]. Each failure has an immutable alert file in /home/heck2/sbhansali8/SpecTLM/artifacts/REV4_launch_health_20261011_0250; explicit resolution records required. No failed job is silently retried or treated as running.

### 2026-10-11T05:42:31.804544-04:00 — codex-1 — D50 launch health
Free disk 383.7GB; new failures=[]; unresolved failures=[]. Each failure has an immutable alert file in /home/heck2/sbhansali8/SpecTLM/artifacts/REV4_launch_health_20261011_0250; explicit resolution records required. No failed job is silently retried or treated as running.

### 2026-10-11T06:42:44.964695-04:00 — codex-1 — D50 launch health
Free disk 382.3GB; new failures=[]; unresolved failures=[]. Each failure has an immutable alert file in /home/heck2/sbhansali8/SpecTLM/artifacts/REV4_launch_health_20261011_0250; explicit resolution records required. No failed job is silently retried or treated as running.

### 2026-10-11T07:42:55.173650-04:00 — codex-1 — D50 launch health
Free disk 384.4GB; new failures=[]; unresolved failures=[]. Each failure has an immutable alert file in /home/heck2/sbhansali8/SpecTLM/artifacts/REV4_launch_health_20261011_0250; explicit resolution records required. No failed job is silently retried or treated as running.

### 2026-10-11T08:43:10.558392-04:00 — codex-1 — D50 launch health
Free disk 382.9GB; new failures=[]; unresolved failures=[]. Each failure has an immutable alert file in /home/heck2/sbhansali8/SpecTLM/artifacts/REV4_launch_health_20261011_0250; explicit resolution records required. No failed job is silently retried or treated as running.

## 2026-10-11T09:16:59.004195-04:00 — codex-1 — P0 completion ping

All141P0 jobs successful, six acceptance and56timing contrasts independently reduced. P0 moved to review; P1/P2 remain separate. Evidence /home/heck2/sbhansali8/SpecTLM/artifacts/REV4_P0_live_20261011_0322/20261011_091644_963445. No scientific promotion.
