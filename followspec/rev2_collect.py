"""Incremental immutable REV2 raw reductions and separate Markdown evidence.

Never changes paper files, dispatch, gates or board completion. Reads completed
cell markers, re-derives counters and writes a new timestamped evidence directory.
"""
import argparse,fcntl,hashlib,json,time,traceback,subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from followspec.rev2_training_analysis import e8
from followspec.rev2_results import analyze as acceptance
from followspec.rev2_timing_analysis import analyze as timing
from followspec.rev2_profile_analysis import analyze as profiles
from followspec.rev2_data_analysis import analyze as data_stats
from ops.track_t import WS

STAGES=['REV2_E8_20261010_0425','REV2_panels_20261010_0430_v2','REV2_P1_20261010_0437','REV2_E15_20261010_0445','REV2_E12_controls_20261010_0445']
TIMINGS=['REV2_E10a_20261010_0430','REV2_E10b_20261010_0430','REV2_E11_20261010_0437','REV2_E12_controls_20261010_0445']
FOLLOW=WS/'artifacts/REV2_followups_20261010_0500'
PANELS=WS/'artifacts/REV2_panels_20261010_0430_v2'
BEGIN='<!-- REV2 LIVE RAW RESULTS BEGIN -->';END='<!-- REV2 LIVE RAW RESULTS END -->'


def inputs():
    stages=[WS/'artifacts'/s for s in STAGES]+sorted(FOLLOW.glob('training-t*'))
    stages=[s for s in stages if (s/'plan.json').exists()]
    plans=[WS/'artifacts'/s/'plan.json' for s in TIMINGS]+[FOLLOW/'qwen-repair-timing/plan.json']
    plans=[p for p in plans if p.exists()]
    paths=[]
    data_plan=WS/'artifacts/REV2_data_20261010_0430/plan.json'
    for r in json.loads(data_plan.read_text()):
        result=Path(r['run_dir'])/'results.json'
        if result.exists():paths.append(result)
    for p in [s/'plan.json' for s in stages]+[p for s in stages for p in s.glob('eval-plan-*.json')]+plans:
        paths.append(p)
        for r in json.loads(p.read_text()):
            result=Path(r['run_dir'])/'results.json'
            if result.exists():paths.append(result)
    return stages,plans,sorted(set(paths))


def fingerprint(paths):
    return hashlib.sha256(json.dumps([(str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in paths]).encode()).hexdigest()


def collect(out,stages,plans):
    out.mkdir(exist_ok=False)
    e8(WS/'artifacts/REV2_E8_20261010_0425',PANELS,out/'E8')
    acceptance(stages,out/'acceptance');timing(plans,out/'timing')
    profiles(WS/'artifacts/REV2_P1_20261010_0437',out/'E16')
    data_stats(WS/'artifacts/REV2_data_20261010_0430',out/'data')
    text=['## Live raw-result tables','',f'Independent reduction snapshot: {datetime.now(ZoneInfo("America/New_York")).isoformat()}. Incomplete groups remain pending; no provisional acceptance values are substituted.']
    total=0
    for key,title in [('E8','E8 matched-capacity'),('acceptance','E9/E12/E13/E14/E15/E17 acceptance'),('timing','E10/E11/E12 timing'),('E16','E16 resources'),('data','E9/E12 response data')]:
        data=json.loads((out/key/'results.json').read_text());n=len(data['records']);total+=n
        text+=['',f'### {title}',f'Completed comparison rows: {n}; pending inputs: {len(data["pending"])}.',f'[Immutable table](../{(out/key/"report.md").relative_to(WS)}) · [Numbers, intervals, n and sources](../{(out/key/"results.json").relative_to(WS)})']
        if n:
            table=(out/key/'report.md').read_text().splitlines();text+=['']+[s for s in table if s.startswith('|')]
    from followspec.rev2_progress import progress
    state=progress(out);(out/'progress.json').write_text(json.dumps(state,indent=2))
    text+=['','### Run-list completion','', '| Level | Successful jobs / planned / final expected | Analysis complete | Ready for review |','|---|---:|---|---|']
    for level,r in state['levels'].items():text.append(f"| {level} | {r['completed']} / {r['planned']} / {r['expected']} | {r['analysis_complete']} | {r['ready_for_review']} |")
    (out/'summary.md').write_text('\n'.join(text)+'\n')
    return '\n'.join(text),total


def integrate(text):
    report=WS/'reports/REV2-results-20261010.md';s=report.read_text();block=BEGIN+'\n'+text+'\n'+END
    if BEGIN in s:
        if s.count(BEGIN)!=1 or s.count(END)!=1:raise ValueError('ambiguous report block')
        s=s[:s.index(BEGIN)]+block+s[s.index(END)+len(END):]
    else:s=s.rstrip()+'\n\n'+block+'\n'
    tmp=report.with_suffix('.md.rev2-tmp');tmp.write_text(s);tmp.replace(report)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--watch',action='store_true');p.add_argument('--update-report',action='store_true');p.add_argument('--ping-board',action='store_true',help='publish own row to review after all prescribed jobs and independent analyses complete');a=p.parse_args()
    a.root.mkdir(exist_ok=True);lock=(a.root/'collector.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);last=None;last_snapshot=None;last_progress=None
    while True:
        stages,plans,paths=inputs();current=fingerprint(paths)
        if current!=last:
            out=a.root/datetime.now(ZoneInfo('America/New_York')).strftime('%Y%m%d_%H%M%S_%f')
            try:
                text,n=collect(out,stages,plans)
                if a.update_report:integrate(text)
                print('REDUCED',out,'comparison rows',n,flush=True)
                last=current;last_snapshot=out
            except Exception:
                error=traceback.format_exc();print('ALERT raw reduction failed',error,flush=True)
                if out.exists():(out/'error.txt').write_text(error)
                raise
        if last_snapshot is not None:
            from followspec.rev2_progress import progress,ping_board
            state=progress(last_snapshot);key=json.dumps(state,sort_keys=True)
            if key!=last_progress:
                stamp=datetime.now(ZoneInfo('America/New_York')).isoformat();proof=a.root/('progress-'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.json')
                proof.write_text(json.dumps(state|dict(raw_analysis_snapshot=str(last_snapshot),updated_at=stamp),indent=2));last_progress=key
                print('PROGRESS', {k:(v['completed'],v['expected'],v['ready_for_review']) for k,v in state['levels'].items()},flush=True)
                if a.ping_board:
                    for level,v in state['levels'].items():
                        if not v['ready_for_review']:continue
                        board=(WS/'MASTER.md').read_text();row=next(x for x in board.splitlines() if x.startswith('| REV2-'+level+' |'))
                        if row.split('|')[7].strip() in ['review','done']:continue
                        if subprocess.check_output(['git','branch','--show-current'],cwd=WS,text=True).strip()!='main':raise ValueError('board publication requires main')
                        if subprocess.check_output(['git','diff','--','MASTER.md'],cwd=WS,text=True).strip():raise ValueError('uncommitted board changes; operator merge needed')
                        subprocess.run(['git','pull','--ff-only'],cwd=WS,check=True)
                        if ping_board(WS,level,v,str(proof.relative_to(WS)),stamp):
                            subprocess.run(['git','add','MASTER.md','notes/REV2.md','ledger/EXP-ATL-027.md','reports/REV2-results-20261010.md'],cwd=WS,check=True)
                            subprocess.run(['git','commit','-m','board: REV2-'+level+' review with completed raw evidence'],cwd=WS,check=True)
                            subprocess.run(['git','push','origin','main'],cwd=WS,check=True)
            if a.watch and all(v['ready_for_review'] for v in state['levels'].values()):
                print('All mandatory D54 levels complete; owner selection/promotion remains separate.',flush=True);break
        if not a.watch:break
        time.sleep(30)
