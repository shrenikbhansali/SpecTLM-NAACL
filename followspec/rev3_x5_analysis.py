"""X5 raw-counter seed/query CIs; separate independent-process timing CIs."""
import argparse,fcntl,json,time,subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from followspec.rev2_analysis import load_raw
from followspec.rev2_training_analysis import combine,matched_training
from followspec.rev2_timing_analysis import analyze as analyze_timing
from ops.track_t import WS,lines,write

BEGIN='<!-- REV3 X5 LIVE BEGIN -->';END='<!-- REV3 X5 LIVE END -->'

def seed_group_ready(rows,target):return sorted(r['seed'] for r in rows)==([0,1,2] if target==0 else [0])

def analyze(stage,out):
    out.mkdir(exist_ok=False);plans=[stage/'control-plan.json']+sorted(stage.glob('final-plan-*.json'));items=[r for p in plans for r in json.loads(p.read_text())]
    groups=defaultdict(list);refs={};pending=[]
    for r in items:
        if r['kind']!='eval':continue
        if not (Path(r['run_dir'])/'results.json').exists():pending.append(r['name']);continue
        if r['arm']=='reuse':refs[r['target'],r['workload']]=r
        else:groups[r['target'],r['arm'],r['workload']].append(r)
    records=[]
    for (t,arm,w),rows in sorted(groups.items()):
        if not seed_group_ready(rows,t) or (t,w) not in refs:continue
        rows.sort(key=lambda r:r['seed']);ref=load_raw(refs[t,w]['run_dir']);cells=[load_raw(r['run_dir']) for r in rows]
        if ref['config']['method']!='dflash' or ref['config']['K']!=10 or any(c['config']['method']!='dflash' for c in cells):raise ValueError('not native DFlashK10')
        records.append(dict(target=t,arm=arm,workload=w,result=combine(ref,cells),training_sources=[r['training_dir'] for r in rows]))
    audits=[];costs=[];bykey={}
    for r in json.loads((stage/'plan.json').read_text()):
        root=Path(r['run_dir'])
        if not (root/'results.json').exists():continue
        cfg=json.loads((root/'config.json').read_text());res=json.loads((root/'results.json').read_text());bykey[r['target'],r['arm'],r['seed']]=cfg
        if cfg['algorithm']!='dflash' or cfg['max_anchors']!=64 or cfg['n']!=16000 or res['steps']!=cfg['steps']:raise ValueError('native training protocol mismatch')
        costs.append(r|dict(steps=res['steps'],train_gpu_hours=res['wall_s']/3600,max_gpu_allocated_gib=res['max_gpu_allocated_gb'],data_sha256=cfg['data_sha256'],native_loss=cfg['loss']))
    for t in [0,1]:
        for s in (range(3) if t==0 else [0]):
            if all((t,a,s) in bykey for a in ['fc','full']):
                a,b=bykey[t,'fc',s],bykey[t,'full',s];matched_training(a,b)
                for k in ['algorithm','max_anchors','checkpoint_dflash_layers','export_only_final']:assert a[k]==b[k]
                audits.append(dict(target=t,seed=s,passed=True))
    write(out/'acceptance.json',dict(status='pilot',records=records,pending=pending,training_costs=costs,matched_audits=audits))
    analyze_timing(plans,out/'timing')
    timings=json.loads((out/'timing/results.json').read_text());allrows=json.loads((stage/'plan.json').read_text())+items
    launched={};finished={}
    for e in lines(WS/'artifacts/M2_D28_20261006/response_queue.log'):
        if e['event']=='launched':launched[e['out_dir']]=e['name']
        if e['event']=='finished':finished[launched[e['out_dir']]]=str(e['exit'])
    assert len({r['name'] for r in allrows})==len(allrows)
    complete=[r['name'] for r in allrows if finished.get(r['name'])=='0' and (Path(r['run_dir'])/'results.json').exists()]
    failed=[r['name'] for r in allrows if finished.get(r['name']) not in [None,'0']]
    ready=len(complete)==len(allrows)==86 and len(records)==12 and len(timings['records'])==20 and len(audits)==4 and not failed
    progress=dict(planned=len(allrows),completed=len(complete),expected=86,failed=failed,ready_for_review=ready)
    write(out/'progress.json',progress)
    def f(v):return f"{v['mean']:.3f} [{v['ci95'][0]:.3f},{v['ci95'][1]:.3f}]"
    text=['### X5 live independently reduced results','',f'Updated {datetime.now(ZoneInfo("America/New_York")).isoformat()}; pilot. Completed{len(complete)}/86planned final jobs; failed={failed}. Three-seed R1 groups required before showing a combined estimate.','', '| Target | Arm | Panel | n/seeds | Reuse τ | Repair τ [95% CI] | Δτ [95% CI] | p1 [95% CI] | Δp1 [95% CI] |','|---|---|---|---:|---:|---|---|---|---|']
    for r in records:
        q=r['result']['metrics'];t=q['tau'];text.append(f"| {r['target']} | {r['arm']} | {r['workload']} | {t['n']}/{t['seeds']} | {t['reference']['mean']:.3f} | {f(t['arm'])} | {f(t['delta'])} | {f(q['p1']['arm'])} | {f(q['p1']['delta'])} |")
    text+=['','SPEED128 timing, seed0 exports, three processes × three warm passes. All128 prompts at both batch sizes. Cold/startup and output-token differences remain in source JSON.']
    text += [s for s in (out/'timing/report.md').read_text().splitlines() if s.startswith('|')]
    text+=['','| Target | Scope | Seed | Native steps | Measured training GPUh | Peak allocated GiB |','|---|---|---:|---:|---:|---:|']
    for r in costs:text.append(f"| {r['target']} | {r['arm']} | {r['seed']} | {r['steps']} | {r['train_gpu_hours']:.3f} | {r['max_gpu_allocated_gib']:.2f} |")
    text+=['',f'[Raw counts, paired seed/query CIs, per-depth acceptance, lengths and hashes](../{(out/"acceptance.json").relative_to(WS)}); [timing intervals and source files](../{(out/"timing/results.json").relative_to(WS)}); [completion evidence](../{(out/"progress.json").relative_to(WS)}).']
    (out/'report.md').write_text('\n'.join(text)+'\n');return '\n'.join(text),progress

def integrate(text):
    p=WS/'reports/REV3-results-20261010.md';s=p.read_text();block=BEGIN+'\n'+text+'\n'+END
    if BEGIN in s:s=s[:s.index(BEGIN)]+block+s[s.index(END)+len(END):]
    else:s=s.rstrip()+'\n\n'+block+'\n'
    temp=p.with_suffix('.md.x5-tmp');temp.write_text(s);temp.replace(p)

def ping_board(workspace,progress,evidence,stamp):
    if not progress['ready_for_review']:return False
    p=workspace/'MASTER.md';rows=p.read_text().splitlines();ii=[i for i,r in enumerate(rows) if r.startswith('| REV3-X5 |')]
    if len(ii)!=1:raise ValueError('X5 row missing/ambiguous')
    i=ii[0];cells=rows[i].split('|')
    if cells[7].strip() in ['review','done']:return False
    if cells[7].strip()!='in progress' or 'codex-1' not in cells[8]:raise ValueError('X5 ownership changed')
    cells[7]=' review ';cells[8]=' codex-1 / '+stamp+' ';cells[9]=' [results](reports/REV3-results-20261010.md); [86-job completion evidence]('+evidence+'); independently reduced, pilot '
    rows[i]='|'.join(cells);tmp=p.with_suffix('.md.x5-ping');tmp.write_text('\n'.join(rows)+'\n');tmp.replace(p);return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--watch',action='store_true');p.add_argument('--update-report',action='store_true');a=p.parse_args()
    a.output.mkdir(exist_ok=False);lock=(a.output/'watch.lock').open('x');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);last=None
    while True:
        plans=[a.stage/'plan.json',a.stage/'control-plan.json']+sorted(a.stage.glob('final-plan-*.json'));paths=list(plans)
        if not all(p.exists() for p in plans):time.sleep(30);continue
        for p in plans:
            for r in json.loads(p.read_text()):
                q=Path(r['run_dir'])/'results.json'
                if q.exists():paths.append(q)
        # Include launcher completion transitions, not only native result markers.
        key=(tuple((str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in paths),(WS/'artifacts/M2_D28_20261006/response_queue.log').stat().st_mtime_ns)
        if key!=last:
            out=a.output/datetime.now().strftime('%Y%m%d_%H%M%S_%f');text,progress=analyze(a.stage,out)
            if a.update_report:integrate(text)
            print('X5 REDUCED',out,progress,flush=True);last=key
            if progress['ready_for_review']:
                stamp=datetime.now(ZoneInfo('America/New_York')).isoformat()
                subprocess.run(['git','pull','--ff-only'],cwd=WS,check=True)
                ping_board(WS,progress,str((out/'progress.json').relative_to(WS)),stamp)
                message=f'\n## {stamp} — codex-1 — X5 completion ping\n\nAll 86 jobs and required raw/CIs complete; pilot; evidence {out}. Board moved to review.\n'
                for path in ['notes/REV3.md','ledger/EXP-ATL-028.md']:
                    with (WS/path).open('a') as f:f.write(message)
                subprocess.run(['git','add','MASTER.md','notes/REV3.md','ledger/EXP-ATL-028.md','reports/REV3-results-20261010.md'],cwd=WS,check=True)
                subprocess.run(['git','commit','-m','board: REV3 X5 review with completed raw evidence'],cwd=WS,check=True)
                subprocess.run(['git','push','origin','main'],cwd=WS,check=True)
                break
        if not a.watch:break
        time.sleep(30)
