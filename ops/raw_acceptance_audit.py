"""Independent re-derivation from raw per-step records. No followspec imports."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics as st
import numpy as np


def read(p): return json.loads(Path(p).read_text())
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    with Path(p).open('x') as f: json.dump(x,f,indent=2,allow_nan=False);f.write('\n')


def prompt_metrics(r,k):
    accepted=r['per_step_accepted'];drafted=r['per_step_drafted']
    if len(accepted)!=len(drafted) or any(type(a)!=int or type(d)!=int or not 0<=a<=d<=k or d==0 for a,d in zip(accepted,drafted)):
        raise ValueError('invalid raw counters')
    tau=1+sum(accepted)/len(accepted) if accepted else None
    if r['acceptance_length']!=tau:raise ValueError('stored acceptance differs from raw counters')
    nums=[sum(a>=i+1 for a in accepted) for i in range(k)]
    dens=[sum(a>=i and d>=i+1 for a,d in zip(accepted,drafted)) for i in range(k)]
    for name,expected in [('per_position_accepted',nums),('per_position_opportunities',dens)]:
        if name in r and r[name]!=expected:raise ValueError('stored position counters differ')
    return dict(tau=tau,conditional=[a/b if b else None for a,b in zip(nums,dens)],
                nums=nums,dens=dens,length=len(r['completion_token_ids']))


def load(run):
    run=Path(run);cfg=read(run/'config.json');result=read(run/'results.json')
    if cfg['engine_version']!='0.31.0' or cfg['code_dirty'] or cfg['temperature']!=0 or cfg['seed']!=0:
        raise ValueError('wrong engine/code/decoding')
    rows={}
    for line in (run/'per_prompt.jsonl').read_text().splitlines():
        r=json.loads(line)
        if r['prompt_id'] in rows:raise ValueError('duplicate raw prompt')
        rows[r['prompt_id']]=prompt_metrics(r,cfg['K'])
    if len(rows)!=cfg['n'] or len(rows)!=result['n_total']:raise ValueError('incomplete raw file')
    values=[r['tau'] for r in rows.values() if r['tau'] is not None]
    macro=st.mean(values) if values else None
    if macro!=result['macro_acceptance_length']:raise ValueError('cell macro differs from raw file')
    return cfg,rows


def paired(a,b,*,resamples=2000):
    if set(a)!=set(b):raise ValueError('prompt identities differ')
    ids=sorted(a);k=len(next(iter(a.values()))['conditional'])
    valid=[i for i in ids if a[i]['tau'] is not None and b[i]['tau'] is not None]
    tau=[st.mean(x[i]['tau'] for i in valid) for x in (a,b)] if valid else [None,None]
    rates=[];ret=[];ns=[];cis=[];micro=[]
    for j in range(k):
        good=[i for i in ids if a[i]['conditional'][j] is not None and b[i]['conditional'][j] is not None]
        ns.append(len(good))
        if not good: rates.append([None,None]);ret.append(None);cis.append(None);micro.append([None,None]);continue
        vals=np.array([[x[i]['conditional'][j] for i in good] for x in (a,b)])
        means=vals.mean(axis=1);rates.append(means.tolist());ret.append(float(means[1]/means[0]) if means[0] else None)
        micro.append([sum(x[i]['nums'][j] for i in good)/sum(x[i]['dens'][j] for i in good) for x in (a,b)])
        samples=np.random.default_rng(20261007).integers(0,len(good),size=(resamples,len(good)))
        boots=vals[:,samples].mean(axis=2);nz=boots[0]>0
        cis.append(np.quantile(boots[1,nz]/boots[0,nz],[.025,.975]).tolist() if nz.all() else None)
    return dict(n_total=len(ids),n_tau=len(valid),tau_A00=tau[0],tau_A10=tau[1],tau_retention=tau[1]/tau[0] if tau[0] else None,
                position_macro_A00_A10=rates,position_retention=ret,position_n=ns,position_retention_ci95=cis,
                position_micro_A00_A10=micro,
                mean_position_retention=st.mean(v for v in ret if v is not None) if any(v is not None for v in ret) else None,
                median_output_length_A00=st.median(a[i]['length'] for i in ids),median_output_length_A10=st.median(b[i]['length'] for i in ids),
                max_length_count_A00=sum(a[i]['length']==512 for i in ids),max_length_count_A10=sum(b[i]['length']==512 for i in ids))


def matched_configs(a,b,*,same_drafter=True):
    fields=['K','seed','engine_version','code_commit','source_sha256','prompt_sha256','temperature','top_p','batch_size','max_new_tokens',
            'max_model_len','gpu_memory_utilization','use_prompt_token_ids','enable_prefix_caching','enable_lora','max_lora_rank']
    if same_drafter:fields+=['drafter','drafter_revision','drafter_files_sha256']
    for k in fields:
        if a.get(k)!=b.get(k):raise ValueError('unmatched setting: '+k)


def bootstrap_median(values):
    if not values:return None
    v=np.array(values);rng=np.random.default_rng(20261007)
    return np.quantile(np.median(v[rng.integers(0,len(v),size=(10000,len(v)))],axis=1),[.025,.975]).tolist()


def t1(index, out, partial=False):
    records=read(index);groups=defaultdict(dict);pending=[];hashes={};allrows=[]
    for r in records:
        if not (Path(r['run_dir'])/'results.json').is_file():pending.append(r['run_id']);continue
        key=(r['model_id'],r['method'])
        if r['cell'] in groups[key]:raise ValueError('duplicate cell')
        cfg,rows=load(r['run_dir'])
        if len(rows)!=128 or cfg['code_commit']!='6da2e4265c0398ec0de5affaf23b0bd1df0be445':raise ValueError('T1 pin/count mismatch')
        if cfg['prompt_sha256']!=digest(r['prompt_file']):raise ValueError('prompt content changed')
        groups[key][r['cell']]=(r,cfg,rows)
        for name in ['config.json','results.json','per_prompt.jsonl']:
            p=Path(r['run_dir'])/name;hashes[str(p)]=digest(p)
    if pending and not partial:raise ValueError(f'{len(pending)} cells pending')
    for (model,method),cells in sorted(groups.items()):
        if set(cells)!={'A00','A10'}:continue
        r,a,ar=cells['A00'];_,b,br=cells['A10'];matched_configs(a,b)
        allrows.append(dict(model=model,method=method,base=r['base'],hypothesis=r['hypothesis'],K=r['K'],**paired(ar,br)))
    models=defaultdict(dict)
    for r in allrows:models[r['model']][r['method']]=r
    hits=defaultdict(list);mean_hits=defaultdict(list)
    for model,rows in models.items():
        if set(rows)!={'eagle3','dflash'}:continue
        h=rows['eagle3']['hypothesis']
        if all(r['position_retention'][0] is not None and r['position_retention'][0]<=.8 for r in rows.values()):hits[h].append(model)
        if all(r['mean_position_retention'] is not None and r['mean_position_retention']<=.8 for r in rows.values()):mean_hits[h].append(model)
    result=dict(status='pilot',n_completed=len(records)-len(pending),n_planned=len(records),pending=pending,rows=allrows,
                position1_both_drafters_hits=dict(hits),mean_position_both_drafters_hits=dict(mean_hits),
                uncertainty='Paired prompt bootstrap, 2000 draws; descriptive, conditional on fixed SPEED128 and one seed; no multiplicity correction.',
                decision_caveat='Numeric screen only; realistic class, checkpoint independence, plausible mechanism and paper framing remain owner decisions. Keep all failures and regressions.',
                metric='Macro conditional acceptance over shared nonzero-opportunity prompts at each position; A10/A00. Micro rates also reported. Length is descriptive, not matched trajectories.')
    out.mkdir(parents=True,exist_ok=False);write(out/'results.json',result);write(out/'config.json',dict(index=str(index),index_sha256=digest(index),inputs_sha256=hashes,analysis_source_sha256=digest(__file__)))
    return result


def m4(report,out):
    records=read(report/'index_k4.json');expected=read(report/'results.json');cells={};hashes={}
    for r in records:
        key=(r['workload'],r['derivative_id'],r['arm'],r['cell'])
        if key in cells:raise ValueError('duplicate cell')
        cells[key]=load(r['run_dir'])
        for n in ['config.json','results.json','per_prompt.jsonl']:
            p=Path(r['run_dir'])/n;hashes[str(p)]=digest(p)
    result=[]
    for workload in sorted({r['workload'] for r in records}):
        targets=sorted({r['derivative_id'] for r in records if r['workload']==workload and r['derivative_id']!='base'})
        per=[]
        for target in targets:
            ac,a=cells[workload,target,'Frozen','A00'];bc,b=cells[workload,target,'Frozen','A10'];matched_configs(ac,bc)
            posids=[i for i in a if a[i]['conditional'][0] is not None and b[i]['conditional'][0] is not None]
            p0=st.mean(a[i]['conditional'][0] for i in posids) if posids else 0
            ret=st.mean(b[i]['conditional'][0] for i in posids)/p0 if p0 else None
            fsconfig,fs=cells[workload,target,'FS','A11'];gains={};ns={}
            for arm in ['Frozen','MVD','PO-D','PO-T']:
                cc,c=cells[workload,target,arm,'A10' if arm=='Frozen' else 'A11'];matched_configs(fsconfig,cc,same_drafter=False)
                if set(fs)!=set(c):raise ValueError('comparison IDs differ')
                ids=[i for i in fs if fs[i]['tau'] is not None and c[i]['tau'] is not None]
                gains[arm]=st.mean(fs[i]['tau'] for i in ids)-st.mean(c[i]['tau'] for i in ids);ns[arm]=len(ids)
            per.append(dict(target=target,frozen_position1_retention=ret,position1_n=len(posids),degraded_tail=ret is not None and ret<.95,gains=gains,n_pairwise=ns))
        summaries={}
        for subset in ['all','degraded_tail']:
            selected=per if subset=='all' else [r for r in per if r['degraded_tail']]
            summaries[subset]={}
            for arm in ['Frozen','MVD','PO-D','PO-T']:
                v=[r['gains'][arm] for r in selected]
                summaries[subset][arm]=dict(n_targets=len(v),median_gain=st.median(v) if v else None,mean_gain=st.mean(v) if v else None,
                    wins=sum(x>0 for x in v),ci95_targets_conditional_on_seed=bootstrap_median(v))
                if subset=='all':
                    exp=next(w for w in expected['workloads'] if w['workload']==workload)['comparisons'][arm]
                    if not math.isclose(exp['median_gain'],st.median(v),abs_tol=1e-12):raise ValueError('headline mismatch')
        result.append(dict(workload=workload,subsets=summaries,per_target=per))
    out.mkdir(parents=True,exist_ok=False)
    value=dict(n_cells=len(cells),workloads=result,status='pilot',gate_certified=False,headline_verified=True,
               tail_rule='Frozen macro first-position conditional acceptance A10/A00 < 0.95, separately per workload, pairwise shared nonzero prompts.',
               uncertainty='10,000 target bootstrap resamples conditional on single seed; no training-seed uncertainty; exploratory subset.')
    write(out/'results.json',value);write(out/'config.json',dict(report=str(report),inputs_sha256=hashes,analysis_source_sha256=digest(__file__)))
    return value


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['t1','m4']);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--partial',action='store_true');a=p.parse_args()
    result=t1(Path(a.input),Path(a.output),a.partial) if a.mode=='t1' else m4(Path(a.input),Path(a.output))
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','workloads']},indent=2))


if __name__=='__main__':main()
