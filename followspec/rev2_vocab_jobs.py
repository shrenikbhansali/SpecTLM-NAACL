"""D54 optional vocabulary intervention; reuse audited 16k data and official init."""
import argparse
from pathlib import Path
from followspec.rev2_launch import training_job
from followspec.review_followup import parts,publish
from followspec.rev2_priority import promote
from ops.track_t import DISPATCH,lines,write

def prepare(stage,code):
    stage.mkdir(exist_ok=False);d={j['name']:j for j in lines(DISPATCH)};jobs=[];records=[]
    for t in [0,1]:
        name=f'REV2-E15-t{t}-full-reselect32k';out=stage/name;j=training_job(d[f'FIX24-official-t{t}-16k-full'],name,out,code,'full');o,i=parts(j);i.append('--reselect-draft-vocab');j['args']=o+['--']+i;jobs.append(j)
        records.append(dict(experiment='E15',kind='train',target=t,seed=0,arm='full-reselect32k',name=name,run_dir=str(out),workloads=['speed128','math64','math500']))
    write(stage/'plan.json',records);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish-initial');promote()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);a=p.parse_args();prepare(a.stage,a.code)
