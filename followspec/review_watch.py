"""CPU-only evidence watcher: immutable snapshots, explicit failure alerts, no launches."""
import argparse,json,time,traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from followspec.review_analysis import analyze

def watch(root,out):
    out.mkdir(parents=True,exist_ok=False)
    stages=[root/'artifacts'/s for s in ['REV1_20261010_0130','REV1_controls_20261010_0140','REV1_sampled_20261010_0140']]
    expected=[]
    for stage in stages:
        for r in json.loads((stage/'plan.json').read_text()):
            if r['kind']=='capacity':expected.extend(stage/'capacity-eval'/(r['name']+'-'+w) for w in ['speed128','math64'])
            else:expected.append(Path(r['run_dir']))
    assert len(expected)==42
    last=-1;alerts=set();deadline=time.monotonic()+12*3600
    while time.monotonic()<deadline:
        now=datetime.now(ZoneInfo('America/New_York'));stamp=now.strftime('%Y%m%d_%H%M%S')
        failures=[str(p) for stage in stages for p in stage.glob('**/failure.json')]
        log=root/'artifacts/M2_D28_20261006/response_queue.log'
        for line in log.read_text().splitlines():
            try:r=json.loads(line)
            except ValueError:continue
            if 'REV1-' in json.dumps(r) and r.get('event')=='launch_failed':failures.append(json.dumps(r))
        for failure in failures:
            if failure not in alerts:
                alerts.add(failure);print('ALERT',failure,flush=True)
                (out/f'alert-{stamp}-{len(alerts)}.json').write_text(json.dumps(dict(time=now.isoformat(),failure=failure)))
        done=sum((p/'results.json').exists() for p in expected)
        if done!=last:
            snapshot=out/('snapshot-'+stamp)
            try:analyze(stages,snapshot)
            except Exception:
                print('ANALYSIS_FAILED',traceback.format_exc(),flush=True)
                (out/f'analysis-failed-{stamp}.txt').write_text(traceback.format_exc())
            else:
                print(f'{now.isoformat()} completed {done}/42 acceptance cells',flush=True)
                entry=f"\n- {now.isoformat()}: **{done}/42** new acceptance cells complete. [Long/sampled results](../{snapshot.relative_to(root)}/report.md); [component/supervision results](../{snapshot.relative_to(root)}/components.md). All are raw-recomputed pilots; pending and null arms retained.\n"
                with (root/'reports/REV1-paper-strengthening-20261010.md').open('a') as f:f.write(entry)
                with (root/'notes/REV1.md').open('a') as f:f.write(f'\n## {now.isoformat()} — codex-1 / CPU watcher\n\n{done}/42 acceptance cells complete. Immutable evidence: `{snapshot.relative_to(root)}`. No jobs launched by this watcher.\n')
                with (root/'ledger/EXP-ATL-026.md').open('a') as f:f.write(entry)
                last=done
        if done==len(expected):print('COMPLETE: all planned acceptance files analyzed',flush=True);return
        time.sleep(30)
    raise TimeoutError('12h evidence watcher deadline; pending results retained')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();watch(a.root.resolve(),a.output.resolve())
