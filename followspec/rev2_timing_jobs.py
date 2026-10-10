"""D54 matched timing panels; independent processes, fresh compile, warm/cold separate."""
import argparse,copy
from pathlib import Path
from followspec.rev2_launch import NODES
from followspec.review_followup import parts,replace,publish
from followspec.independent_kd import jsonl
from ops.track_t import WS,DISPATCH,lines,write,sha

def prepare(stage,code,panels,experiment):
    stage.mkdir(exist_ok=False);d={j['name']:j for j in lines(DISPATCH)};jobs=[];records=[]
    for t,family in [(0,'r1'),(1,'nemo')]:
        arms=['none','official-reused','official-fc','official-full']+(['oracle'] if t==0 else [])
        if experiment!='E10a':arms.append('independent')
        batches=[1] if experiment=='E10a' else ([1,8] if experiment=='E10b' else [16,32])
        for b in batches:
            if experiment=='E10a':promptfile=WS/f'artifacts/REV1_20261010_0130/math32-t{t}.jsonl';cap=8192
            elif experiment=='E10b':
                src=WS/'artifacts/P3_D50_20261009_0200/math500/prompts.jsonl' if t==0 else panels/'math500-t1.jsonl'
                promptfile=stage/f'math500-t{t}-b{b}.jsonl';jsonl(promptfile,lines(src)[:32 if b==1 else 128]);cap=512
            else:
                _,ii=parts(d[f'D52-timing-{family}-none-b8-r0']);promptfile=Path(ii[ii.index('--prompts')+1]);cap=512
            for arm in arms:
                for replicate in range(3):
                    j=copy.deepcopy(d[f'D52-timing-{family}-{arm}-b{1 if b==1 else 8}-r{replicate}']);o,i=parts(j)
                    name=f'REV2-{experiment}-{family}-{arm}-b{b}-r{replicate}';out=stage/'runs'/name
                    for a in (o,i):replace(a,'--prompts',promptfile)
                    for f,v in [('--tag',name),('--code-repo',code),('--note',f'D54 {experiment}; A40 greedy matched timing only; cap{cap}; b{b};3processesx3warm; cold separate; no acceptance metrics')]:replace(o,f,v)
                    for f,v in [('--output',out),('--batch-size',b),('--max-new-tokens',cap),('--max-model-len',12288 if cap>512 else 4096),('--min-free-gb',350)]:replace(i,f,v)
                    j.update(name=name,args=o+['--']+i,allowed_nodes=NODES);jobs.append(j)
                    records.append(dict(experiment=experiment,target=t,arm=arm,batch=b,replicate=replicate,n=32 if b==1 else 128,cap=cap,name=name,run_dir=str(out),prompts=str(promptfile),prompt_sha256=sha(promptfile)))
    write(stage/'plan.json',records);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish-initial')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);p.add_argument('--panels',type=Path,required=True);p.add_argument('--experiment',choices=['E10a','E10b','E11'],required=True);a=p.parse_args();prepare(a.stage,a.code,a.panels,a.experiment)
