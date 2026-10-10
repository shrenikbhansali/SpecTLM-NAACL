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
| Fig. 4a, §6.2: production 64k | full 74.1%, interface 57.0% | E5c 75%-of-epoch exports; replace with final |
| Table 1: Nemotron MATH column | 64-problem MATH sample | Nemotron MATH-500 not run |
| Table 1: R1 MATH-500 ReFit rows | seed 0 | seeds 1–2 MATH-500 not run |
| Dedicated drafter cost | ~4.5k GPU-h (1.3k–19k) | estimate from public-recipe throughput model |
| Fig. 2 component analysis | 256 examples, production drafter, single seed | D46/D48 pilot |
| Table 2 DFlash rows | 256 examples | P4 pilot |
