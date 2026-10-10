#!/usr/bin/env python3
"""Package only standalone manuscript sources; omit machine paths and raw data."""
from pathlib import Path
import zipfile
P=Path(__file__).resolve().parent
files=[P/n for n in ['main.tex','appendix.tex','references.bib','acl.sty','acl_natbib.bst']]
files += sorted((P/'figures').glob('*.tex'))+sorted((P/'tables').glob('*.tex'))+sorted((P/'figures/exports').glob('*.pdf'))
with zipfile.ZipFile(P/'codex-overleaf.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.relative_to(P))
    z.writestr('README.md','# ReFit — independent Codex draft\n\nSet main.tex as the main document and compile with pdfLaTeX. The supplied ACL style is unmodified. All figures are native TikZ/PGFPlots, with separate PDF exports. No external images, Python, experiment data or machine paths are needed.\n\nWorking research draft, measured pilot snapshot dated October 10, 2026. Official 16k results are complete; the main table uses three R1 training seeds on SPEED, seed 0 on full MATH-500, and one Nemotron seed. The original research repository retains data provenance and raw checks. Title/method name are editorial working choices.\n')
print('Packaged',len(files),'source/vector files for Overleaf.')
