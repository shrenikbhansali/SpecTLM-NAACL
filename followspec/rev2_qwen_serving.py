"""D54 Qwen-family serving controls; existing SPEED reuse is never rerun."""
import argparse,copy,json
from pathlib import Path
from followspec.review_followup import parts,replace,publish
from followspec.rev2_panels import eval_job
from followspec.rev2_launch import NODES
from followspec.independent_kd import jsonl
from followspec.rev2_priority import promote
from ops.track_t import WS,DISPATCH,lines,write,sha

def prepare(stage,code,panels,train_stage=None):
    stage.mkdir(exist_ok=False);d={j['name']:j for j in lines(DISPATCH)}
    target=json.loads((WS/'artifacts/P3_D48_20261008_1455/target-2.json').read_text());base=d['T1-qwen3-eagle3-A10-a78899496c39'];oo,ii=parts(base)
    family=(ii[ii.index('--drafter')+1],ii[ii.index('--drafter-revision')+1]);speed=Path(ii[ii.index('--prompts')+1]);math=panels/'math500-t2.jsonl'
    independent=Path('/home/heck2/sbhansali8/HFcache/hub/models--Qwen--Qwen3-0.6B/snapshots/c1899de289a04d12100db370d81485cdf75e47ca')
    def vocab(p):
        z=json.loads((p/'tokenizer.json').read_text());return z['model']['vocab']|{r['content']:r['id'] for r in z['added_tokens']}
    a,b=vocab(Path(target['path'])),vocab(independent);shared=a.keys()&b.keys();assert len(shared)>150000 and all(a[k]==b[k] for k in shared)
    write(stage/'independent-vocabulary.json',dict(target=target,drafter=str(independent),revision=independent.name,shared=len(shared),same_shared_ids=True,target_only=sorted(a.keys()-b.keys()),draft_only=sorted(b.keys()-a.keys()),serving='existing heterogeneous-vocabulary mapping enabled; lexical token IDs identical, special-token aliases differ',target_tokenizer_sha256=sha(Path(target['path'])/'tokenizer.json'),drafter_tokenizer_sha256=sha(independent/'tokenizer.json')))
    arms={'none':family,'reuse':family,'independent':(str(independent),independent.name)}
    if train_stage:
        arms={}
        for arm in ['fc','full']:
            root=train_stage/f'REV2-E12-t2-{arm}-generic16k';cfg=json.loads((root/'config.json').read_text());res=json.loads((root/'results.json').read_text());arms[arm]=(res['exports'][-1],cfg['code_commit'])
    jobs=[];records=[]
    if not train_stage:
        name='REV2-E12-t2-reuse-math500';out=stage/'runs'/name;jobs.append(eval_job(base,name,out,math));records.append(dict(experiment='E12',kind='eval',target=2,arm='reuse',name=name,workload='math500',seed=0,run_dir=str(out)))
        for w,prompts in [('speed128',speed),('math500',math)]:
            src=d['D50-E3-t1-draft_model-K4-LNone-'+('speed128' if w=='speed128' else 'math64')];name='REV2-E12-t2-independent-'+w;out=stage/'runs'/name;j=eval_job(src,name,out,prompts);o,i=parts(j)
            for f,v in [('--base','qwen3'),('--code-repo',code),('--target',target['path']),('--target-rev',target['revision']),('--drafter-model',independent),('--drafter-rev',independent.name)]:replace(o,f,v)
            for f,v in [('--target',target['path']),('--target-revision',target['revision']),('--drafter',independent),('--drafter-revision',independent.name)]:replace(i,f,v)
            j['args']=o+['--']+i;jobs.append(j);records.append(dict(experiment='E12',kind='eval',target=2,arm='independent',workload=w,name=name,seed=0,run_dir=str(out)))
    speed32=stage/'speed32.jsonl';jsonl(speed32,lines(speed)[:32])
    for bsize in [1,8]:
        prompts=speed32 if bsize==1 else speed
        for arm,(drafter,revision) in arms.items():
            for rep in range(3):
                src=d[f'D52-timing-r1-'+('independent' if arm=='independent' else ('none' if arm=='none' else 'official-reused'))+f'-b{bsize}-r{rep}'];j=copy.deepcopy(src);o,i=parts(j);name=f'REV2-E12-t2-timing-{arm}-b{bsize}-r{rep}';out=stage/'timing'/name
                for a in (o,i):replace(a,'--prompts',prompts)
                for f,v in [('--tag',name),('--base','qwen3'),('--code-repo',code),('--target',target['path']),('--target-rev',target['revision']),('--drafter-model',drafter),('--drafter-rev',revision),('--note','D54 E12 A40 Qwen timing; SPEED b1n32/b8n128;3processesx3warm; special-token mapping for independent only')]:replace(o,f,v)
                for f,v in [('--target',target['path']),('--target-revision',target['revision']),('--drafter',drafter),('--drafter-revision',revision),('--output',out),('--min-free-gb',350)]:replace(i,f,v)
                j.update(name=name,args=o+['--']+i,allowed_nodes=NODES);jobs.append(j);records.append(dict(experiment='E12',kind='timing',target=2,arm=arm,batch=bsize,replicate=rep,name=name,run_dir=str(out),n=32 if bsize==1 else 128))
    write(stage/'plan.json',records);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish-initial');promote()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);p.add_argument('--panels',type=Path,required=True);p.add_argument('--train-stage',type=Path);a=p.parse_args();prepare(a.stage,a.code,a.panels,a.train_stage)
