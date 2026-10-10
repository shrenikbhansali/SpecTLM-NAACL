"""D53 bounded reviewer controls; clone validated jobs, never change frozen metrics."""
import argparse
import copy
import json
import subprocess
import sys
import time
from pathlib import Path
from ops.track_t import WS, CODE, DISPATCH, lines, write, sha, frozen_check
from followspec.disk_guard import require_free

NODES=['heck-srv1','heck-srv2','heck-srv3','heck-srv4']

def replace(a,flag,value):
    values=value if isinstance(value,list) else [str(value)]
    if flag not in a: a.extend([flag]+values);return
    i=a.index(flag);j=i+1
    while j<len(a) and not a[j].startswith('--'):j+=1
    a[i+1:j]=values

def parts(job):
    a=job['args'];i=a.index('--');return a[:i],a[i+1:]

def long_cell(source,name,prompts,out,cap):
    j=copy.deepcopy(source);outer,inner=parts(j)
    for a in (outer,inner):replace(a,'--prompts',str(prompts))
    replace(outer,'--tag',name);replace(outer,'--note',f'D53 reviewer long-generation pilot; fixed MATH32; cap={cap}; matched family arms; no changed engine')
    replace(inner,'--output',str(out));replace(inner,'--max-new-tokens',cap);replace(inner,'--max-model-len',12288)
    j.update(name=name,args=outer+['--']+inner,allowed_nodes=NODES);return j

def capacity_cell(source,name,out,variant,rank,code):
    j=copy.deepcopy(source);outer,inner=parts(j)
    replace(outer,'--tag',name);replace(outer,'--code-repo',str(code))
    replace(outer,'--note','D53 capacity control, native TTT3 self256/300steps, exact D46 data/seed/order; not EDA')
    for flag,v in [('--output',str(out)),('--variant',variant),('--lora-rank',rank),('--lora-alpha',2*rank),('--export-steps',['300']),('--shared-export-root',str(out.parent/'shared-shards')),('--min-free-gb',350)]:replace(inner,flag,v)
    if '--compact-checkpoints' not in inner:inner.append('--compact-checkpoints')
    j.update(name=name,args=outer+['--']+inner,allowed_nodes=NODES);return j

def publish(jobs,out):
    sys.path.insert(0,str(WS/'artifacts/P3_repair_20261008_0305'))
    from publish_common import publish as p
    print(subprocess.check_output(['pgrep','-af','[q]ueue.py'],text=True),flush=True)
    print('stage contents',sorted(x.name for x in out.parent.iterdir()),flush=True)
    require_free(out.parent,350)
    groups={}
    for j in jobs:
        outer,_=parts(j);code=Path(outer[outer.index('--code-repo')+1]);groups.setdefault(code,[]).append(j)
    if len(groups)==1:
        code,group=next(iter(groups.items()));p(group,code,out)
    else:
        out.mkdir(exist_ok=False)
        for k,(code,group) in enumerate(groups.items()):p(group,code,out/f'group-{k}')

def prepare(stage,code):
    frozen_check();require_free(WS,350);stage.mkdir(exist_ok=False)
    jobs=lines(DISPATCH);byname={j['name']:j for j in jobs};assert len(byname)==len(jobs)
    alljobs=[];records=[]
    for target in [0,1]:
        base=byname[f'D50-E1-official-t{target}-math64']
        _,inner=parts(base);source=Path(inner[inner.index('--prompts')+1]);rows=lines(source)
        # Predeclared first 32 of the existing fixed evaluation order; selection ignores outputs.
        panel=stage/f'math32-t{target}.jsonl'
        with panel.open('x') as f:
            for r in rows[:32]:f.write(json.dumps(r)+'\n')
        write(stage/f'panel-t{target}.json',dict(n=32,source=str(source),source_sha256=sha(source),sha256=sha(panel),selection='first32 existing fixed MATH64 order; no output conditioning',decoded_samples=[r['prompt'] for r in rows[:5]]))
        step=4477 if target==0 else 2625
        sources={'reuse':base,'fc':byname[f'FIX24-official-t{target}-16k-fc-s{step}-math64'],'full':byname[f'FIX24-official-t{target}-16k-full-s{step}-math64']}
        if target==0:
            oracle=copy.deepcopy(base);o,i=parts(oracle)
            from ops.track_t import snapshot
            # Copy oracle pin/path from an existing completed dedicated R1 cell.
            candidates=[j for j in jobs if any('EAGLE3-DeepSeek-R1-Distill-LLaMA-8B' in a for a in j['args']) and 'atlas.run_cell' in j['args']]
            assert candidates
            oo,ii=parts(candidates[0])
            for dst,src,flags in [(o,oo,['--drafter-model','--drafter-rev']),(i,ii,['--drafter','--drafter-revision'])]:
                for flag in flags:replace(dst,flag,src[src.index(flag)+1])
            oracle['args']=o+['--']+i;sources['oracle']=oracle
        for cap in [512,2048,8192]:
            for arm,src in sources.items():
                name=f'REV1-long-t{target}-{arm}-{cap}';out=stage/'long'/name
                alljobs.append(long_cell(src,name,panel,out,cap));records.append(dict(kind='long',target=target,arm=arm,cap=cap,n=32,run_dir=str(out),name=name))
    source=byname['P3-D46-train-decoder-self-0355']
    for arm,variant,rank,params in [('decoder-r655','decoder_lora',655,50304000),('interface-r75','fc_lowrank',75,1228800)]:
        name=f'REV1-capacity-{arm}';out=stage/name
        alljobs.append(capacity_cell(source,name,out,variant,rank,code));records.append(dict(kind='capacity',arm=arm,rank=rank,parameters=params,run_dir=str(out),name=name))
    write(stage/'plan.json',records);write(stage/'jobs.json',alljobs)
    publish(alljobs,stage/'publish-initial')

def watch(stage):
    while True:
        records=json.loads((stage/'plan.json').read_text());pending=0
        jobs=lines(DISPATCH);byname={j['name']:j for j in jobs}
        for r in records:
            if r['kind']!='capacity':continue
            root=Path(r['run_dir']);export=root/'export-300';dest=stage/('publish-eval-'+r['arm'])
            if dest.exists():continue
            if (root/'failure.json').exists():print('FAILED',root,flush=True);continue
            if not (export/'repair_provenance.json').exists():pending+=1;continue
            cfg=json.loads((root/'config.json').read_text());ready=[]
            for w in ['speed128','math64']:
                j=copy.deepcopy(byname['P3-D46-decoder-s300-'+w]);o,i=parts(j);name=r['name']+'-'+w
                replace(o,'--tag',name)
                for a,f,g in [(o,'--drafter-model','--drafter-rev'),(i,'--drafter','--drafter-revision')]:replace(a,f,str(export));replace(a,g,cfg['code_commit'])
                replace(i,'--output',str(stage/'capacity-eval'/name));j.update(name=name,args=o+['--']+i,allowed_nodes=NODES);ready.append(j)
            publish(ready,dest)
        if not pending:return
        time.sleep(30)

def controls(stage,code):
    """Second-review interventions, fixed before looking at their outcomes."""
    frozen_check();require_free(WS,350);stage.mkdir(exist_ok=False)
    jobs=lines(DISPATCH);byname={j['name']:j for j in jobs}
    source=byname['P3-D46-train-decoder-self-0355']
    parent=stage/'parent.json'
    from ops.track_t import snapshot
    parent_path=Path('/home/heck2/sbhansali8/HFcache/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659')
    assert parent_path.is_dir()
    write(parent,dict(id='meta-llama/Llama-3.1-8B-Instruct',revision=parent_path.name,path=str(parent_path)))
    ready=[];records=[]
    # Two learning rates for the low-rank control; the original 2e-5 already exists.
    variants=[('parent-fc','fc',16,2e-5,True),('parent-full','full',16,2e-5,True),
              ('decoder-dense','decoder_dense',16,2e-5,False),
              ('decoder-qo','decoder_qo',16,2e-5,False),
              ('decoder-r16-lr1e4','decoder_lora',16,1e-4,False)]
    for arm,variant,rank,lr,alternate in variants:
        name='REV1-control-'+arm;out=stage/name
        j=capacity_cell(source,name,out,variant,rank,code);o,i=parts(j)
        replace(i,'--lr',lr)
        if alternate:replace(i,'--supervision-row',str(parent))
        replace(o,'--note','D53 second review: fixed derivative text; parent-supervision or full-rank decoder/LR control; self256/300steps native TTT3 seed0')
        j['args']=o+['--']+i;ready.append(j)
        records.append(dict(kind='capacity',arm=arm,variant=variant,lr=lr,alternate_supervision=alternate,run_dir=str(out),name=name))
    write(stage/'plan.json',records);write(stage/'jobs.json',ready)
    publish(ready,stage/'publish-initial')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','watch','controls']);p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
    if a.action=='watch':watch(a.stage)
    else:globals()[a.action](a.stage,a.code)
