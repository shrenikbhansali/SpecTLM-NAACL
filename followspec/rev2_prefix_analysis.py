"""Supplementary A4c: frozen online acceptance by generated-prefix length."""
import argparse,json
from pathlib import Path
import numpy as np
from followspec.rev2_analysis import load_raw,assert_prompts,paired_seed_query
from ops.track_t import lines,write
EDGES=[(0,512),(512,2048),(2048,4096),(4096,8192)]


def bins(row,edges=EDGES):
    a=np.asarray(row['per_step_accepted']);d=np.asarray(row['per_step_drafted'])
    if len(a)!=len(d) or np.any(a>d) or np.any(a<0):raise ValueError('invalid raw counters')
    residual=len(row['completion_token_ids'])-int((a+1).sum())
    if residual not in [0,1]:raise ValueError('unexplained prefill/terminal token accounting')
    # One target-prefill token precedes drafting; nonterminal step advances a+1.
    # Drop terminal step, whose nominal bonus can be suppressed at EOS/cap.
    prefix=1+np.r_[0,np.cumsum(a[:-1]+1)] if len(a) else np.array([])
    out=[]
    for lo,hi in edges:
        take=(prefix>=lo)&(prefix<hi)&(d>=1)
        if len(take):take[-1]=False
        out.append(dict(p1=float((a[take]>=1).mean()),tau=float(1+a[take].mean()),steps=int(take.sum())) if take.any() else None)
    return out


def analyze(stage,out):
    out.mkdir(exist_ok=False);records=[];audit=[]
    for t in [0,1]:
        paths={arm:stage/'long'/f'REV1-long-t{t}-{arm}-8192' for arm in ['reuse','fc','full']};raw={k:load_raw(v) for k,v in paths.items()};series={}
        for arm,p in paths.items():
            assert_prompts(raw['reuse'],raw[arm]);assert raw[arm]['config']['code_commit']=='6da2e4265c0398ec0de5affaf23b0bd1df0be445'
            rs=lines(p/'per_prompt.jsonl');series[arm]={r['prompt_id']:bins(r) for r in rs};audit.append(dict(target=t,arm=arm,source=str(p),sha256=raw[arm]['sha256'],residuals=[len(r['completion_token_ids'])-sum(v+1 for v in r['per_step_accepted']) for r in rs]))
        for b,(lo,hi) in enumerate(EDGES):
            ids=sorted(k for k in series['reuse'] if all(series[arm][k][b] is not None for arm in series))
            if not ids:continue
            for arm in ['fc','full']:
                metrics={key:paired_seed_query([[series['reuse'][k][b][key] for k in ids]],[[series[arm][k][b][key] for k in ids]]) for key in ['p1','tau']}
                records.append(dict(target=t,arm=arm,prefix=[lo,hi],n=len(ids),prompt_ids=ids,metrics=metrics,steps={a:sum(series[a][k][b]['steps'] for k in ids) for a in series}))
    write(out/'results.json',dict(status='pilot_supplementary',records=records,audit=audit,scope='Official16k seed0; existing frozenMATH32 cap8192. Bins by generated-prefix length at speculative-step start; target-prefill token accounted; terminal step dropped to remove EOS/bonus clipping. Macro over queries shared by reuse/interface/full within each bin. Later bins condition on all arms surviving, so they do not estimate a causal effect of growing context or share the same query cohort as earlier bins.'))
    text=['# A4c acceptance along generated trajectories — supplementary pilot','', 'Existing frozen MATH32 at8192 cap, official16k seed0. Generated-prefix length is reconstructed from the initial target token and accepted+bonus advances. The terminal step is excluded; every record has the expected0/1 terminal residual. Each bin pairs the same queries across reuse/interface/full. Late-bin cohorts are small and selected by continuation length; these are not fixed-text causal effects or a substitute for the whole-panel cap comparisons.','', '| Target | Prefix tokens | n/seed | Arm | p1 | Δp1 [95% CI] | τ | Δτ [95% CI] |','|---|---|---:|---|---:|---|---:|---|']
    for r in records:
        p=r['metrics']['p1'];q=r['metrics']['tau'];d=p['delta'];e=q['delta'];text.append(f"| {r['target']} | {r['prefix'][0]}–{r['prefix'][1]-1} | {r['n']}/1 | {r['arm']} | {p['arm']['mean']:.3f} | {d['mean']:+.3f} [{d['ci95'][0]:+.3f},{d['ci95'][1]:+.3f}] | {q['arm']['mean']:.3f} | {e['mean']:+.3f} [{e['ci95'][0]:+.3f},{e['ci95'][1]:+.3f}] |")
    (out/'report.md').write_text('\n'.join(text)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.stage,a.output)
