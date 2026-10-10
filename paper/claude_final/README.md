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
