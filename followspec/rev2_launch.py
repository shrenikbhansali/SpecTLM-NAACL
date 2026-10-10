"""D54 bounded jobs, cloned from successful pinned recipes. No second dispatcher."""
import argparse,copy,json
from pathlib import Path
from followspec.review_followup import parts,replace,publish
from ops.track_t import WS,DISPATCH,lines,write,frozen_check
from followspec.disk_guard import require_free
NODES=['heck-srv1','heck-srv2','heck-srv3','heck-srv4','heck-srv5']

def training_job(src,name,out,code,variant,rank=16,seed=0):
    j=copy.deepcopy(src);o,i=parts(j)
    for a in (o,i):replace(a,'--seed',seed)
    for f,v in [('--tag',name),('--code-repo',code),('--note','D54 REV2 pilot; matched official initialization/FIX24, native TTT3, one epoch; compact final only')]:replace(o,f,v)
    for f,v in [('--output',out),('--variant',variant),('--lora-rank',rank),('--lora-alpha',2*rank),('--epoch-export-fractions',['1']),('--shared-export-root',out.parent/'shared-shards'),('--min-free-gb',350)]:replace(i,f,v)
    for f in ['--compact-checkpoints','--omit-final-optimizer']:
        if f not in i:i.append(f)
    j.update(name=name,args=o+['--']+i,allowed_nodes=NODES);return j

def e8_jobs(byname,stage,code):
    jobs=[];records=[]
    for t in [0,1]:
        for seed in range(3):
            arms=[('decoder-qo','decoder_qo',16,50331648),('interface-r75','fc_lowrank',75,1228800),('decoder-r16','decoder_lora',16,1228800)]
            if t==1 and seed:arms.append(('interface','fc',16,50331648))
            for arm,variant,rank,count in arms:
                name=f'REV2-E8-t{t}-{arm}-seed{seed}';out=stage/name
                jobs.append(training_job(byname[f'FIX24-official-t{t}-16k-fc'],name,out,code,variant,rank,seed))
                records.append(dict(experiment='E8',kind='train',target=t,seed=seed,arm=arm,variant=variant,expected_trainable=count,name=name,run_dir=str(out),workloads=['speed128','math64']+(['math500'] if seed==0 else [])))
    return jobs,records

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['e8']);p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);p.add_argument('--publish',action='store_true');a=p.parse_args()
    frozen_check();require_free(WS,350);a.stage.mkdir(exist_ok=False)
    d={j['name']:j for j in lines(DISPATCH)};jobs,records=e8_jobs(d,a.stage,a.code)
    write(a.stage/'plan.json',records);write(a.stage/'jobs.json',jobs)
    if a.publish:publish(jobs,a.stage/'publish-initial')
if __name__=='__main__':main()
