#!/usr/bin/env python3
"""Freeze existing, independently checked summaries; no experimental jobs.

Run once with --repo /path/to/SpecTLM. The Overleaf package is self-contained
and does not need this script or the original research workspace to compile.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, required=True)
args = p.parse_args()
provenance = []

def read(rel):
    path = args.repo / rel
    raw = path.read_bytes()
    provenance.append({'path': rel, 'sha256': hashlib.sha256(raw).hexdigest()})
    return json.loads(raw)

d51 = read('artifacts/D51_reports_20261009_1627/snapshot-20261009_192136/results.json')
d50 = read('artifacts/D50_final_20261009_1451/results.json')
math = read('artifacts/D52_analysis_20261010_0020/math500/results.json')
timing = {t: read(f'artifacts/D52_analysis_20261010_0020/timing-{t}/snapshot-{stamp}/results.json')
          for t, stamp in [('r1', '20261010_001805'), ('nemo', '20261010_001811')]}

def rec(target, arm, workload, budget=16000):
    return next(r for r in d51['records'] if (r['target'],r['arm'],r['workload'],r['budget']) == (target,arm,workload,budget))

def old(label, target, workload, step=None):
    rows = [r for r in d50['records'] if (r['label'],r['target'],r['workload']) == (label,target,workload) and (step is None or r['step']==step)]
    assert len(rows)==1, (label,target,workload,step,len(rows))
    return rows[0]['statistics']

def m500(arm):
    return next(r['statistics'] for r in math['records'] if r['arm']==arm)

main = []
for target in (0,1):
    for arm in ['reused','fc','full','independent'] + (['oracle'] if target==0 else []):
        metrics = {}
        for workload in ['speed128', 'math500' if target==0 else 'math64']:
            if workload=='math500':
                s=m500('official-'+arm if arm in ['reused','fc','full'] else arm)
            elif arm=='reused':
                s=rec(target,'fc',workload)['official_reuse']
            elif arm in ['fc','full']:
                s=rec(target,arm,workload)['official']
            elif arm=='independent':
                s=old('draft_model-K4-LNone',target,workload)
            else:
                s=old('oracle',target,workload)
            metrics[workload]=s
        main.append({'target':target,'arm':arm,'statistics':metrics})

def cell(metric, percent=False):
    scale=100 if percent else 1
    digits=1 if percent else 2
    a,b=metric['ci95']
    return r'\stat{'+f"{metric['mean']*scale:.{digits}f}"+r'}{'+f'{a*scale:.{digits}f}--{b*scale:.{digits}f}'+'}'

names={'reused':'Reuse family drafter','fc':r'\textbf{ReFit--interface}','full':r'\textbf{ReFit--full}', 'independent':'Independent 1B drafter','oracle':'Dedicated R1 drafter'}
lines=[r'\begin{tabular}{@{}lccccc@{}}',r'\toprule',r'& \multicolumn{3}{c}{SPEED-128} & \multicolumn{2}{c}{MATH} \\',r'\cmidrule(lr){2-4}\cmidrule(l){5-6}',r'Drafter & $p_1$ (\%) & $\tau$ & $\Delta\tau$ & $p_1$ (\%) & $\tau$ \\']
for target in (0,1):
    lines += [r'\midrule',r'\multicolumn{6}{@{}l}{\textit{'+('R1-Distill-Llama-8B; MATH-500' if target==0 else 'Nemotron-Nano-8B; MATH-64')+r'}} \\']
    for row in [r for r in main if r['target']==target]:
        s=row['statistics']['speed128'];m=row['statistics']['math500' if target==0 else 'math64'];a=row['arm']
        delta=cell(s['delta']['tau']) if a in ['fc','full'] else ('0.00' if a=='reused' else r'---')
        lines.append(' & '.join([names[a],cell(s['metrics']['p1'],True),cell(s['metrics']['tau']),delta,cell(m['metrics']['p1'],True),cell(m['metrics']['tau'])])+r' \\[2pt]')
lines += [r'\bottomrule',r'\end{tabular}']
(HERE/'tables/main.tex').write_text('\n'.join(lines)+'\n')

# Full precision numbers, uncertainty, lengths, source pointers and controls.
selected=[r for r in d50['records'] if r['label'] in ['E4-scratch16k','E5-second-epoch','E5-ttt4-fc','E5-ttt4-full','generic4k-fc','generic4k-full','generic16k-fc','generic16k-full','self1k-fc','self1k-full','self4k-fc','self4k-full'] or r['label'].startswith(('self256','ngram'))]
out={'status':'pilot; manuscript working snapshot 2026-10-10', 'main':main,'d51':d51,'math500':math,'timing':timing,'ablations':selected}
(HERE/'data/results.json').write_text(json.dumps(out,indent=2)+'\n')
(HERE/'data/provenance.json').write_text(json.dumps({'sources':provenance,'rules':['All acceptance numbers from frozen 6da2e42 / vLLM 0.31.0 / A40.','Main drafter selected by matched 16k repair deltas, not absolute acceptance.','R1 SPEED/MATH64 repair: three seeds; MATH500 and timing: seed 0.','64k ongoing, not substituted for a completed epoch.','FIX24 invalid repairs excluded.']},indent=2)+'\n')

# Exact timing confidence intervals in an appendix table.
ls=[r'\begin{tabular}{@{}llccc@{}}',r'\toprule',r'Target / batch & Drafter & Warm speedup & Token throughput & Startup inclusive \\',r'\midrule']
for t in ['r1','nemo']:
    for batch in [1,8]:
        for r in timing[t]['records']:
            if r['batch_size']!=batch or r['reference']!='none':continue
            w=r['metrics']['warm'];c=r['metrics']['cold']
            def fmt(mean,ci): return f'{mean:.2f} [{ci[0]:.2f}, {ci[1]:.2f}]'
            ls.append(' & '.join([('R1' if t=='r1' else 'Nemotron')+f' / {batch}',names[r['arm']].replace(r'\textbf{','').replace('}',''),fmt(w['panel_time_speedup'],w['paired_process_batch_ci95']),fmt(w['token_throughput_ratio'],w['token_throughput_ci95']),fmt(c['startup_inclusive_speedup'],c['startup_inclusive_ci95'])])+r' \\')
        ls.append(r'\addlinespace[2pt]')
ls += [r'\bottomrule',r'\end{tabular}']
(HERE/'tables/timing.tex').write_text('\n'.join(ls)+'\n')

# All low-budget component variants (including unchanged and weak variants).
ls=[r'\begin{tabular}{@{}lccc@{}}',r'\toprule',r'Updated component & $p_1$ (\%) & $\tau$ & Gap recovered (\%) \\',r'\midrule']
labels={'self256-rms':'RMS calibration','self256-fc':'Interface','self256-fc-r8':'Interface LoRA, rank 8','self256-fc-r32':'Interface LoRA, rank 32','self256-decoder':'Decoder LoRA','self256-fc-decoder':'Interface + decoder LoRA','self256-full':'Full warm start','self256-scratch':'Scratch draft layers/head'}
for label,name in labels.items():
    rows=[r for r in selected if r['label']==label and r['workload']=='speed128' and (r['step']==300 or label=='self256-rms')]
    assert len(rows)==1,(label,len(rows))
    s=rows[0]['statistics']
    ls.append(' & '.join([name,cell(s['metrics']['p1'],True),cell(s['metrics']['tau']),cell(s['recovery'],True)])+r' \\[2pt]')
ls += [r'\bottomrule',r'\end{tabular}']
(HERE/'tables/components.tex').write_text('\n'.join(ls)+'\n')
print('Wrote frozen results, source hashes, main/component/timing tables.')
