"""Independent raw-counter reproduction gate. Does not import atlas/followspec metrics."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def raw_metric(row):
    accepted=row['per_step_accepted'];drafted=row['per_step_drafted']
    if len(accepted)!=len(drafted) or any(type(a)!=int or type(d)!=int or not 0<=a<=d<=4 or d==0 for a,d in zip(accepted,drafted)):
        raise ValueError('Invalid K4 raw counters')
    if not accepted:return None
    return 1+sum(accepted)/len(accepted),sum(x>0 for x in accepted)/len(accepted)


def paired(old,new):
    aa={r['prompt_id']:r for r in old};bb={r['prompt_id']:r for r in new}
    if len(aa)!=len(old) or len(bb)!=len(new) or set(aa)!=set(bb):raise ValueError('Mismatched/duplicate prompt IDs')
    pairs=[(raw_metric(aa[k]),raw_metric(bb[k])) for k in sorted(aa)]
    values=np.array([p for p in pairs if p[0] is not None and p[1] is not None])
    if not len(values):raise ValueError('No nonzero paired queries')
    draws=np.random.default_rng(0).integers(len(values),size=(10000,len(values)))
    delta=values[:,1,0]-values[:,0,0]
    return dict(n=len(values),excluded_zero_step=len(pairs)-len(values),old_tau=float(values[:,0,0].mean()),new_tau=float(values[:,1,0].mean()),
                old_p1=float(values[:,0,1].mean()),new_p1=float(values[:,1,1].mean()),delta_tau=float(delta.mean()),
                delta_tau_ci95=np.quantile(delta[draws].mean(1),[.025,.975]).tolist(),
                new_tau_ci95=np.quantile(values[:,1,0][draws].mean(1),[.025,.975]).tolist())


SOURCES={
 (0,'reuse','speed128'):'artifacts/P3_D50_20261009_0200/E1-reuse/runs/D50-E1-official-t0-speed128',
 (0,'full','speed128'):'artifacts/FIX24_20261009_1420/repair-eval/runs/FIX24-official-t0-16k-full-s4477-speed128',
 (0,'dedicated','speed128'):'artifacts/T1b_cells_20261008_0145/runs/T4-phase1b-R1-dedicated',
 (0,'reuse','math500'):'artifacts/D52_official_followups_20261009/math500/runs/D52-MATH500-official-reused',
 (0,'full','math500'):'artifacts/D52_official_followups_20261009/math500/runs/D52-MATH500-official-full',
 (0,'dedicated','math500'):'artifacts/P3_D50_20261009_0200/math500/runs/D50-MATH500-oracle',
 (1,'reuse','speed128'):'artifacts/P3_D50_20261009_0200/E1-reuse/runs/D50-E1-official-t1-speed128',
 (1,'full','speed128'):'artifacts/FIX24_20261009_1420/repair-eval/runs/FIX24-official-t1-16k-full-s2625-speed128',
 (1,'reuse','math500'):'artifacts/REV2_panels_20261010_0430_v2/runs/REV2-E14-t1-reuse-seed0-math500',
 (1,'full','math500'):'artifacts/REV2_panels_20261010_0430_v2/runs/REV2-E14-t1-full-seed0-math500',
}
ANCHORS={(0,'reuse'):(1.76,1.93),(0,'full'):(2.54,2.97),(0,'dedicated'):(2.85,3.84),
         (1,'reuse'):(1.76,1.69),(1,'full'):(2.49,2.86)}


def validate_config(old, new):
    for key in ['prompt_sha256','K','seed','max_new_tokens','batch_size',
                'engine_version','target_revision','drafter_revision']:
        if old[key] != new[key]:
            raise ValueError(f'Baseline setting/file mismatch: {key}')
    for key in ['target_files_sha256','drafter_files_sha256']:
        # Restoring the same snapshot may also fetch its model card/license.
        # Every original file must match; no new model/config file is allowed.
        if any(new[key].get(k) != v for k,v in old[key].items()):
            raise ValueError(f'Baseline original-file mismatch: {key}')
        if set(new[key])-set(old[key])-{'README.md','LICENSE','LICENSE.txt','LICENSE.md'}:
            raise ValueError(f'Baseline unexpected model file: {key}')
    if new['code_commit'] != '6da2e4265c0398ec0de5affaf23b0bd1df0be445':
        raise ValueError('Wrong frozen code')


def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--suffix',default='_cachefix1');p.add_argument('--run-map',type=Path)
    a=p.parse_args();results=[];run_map=json.loads(a.run_map.read_text()) if a.run_map else {}
    for (target,arm,bench),source in SOURCES.items():
        name=f'BASELINE_t{target}_{arm}_{bench}_s0'+a.suffix
        name=run_map.get(name,name);run=a.workspace/'rebuttal/runs'/name
        record=dict(target=target,arm=arm,benchmark=bench,name=name,old_source=source)
        if not (run/'metrics.json').exists():results.append(record|dict(status='pending'));continue
        metadata=json.loads((run/'metrics.json').read_text())
        if metadata['exit_code']!=0:results.append(record|dict(status='failed',reason='process exit nonzero'));continue
        old=a.workspace/source;new=run/'cell';oc=json.loads((old/'config.json').read_text());nc=json.loads((new/'config.json').read_text())
        try:validate_config(oc,nc)
        except ValueError as exc:
            results.append(record|dict(status='failed',reason=str(exc)));continue
        def read(path):return [json.loads(x) for x in (path/'per_prompt.jsonl').read_text().splitlines()]
        result=paired(read(old),read(new));anchor=ANCHORS[(target,arm)][bench=='math500']
        status='pass' if abs(result['new_tau']-anchor)<=.03 and abs(result['delta_tau'])<=.03 else 'failed'
        results.append(record|result|dict(status=status,paper_anchor=anchor,paper_delta=result['new_tau']-anchor,
            gpu_hours=metadata['gpu_hours'],raw_sha256=hashlib.sha256((new/'per_prompt.jsonl').read_bytes()).hexdigest()))
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    for t in [0,1]:
        subset=[r for r in results if r['target']==t]
        if all(r['status']=='pass' for r in subset):
            (a.output/f't{t}-pass.json').write_text(json.dumps(dict(status='pass',cells=[r['name'] for r in subset]),indent=2)+'\n')
    print(json.dumps(results,indent=2))


if __name__=='__main__':main()
