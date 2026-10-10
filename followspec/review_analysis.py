"""Independent raw-counter REV1 analysis; imports no harness metric functions."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import numpy as np

FROZEN='6da2e4265c0398ec0de5affaf23b0bd1df0be445'

def repeated_coverage(ids):
    positions=defaultdict(list)
    for i in range(len(ids)-3):positions[tuple(ids[i:i+4])].append(i)
    return max((len({j for i in starts for j in range(i,i+4)})/len(ids)
                for starts in positions.values() if len(starts)>1),default=0.)

def counter_metrics(row,lo=0,hi=float('inf')):
    aa=row['per_step_accepted'];dd=row['per_step_drafted']
    if len(aa)!=len(dd) or any(type(a)!=int or type(d)!=int or not 0<=a<=d<=4 or d<1 for a,d in zip(aa,dd)):
        raise ValueError('invalid K4 raw counters')
    progress=1;steps=[]
    for a,d in zip(aa,dd):
        if lo<=progress<hi:steps.append((a,d))
        progress+=a+1
    n=len(steps)
    cond=[]
    for k in range(1,5):
        den=sum(a>=k-1 and d>=k for a,d in steps)
        cond.append(sum(a>=k for a,d in steps)/den if den else None)
    return dict(p1=cond[0],tau=1+sum(a for a,d in steps)/n if n else None,conditional=cond,
                steps=n,length=len(row['completion_token_ids']),progress_minus_length=progress-len(row['completion_token_ids']))

def paired(a,b):
    ids=sorted(i for i in a.keys()&b.keys() if a[i] is not None and b[i] is not None)
    if not ids:return dict(n=0,mean=None,ci95=None)
    d=np.array([b[i]-a[i] for i in ids]);rng=np.random.default_rng(20261010)
    draws=d[rng.integers(0,len(d),(10000,len(d)))].mean(1)
    return dict(n=len(ids),mean=float(d.mean()),ci95=np.quantile(draws,[.025,.975]).tolist())

def read_cell(path):
    if not (path/'results.json').exists():return None
    cfg=json.loads((path/'config.json').read_text())
    result=json.loads((path/'results.json').read_text())
    if cfg['engine_version']!='0.31.0' or 'A40' not in result['gpu_type'] or cfg['K']!=4:raise ValueError('protocol mismatch')
    if cfg['code_commit']!=FROZEN and not cfg.get('protocol','').startswith('D53 supplementary'):raise ValueError('unapproved acceptance source')
    raw=[json.loads(l) for l in (path/'per_prompt.jsonl').read_text().splitlines()]
    if len(raw)!=cfg['n'] or len({r['prompt_id'] for r in raw})!=len(raw):raise ValueError('incomplete or duplicate prompts')
    rows={r['prompt_id']:counter_metrics(r) for r in raw}
    tau=np.mean([r['tau'] for r in rows.values() if r['tau'] is not None])
    if abs(tau-result['macro_acceptance_length'])>1e-10:raise ValueError('raw tau mismatch')
    bins={}
    # The scheduler counts accepted drafts before final EOS/max-token truncation.
    # Sum(a+1)+one initial token reconstructs progress except the final <=K tail.
    ok=all(0<=r['progress_minus_length']<=4 for r in rows.values())
    if ok:
        for lo,hi in [(0,512),(512,2048),(2048,8192)]:
            bins[f'{lo}:{hi}']={r['prompt_id']:counter_metrics(r,lo,hi) for r in raw}
    return dict(path=str(path),config=cfg,rows=rows,bins=bins,position_reconstruction_valid=ok,
                raw_sha256=hashlib.sha256((path/'per_prompt.jsonl').read_bytes()).hexdigest(),
                repeated4_flagged=sum(repeated_coverage(r['completion_token_ids'])>.5 for r in raw),
                cap_hits=sum(len(r['completion_token_ids'])>=cfg['max_new_tokens'] for r in raw))

def compatible(a,b):
    keys=['prompt_sha256','target','target_revision','method','K','seed','batch_size','max_model_len','max_new_tokens','temperature','top_p','engine_version','code_commit']
    for k in keys:
        if a['config'].get(k)!=b['config'].get(k):raise ValueError('unmatched '+k)
    if a['rows'].keys()!=b['rows'].keys():raise ValueError('unpaired IDs')

def fmt(x):
    if x['mean'] is None:return '--'
    return f"{x['mean']:+.3f} [{x['ci95'][0]:+.3f}, {x['ci95'][1]:+.3f}]"

def analyze(stages,out):
    out.mkdir(parents=True,exist_ok=False);cells={};comparisons=[];pending=[]
    for stage in stages:
        for r in json.loads((stage/'plan.json').read_text()):
            if r['kind'] not in {'long','sampled'}:continue
            c=read_cell(Path(r['run_dir']))
            if c is None:pending.append(r['name']);continue
            c['plan']=r;cells[r['name']]=c
    text=['# REV1 long-generation / sampling raw-counter results — pilot','',
          '10,000 paired query bootstrap draws, seed 20261010. MATH first32 fixed before outcomes; one evaluation seed. Greedy and supplementary sampled cells are separate. Completion caps are not guaranteed complete solutions. No repeat-flagged samples are removed.','',
          '| Mode | Target | Cap | Arm | n | p1 | τ | Δp1 [95% CI] | Δτ [95% CI] | Mean length | Cap hits | Repeat flags |',
          '|---|---|---:|---|---:|---:|---:|---|---|---:|---:|---:|']
    for name,c in sorted(cells.items()):
        r=c['plan'];base_name=name.replace('-'+r['arm']+'-','-reuse-');base=cells.get(base_name)
        if base is None:continue
        compatible(base,c)
        deltas={k:paired({i:v[k] for i,v in base['rows'].items()},{i:v[k] for i,v in c['rows'].items()}) for k in ['p1','tau']}
        means={k:float(np.mean([v[k] for v in c['rows'].values() if v[k] is not None])) for k in ['p1','tau','length']}
        bins={}
        for bin in c['bins'].keys()&base['bins'].keys():
            bins[bin]={k:paired({i:v[k] for i,v in base['bins'][bin].items()},{i:v[k] for i,v in c['bins'][bin].items()}) for k in ['p1','tau']}
        comparisons.append(dict(name=name,baseline=base_name,means=means,delta=deltas,bins=bins))
        text.append(f"| {r['kind']} | {'R1' if r['target']==0 else 'Nemotron'} | {r['cap']} | {r['arm']} | {deltas['p1']['n']} | {means['p1']:.3f} | {means['tau']:.3f} | {fmt(deltas['p1'])} | {fmt(deltas['tau'])} | {means['length']:.1f} | {c['cap_hits']}/{len(c['rows'])} | {c['repeated4_flagged']}/{len(c['rows'])} |")
    text+=['','## Progress-stratified comparisons','',
           'Step origins reconstructed from one initial token plus cumulative accepted+bonus counts. Final EOS/cap truncation is checked to be ≤K tokens; cells failing this audit have no progress analysis. Each bin pairs only queries with at least one speculative step in both arms; this is a conditional subset, not a new population estimate.','',
           '| Cell | Verified-progress bin | Paired n | Δp1 [95% CI] | Δτ [95% CI] |','|---|---|---:|---|---|']
    for r in comparisons:
        if '-8192' not in r['name'] or '-reuse-' in r['name']:continue
        for b,d in sorted(r['bins'].items()):text.append(f"| {r['name']} | {b} | {d['p1']['n']} | {fmt(d['p1'])} | {fmt(d['tau'])} |")
    text+=['','Pending: '+', '.join(pending), '', 'Raw hashes, full counters, configs, per-depth conditional rates, and reconstruction audits are in results.json.']
    (out/'results.json').write_text(json.dumps(dict(status='pilot',cells=cells,comparisons=comparisons,pending=pending),indent=2))
    (out/'report.md').write_text('\n'.join(text)+'\n')
    print('\n'.join(text[:20]))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stages',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.stages,a.output)
