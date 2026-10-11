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
