"""D-39 matched K8 operations, using the unchanged frozen evaluation harness."""
import argparse
import copy
from datetime import datetime,timezone
import fcntl
import importlib.util
import json
from pathlib import Path
import time
from ops.method_recovery import read,lines,sha,write,frozen_modules,preflight,append_jobs,retry_plan,apply_overlay


def key(r):return tuple(r[k] for k in ('seed','derivative_id','workload','cell','pool'))


def k8_job(record,job,output):
    if record['K']!=4 or record['argv'][record['argv'].index('--K')+1]!='4':raise ValueError('K4 source required')
    args=job['args'];split=args.index('--');cmd=args[split+1:]
    if [v for i,v in enumerate(cmd) if not(i==1 and v=='-u')]!=record['argv']:raise ValueError('source launcher command differs')
    if job['name']!=record['run_id'] or args[args.index('--k')+1]!='4':raise ValueError('source job identity differs')
    r=copy.deepcopy(record);j=copy.deepcopy(job);name='d39-k8-'+record['run_id'].replace('-k4-','-k8-');dest=str(Path(output)/'runs'/name)
    r.update(K=8,run_id=name,run_dir=dest);r['argv'][r['argv'].index('--K')+1]='8';r['argv'][r['argv'].index('--output')+1]=dest
    r['env']['VLLM_CACHE_ROOT']=str(Path(dest)/'vllm_cache')
    j['name']=name;a=j['args'];a[a.index('--k')+1]='8';a[a.index('--tag')+1]=name
    a[a.index('--K',split+1)+1]='8';a[a.index('--output',split+1)+1]=dest
    return r,j


def matched_indexes(base,variants):
    controls=[r for r in base if r['arm']!='FS'];reference=[r for r in base if r['arm']=='FS']
    if {r['arm'] for r in base}!={'FS','MVD','PO-D','PO-T','Frozen'} or any(r['K']!=8 for r in base):raise ValueError('matched K8 base matrix required')
    indexes={'010':base}
    if set(variants)!={'000','003','030'}:raise ValueError('matched approved lambda variants required')
    for label,fs in variants.items():
        if len(fs)!=len(reference) or {key(r) for r in fs}!={key(r) for r in reference} or any(r['K']!=8 or r['arm']!='FS' for r in fs):raise ValueError('matched FS cells required')
        indexes[label]=controls+fs
    return indexes


def prepare(a,m):
    out=Path(a.output).resolve();source=Path(a.stress_prepared);lw=Path(a.lambda_watch);checked=m['followspec.production_pipeline'].checked_stage
    base,cfg=checked(source/'evaluation');base_records=read(base/'index_k4.json');sources={'010':(base,base_records)}
    proof={str(base/'stage_files.json'):sha(base/'stage_files.json')}
    for label in ('000','003','030'):
        stage,scfg=checked(lw/label/'evaluation')
        if scfg['targets_sha256']!=cfg['targets_sha256'] or scfg['prompt_sha256']!=cfg['prompt_sha256']:raise ValueError('lambda target panel changed')
        sources[label]=(stage,[r for r in read(stage/'index_k4.json') if r['arm']=='FS'])
        proof[str(stage/'stage_files.json')]=sha(stage/'stage_files.json')
    rows={};jobs=[]
    for label,(stage,records) in sources.items():
        byname={j['name']:j for j in lines(stage/'effective_jobs.jsonl')};rows[label]=[]
        for r in records:
            rr,jj=k8_job(r,byname[r['run_id']],out);rows[label].append(rr);jobs.append(jj)
    indexes=matched_indexes(rows['010'],{k:v for k,v in rows.items() if k!='010'})
    if any(len(v)!=70 for v in indexes.values()) or len(jobs)!=112 or len({j['name'] for j in jobs})!=112:raise ValueError('complete fixed six-condition K8 panel required')
    out.mkdir(parents=True,exist_ok=False)
    for label,index in indexes.items():write(out/('index_'+label+'.json'),index)
    write(out/'jobs.json',jobs)
    write(out/'config.json',vars(a)|dict(input_sha256=proof,operation_source_sha256=sha(__file__),decision_id='D-39',K=8,n_unique_jobs=112,training_launched=False))
    preflight(jobs,Path(a.frozen_code),out/'preflight')
    write(out/'prepared_sha256.json',{str(p):sha(p) for p in [out/'config.json',out/'jobs.json',out/'preflight/results.json',*[out/('index_'+k+'.json') for k in indexes]]})
    return out


def summarize(records,m,quality):
    rows=m['followspec.evaluate'].load_measurements(records);pair=m['followspec.pilot_report'].paired_values
    if any(r['K']!=8 or r['seed']!=0 for r in rows):raise ValueError('K8 seed0 required')
    by={(r['derivative_id'],r['workload'],r['arm'],r['cell']):r for r in rows};result=[]
    for target,workload in sorted({(r['derivative_id'],r['workload']) for r in rows if r['pool']=='test'}):
        parent=by[target,workload,'Frozen','A00'];child=by[target,workload,'Frozen','A10'];fp=pair(parent,child);comparisons={};retention={}
        fs=by[target,workload,'FS','A11']
        for arm in ('Frozen','MVD','PO-D','PO-T'):
            other=by[target,workload,arm,'A10' if arm=='Frozen' else 'A11']
            if fs['target_identity']!=other['target_identity']:raise ValueError('comparison target identity differs')
            p=pair(fs,other);comparisons[arm]=dict(gain=p['values'][0]-p['values'][1],paired=p,uncertainty=quality.acceptance_interval(fs,other))
        for arm in ('FS','MVD','PO-D','PO-T'):
            p=by[target,workload,arm,'A01']
            if p['target_identity']!=parent['target_identity']:raise ValueError('parent target differs')
            v=pair(p,parent);retention[arm]=v|dict(relative_change=v['values'][0]/v['values'][1]-1)
        result.append(dict(target=target,workload=workload,frozen_pair=fp,frozen_retention=fp['values'][1]/fp['values'][0],
            frozen_uncertainty=quality.acceptance_interval(parent,child),fs_vs_controls=comparisons,parent_retention=retention))
    return dict(status='pilot',K=8,n_training_seeds=1,n_conditions=len(result),n_training_trajectories=len({r['workload'] for r in result}),rows=result,
        gate_certified=False,confirmation_evaluated=False,caveat='All fixed discovery conditions; shared target trajectories and prompts. Paired prompt uncertainty only; no compilation/seed uncertainty or multiple-comparison adjustment. K4 quality remains a separate diagnostic.')


def watch(out,m):
    cfg=read(out/'config.json');code=Path(cfg['frozen_code']);handle=(out/'watch.lock').open('a+');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for path,h in read(out/'prepared_sha256.json').items():
        if sha(path)!=h:raise ValueError('prepared K8 plan changed')
    for path,h in cfg['input_sha256'].items():
        if sha(path)!=h:raise ValueError('source stage changed')
    spec=importlib.util.spec_from_file_location('d39_k8_quality',Path(__file__).resolve().parents[1]/'followspec/stress_quality.py')
    quality=importlib.util.module_from_spec(spec);spec.loader.exec_module(quality)
    indexes={label:read(out/('index_'+label+'.json')) for label in ('000','003','010','030')};jobs=read(out/'jobs.json');byjob={j['name']:j for j in jobs}
    unique={r['run_id']:r for rows in indexes.values() for r in rows};overlays={p.stem[len('overlay-'):]:read(p) for p in out.glob('overlay-*.json')};blocked=set();done={l for l in indexes if (out/('report_'+l)/'results.json').is_file()}
    def event(**row):
        with (out/'events.jsonl').open('a') as f:f.write(json.dumps(row|dict(time=datetime.now(timezone.utc).isoformat()))+'\n')
    event(event='dispatch',n_added=append_jobs(cfg['dispatch_jobs'],jobs))
    while len(done)<len(indexes):
        launches={e['name']:e for e in lines(cfg['queue_log']) if e.get('event')=='launched'}
        for original,r in unique.items():
            active=overlays.get(original,{}).get('record',r);launch=launches.get(active['run_id'])
            if original in blocked or not (Path(active['run_dir'])/'failure.json').exists() or not launch or not (Path(launch['out_dir'])/'exit_code').is_file():continue
            try:
                rr,jj,proof=retry_plan(active,byjob[original],launch['out_dir'],out/'retries',attempt=2 if original in overlays else 1,expected_prompt_sha=sha(r['prompt_file']),expected_source_sha=sha(code/'atlas/run_cell.py'))
                preflight([jj],code,out/('preflight-'+rr['run_id']));overlay=dict(record=rr,job=jj,proof=proof);write(out/('overlay-'+original+'.json'),overlay)
                overlays[original]=overlay;append_jobs(cfg['dispatch_jobs'],[jj]);event(event='collision_retry',original=original)
            except ValueError as e:blocked.add(original);event(event='blocked',original=original,error=str(e))
        for label,records in indexes.items():
            if label in done:continue
            active=apply_overlay(records,{k:v for k,v in overlays.items() if k in {r['run_id'] for r in records}})
            if any(not (Path(r['run_dir'])/'results.json').is_file() for r in active):continue
            result=summarize(active,m,quality);dest=out/('report_'+label);dest.mkdir();write(dest/'index.json',active)
            proof=dict(plan_sha256=sha(out/'prepared_sha256.json'),quality_source_sha256=sha(quality.__file__),frozen_commit=cfg['frozen_commit'],lambda_value=int(label)/100,
                inputs_sha256={str(Path(r['run_dir'])/n):sha(Path(r['run_dir'])/n) for r in active for n in ('config.json','results.json','per_prompt.jsonl')})
            write(dest/'config.json',proof);write(dest/'results.json',result)
            write(dest/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title='D-39 K8 lambda '+label,landed=str(datetime.now().date()),status='pilot',what_why='Matched K8 stress comparison',new='K-only follow-up; no new training',artifacts=str(dest),config_results=dict(config=proof,results=result),caveats=result['caveat']))
            done.add(label);event(event='report_ready',label=label)
        if len(done)<len(indexes):time.sleep(60)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--resume');p.add_argument('--prepare-only',action='store_true')
    for name in ('stress-prepared','lambda-watch','output','frozen-code','frozen-commit','dispatch-jobs','queue-log'):p.add_argument('--'+name)
    a=p.parse_args()
    if a.resume:
        out=Path(a.resume).resolve();cfg=read(out/'config.json');m=frozen_modules(Path(cfg['frozen_code']),cfg['frozen_commit'])
    else:
        if any(getattr(a,k) is None for k in ('stress_prepared','lambda_watch','output','frozen_code','frozen_commit','dispatch_jobs','queue_log')):p.error('all preparation arguments required')
        m=frozen_modules(Path(a.frozen_code),a.frozen_commit);out=prepare(a,m)
    if not a.prepare_only:watch(out,m)


if __name__=='__main__':main()
