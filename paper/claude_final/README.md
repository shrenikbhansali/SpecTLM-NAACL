# Final merged draft (Claude): "ReFit: Repairing Speculative Drafters for Post-Trained Language Models"

Build: `latexmk -pdf main.tex`. Merges `paper/claude/` and `paper/codex/`.

## Taken from each draft
- **Claude draft:** narrative and section structure; census teaser (Fig. 1); explanatory method hero figure (Fig. 3);
  scaling + compute-vs-speedup figure (Fig. 4); single main table with speedups and cost; generality table.
- **Codex draft:** method name **ReFit** and the ReFit-interface / ReFit-full naming; fixed-text crossover (feature vs policy shift)
  as mechanism evidence; first-token acceptance column and paired confidence intervals for the headline numbers; component
  comparison as a bar chart (rebuilt here with all seven variants, Fig. 2); verified references (H-Spec, FlexSpec, Draft-OPD,
  EAGLE 3.1, domain draft models); ethics statement.
- **Dropped:** Codex's separate timing bar chart (speedups now live in Table 1), its narrower retention figure (superseded by the
  174-derivative census), and long hedged protocol prose (kept only essentials in the appendix).

## Numbers to update before submission (marked `% TODO` in main.tex)
| Where | Current value | Status |
|---|---|---|
| Table 1: Nemotron MATH column | 64-problem MATH sample | Nemotron MATH-500 not run |
| Table 1: R1 MATH-500 ReFit rows | seed 0 | seeds 1–2 MATH-500 not run |
| Dedicated drafter cost | ~4.5k GPU-h (1.3k–19k) | estimate from public-recipe throughput model |
| Fig. 2 component analysis | 256 examples, production drafter, single seed | D46/D48 pilot |
| Table 2 DFlash rows | 256 examples | P4 pilot |

## REV1 additions (2026-10-10, from reports/REV1-paper-strengthening-20261010.md)
- §3 + Fig. 2: matched-capacity component controls (interface vs decoder at 1.2M and 50M parameters; whole decoder; entire drafter).
  The claim is now "the interface is the most effective place to repair" (supported); the earlier "damage concentrates in the interface"
  wording was dropped because a 243M whole-decoder update recovers more than the 50M interface.
- §6.1 "What makes ReFit work": warm start (scratch 1.52) and derivative supervision (parent-supervised control on identical text).
- §6.1: paired full/reuse speed ratio 1.39x [1.32,1.47] R1, [1.31,1.48] Nemotron.
- §6.2 + Table 2: long reasoning (MATH32, up to 8,192 tokens) greedy and sampled (T=0.6, top-p 0.95); 2,048-token gap closed 52%.
- §6.4 + Table 3: Qwen3-family drafter on DeepSeek-R1-0528-Qwen3-8B (256 examples).
- §4: cost split (8.9 GPU-h generation, 2.2 GPU-h training). Appendix: matched-capacity details, parent-supervision control,
  long-reasoning protocol, TTT depth 3 vs 4, census 87+87, timing CI method.
- Not included (pilot nuances, kept in the REV1 report): R1 late-trace (2k-8k token) bin is not significant for full repair;
  decoder-LoRA learning-rate sensitivity (1e-4); MATH difference for the 50M decoder LoRA includes zero.

## REV2 integration (2026-10-10 ~13:30 ET, from reports/REV2-results-20261010.md)
Added:
- Table 1: Nemotron MATH-500 (reuse 1.69, indep 2.79, interface 2.66, full 2.86) and R1 MATH-500 three-seed means.
- New Table 2: wall-clock on reasoning (MATH-500 b1/b8, 8k-token b1); MATH-500 headline 2.31x.
- §3: "the model moves, not only its text": Qwen3 thinking 104% (EAGLE-3), RL reasoning derivatives 97-100%, Llama base 122%,
  Tülu SFT 92% -> DPO 81% -> RLVR 80%, crossover on parent-generated text (-4.3/-9.2) and public text (-5.0/-10.2), GRPO ~0.
- §6.1: whole-drafter LoRA (50.3M) baseline, which ReFit-full beats by 0.09 (R1) / 0.06 (Nemotron); all 11 SPEED domains improve (App. C).
- §6.4 + Table 3: Qwen3 family at 16k (reuse 1.93 -> 2.18 / 2.30; b1 speedup 1.55x -> 1.85x vs independent 1.52x).
- §4 + App. A: ReFit-interface trains 13% faster per step with 12% less memory; 100 MB vs 849 MB; self-elicited prompts match Alpaca on
  SPEED; vocabulary re-selection gives no change (vocab not a bottleneck); exact renormalized KL; corrected TTT description.
- Compute claim: ">400x" -> "more than 100x" (abstract/intro); "120 to 1,700x" with the 10-40 epoch recipe estimate (§6.3).
- Fig. 1a: dropped the 2-model "teacher distillation" bar (heterogeneous domain distillations); full census table in App. D.
- Component figure moved to the appendix; the 256-example claims are scoped to that regime.
Not used (in the REV2 report): E8 matched-capacity at 16k (interface ~ decoder, CIs include 0; R1 MATH-500 favors decoder by .02-.03);
E11 batch 16/32 (absolute slowdown at b32, still 1.10x vs reuse); interface vs whole-drafter LoRA (LoRA slightly ahead).
Pending: E9 long-response repair (retrying), E13 scratch drafter on 64k.

## REV3 writing pass (2026-10-10 ~15:00 ET)
- Fig. 1a: focused 21-derivative SPEED-128 cohort, per model (on-policy RL vs off-policy), DFlash diamonds; full census in App. D.
- Census claim: off-policy post-training breaks drafters, most severely extensive pipelines (R1-Distill, R1-0528-Qwen3, Nemotron,
  Tülu 3, Skywork-o1, Qwen3-Swallow: 70-86%); on-policy RL 97-103%; weight-space edits 96-100%.
- "What changes": text, hidden states, policy; parent-supervision control stated as ~60% from text, rest from derivative signals.
- Related work rewritten in four categories with explicit novelty sentences (training recipes; standalone drafter alignment;
  adapting when the target changes: EDA, FlexSpec; online/RL adaptation), plus H-Spec's concurrent R1-Distill observation.
- Intro novelty sentence; first systematic census; DFlash highlighted (abstract, intro, contribution, Generality paragraph).
- Cost: "two orders of magnitude"; dedicated drafter cost shown as the 1.3k-19k recipe range; Fig. 4b moved to App. C with CIs table.
- Pending: X1 Nemotron reasoning mode, X2 linear alignment, X4 n=128 timing, X5 DFlash 16k + timing, X3, X8; E9, E13.

## REV3/REV2-final integration (2026-10-11, claude-ops; sources: reports/REV3-results-20261010.md, reports/REV2-REV3-synthesis-20261011.md)
Added (numbers re-checked against artifacts/REV3_X5_live_analysis_20261010_1420/20261010_170126_526250/acceptance.json and timing/):
- New §6.3 "Block-Diffusion Drafters" + Table 3 (DFlash, 16k, same responses, native block objective): SPEED tau R1 2.05 -> 2.39/2.52
  (3 seeds; full delta 0.470 [0.433,0.506]), Nemotron 2.08 -> 2.43/2.59 (0.513 [0.466,0.560]); MATH-500 +24%/+29%; MATH 8k +0.61/+0.48;
  b1 speedup 1.54x -> 1.86x (R1), 1.55x -> 1.89x (Nemotron), full/reuse 1.21x [1.18,1.23] and 1.22x [1.19,1.26]; b8 1.18x/1.21x vs reuse.
  "First adaptation of a block-diffusion drafter to a post-trained target" (to our knowledge) in abstract, intro, contribution, §6.3.
- Abstract + intro: DFlash sentence (23-29% tau, 1.54-1.55x -> 1.86-1.89x).
- §6.1 warm start: E13 scratch on 64k (10.2 GPU-h training) only matches reuse (SPEED 1.74 vs 1.76; MATH-500 1.97 vs 1.93) vs
  ReFit-full 2.54/2.97 from 16k.
- App. A: DFlash implementation paragraph (83.9M interface / 1.05B full; 1.26-1.50 GPU-h R1, 0.82-0.93 Nemotron; no public dedicated
  DFlash drafter for either target). App. D: Table 7 DFlash timing CIs (n=128, both batch sizes).
Moved/trimmed for the 8-page limit: EAGLE-3 robustness table -> App. C (numbers kept in §6.5 text); DFlash rows removed from it;
probe AUROC sentence (kept in App. F); 256-example matched-1.2M location sentence (kept in App. Fig. 4); shorter captions;
Fig. 3 redrawn at 3.7 cm with a compact legend.
Not used: E9 R1 long4k/mixed (+0.07/+0.03, CIs include 0); E15 vocab reselection on R1 (no resolved gain; Nemotron "not a bottleneck"
line kept); E11 b32; E8 16k location null; whole-LoRA vs interface. X1/X2/X3/X4/X6/X8 were not run (only X5 was dispatched).

## REV4 integration (2026-10-11 16:25 ET, claude-ops; source: reports/REV4-results-20261011.md, raw JSON re-checked)
Added:
- Y1: all batch-1 timing now n=128 (SPEED-128, first 128 MATH-500), 3 processes x 3 warm passes. Headlines: R1 SPEED 1.34x -> 1.85x
  (dedicated 2.08x), MATH-500 1.49x -> 2.32x (dedicated 2.94x); Nemotron SPEED 1.33x -> 1.84x, MATH-500 full 2.22x; full/reuse
  1.39x [1.35,1.43] and 1.38x [1.33,1.44]. Abstract, intro, Tables 1/2, teaser (b), App. D table updated.
  EXCEPTION: Nemotron reuse MATH-500 b1 at n=128 had one disturbed process (0.84x vs 1.31x/1.31x; cold pass normal), so the cell
  keeps the 32-prompt E10b value 1.32 [1.29,1.36] (disclosed in App. D). Rerun requested (REV4-R1). Replace when it lands.
- Y2: DFlash MATH-500 speedups (Table 3 rows, §6.3, App. Table 7): R1 1.79x -> 2.26x b1, 1.53x -> 1.93x b8; Nemotron 1.65x -> 2.11x,
  1.43x -> 1.79x; full/reuse 1.21-1.28x (b1), 1.18-1.26x (b8). Abstract: "decodes up to 1.28x faster ... 2.26x on MATH-500".
- Y5: DFlash Nemotron now 3 seeds (SPEED 2.08/2.44/2.58; MATH 2.17/2.59/2.80; 8k 2.41/2.73/2.91).
- Y3a/Y3b: §6.2 "Reasoning mode" paragraph (Nemotron thinking-on: MATH-500 1.70 -> 2.86, 1.68x vs reuse [1.66,1.71]; mode-matched
  data 2.87); 8k and SPEED values in App. B.
- Y7: parent-supervision control at 16k replaces the 256-example numbers (text share 54-62%; derivative signals +0.29/+0.31 SPEED,
  +0.39/+0.40 MATH-500).
- Y8: baseline (vi) training-free feature alignment (best +0.17 tau; loses on Nemotron); details in App. A.
- Y6: official 0.5k scaling point (53% / 40% gap closed, 0.4 GPU-h incl. data) in Fig. 4 + §6.4 text.
- Y9: pooled census retention (weight edits 98-100%, on-policy RL 104%/100%); abstract/intro "96-103%" -> "98-104%"; fixed the
  "all five RL derivatives retain 97-103%" sentence (true for EAGLE-3 only; GT-DAPO DFlash is 90%).
Moved for space: scaling figure -> App. C (text keeps numbers). Intro DFlash wording "carries over unchanged" -> "also repairs".
Not used: Y4 Qwen3 DFlash (b16) repair REGRESSES (full dtau -0.20 SPEED, -0.32 MATH-500; slower than reuse) -> claims scoped to
the Llama-3.1 DFlash drafter; Y8 least-squares regressions (App. A only); Y9 SFT/distillation pooled means (>1, wide).
Pending: Y6 official 64k (ETA Mon 01-03 ET), Y3b full timing, Y10, REV4-R1 rerun.

## 64k official scaling point (2026-10-12 00:57 ET, claude-ops)
Y6 official 64k (Alpaca+Dolly, one epoch, seed 0): SPEED tau full 2.622 (delta 0.858 [0.802,0.911]; gap closed 79.1%),
interface 2.484 (0.721; 66.4%); MATH-500 full 3.067, interface 2.874. Training 9.09 / 8.06 GPU-h. Added to §6.4 text and Fig. 4.
64k timing (3 processes) still running; full SPEED eval needed a GPU-collision retry (identical command).
64k official timing (03:20 ET): full/none 1.905x [1.802,2.007] (processes 1.922/1.904/1.888), full/reuse 1.426x [1.381,1.472]
-> §6.4. NOT used: fc 64k timing, original r1 process disturbed (1.058x vs 1.804x/1.798x; ran 1h48m on srv4:7).
REV4-R1 (05:00 ET): Nemotron reuse/none MATH-500 first-128 b1 rerun = 1.296x [1.218,1.383] (processes 1.291/1.370/1.232;
cold 1.268) -> Table 2 and App. D (replaces the 32-prompt 1.32 stand-in; disclosure sentence removed).
