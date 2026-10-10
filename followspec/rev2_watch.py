"""Publish frozen evaluations only after completed, scope-audited D54 training."""
import argparse,copy,json,time
from pathlib import Path
from followspec.review_followup import parts,replace,publish
from followspec.rev2_panels import eval_job
from ops.track_t import WS,DISPATCH,lines,write

def sweep(stage,panels):
    d={j['name']:j for j in lines(DISPATCH)};pending=0
    for r in json.loads((stage/'plan.json').read_text()):
        if r.get('kind')!='train':continue
        root=Path(r['run_dir']);dest=stage/('publish-eval-'+r['name'])
        if (dest/'published.json').exists():continue
        if dest.exists():raise RuntimeError('Incomplete publication needs investigation: '+str(dest))
        if not (root/'results.json').exists():pending+=1;continue
        cfg=json.loads((root/'config.json').read_text());result=json.loads((root/'results.json').read_text());proof=json.loads((root/'parameters.json').read_text())
        if r.get('expected_trainable') is not None:assert proof['trainable_parameters']==r['expected_trainable'],r
        assert result['steps']==cfg['steps'] and result['n']==cfg['n']
        export=Path(result['exports'][-1]);assert (export/'repair_provenance.json').exists()
        ready=[];records=[];t=r['target']
        for w in r['workloads']:
            source=d['P3-D48-g2-fc-'+('math64' if w.startswith('math') else w)] if t==2 else d[f'FIX24-official-t{t}-16k-fc-s{4477 if t==0 else 2625}-'+('math64' if w.startswith('math') else w)]
            _,ii=parts(source);prompts=Path(ii[ii.index('--prompts')+1]);cap=512
            if w=='math500':prompts=WS/'artifacts/P3_D50_20261009_0200/math500/prompts.jsonl' if t==0 else panels/f'math500-t{t}.jsonl'
            if w.startswith('math32-'):prompts=WS/f'artifacts/REV1_20261010_0130/math32-t{t}.jsonl';cap=int(w.split('-')[1])
            name=r['name']+'-'+w;out=stage/'eval'/name;j=eval_job(source,name,out,prompts);o,i=parts(j)
            for a,f,g in [(o,'--drafter-model','--drafter-rev'),(i,'--drafter','--drafter-revision')]:replace(a,f,export);replace(a,g,cfg['code_commit'])
            replace(i,'--max-new-tokens',cap)
            if cap>512:replace(i,'--max-model-len',12288)
            j['args']=o+['--']+i;ready.append(j)
            records.append(r|dict(kind='eval',workload=w,n=128 if w=='speed128' else (500 if w=='math500' else (32 if w.startswith('math32') else 64)),name=name,run_dir=str(out),training_dir=str(root),drafter=str(export)))
        write(stage/('eval-plan-'+r['name']+'.json'),records);publish(ready,dest)
    return pending

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--panels',type=Path,required=True);a=p.parse_args();seen=set()
    while True:
        from followspec.rev2_priority import promote
        promote()
        for line in (WS/'artifacts/M2_D28_20261006/response_queue.log').read_text().splitlines():
            if 'REV2-' in line and 'launch_failed' in line and line not in seen:print('ALERT launch_failed',line,flush=True);seen.add(line)
        n=sweep(a.stage,a.panels);print(time.strftime('%Y-%m-%d %H:%M:%S'), 'pending trainings',n,flush=True)
        if not n:return
        time.sleep(30)
if __name__=='__main__':main()
