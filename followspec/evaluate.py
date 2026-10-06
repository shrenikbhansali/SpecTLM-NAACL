"""Print B2 evaluation plans and aggregate paired held-out evidence for Gate 3.

This module never launches jobs or makes the owner's framing decision.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import numpy as np
from scipy import stats
from atlas.paired_cells import read_cell,paired_values

ARMS=('FS','MVD','PO-D','PO-T')


def finite(values):
    x=np.asarray(values,dtype=float)
    if x.ndim!=1 or not len(x) or not np.isfinite(x).all():raise ValueError('need finite nonempty vector')
    return x


def median_interval(values,resamples=10000,seed=0):
    x=finite(values);rng=np.random.default_rng(seed)
    if resamples<100:raise ValueError('insufficient bootstrap resamples')
    medians=np.median(x[rng.integers(0,len(x),size=(resamples,len(x)))],axis=1)
    return np.quantile(medians,[.025,.975]).tolist()


def paired_summary(fs,control,base,resamples=10000,seed=0):
    x,y,b=map(finite,(fs,control,base))
    if not (len(x)==len(y)==len(b)) or np.any(b<=0):raise ValueError('invalid paired derivative arrays')
    delta=x-y;retention=x/b;tail=max(1,math.ceil(.1*len(x)))
    return dict(n_derivatives=len(x),median_gain=float(np.median(delta)),mean_gain=float(np.mean(delta)),
        median_gain_ci95=median_interval(delta,resamples,seed),win_rate=float(np.mean(delta>0)),
        worst_decile_retention=float(np.mean(np.sort(retention)[:tail])),worst_decile_n=tail,
        bootstrap_unit='derivatives after matched training-seed averaging',bootstrap_resamples=resamples)


def parent_tost(trained,frozen,margin=.02):
    x,b=map(finite,(trained,frozen))
    if len(x)!=len(b) or len(x)<2 or np.any(b<=0):raise ValueError('need at least2 paired independent training seeds')
    d=(x-b)/b;n=len(d);mean=float(d.mean());se=float(d.std(ddof=1)/np.sqrt(n))
    if se==0:
        lo=hi=mean;p_lower=0. if mean>-margin else 1.;p_upper=0. if mean<margin else 1.
    else:
        half=float(stats.t.ppf(.95,n-1))*se;lo,hi=mean-half,mean+half
        p_lower=float(stats.t.sf((mean+margin)/se,n-1));p_upper=float(stats.t.cdf((mean-margin)/se,n-1))
    return dict(n_training_seeds=n,df=n-1,mean_relative_change=mean,ci90=[lo,hi],margin=margin,
        p_lower=p_lower,p_upper=p_upper,equivalent=p_lower<.05 and p_upper<.05,
        inference_unit='paired training seeds; prompt observations are not independent training replicates')


def pin(value):
    if not re.fullmatch('[a-f0-9]{40}',value):raise ValueError('model revisions must be commit hashes')


def schedule(spec,output_root):
    pin(spec['base_revision']);plans=[];seen=set()
    for ck in spec['checkpoints']:
        pin(ck['revision'])
        if ck['arm'] not in (*ARMS,'Frozen'):raise ValueError('unknown arm')
        for target in spec['targets']:
            if target['pool'] not in ('test','base'):raise ValueError('held-out scheduling excludes bank targets')
            pin(target['revision'])
            for workload,prompt_file in target['workloads'].items():
                for k in spec['K']:
                    if k not in (2,4,8):raise ValueError('unsupported atlas K')
                    for role in ('parent','child'):
                        if target['pool']=='base' and role=='child':continue
                        frozen=ck['arm']=='Frozen';cell=('A00' if frozen else 'A01') if role=='parent' else ('A10' if frozen else 'A11')
                        derivative='base' if target['pool']=='base' else target['model_id']
                        key=(ck['arm'],ck['seed'],derivative,workload,k,cell)
                        if key in seen:raise ValueError('duplicate planned cell')
                        seen.add(key);suffix=hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
                        run_id=f"eval-{ck['arm']}-s{ck['seed']}-k{k}-{cell}-{suffix}";out=str(Path(output_root)/run_id)
                        parent=role=='parent';adapter=target.get('adapter') if not parent else None
                        model=spec['base_id'] if parent or adapter else target['model_id']
                        revision=spec['base_revision'] if parent or adapter else target['revision']
                        argv=['python','-m','atlas.run_cell','--target',model,'--target-revision',revision,
                            '--drafter',ck['model_id'],'--drafter-revision',ck['revision'],'--method',ck.get('method','eagle3'),
                            '--K',str(k),'--seed',str(spec.get('evaluation_seed',0)),
                            '--max-new-tokens',str(spec.get('max_new_tokens',512)),'--prompts',prompt_file,'--output',out]
                        if adapter:argv+=['--adapter',adapter,'--adapter-revision',target['revision']]
                        plans.append(dict(run_id=run_id,run_dir=out,arm=ck['arm'],seed=ck['seed'],derivative_id=derivative,
                            workload=workload,K=k,cell=cell,pool=target['pool'],prompt_file=prompt_file,argv=argv,
                            env={'VLLM_CACHE_ROOT':str(Path(out)/'vllm_cache')},launch=False))
    return plans


def load_measurements(index):
    rows=[];seen=set()
    for record in index:
        key=tuple(record[k] for k in ('arm','seed','derivative_id','workload','K','cell'))
        if key in seen:raise ValueError('duplicate measurement')
        seen.add(key)
        if record['pool'] not in ('test','base'):raise ValueError('bank result in held-out report')
        loaded=read_cell(record['run_dir']);cfg=loaded.pop('config');loaded.pop('results')
        if cfg['K']!=record['K']:raise ValueError('invalid cell config')
        pin(cfg['target_revision']);pin(cfg['drafter_revision'])
        target_identity={q:cfg.get(q) for q in ('target','target_revision','target_files_sha256','adapter_revision','adapter_files_sha256')}
        drafter_identity={q:cfg.get(q) for q in ('drafter','drafter_revision','drafter_files_sha256','method')}
        rows.append(record|loaded|dict(target_identity=target_identity,drafter_identity=drafter_identity))
    return rows


def aggregate(rows):
    groups=defaultdict(list);checkpoints={};parent_target=None;seen=set()
    for r in rows:
        if r['arm'] not in (*ARMS,'Frozen') or r['pool'] not in ('test','base'):raise ValueError('unknown arm or non-held-out pool')
        allowed=('A00','A10') if r['arm']=='Frozen' else ('A01','A11')
        if r['cell'] not in allowed or (r['pool']=='base' and r['cell'] not in ('A00','A01')):raise ValueError('invalid cell role')
        if (r['pool']=='base')!=(r['derivative_id']=='base'):raise ValueError('base/held-out identity mismatch')
        key=tuple(r[q] for q in ('K','workload','derivative_id','arm','seed','cell'))
        if key in seen:raise ValueError('duplicate cell')
        seen.add(key)
        ck=(r['arm'],r['seed'] if r['arm']!='Frozen' else 'frozen')
        if ck in checkpoints and checkpoints[ck]!=r['drafter_identity']:raise ValueError('checkpoint mismatch across cells')
        checkpoints[ck]=r['drafter_identity']
        if r['cell'] in ('A00','A01'):
            if parent_target is not None and parent_target!=r['target_identity']:raise ValueError('parent target mismatch')
            parent_target=r['target_identity']
        groups[(r['K'],r['workload'])].append(r)
    summaries=[];derivative_rows=[]
    for (k,workload),group in sorted(groups.items()):
        cells=defaultdict(dict)
        for r in group:cells[(r['derivative_id'],r['arm'],int(r['seed']))][r['cell']]=r
        targets=sorted({r['derivative_id'] for r in group if r['pool']=='test'})
        if not targets:raise ValueError('no held-out derivatives')
        common_seeds=None;retentions=[]
        for target in targets:
            seeds={seed for t,arm,seed in cells if t==target and arm=='FS'}
            if len(seeds)!=3:raise ValueError('Gate3 requires3 matched training seeds')
            if common_seeds is None:common_seeds=seeds
            if common_seeds!=seeds:raise ValueError('training seeds differ across derivatives')
            for arm in (*ARMS,'Frozen'):
                if {s for t,a,s in cells if t==target and a==arm}!=seeds:raise ValueError('unmatched arm/seed set')
            for seed in sorted(seeds):
                frozen_cells=cells[(target,'Frozen',seed)]
                if set(frozen_cells)!= {'A00','A10'}:raise ValueError('missing frozen target cells')
                frozen=frozen_cells['A00']
                if any(frozen_cells['A10'][q]!=frozen[q] for q in ('prompt_sha256','prompt_ids','settings')):raise ValueError('frozen controls not matched')
                for arm in ARMS:
                    entry=cells[(target,arm,seed)]
                    if set(entry)!={'A01','A11'}:raise ValueError('missing trained target cells')
                    for cell in ('A01','A11'):
                        candidate=entry[cell]
                        if any(candidate[q]!=frozen[q] for q in ('prompt_sha256','prompt_ids','settings')):raise ValueError('controls not matched')
                        expected=frozen_cells['A00' if cell=='A01' else 'A10']
                        if candidate['target_identity']!=expected['target_identity']:raise ValueError('paired target identity mismatch')
            def pairs(arm,left,right):
                return {str(seed):paired_values(cells[(target,arm,seed)][left],cells[(target,arm,seed)][right]) for seed in sorted(seeds)}
            frozen_pairs=pairs('Frozen','A00','A10')
            a00,a10=np.mean([p['values'] for p in frozen_pairs.values()],axis=0)
            for arm in ARMS:
                trained_pairs=pairs(arm,'A01','A11')
                a01,a11=np.mean([p['values'] for p in trained_pairs.values()],axis=0)
                retention_pairs={str(seed):paired_values(cells[(target,arm,seed)]['A11'],cells[(target,'Frozen',seed)]['A00']) for seed in sorted(seeds)}
                numerator,denominator=np.mean([p['values'] for p in retention_pairs.values()],axis=0)
                if arm=='FS':retentions.append(float(numerator/denominator))
                derivative_rows.append(dict(K=k,workload=workload,derivative_id=target,arm=arm,n_training_seeds=3,
                    A01=float(a01),A11=float(a11),A00=float(a00),A10=float(a10),retention=float(numerator/denominator),
                    pairing_A00_A10=json.dumps(frozen_pairs),pairing_A01_A11=json.dumps(trained_pairs),pairing_retention=json.dumps(retention_pairs),
                    run_ids=json.dumps([cells[(target,a,s)][c]['run_id'] for s in sorted(seeds) for a,cs in ((arm,('A01','A11')),('Frozen',('A00','A10'))) for c in cs])))
        comparisons={};comparison_pairing={}
        for arm in ARMS:
            if arm=='FS':continue
            fs_values=[];control_values=[];comparison_pairing[arm]={}
            for target in targets:
                pairs={str(seed):paired_values(cells[(target,'FS',seed)]['A11'],cells[(target,arm,seed)]['A11']) for seed in sorted(common_seeds)}
                fs,control=np.mean([p['values'] for p in pairs.values()],axis=0)
                fs_values.append(fs);control_values.append(control);comparison_pairing[arm][target]=pairs
            result=paired_summary(fs_values,control_values,np.ones(len(targets)),seed=0)
            # Gains and retention compare different cell pairs. Each ratio uses
            # its own paired numerator/denominator, never an independent macro.
            result['worst_decile_retention']=float(np.mean(np.sort(retentions)[:result['worst_decile_n']]))
            comparisons[arm]=result
        parent={};parent_seeds=sorted(common_seeds)
        for arm in ARMS:
            try:
                trained=[cells[('base',arm,s)]['A01'] for s in parent_seeds]
                frozen=[cells[('base','Frozen',s)]['A00'] for s in parent_seeds]
            except KeyError:raise ValueError('parent-retention cells missing')
            for t,b in zip(trained,frozen):
                if any(t[q]!=b[q] for q in ('prompt_sha256','prompt_ids','settings')):raise ValueError('parent controls not matched')
            pairs={str(seed):paired_values(t,b) for seed,t,b in zip(parent_seeds,trained,frozen)}
            parent[arm]=parent_tost([p['values'][0] for p in pairs.values()],[p['values'][1] for p in pairs.values()])
            parent[arm]['pairing']=pairs
        numerical_pass=all(r['median_gain_ci95'][0]>0 for r in comparisons.values()) and parent['FS']['equivalent']
        summaries.append(dict(K=k,workload=workload,comparisons=comparisons,comparison_pairing=comparison_pairing,parent_retention=parent,
            numerical_criteria_met=numerical_pass,owner_gate_decision='pending',source_run_ids=sorted(r['run_id'] for r in group)))
    return summaries,derivative_rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['plan','aggregate']);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--artifact-root');a=p.parse_args()
    data=json.loads(Path(a.input).read_text());out=Path(a.output)
    if a.mode=='plan':
        result=schedule(data,a.artifact_root or str(out.parent/'runs'))
        with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
        return
    measurements=load_measurements(data);summaries,rows=aggregate(measurements);out.mkdir(parents=True,exist_ok=False)
    with (out/'summary.json').open('x') as f:json.dump(summaries,f,indent=2);f.write('\n')
    with (out/'per_derivative.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    fields=['K','workload','derivative_id','pool','arm','seed','cell','value','n_prompts','n_valid','n_zero_step','run_id','run_dir','prompt_sha256']
    with (out/'per_seed.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(measurements)
    (out/'provenance.json').write_text(json.dumps(dict(input_index_sha256=hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),engine_version='0.31.0',
        source_run_ids=sorted(r['run_id'] for r in measurements)),indent=2)+'\n')
    text='# Gate 3 — evidence for owner review\n\nD32: every direct comparison uses shared nonzero-step prompt IDs; counts and excluded IDs per derivative and seed are in per_derivative.csv and summary.json. Empty intersections block the report. No framing decision is made by this report. Intervals resample derivatives after averaging 3 training seeds. Parent TOST uses independent training seeds, relative margin 2%. Workloads and K are reported separately; the owner chooses the prespecified gate comparison.\n'
    for s in summaries:
        text+=f"\n## K={s['K']}, workload={s['workload']}\n\n| FS versus | n derivatives | Median gain | Bootstrap95% CI | Win rate | Worst-decile retention |\n| --- | --- | --- | --- | --- | --- |\n"
        for arm,r in s['comparisons'].items():text+=f"| {arm} | {r['n_derivatives']} | {r['median_gain']:.6f} | {r['median_gain_ci95']} | {r['win_rate']:.4f} | {r['worst_decile_retention']:.6f} |\n"
        text+=f"\nFS parent TOST: {json.dumps(s['parent_retention']['FS'])}. Numerical criteria met: {s['numerical_criteria_met']}; owner decision pending. Source run IDs and all arms' parent tests are in summary.json.\n"
    (out/'GATE-3.md').write_text(text)

if __name__=='__main__':main()
