#!/usr/bin/env python3
"""Export each native TikZ figure as a tightly sized vector PDF."""
from pathlib import Path
import shutil
import subprocess
P=Path(__file__).resolve().parent
(P/'build/vector-exports').mkdir(parents=True,exist_ok=True)
(P/'figures/exports').mkdir(exist_ok=True)
preamble=r'''\documentclass[11pt]{article}
\usepackage{times}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,tikz,pgfplots}
\usetikzlibrary{arrows.meta,positioning,calc,fit,backgrounds}
\usepgfplotslibrary{groupplots}
\pgfplotsset{compat=1.18}
\definecolor{ink}{HTML}{20334D}
\definecolor{teal}{HTML}{087E8B}
\definecolor{orange}{HTML}{CC702D}
\definecolor{bluegray}{HTML}{5C6E91}
\definecolor{mist}{HTML}{EDF1F5}
\pagestyle{empty}
\newsavebox{\figurebox}
\begin{document}
'''
for name in ['hero','retention','components','timing']:
    source=preamble+r'\savebox{\figurebox}{\input{figures/'+name+r'}}'+r'''
\pdfpagewidth=\dimexpr\wd\figurebox+8pt\relax
\pdfpageheight=\dimexpr\ht\figurebox+\dp\figurebox+8pt\relax
\hoffset=-1in
\voffset=-1in
\shipout\vbox{\kern4pt\hbox{\kern4pt\usebox{\figurebox}\kern4pt}\kern4pt}
\end{document}
'''
    tex=P/'build/vector-exports'/f'{name}.tex';tex.write_text(source)
    with (P/'build/vector-exports'/f'{name}-compile.log').open('w') as log:
        subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory=build/vector-exports',str(tex.relative_to(P))],cwd=P,stdout=log,stderr=subprocess.STDOUT,check=True)
    shutil.copy2(P/'build/vector-exports'/f'{name}.pdf',P/'figures/exports'/f'{name}.pdf')
    print(name,'exported')
