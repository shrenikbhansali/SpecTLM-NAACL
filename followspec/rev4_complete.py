"""D56 board pings only after mandatory published jobs and raw analyses finish."""
import argparse,json,time,subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
from followspec.rev4_results import inventory
from followspec.rev4_math import prerequisites
from ops.track_t import WS,lines,write

def timing_counts():
 # Y4: two batches times (reuse/none plus two repairs vs none and reuse).
 return {'Y4':2*(1+2*2),'Y6':2*2,'Y3b':2*2}

def ready(level,rows,done,progress,timing):
 expected={'Y3b':6,'Y4':4,'Y5':6,'Y6':8,'Y7':8,'Y8':8} if level=='P1' else {'Y10':24}
 subset=[r for r in rows if r['experiment'] in expected]
 if not subset or any(progress.get('acceptance_counts',{}).get(k)!=v for k,v in expected.items()):return False
 if any(done.get(r['name'])!='0' or not (Path(r['run_dir'])/'results.json').exists() for r in subset):return False
 if level=='P1':
  if not prerequisites(subset)['ready'] or not progress.get('y9_complete'):return False
  counts=Counter(r['experiment'].split('-')[0] for r in timing)
  return all(counts[k]==v for k,v in timing_counts().items())
 c=Counter(r['kind'] for r in subset)
 return all(c[k]==v for k,v in {'data':16,'train':8,'eval':24}.items())

def finish(level,analysis,records,out):
 stamp=datetime.now(ZoneInfo('America/New_York')).isoformat();proof=out/f'{level}-complete.json'
 if proof.exists():return
 write(proof,dict(level=level,timestamp=stamp,analysis=str(analysis),jobs=records,status='pilot_ready_for_operator_review'))
 subprocess.run(['git','pull','--ff-only'],cwd=WS,check=True)
 p=WS/'MASTER.md';rows=p.read_text().splitlines()
 for i,r in enumerate(rows):
  if r.startswith('| REV4-'+level+' |'):
   c=r.split('|')
   if c[7].strip() in ['done','review']:return
   assert c[7].strip()=='in progress' and 'codex-1' in c[8];c[7]=' review ';c[8]=f' codex-1 / {stamp} ';c[9]=f' [pilot results](reports/REV4-results-20261011.md); [raw completion proof]({proof.relative_to(WS)}) ';rows[i]='|'.join(c)
 p.write_text('\n'.join(rows)+'\n')
 for name in ['notes/REV4.md','ledger/EXP-ATL-029.md']:
  with (WS/name).open('a') as f:f.write(f'\n### {stamp} — codex-1 — {level} completion ping\nMandatory jobs exit0 with raw files and required paired analyses complete. Board moved to review, not scientific promotion. Evidence {proof}. Owner selects paper results.\n')
 subprocess.run(['git','add','MASTER.md','notes/REV4.md','ledger/EXP-ATL-029.md','reports/REV4-results-20261011.md'],cwd=WS,check=True);subprocess.run(['git','commit','-m',f'board: REV4 {level} review with complete raw evidence'],cwd=WS,check=True);subprocess.run(['git','push','origin','main'],cwd=WS,check=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--analysis-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False)
 while True:
  candidates=sorted(a.analysis_root.glob('*/progress.json'))
  if candidates:
   analysis=candidates[-1].parent;progress=json.loads(candidates[-1].read_text());timing=json.loads((analysis/'timing/results.json').read_text())['records'];launched={};done={}
   for e in lines(WS/'artifacts/M2_D28_20261006/response_queue.log'):
    if e['event']=='launched':launched[e['out_dir']]=e['name']
    elif e['event']=='finished':done[launched[e['out_dir']]]=str(e['exit'])
   rows=inventory()
   for level in ['P1','P2']:
    if ready(level,rows,done,progress,timing):finish(level,analysis,rows,a.output)
  if all((a.output/(level+'-complete.json')).exists() for level in ['P1','P2']):break
  time.sleep(60)
