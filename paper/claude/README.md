# Claude's independent paper draft (NAACL 2027, ACL template)

Build: `latexmk -pdf main.tex` (TikZ/pgfplots figures in `figures/`; references in `custom.bib`).
This draft was written independently of `paper/codex/`.

## Numbers to update before submission

Every number comes from operator-verified raw recomputation (notes/OPERATOR.md, notes/FIX-24.md,
reports/GATE-D50-freeze-20261009.md). The cells below are in progress or stand-ins; the matching
`% TODO` comments are in `main.tex`.

| Where | Current value | Status / source |
|---|---|---|
| Fig. 3a, §6.2: production 64k points | full 70.6%, interface 57.0% | E5c in progress (50% / 75% exports); replace with final 64k |
| Table 2: Nemotron MATH column | 64-problem MATH subset | full MATH-500 for Nemotron not run |
| Table 2: n-gram and scratch MATH (R1) | 64-problem subset | MATH-500 not run for these rows |
| Table 2: n-gram speedups, scratch speedups | "--" | not timed |
| Table 2: R1 MATH-500 fc/full | seed 0 only (2.77 / 2.97) | seeds 1–2 MATH-500 not run |
| Table 1 (component analysis) | 256 self-elicited examples, production drafter | D46/D48 component pilot, single seed |
| Fig. 3b / Fig. 1b dedicated cost | ~4.5k GPU-h (1.3k–19k range) | estimate from P6 public-recipe model, not a measured bill |
| Census bars (Fig. 1a) | P1 typed table + T1 | own-domain 64 / SPEED-128 workloads mixed across groups |
| DFlash rows (Table 3) | 256 examples, 300 steps | P4 pilot; no 16k DFlash repair |
