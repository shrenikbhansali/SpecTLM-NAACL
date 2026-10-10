"""D54 P1 whole-drafter LoRA, scratch64k and bounded training profiles."""
import argparse,json
from pathlib import Path
from followspec.rev2_launch import training_job
from followspec.review_followup import parts,replace,publish
from followspec.rev2_priority import promote
from ops.track_t import WS,DISPATCH,lines,write

def remove(a,flag):
    if flag not in a:return
    i=a.index(flag);j=i+1
    while j<len(a) and not a[j].startswith('--'):j+=1
    del a[i:j]

def prepare(stage,code):
    stage.mkdir(exist_ok=False);d={j['name']:j for j in lines(DISPATCH)};jobs=[];records=[]
    for t in [0,1]:
        for seed in (range(3) if t==0 else [0]):
            for rank in [16,343]:
                name=f'REV2-E17-t{t}-whole-r{rank}-seed{seed}';out=stage/name
                jobs.append(training_job(d[f'FIX24-official-t{t}-16k-fc'],name,out,code,'whole_lora',rank,seed))
                records.append(dict(experiment='E17',kind='train',target=t,seed=seed,arm=f'whole-r{rank}',expected_trainable=146688*rank,name=name,run_dir=str(out),workloads=['speed128','math64','math500']))
    name='REV2-E13-t0-scratch64k-seed0';out=stage/name
    j=training_job(d['E5c-generic64k-full'],name,out,code,'full');o,i=parts(j);oo,ii=parts(d['FIX24-official-t0-16k-full'])
    for a,f,src,g in [(o,'--drafter-model',oo,'--drafter-model'),(o,'--drafter-rev',oo,'--drafter-rev'),(i,'--drafter',ii,'--drafter')]:replace(a,f,src[src.index(g)+1])
    i.append('--scratch');replace(o,'--note','D54 scratch64k official architecture/vocabulary; fixed target embedding; existing Alpaca+Dolly source mixture; one epoch/final export')
    j['args']=o+['--']+i;jobs.append(j);records.append(dict(experiment='E13',kind='train',target=0,seed=0,arm='scratch64k',name=name,run_dir=str(out),workloads=['speed128','math64','math500']))
    for arm,variant,rank in [('interface','fc',16),('full','full',16),('whole-r16','whole_lora',16),('whole-r343','whole_lora',343)]:
        name=f'REV2-E16-t0-{arm}-profile200';out=stage/name
        j=training_job(d['FIX24-official-t0-16k-fc'],name,out,code,variant,rank);o,i=parts(j)
        remove(i,'--one-epoch');remove(i,'--epoch-export-fractions')
        for f,v in [('--steps',200),('--export-steps',['200']),('--schedule-steps',4477)]:replace(i,f,v)
        i.append('--profile-training');replace(o,'--note','D54 E16 matched first200 batches, original4477step horizon; synchronized step time includes capture/forward/backward/optimizer, exports excluded')
        j['args']=o+['--']+i;jobs.append(j);records.append(dict(experiment='E16',kind='profile',target=0,seed=0,arm=arm,name=name,run_dir=str(out)))
    write(stage/'plan.json',records);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish-initial');promote()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);a=p.parse_args();prepare(a.stage,a.code)
