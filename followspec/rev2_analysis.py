"""D54 raw counters; paired seeds and queries. No evaluation-metric imports."""
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
DRAWS=10000

def summary(x,mean):return dict(mean=float(mean),ci95=np.quantile(x,[.025,.975]).tolist())
def paired_seed_query(a,b,oracle=None):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    if a.ndim!=2 or a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('paired seed/query matrices required')
    s,n=a.shape;rng=np.random.default_rng(20261010);ss=rng.integers(s,size=(DRAWS,s));qq=rng.integers(n,size=(DRAWS,n))
    aa=a[ss[:,:,None],qq[:,None,:]].mean((1,2));bb=b[ss[:,:,None],qq[:,None,:]].mean((1,2))
    r=dict(n=n,seeds=s,reference=summary(aa,a.mean()),arm=summary(bb,b.mean()),delta=summary((b-a)[ss[:,:,None],qq[:,None,:]].mean((1,2)),(b-a).mean()))
    if oracle is not None:
        c=np.broadcast_to(np.asarray(oracle),a.shape);cc=c[ss[:,:,None],qq[:,None,:]].mean((1,2));den=cc-aa
        r['recovery']=summary((bb-aa)/den,(b.mean()-a.mean())/(c.mean()-a.mean())) if np.all(den!=0) else None
    return r

def load_raw(path):
    p=Path(path);config=json.loads((p/'config.json').read_text());results=json.loads((p/'results.json').read_text())
    if config['engine_version']!='0.31.0' or 'A40' not in results.get('gpu_type',''):raise ValueError('engine/hardware mismatch '+str(p))
    records={}
    for line in (p/'per_prompt.jsonl').read_text().splitlines():
        r=json.loads(line);a=np.asarray(r['per_step_accepted']);d=np.asarray(r['per_step_drafted'])
        if len(a)!=len(d) or np.any(a<0) or np.any(a>d):raise ValueError('invalid raw counters')
        if r['prompt_id'] in records:raise ValueError('duplicate prompt ID')
        records[r['prompt_id']]=dict(p1=float((a[d>=1]>=1).mean()) if np.any(d>=1) else None,tau=float(1+a.mean()) if len(a) else None,length=len(r['completion_token_ids']),conditional=[float((a[(d>=k)&(a>=k-1)]>=k).mean()) if np.any((d>=k)&(a>=k-1)) else None for k in range(1,config['K']+1)])
    if len(records)!=config['n']:raise ValueError('incomplete cell')
    return dict(config=config,rows=records,source=str(p),sha256=hashlib.sha256((p/'per_prompt.jsonl').read_bytes()).hexdigest())

def assert_prompts(a,b):
    for k in ['prompt_sha256','engine_version','K','batch_size','seed','max_new_tokens','temperature','top_p']:
        if a['config'].get(k)!=b['config'].get(k):raise ValueError('unmatched '+k)
    if a['rows'].keys()!=b['rows'].keys():raise ValueError('unmatched prompt IDs')

def census(source,out):
    out.mkdir(exist_ok=False);meta=list(csv.DictReader(source.open()));rng=np.random.default_rng(20261010);groups=defaultdict(list);allrows=[];audit=[]
    for idx,r in enumerate(meta):
        src=json.loads(r['source']);paths=src if isinstance(src,list) else [src[x]['run_dir'] for x in ['A00','A10']]
        a,b=map(load_raw,paths);assert_prompts(a,b)
        ids=sorted(k for k in a['rows'] if a['rows'][k]['p1'] is not None and b['rows'][k]['p1'] is not None)
        x=np.array([a['rows'][k]['p1'] for k in ids]);y=np.array([b['rows'][k]['p1'] for k in ids]);n=len(ids)
        draws=rng.integers(n,size=(DRAWS,n));ratios=y[draws].mean(1)/x[draws].mean(1);point=y.mean()/x.mean()
        if abs(point-float(r['p1_retention']))>1e-8:raise ValueError('archived retention mismatch '+r['model'])
        key=(r['population'],r['family'].replace('qwen','qwen3') if r['family']=='qwen' else r['family'],r['workload'],r['lineage'],r['history'],r['method'])
        groups[key].append((point,ratios,n,r['model']))
        row=r|dict(n=n,p1_retention=point,p1_low=float(np.quantile(ratios,.025)),p1_high=float(np.quantile(ratios,.975)),parent_p1=float(x.mean()),child_p1=float(y.mean()),A00=paths[0],A10=paths[1],A00_sha256=a['sha256'],A10_sha256=b['sha256']);allrows.append(row)
        audit.append(dict(model=r['model'],method=r['method'],n=n,total=len(a['rows']),excluded_no_steps=len(a['rows'])-n,code_commits=[a['config']['code_commit'],b['config']['code_commit']]))
        if idx%40==0:print('census',idx,flush=True)
    with (out/'census.csv').open('x') as f:
        w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
    grouped=[]
    for key,items in sorted(groups.items()):
        n=len(items);vals=np.array([r[0] for r in items]);pool=np.array([r[1] for r in items]);mm=rng.integers(n,size=(DRAWS,n));pp=rng.integers(DRAWS,size=(DRAWS,n));draw=pool[mm,pp].mean(1)
        grouped.append(dict(zip(['population','family','workload','lineage','history','drafter'],key))|dict(checkpoints=n,prompt_pairs=sum(r[2] for r in items),p1_retention=summary(draw,vals.mean()),models=[r[3] for r in items]))
    (out/'groups.json').write_text(json.dumps(grouped,indent=2));(out/'audit.json').write_text(json.dumps(audit,indent=2))
    text=['# A2 census composition — independent raw recomputation','', '10,000 hierarchical checkpoint/paired-query bootstrap draws; equal checkpoint weights. Compound histories retained as combinations. Historical and focused populations and workloads remain separate. Paired zero-step exclusions listed in audit.json.','', '| Population | Family | Panel | Lineage | History | Drafter | Models | Prompt pairs | p1 retention [95% CI] |','|---|---|---|---|---|---|---:|---:|---|']
    for g in grouped:
        v=g['p1_retention'];text.append('| '+' | '.join(str(g[k]) for k in ['population','family','workload','lineage','history','drafter','checkpoints','prompt_pairs'])+f" | {v['mean']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}] |")
    (out/'census-table.md').write_text('\n'.join(text)+'\n')

def domains(dispatch,public,out):
    out.mkdir(exist_ok=False);d={j['name']:j for j in map(json.loads,dispatch.read_text().splitlines())};cats={r['prompt_id']:r['category'] for r in map(json.loads,public.read_text().splitlines())}
    def cell(name):
        args=d[name]['args'];return load_raw(args[args.index('--output')+1])
    results=[]
    for t in [0,1]:
        reuse=cell(f'D50-E1-official-t{t}-speed128');arms={}
        for arm in ['fc','full']:
            arms[arm]=[cell(f'FIX24-official-t{t}-16k-{arm}-s{4477 if t==0 else 2625}-speed128')]
            if t==0:arms[arm]+=[cell(f'FIX24-official-t0-16k-{arm}-seed{s}-s{step}-speed128') for s,step in [(1,4472),(2,4481)]]
        arms['independent']=[cell(f'D50-E3-t{t}-draft_model-K4-LNone-speed128')]
        if t==0:arms['oracle']=[cell('T4-phase1b-R1-dedicated')]
        arms['reuse']=[reuse]
        for arm,cells in arms.items():
            for c in cells:assert_prompts(reuse,c)
            for category in sorted(set(cats.values())):
                ids=sorted(k for k in reuse['rows'] if cats[k]==category and reuse['rows'][k]['p1'] is not None and all(c['rows'][k]['p1'] is not None for c in cells))
                metrics={}
                for key in ['p1','tau','length']:
                    a=np.array([[reuse['rows'][k][key] for k in ids]]*len(cells));b=np.array([[c['rows'][k][key] for k in ids] for c in cells]);metrics[key]=paired_seed_query(a,b)
                results.append(dict(target=t,arm=arm,category=category,metrics=metrics,sources=[c['source'] for c in cells],reference=reuse['source']))
    (out/'domains.json').write_text(json.dumps(results,indent=2))
    text=['# A1 per-domain SPEED results — pilot','', 'Official16k: R1 repairs three training seeds, Nemotron seed0; all other arms one seed. Paired seed/query draws, n within each domain; tiny domains have correspondingly imprecise intervals.','', '| Target | Domain | Arm | n/seeds | p1 | τ | Δτ [95% CI] |','|---|---|---|---:|---:|---:|---|']
    for r in results:
        m=r['metrics'];v=m['tau']['delta'];text.append(f"| {r['target']} | {r['category']} | {r['arm']} | {m['tau']['n']}/{m['tau']['seeds']} | {m['p1']['arm']['mean']:.3f} | {m['tau']['arm']['mean']:.3f} | {v['mean']:+.3f} [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}] |")
    (out/'domains.md').write_text('\n'.join(text)+'\n')

def long_recovery(stage,out):
    out.mkdir(exist_ok=False);rows=json.loads((stage/'plan.json').read_text());cells={r['name']:load_raw(r['run_dir']) for r in rows if r['kind']=='long'};results=[]
    for cap in [512,2048,8192]:
        base=cells[f'REV1-long-t0-reuse-{cap}'];oracle=cells[f'REV1-long-t0-oracle-{cap}'];assert_prompts(base,oracle)
        for arm in ['fc','full']:
            c=cells[f'REV1-long-t0-{arm}-{cap}'];assert_prompts(base,c)
            ids=sorted(k for k in base['rows'] if all(v['rows'][k]['tau'] is not None for v in [base,oracle,c]))
            arrays=[np.array([[x['rows'][k]['tau'] for k in ids]]) for x in [base,c,oracle]];r=paired_seed_query(*arrays);results.append(dict(cap=cap,arm=arm,results=r,sources=[x['source'] for x in [base,c,oracle]]))
    (out/'recovery.json').write_text(json.dumps(results,indent=2));text=['# A4 long-workload dedicated-gap recovery — pilot','', 'Official16k short-response repairs, matched fixed MATH32, frozen greedy K4. Recovery is ratio of paired mean differences, not mean of per-query ratios; oracle/repair/reuse share each query draw.','', '| Cap | Arm | n | τ | Δτ [95% CI] | Gap closed [95% CI] |','|---:|---|---:|---:|---|---|']
    for r in results:
        q=r['results'];v=q['delta'];g=q['recovery'];text.append(f"| {r['cap']} | {r['arm']} | {q['n']} | {q['arm']['mean']:.3f} | {v['mean']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}] | {100*g['mean']:.1f}% [{100*g['ci95'][0]:.1f}, {100*g['ci95'][1]:.1f}] |")
    (out/'recovery.md').write_text('\n'.join(text)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['census','domains','long']);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--public',type=Path);a=p.parse_args()
    if a.action=='census':census(a.source,a.output)
    elif a.action=='long':long_recovery(a.source,a.output)
    else:domains(a.source,a.public,a.output)
