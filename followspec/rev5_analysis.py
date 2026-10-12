"""CPU-only REV5 secondary analysis. No engine or evaluation defaults change."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import rankdata


def corr(x,y):
    x=x-x.mean(axis=-1,keepdims=True);y=y-y.mean(axis=-1,keepdims=True)
    den=np.sqrt((x*x).sum(axis=-1)*(y*y).sum(axis=-1))
    return np.divide((x*y).sum(axis=-1),den,out=np.full_like(den,np.nan),where=den>0)


def rank_correlation(x,y,draws=10000):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    good=np.isfinite(x)&np.isfinite(y);x=x[good];y=y[good];n=len(x)
    if n<3 or len(set(x))<2 or len(set(y))<2:return dict(n=n,rho=None,ci95=None)
    estimate=float(corr(rankdata(x),rankdata(y)))
    ii=np.random.default_rng(0).integers(n,size=(draws,n))
    boot=corr(rankdata(x[ii],axis=1),rankdata(y[ii],axis=1));boot=boot[np.isfinite(boot)]
    return dict(n=n,rho=estimate,ci95=np.quantile(boot,[.025,.975]).tolist(),valid_bootstrap_draws=len(boot))


def amortize(arm,base,n,gpu_hours,draws=10000):
    """Paired process/query-batch bootstrap; each batch contributes its time once."""
    arm=np.asarray(arm,dtype=float);base=np.asarray(base,dtype=float)
    assert arm.shape==base.shape and arm.ndim==2 and n>0 and gpu_hours>0
    ns,nb=arm.shape;rng=np.random.default_rng(0)
    ri=rng.integers(ns,size=(draws,ns));bi=rng.integers(nb,size=(draws,nb))
    delta=base-arm;point=float(delta.sum(1).mean()/n)
    boot=delta[ri[:,:,None],bi[:,None,:]].sum(2).mean(1)/n
    lo,hi=np.quantile(boot,[.025,.975]);cost=3600*gpu_hours
    return dict(seconds_saved_per_request=dict(mean=point,ci95=[float(lo),float(hi)]),
                requests=dict(mean=cost/point if point>0 else None,
                              ci95=[cost/hi if hi>0 else None,cost/lo if lo>0 else None]),
                positive_savings_fraction=float(np.mean(boot>0)),gpu_hours=gpu_hours)


def run(ws,out):
    out.mkdir(exist_ok=False,parents=True);sources={}
    def read(p):
        p=Path(p);raw=p.read_bytes();sources[str(p)]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
    archive=read(ws/'artifacts/T1b_report_20261008_0200/kl-points.json');rows=[]
    cache={}
    for r in archive['atlas']:
        p=Path(r['covariates']['path'])
        if p not in cache:cache[p]=read(p/'results.json')
        z=cache[p];assert np.isclose(r['covariates']['kl'],z['kl_child_base'])
        rows.append(dict(cohort='atlas',model=r['m'],family=r['base'],method={'A4':'eagle3','A7':'dflash'}[r['task']],
                         retention=r['pos1_ret'],kl=z['kl_child_base'],
                         cosine=np.mean([v['cosine_displacement'] for v in z['features'].values()]),
                         relative_l2=np.mean([v['relative_l2'] for v in z['features'].values()]),
                         type=r['type'],support='archive',collapsed=False,source=str(p)))
    for r in archive['t1']:
        rows.append(dict(cohort='T1',model=r['model'],family=r['base'],method=r['method'],retention=r['p1_retention'],
                         kl=r['kl']['conditional_common_vocab_kl'],cosine=None,relative_l2=None,type=r['kl']['hypothesis'],
                         support=r['kl']['support'],collapsed=r['model'].startswith('luckeciano/'),source=r['kl']['path']))
    groups=defaultdict(list)
    for r in rows:groups[r['cohort'],r['family'],r['method']].append(r)
    stats=[]
    for key,rr in sorted(groups.items()):
        assert len({r['model'] for r in rr})==len(rr), 'checkpoint duplicated within method/family'
        filters=['all'] if key[0]=='atlas' else ['all','not_collapsed','not_collapsed_identical_vocab']
        for filt in filters:
            zz=[r for r in rr if filt=='all' or (not r['collapsed'] and (filt!='not_collapsed_identical_vocab' or r['support']=='identical'))]
            for metric in (['kl','cosine','relative_l2'] if key[0]=='atlas' else ['kl']):
                v=rank_correlation([r[metric] for r in zz],[r['retention'] for r in zz])
                stats.append(dict(cohort=key[0],family=key[1],method=key[2],subset=filt,metric=metric)|v)
    with (out/'drift-models.csv').open('x') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    timing=read(ws/'artifacts/REV4_P0_live_20261011_0322/20261011_091644_963445/timing/results.json')
    costs={}
    for target in [0,1]:
        for arm in ['fc','full']:
            p=ws/f'artifacts/FIX24_20261009_1420/FIX24-official-t{target}-16k-{arm}'
            cfg=read(p/'config.json');res=read(p/'results.json');assembly=read(Path(cfg['data']).parent/'assembly.json')
            costs[target,arm]=dict(data_gpu_hours=assembly['generation_gpu_hours'],train_gpu_hours=res['wall_s']/3600)
    economics=[]
    for r in timing['records']:
        if not r['experiment'].startswith('Y1-') or r['arm'] not in ['fc','full']:continue
        cells=[]
        for p in map(Path,r['sources']):
            t=read(p/'timing.json');c=read(p/'config.json')
            assert c['harness_commit'].startswith('6da2e42') and c['engine_version']=='0.31.0' and c['gpu_type']=='NVIDIA A40'
            assert c['n']==r['n'] and c['temperature']==0
            cells.append((t,c))
        reference_ids=None;panels=[];tokens=[]
        for t,c in cells:
            assert len(t['passes'])==4
            batch_times=[];total_tokens=[]
            for a in t['passes'][1:]:
                ids=[b['prompt_ids'] for b in a['batches']]
                if reference_ids is None:reference_ids=ids
                assert ids==reference_ids
                batch_times.append([b['wall_s'] for b in a['batches']]);total_tokens.append(a['output_tokens'])
            panels.append(np.mean(batch_times,axis=0));tokens.append(float(np.mean(total_tokens)))
        for i in range(3):
            for k in ['prompt_sha256','target_revision','batch_size','max_new_tokens','seed','temperature','gpu_memory_utilization']:
                assert cells[i][1].get(k)==cells[i+3][1].get(k),k
        cost=costs[r['target'],r['arm']];gh=sum(cost.values());z=amortize(panels[:3],panels[3:],r['n'],gh)
        economics.append({k:r[k] for k in ['experiment','target','batch','arm','reference','n']}|cost|z|
                         dict(repaired_output_tokens_per_request=float(np.mean(tokens[:3])/r['n']),sources=r['sources']))
    result=dict(status='pilot',drift=stats,economics=economics,
                uncertainty='Drift: checkpoint bootstrap within family/cohort/method (10000 draws), conditional on archived per-checkpoint estimates; not measurement-error corrected or a causal estimate. Economics: 10000 paired process/query-batch draws, three warm repeats averaged; training seed 0 fixed, measured cost fixed; no training-seed uncertainty.',
                exclusions='All atlas points with archived A6 remain; T1 all and two explicitly labelled sensitivities. Tulu finite KL is conditional on common vocabulary. Collapsed RL kept in all analysis, omitted only in labelled sensitivity. Retention above one is retained.',
                provenance=sources)
    (out/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    text=['# REV5 CPU evidence — pilot','',result['uncertainty'],'',result['exclusions'],'',
          '| Cohort | Family | Drafter | Subset | Drift metric | n checkpoints | Spearman rho [95% CI] |','|---|---|---|---|---|---:|---|']
    for r in stats:
        val='undefined' if r['rho'] is None else f"{r['rho']:.3f} [{r['ci95'][0]:.3f}, {r['ci95'][1]:.3f}]"
        text.append(f"| {r['cohort']} | {r['family']} | {r['method']} | {r['subset']} | {r['metric']} | {r['n']} | {val} |")
    text+=['','## Measured-cost break-even','',
           'Warm steady occupancy, A40, seed-0 official 16k repairs. Data cost charged once to each alternative. Includes data generation and training, excludes engineering/search/evaluation and service startup. Requests inherit the fixed panel\'s capped workload, not arbitrary complete conversations. Infinity/unresolved bounds appear as null in JSON.','',
           '| Panel | Target | Arm / reference | n | Repair GPUh | GPU seconds saved/request [95% CI] | Requests to break even [95% CI] |','|---|---|---|---:|---:|---|---|']
    for r in economics:
        s=r['seconds_saved_per_request'];q=r['requests']
        def fmt(v):return 'unbounded' if v is None else f'{v:,.0f}'
        text.append(f"| {r['experiment']} | {r['target']} | {r['arm']} / {r['reference']} | {r['n']} | {r['gpu_hours']:.3f} | {s['mean']:.3f} [{s['ci95'][0]:.3f}, {s['ci95'][1]:.3f}] | {fmt(q['mean'])} [{fmt(q['ci95'][0])}, {fmt(q['ci95'][1])}] |")
    (out/'report.md').write_text('\n'.join(text)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.workspace,a.output)
