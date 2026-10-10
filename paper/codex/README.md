# Independent Codex draft

**Working title:** *ReFit: Repairing Speculative Decoding after Target Post-Training*

Open **main.pdf** to read the complete paper. Upload **codex-overleaf.zip** to Overleaf and select **main.tex** as the main document, using pdfLaTeX. This is the independent Codex version; no other paper draft was read or reused.

The draft uses the supplied ACL template, including its unmodified `acl.sty` and `acl_natbib.bst`, in anonymous review mode. All four figures are editable TikZ/PGFPlots, with separate vector PDF exports. Main results are centralized in Table 1. The appendices contain protocol, three-seed robustness, conditional-depth acceptance, component/data comparisons, DFlash, timing/cost, population provenance, and compatibility triage.

## Build

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

Overleaf requires no Python, original model checkpoints, or external image assets. Local data regeneration is optional: `collect_results.py --repo /path/to/SpecTLM`, then `make_plots.py` and `additional_tables.py` (the last script needs the original raw result files and NumPy). The committed tables and figures are sufficient for compilation. The ZIP contains the manuscript sources rather than local machine paths or experiment data.

## Measurement snapshot

This is a **working draft using measured pilot results**, not a submission or a promotion of experiment status. Source measurements are frozen to the completed analyses listed in `EVIDENCE.md` and `data/provenance.json`. `data/raw-verification.json` independently checks the focal acceptance and output-length numbers against raw counters; `validation.json` records document checks.

- Main initialization: official yuhuili EAGLE-3, selected under D-51 by larger **paired repair gains over its own reuse** at matched 16k/one-epoch budgets. The RedHat release remains a robustness comparison.
- R1 SPEED-128 and MATH-64 repair summaries use three training seeds. Full MATH-500 uses seed 0 and includes MATH-64; it is an expanded panel, not an independent replication. Nemotron and the smaller DFlash extension use one seed.
- All acceptance numbers use frozen harness `6da2e42`, vLLM 0.31.0, A40, and matched target-rendered prompt IDs. HF crossover agreement is explicitly separate from online acceptance.
- Timing uses three processes with three warm passes each and seed-0 repair exports. Startup-inclusive results, token throughput, and output lengths are retained. The 11.12-GPU-hour R1 cost includes response generation; it excludes evaluation and the broader experimental search.
- FIX-24-invalid official repairs are excluded. The draft makes no invented final-64k or dedicated-training-cost claim.

## Updates after this draft

The official 16k main results, including all three R1 seeds, full MATH-500, and official timing, are complete. The production 64k fc/full jobs were still running at this writing snapshot. Their final results can extend the appendix scaling table when verified; label the additional Alpaca+Dolly source mixture and use their own production-reuse baseline. No missing final result has been silently filled with a partial-epoch value. Existing 256/1k/4k/16k measurements already provide a complete draft structure.

The method name and title are working editorial choices. Author information, acknowledgments, final experiment promotion, and submission checklist answers remain for the owner. No submission has been made.
