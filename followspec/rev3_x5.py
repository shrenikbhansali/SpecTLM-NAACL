"""D55 X5 native DFlash16k, frozen acceptance and independent-process timing."""
import argparse,copy,json,time
from pathlib import Path
from followspec.rev2_launch import training_job,NODES
from followspec.rev2_p1_jobs import remove
from followspec.review_followup import parts,replace,publish
from followspec.rev2_panels import eval_job
from ops.track_t import WS,DISPATCH,lines,write,frozen_check

WORKLOADS=['speed128','math500','math32-8192']

def training_specs():
    return [dict(experiment='X5',kind='train',target=t,arm=a,seed=s,workloads=WORKLOADS) for t in [0,1] for s in (range(3) if t==0 else [0]) for a in ['fc','full']]

def panel(t,w,d):
    if w=='math32-8192':return WS/f'artifacts/REV1_20261010_0130/math32-t{t}.jsonl'
    if w=='math500':return WS/('artifacts/P3_D50_20261009_0200/math500/prompts.jsonl' if t==0 else 'artifacts/REV2_panels_20261010_0430_v2/math500-t1.jsonl')
    _,i=parts(d[f'D50-E1-official-t{t}-speed128']);return Path(i[i.index('--prompts')+1])

def accept(d,stage,t,arm,seed,w,drafter,revision):
    name=f'REV3-X5-t{t}-{arm}-seed{seed}-{w}';out=stage/'eval'/name
    j=eval_job(d[f'P4-D48-t{t}-fc-s300-'+('speed128' if w=='speed128' else 'math64')],name,out,panel(t,w,d));o,i=parts(j)
    for args,f,r in [(o,'--drafter-model','--drafter-rev'),(i,'--drafter','--drafter-revision')]:replace(args,f,drafter);replace(args,r,revision)
    for f,v in [('--max-new-tokens',8192 if w=='math32-8192' else 512),('--max-model-len',12288 if w=='math32-8192' else 4096),('--batch-size',8)]:replace(i,f,v)
    replace(o,'--note','D55 X5 DFlash nativeK10, frozen6da2e42, identical derivative-rendered IDs; pilot')
    j.update(name=name,args=o+['--']+i,allowed_nodes=NODES)
    return j,dict(experiment='X5',kind='eval',target=t,arm=arm,seed=seed,workload=w,name=name,run_dir=str(out))

def timing(d,stage,code,t,arm,drafter=None,revision=None):
    jobs=[];records=[];family='r1' if t==0 else 'nemo'
    for batch in [1,8]:
        for rep in range(3):
            src=d[f'D52-timing-{family}-'+('none' if arm=='none' else 'official-reused')+f'-b{batch}-r{rep}'];j=copy.deepcopy(src);o,i=parts(j)
            name=f'REV3-X5-t{t}-{arm}-timing-b{batch}-r{rep}';out=stage/'timing'/name;prompts=panel(t,'speed128',d)
            for args in [o,i]:replace(args,'--prompts',prompts)
            for f,v in [('--tag',name),('--code-repo',code),('--drafter','dflash'),('--k',10),('--note','D55 X5 A40 SPEED128 all128prompts b1/b8,3processesx3warm; nativeK10; timingonly')]:replace(o,f,v)
            for f,v in [('--output',out),('--method','dflash'),('--K',10),('--min-free-gb',350)]:replace(i,f,v)
            if arm!='none':
                for args,f,r in [(o,'--drafter-model','--drafter-rev'),(i,'--drafter','--drafter-revision')]:replace(args,f,drafter);replace(args,r,revision)
            j.update(name=name,args=o+['--']+i,allowed_nodes=NODES);jobs.append(j)
            records.append(dict(experiment='X5',kind='timing',target=t,arm=arm,batch=batch,replicate=rep,n=128,name=name,run_dir=str(out)))
    return jobs,records

def prepare(stage,code):
    frozen_check();stage.mkdir(exist_ok=False);d={j['name']:j for j in lines(DISPATCH)};jobs=[];records=[]
    for r in training_specs():
        t,arm,seed=r['target'],r['arm'],r['seed'];name=f'REV3-X5-t{t}-{arm}-seed{seed}';out=stage/name
        j=training_job(d[f'P4-D48-train-{t}-{arm}'],name,out,code,arm,seed=seed);o,i=parts(j)
        _,src=parts(d[f'FIX24-official-t{t}-16k-fc']);data=src[src.index('--data')+1];audit=src[src.index('--audit')+1]
        replace(o,'--prompts',data);replace(o,'--note','D55 X5 nativeDFlash16k oneepoch; exact existingdata;2048tokens64anchors; finalsharedexportonly')
        for f,v in [('--data',data),('--audit',audit),('--batch-tokens',2048)]:replace(i,f,v)
        remove(i,'--schedule-steps');i+=['--one-epoch','--export-only-final'];j['args']=o+['--']+i;jobs.append(j);records.append(r|dict(name=name,run_dir=str(out)))
    # Published before controls so training is eligible immediately.
    write(stage/'plan.json',records);publish(jobs,stage/'publish-training')
    jobs=[];controls=[]
    for t in [0,1]:
        _,i=parts(d[f'P4-D48-train-{t}-fc']);drafter=i[i.index('--drafter')+1];revision=Path(drafter).name
        for w in WORKLOADS:
            j,r=accept(d,stage,t,'reuse',0,w,drafter,revision);jobs.append(j);controls.append(r)
        for arm in ['none','reuse']:
            jj,rr=timing(d,stage,code,t,arm,drafter,revision);jobs+=jj;controls+=rr
    write(stage/'control-plan.json',controls);publish(jobs,stage/'publish-controls')

def sweep(stage,code):
    d={j['name']:j for j in lines(DISPATCH)};pending=0
    for r in json.loads((stage/'plan.json').read_text()):
        root=Path(r['run_dir']);dest=stage/('publish-final-'+r['name'])
        if (dest/'published.json').exists():continue
        if not (root/'results.json').exists():pending+=1;continue
        c=json.loads((root/'config.json').read_text());res=json.loads((root/'results.json').read_text());assert c['steps']==res['steps'] and c['n']==res['n']==16000
        export=Path(res['exports'][-1]);assert (export/'repair_provenance.json').exists();jobs=[];records=[]
        for w in WORKLOADS:
            j,rr=accept(d,stage,r['target'],r['arm'],r['seed'],w,export,c['code_commit']);jobs.append(j);records.append(rr|dict(training_dir=str(root)))
        if r['seed']==0:
            jj,rr=timing(d,stage,code,r['target'],r['arm'],export,c['code_commit']);jobs+=jj;records+=rr
        write(stage/('final-plan-'+r['name']+'.json'),records);publish(jobs,dest)
    return pending

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','watch']);p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);a=p.parse_args()
    if a.action=='prepare':prepare(a.stage,a.code)
    else:
        while True:
            n=sweep(a.stage,a.code);print('X5 pending trainings',n,flush=True)
            if not n:break
            time.sleep(30)
