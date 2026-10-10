#!/usr/bin/env python3
"""Generate editable TikZ/PGFPlots from the portable result snapshot."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
d=json.loads((P/'data/results.json').read_text())
ls=[r'\begin{tikzpicture}',r'\begin{groupplot}[group style={group size=2 by 1,horizontal sep=1.2cm},',
    r'width=7.8cm,height=4.7cm,ymin=.9,ymax=2.36,ytick={1,1.5,2},',
    r'axis x line*=bottom,axis y line*=left,ymajorgrids,grid style={gray!15},',
    r'tick label style={font=\scriptsize},title style={font=\small\bfseries},',
    r'ylabel style={font=\small},enlarge x limits=.14,',
    r'legend style={draw=none,font=\scriptsize,legend columns=2,at={(.5,1.03)},anchor=south}]']
for t in ['r1','nemo']:
    names=['reused','fc','full','independent']+(['oracle'] if t=='r1' else [])
    ticks=','.join(map(str,range(len(names))))
    labels='Reuse,Interface,Full,1B'+(',Dedicated' if t=='r1' else '')
    ls.append(r'\nextgroupplot[title={'+('R1-Distill-Llama-8B' if t=='r1' else 'Nemotron-Nano-8B')+r'},title style={yshift=17pt},xtick={'+ticks+r'},xticklabels={'+labels+r'}'+(r',ylabel={Warm speedup over target-only}' if t=='r1' else '')+']')
    ls.append(r'\draw[dashed,ink!65] (axis cs:-.5,1)--(axis cs:'+str(len(names)-.5)+',1);')
    for b,color,shift in [(1,'teal',-4),(8,'bluegray',4)]:
        coords=[]
        for i,arm in enumerate(names):
            r=next(r for r in d['timing'][t]['records'] if r['arm']==arm and r['reference']=='none' and r['batch_size']==b)
            m=r['metrics']['warm'];v=m['panel_time_speedup'];lo,hi=m['paired_process_batch_ci95']
            coords.append(f'({i},{v:.6f}) +=(0,{hi-v:.6f}) -=(0,{v-lo:.6f})')
        ls.append(r'\addplot+[ybar,bar width=7pt,bar shift='+str(shift)+r'pt,mark=none,fill='+color+r'!75,draw='+color+r',error bars/.cd,y dir=both,y explicit,error bar style={black!75,line width=.5pt}] coordinates {'+' '.join(coords)+'};')
        ls.append(r'\addlegendentry{Batch '+str(b)+'}')
ls += [r'\end{groupplot}',r'\end{tikzpicture}']
(P/'figures/timing.tex').write_text('\n'.join(ls)+'\n')

ls=[r'\begin{tikzpicture}',r'\begin{axis}[width=8.0cm,height=4.6cm,ymin=0,ymax=56,',
    r'ylabel={Dedicated-drafter gap recovered (\%)},ylabel style={font=\small},',
    r'xtick={0,1,2,3},xticklabels={Decoder\\LoRA,Interface,Interface +\\decoder LoRA,Full},',
    r'x tick label style={font=\scriptsize,align=center},tick label style={font=\scriptsize},',
    r'ymajorgrids,grid style={gray!15},axis x line*=bottom,axis y line*=left,enlarge x limits=.18]',
    r'\addplot+[ybar,mark=none,bar width=23pt,fill=teal!65,draw=teal,error bars/.cd,y dir=both,y explicit,error bar style={black!75}] coordinates {']
for i,name in enumerate(['self256-decoder','self256-fc','self256-fc-decoder','self256-full']):
    r=next(r for r in d['ablations'] if r['label']==name and r['step']==300 and r['workload']=='speed128')
    m=r['statistics']['recovery'];v=m['mean']*100;lo,hi=[x*100 for x in m['ci95']]
    ls.append(f'({i},{v:.6f}) +=(0,{hi-v:.6f}) -=(0,{v-lo:.6f})')
ls += ['};',r'\end{axis}',r'\end{tikzpicture}']
(P/'figures/components.tex').write_text('\n'.join(ls)+'\n')
print('Generated timing and component figures with source CIs.')
