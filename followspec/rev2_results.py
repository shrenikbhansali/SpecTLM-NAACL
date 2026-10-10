"""D54 completed export/cell tables, including all nulls and pending cells."""
import argparse,json
from collections import defaultdict
from pathlib import Path
from followspec.rev2_analysis import load_raw
from followspec.rev2_training_analysis import combine
from followspec.review_followup import parts
from ops.track_t import WS,DISPATCH,lines,write

def analyze(stages,out):
    out.mkdir(exist_ok=False);jobs={j['name']:j for j in lines(DISPATCH)};groups=defaultdict(list);pending=[]
    def path(name):
        _,i=parts(jobs[name]);return Path(i[i.index('--output')+1])
    def baseline(t,w,arm='reuse'):
        if w.startswith('math32-'):return path(f'REV1-long-t{t}-{arm}-{w.split("-")[1]}')
        if t==2:
            if arm=='reuse':return path('T1-qwen3-eagle3-A10-a78899496c39') if w=='speed128' else path('REV2-E12-t2-reuse-math500')
            return None
        if w=='math500':
            if arm=='oracle':return path('D50-MATH500-oracle-v2')
            return path(f'D52-MATH500-official-'+('reused' if arm=='reuse' else arm)) if t==0 else path(f'REV2-E14-t1-{arm}-seed0-math500')
        if arm=='reuse':return path(f'D50-E1-official-t{t}-{w}')
        if arm=='oracle':return path('T4-phase1b-R1-dedicated' if w=='speed128' else 'P3-math-oracle-0-0310')
        return path(f'FIX24-official-t{t}-16k-{arm}-s{4477 if t==0 else 2625}-{w}')
    for stage in stages:
        main=json.loads((stage/'plan.json').read_text());records=[r for r in main if r.get('kind')=='eval' or r.get('experiment')=='E14']
        for p in stage.glob('eval-plan-*.json'):records+=json.loads(p.read_text())
        for r in records:
            if r['experiment']=='E8':continue
            p=Path(r['run_dir'])
            if not (p/'results.json').exists():pending.append(r['name']);continue
            key=(r['experiment'],r['target'],r['arm'],r.get('data_label',''),r['workload']);groups[key].append((r,load_raw(p)))
    records=[]
    for key,items in sorted(groups.items()):
        exp,t,arm,data,w=key;items.sort(key=lambda x:x[0].get('seed',0))
        if exp=='E14' and t==0:
            # Seed0 already measured in D52; include it once alongside newly completed seeds1/2.
            zero=load_raw(baseline(t,w,arm));items.insert(0,(dict(seed=0,name='D52-seed0'),zero))
            if len(items)!=3:continue
        if exp=='E17' and t==0 and len(items)!=3:continue
        p=baseline(t,w)
        if p is None or not (p/'results.json').exists():pending.append(f'baseline t{t} {w}');continue
        ref=load_raw(p);oracle=load_raw(baseline(t,w,'oracle')) if t==0 else None;cells=[c for _,c in items]
        result=combine(ref,cells,oracle);contrasts={}
        if exp in ['E9','E15','E17','E13']:
            for comparator in ['fc','full']:
                p=baseline(t,w,comparator)
                if p and (p/'results.json').exists():
                    references=[load_raw(p)]
                    if exp=='E17' and t==0:
                        for seed,step in [(1,4472),(2,4481)]:
                            name=f'REV2-E14-t0-{comparator}-seed{seed}-math500' if w=='math500' else f'FIX24-official-t0-16k-{comparator}-seed{seed}-s{step}-{w}'
                            pp=path(name)
                            if (pp/'results.json').exists():references.append(load_raw(pp))
                        if len(references)!=len(cells):pending.append(f'matched seed comparator {comparator} {w}');continue
                    contrasts[comparator+'-16k512']=combine(references if len(references)>1 else references[0],cells)
        training=[]
        for item,_ in items:
            if 'training_dir' not in item:continue
            root=Path(item['training_dir']);cfg=json.loads((root/'config.json').read_text());res=json.loads((root/'results.json').read_text())
            training.append(dict(path=str(root),seed=cfg['seed'],n=cfg['n'],steps=res['steps'],gpu_hours=res['wall_s']/3600,batch_tokens=cfg.get('batch_tokens'),sequence_tokens=cfg.get('token_budget'),lr=cfg.get('lr'),ttt_steps=cfg.get('ttt_steps'),data_sha256=cfg.get('data_sha256'),scope='online target capture plus native trainer, initialization and export included; data generation separately recorded'))
        records.append(dict(experiment=exp,target=t,arm=arm,data_label=data,workload=w,seeds=[r.get('seed',0) for r,_ in items],result=result,contrasts=contrasts,training=training))
    write(out/'results.json',dict(status='pilot',records=records,pending=pending))
    text=['# REV2 completed acceptance — pilot','', 'Independent reconstruction from raw per-step counters. Paired seed/query bootstrap10000 draws; full three-seed groups required where planned. Refer to source paths for hashes and exact rendered prompt identities.','', '| Experiment | Target | Arm / data | Panel | n/seeds | p1 [95% CI] | τ [95% CI] | Δτ vs reuse [95% CI] | Oracle recovery [95% CI] |','|---|---|---|---|---:|---|---|---|---|']
    def f(v):return '--' if v is None else f"{v['mean']:.3f} [{v['ci95'][0]:.3f},{v['ci95'][1]:.3f}]"
    for r in records:
        m=r['result']['metrics'];q=m['tau'];text.append(f"| {r['experiment']} | {r['target']} | {r['arm']} / {r['data_label']} | {r['workload']} | {q['n']}/{q['seeds']} | {f(m['p1']['arm'])} | {f(q['arm'])} | {f(q['delta'])} | {f(q.get('recovery'))} |")
    seen=set();text+=['','| Training arm | Target | Seed | Examples | Steps | Batch tokens | Measured train GPUh |','|---|---|---:|---:|---:|---:|---:|']
    for r in records:
        for t in r['training']:
            if t['path'] in seen:continue
            seen.add(t['path']);text.append(f"| {r['experiment']} {r['arm']} {r['data_label']} | {r['target']} | {t['seed']} | {t['n']} | {t['steps']} | {t['batch_tokens']} | {t['gpu_hours']:.3f} |")
    text+=['',f'Pending inputs explicitly observed: {len(pending)}. Training stages without exports are listed in their plan, not counted here.'];(out/'report.md').write_text('\n'.join(text)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stages',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.stages,a.output)
