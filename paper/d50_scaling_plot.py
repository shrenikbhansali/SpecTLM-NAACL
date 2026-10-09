"""Plot raw-recomputed pilot scaling, separating prompt-source changes."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output;d=json.loads((out/'results.json').read_text());rows=d['records'];points=[]
 for arm in ['fc','full']:
  for label,n,source,campaign in [('self256-'+arm,256,'self','D46'),('self1k-'+arm,1000,'self','D48'),('self4k-'+arm,4000,'self','D48'),('generic4k-'+arm,4000,'generic','D48'),('generic16k-'+arm,16000,'generic','three-seed'),('E5c-generic64k-'+arm,64000,'Alpaca+Dolly extension','P3_E5c64k_20261009_1420')]:
   for w in ['speed128','math64']:
    rr=[r for r in rows if r['target']==0 and r['label']==label and r['campaign']==campaign and r['workload']==w]
    if not rr:continue
    if campaign!='three-seed':rr=[max(rr,key=lambda r:r['step'])]
    r=rr[0]
    if n==64000:
     cfg=json.loads(Path(r['output'],'config.json').read_text())
     if r['step']!=cfg['steps']:continue
    points.append(dict(arm=arm,n=n,source=source,workload=w,statistics=r['statistics'],step=r['step']))
 fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained')
 for row,w in enumerate(['speed128','math64']):
  for col,metric in enumerate(['p1','tau']):
   ax=axes[row,col]
   for arm,color in [('fc','tab:blue'),('full','tab:orange')]:
    for source,style,marker in [('self',':','o'),('generic','-','s'),('Alpaca+Dolly extension','None','D')]:
     pp=sorted([q for q in points if q['arm']==arm and q['source']==source and q['workload']==w],key=lambda q:q['n'])
     if not pp:continue
     y=[q['statistics']['metrics'][metric]['mean'] for q in pp];lo=[v-q['statistics']['metrics'][metric]['ci95'][0] for q,v in zip(pp,y)];hi=[q['statistics']['metrics'][metric]['ci95'][1]-v for q,v in zip(pp,y)]
     ax.errorbar([q['n'] for q in pp],y,yerr=[lo,hi],label=arm+' / '+source,color=color,linestyle=style,marker=marker,capsize=3)
   ax.set_xscale('log',base=2);ax.set_xticks([256,1000,4000,16000,64000],['256','1k','4k','16k','64k']);ax.set_xlabel('Training examples');ax.set_ylabel('Position-1 acceptance' if metric=='p1' else 'Macro acceptance length');ax.set_title(w);ax.grid(alpha=.2)
 axes[0,0].legend(fontsize=7);fig.suptitle('Pilot scaling: prompt sources shown separately; 64k pending unless plotted')
 fig.savefig(out/'scaling.pdf');fig.savefig(out/'scaling.png',dpi=180);plt.close(fig)
 (out/'scaling-points.json').open('x').write(json.dumps(points,indent=2)+'\n')
 with (out/'report.md').open('a') as f:f.write('\n![Pilot scaling](scaling.png)\n\nSelf256 uses 300 steps; self1k/4k and generic4k/16k use one epoch with different token totals. The16k point averages3seeds; other points use seed0. This is not a single-factor scaling experiment. The64k point is added only after its final one-epoch export is evaluated and is marked separately for its Alpaca+Dolly mixture change.\n')
if __name__=='__main__':main()
