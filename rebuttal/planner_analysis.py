"""D61 report additions, independently reduced from immutable raw evidence."""
import argparse
import json
from pathlib import Path
import numpy as np
from rebuttal.crossover import reduce_cells
from rebuttal.reduce_e45 import acceptance_contrast, rows, sha, FROZEN


def deployment_ratio(cells):
    x=np.asarray(cells,dtype=float)
    if x.ndim!=2 or x.shape[1]!=4 or len(x)==0 or not np.isfinite(x).all():raise ValueError('expected finite paired a,b,c,d rows')
    idx=np.random.default_rng(0).integers(len(x),size=(10000,len(x)))
    boot=x[idx].mean(1);mean=x.mean(0);den=boot[:,3]-boot[:,0];valid=den!=0
    ratio=(boot[valid,3]-boot[valid,1])/den[valid]
    ci=np.quantile(den,[.025,.975]).tolist()
    return {'mean':float((mean[3]-mean[1])/(mean[3]-mean[0])) if mean[3]!=mean[0] else None,
            'ci95':np.quantile(ratio,[.025,.975]).tolist() if len(ratio) else None,
            'undefined_draws':int((~valid).sum()),'denominator_ci95':ci,'denominator_ci_crosses_zero':ci[0]<=0<=ci[1]}


def e1(root):
    stage=root/'artifacts/P2_crossover_20261008_0348/full64';result=[]
    for spec in json.loads((stage/'index.json').read_text()):
        if spec['origin']!='child' or 'Tulu' in spec['model']['id']:continue
        raw=stage/'runs'/spec['run_id']/'per_prompt.jsonl';rr=rows(raw)
        if len(rr)!=64 or len({r['prompt_id'] for r in rr})!=64:raise ValueError('unpaired E1 contexts')
        cells=np.asarray([r['matrix'] for r in rr]).reshape(64,4)
        result.append({'model':spec['model']['id'],'n':64,'source':str(raw),'sha256':sha(raw),
                       'cells':reduce_cells(cells),'deployment_ratio':deployment_ratio(cells)})
    return result


def e2(root):
    prior=json.loads((root/'rebuttal/E2/reduction_20261125_2010/results.json').read_text());result=[]
    for target in [0,1]:
        for panel in ['speed128','math128']:
            sources=[r for r in prior['sources'] if r['target']==target and r['benchmark']==panel]
            def load(variant):
                rr=[r for r in sources if r['variant']==variant];loaded={}
                for r in rr:
                    raw=root/'rebuttal/runs'/r['run']/'cell/per_prompt.jsonl'
                    if sha(raw)!=r['raw_sha256']:raise ValueError('E2 evidence changed')
                    loaded[r['seed']]=rows(raw)
                if set(loaded)!={0,1,2}:raise ValueError('incomplete E2 seeds')
                return loaded
            if len({r['prompt_sha256'] for r in sources})!=1:raise ValueError('unpaired E2 prompts')
            ref=load('lora-all')
            for variant in ['lora-all','lora-fc_only','lora-no_fc']:
                result.append({'target':target,'benchmark':panel,'variant':variant,'sources':sources,
                               **acceptance_contrast(ref,load(variant),4,4)})
    return result


def e3(root):
    def remap(p):return Path(str(p).replace('/home/heck2/sbhansali8/SpecTLM',str(root)))
    assembly=root/'artifacts/P3_E5c64k_20261009_1420/sealed-generic64k/assembly.json'
    a=json.loads(assembly.read_text());old=remap(a['reused16000'])/'assembly.json';b=json.loads(old.read_text());sources=[]
    for record in a['sources']+b['sources']:
        directory=remap(record.get('path',record.get('directory')));p=directory/'results.json'
        if not p.exists():sources.append({'path':str(p),'missing':True});continue
        r=json.loads(p.read_text())
        if r!=record['results'] or r['per_prompt_sha256']!=record['sha256']:raise ValueError('64k source results mismatch')
        c=json.loads((directory/'config.json').read_text())
        sources.append({'path':str(p),'sha256':sha(p),'n':r['n'],'wall_s':r['wall_s'],'generation_gpu_h':r['wall_s']/3600,
                        'gpu_type':c.get('gpu_type',c.get('gpu','not recorded in cell config'))})
    known=[s for s in sources if not s.get('missing')];missing=[s for s in sources if s.get('missing')]
    cost=sum(s['generation_gpu_h'] for s in known) if not missing else None
    if cost is not None and (sum(s['n'] for s in known)!=64000 or abs(cost-a['generation_gpu_hours'])>1e-10):raise ValueError('generation accounting mismatch')
    run=root/'rebuttal/runs/E3b_t0_scratch20ep_s0_gcc13';cfg=json.loads((run/'cell/config.json').read_text());checkpoints=[]
    for p in sorted((run/'cell').glob('export-*/repair_provenance.json'),key=lambda p:int(p.parent.name.split('-')[-1])):
        r=json.loads(p.read_text());step=r['step'];epoch=cfg['epoch_end_steps'].index(step)+1
        record={'epoch':epoch,'step':step,'train_gpu_h_cumulative':r['elapsed_s']/3600,'generation_gpu_h':cost,
                'total_gpu_h':r['elapsed_s']/3600+cost if cost is not None else None,'source':str(p),'sha256':sha(p),'acceptance':{}}
        for panel in ['speed128','math128']:
            evaluation=root/'rebuttal/runs'/f'{run.name}_all_step{step}_{panel}'
            if not (evaluation/'metrics.json').exists() or json.loads((evaluation/'metrics.json').read_text())['exit_code']!=0:continue
            ec=json.loads((evaluation/'cell/config.json').read_text());raw=evaluation/'cell/per_prompt.jsonl'
            if ec.get('frozen_harness_commit',ec.get('code_commit'))!=FROZEN or ec['engine_version']!='0.31.0' or ec['K']!=4:raise ValueError('nonfrozen scratch acceptance')
            rr=rows(raw);record['acceptance'][panel]={'source':str(raw),'sha256':sha(raw),**acceptance_contrast({0:rr},{0:rr},4,4)}
        checkpoints.append(record)
    return {'generation_gpu_h':cost,'generation_sources':sources,'checkpoints':checkpoints,
            'cost_scope':'sum of recorded successful generation wall_s on one A40 per shard; training is cumulative trainer elapsed_s on one A40 including initialization/checkpoint exports, excluding outer launch wrapper, acceptance and failed attempts; no inferred missing times',
            'source_mixture':'existing16k Alpaca +48k Alpaca/Dolly extension; continuous20epoch cosine schedule; mandatory stop Nov28 noon ET'}


def e4c(root):
    result=[];pending=[];configs={}
    for subset in ['selected','random']:
        for panel in ['speed128','math128']:
            arms={};sources=[]
            for method in ['eda50m','interface']:
                seeds={}
                for seed in [0,1]:
                    name=f'E4_t0_eda_w4096_selected8k_s{seed}' if method=='eda50m' and subset=='selected' else f'E4c_t0_{method}_{subset}8k_s{seed}'
                    run=root/'rebuttal/runs'/(name+'_'+panel)
                    if not (run/'metrics.json').exists() or json.loads((run/'metrics.json').read_text())['exit_code']!=0:
                        pending.append(run.name);continue
                    raw=run/'cell/per_prompt.jsonl';c=json.loads((run/'cell/config.json').read_text())
                    if c.get('frozen_harness_commit',c.get('code_commit'))!=FROZEN or c['engine_version']!='0.31.0' or c['K']!=4 or c['temperature']!=0 or c['max_new_tokens']!=512 or c['batch_size']!=8:raise ValueError('changed E4c protocol')
                    seeds[seed]=rows(raw);sources.append({'run':run.name,'raw_sha256':sha(raw),'prompt_sha256':c['prompt_sha256']})
                    configs[subset,method,seed]=json.loads((root/'rebuttal/runs'/name/'cell/config.json').read_text())
                arms[method]=seeds
            if sources and len({r['prompt_sha256'] for r in sources})!=1:raise ValueError('unpaired E4c renders')
            for method,rr in arms.items():
                if rr:result.append({'subset':subset,'benchmark':panel,'method':method,'kind':'mean','sources':sources,**acceptance_contrast(rr,rr,4,4)})
            shared=set(arms['eda50m'])&set(arms['interface'])
            if shared:
                for seed in shared:
                    left,right=[configs[subset,m,seed] for m in ['eda50m','interface']]
                    for key in ['data_sha256','seed','steps','batch_tokens','batch_plan','lr','ttt_steps','target','optimizer','weight_decay','scheduler','warmup_ratio','scratch','drafter']:
                        if left.get(key)!=right.get(key):raise ValueError('E4c training mismatch '+key)
                result.append({'subset':subset,'benchmark':panel,'kind':'paired interface minus EDA50M','sources':sources,**acceptance_contrast(arms['eda50m'],arms['interface'],4,4)})
    cost=0
    for p in (root/'rebuttal/runs').glob('E4c*/metrics.json'):cost+=json.loads(p.read_text())['gpu_hours']
    return {'results':result,'pending':pending,'completed_gpu_hours_including_failures':cost,'budget_gpu_hours':15}


def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    prior=json.loads((a.workspace/'rebuttal/E45_verify_20261126_1535/results.json').read_text())
    small=[r for r in prior['paired'] if r['reference']=='E4_t0_eda_w4096_selected8k' and r['candidate']=='E4b_t0_full_selected8k']
    result={'status':'pilot','E1':e1(a.workspace),'E2_restoration':e2(a.workspace),'E3':e3(a.workspace),'E4_small_vs_full':small,'E4c':e4c(a.workspace)}
    (a.output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'E1':len(result['E1']),'E2':len(result['E2_restoration']),'E3':result['E3']['checkpoints'],'E4c_pending':result['E4c']['pending']},indent=2))


if __name__=='__main__':main()
