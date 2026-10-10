"""D54 exact existing Alpaca queries; 8 long-response and 8 Qwen shards."""
import argparse,copy,json
from pathlib import Path
from followspec.review_followup import parts,replace,publish
from followspec.independent_kd import jsonl
from followspec.rev2_launch import NODES
from ops.track_t import WS,DISPATCH,lines,write,sha
from followspec.disk_guard import require_free

def prepare(stage,code):
    require_free(WS,350);stage.mkdir(exist_ok=False)
    d={j['name']:j for j in lines(DISPATCH)};jobs=[];records=[]
    r1=WS/'artifacts/P3_D49_20261008_1800/sealed-generic16k/per_prompt.jsonl'
    nemo=WS/'artifacts/P3_D50_20261009_0200/E7-sealed16000/per_prompt.jsonl'
    for t,experiment,source,count,size,cap in [(0,'E9',r1,4000,1000,2048),(1,'E9',nemo,4000,1000,2048),(2,'E12',r1,16000,2000,512)]:
        rows=lines(source)[:count];assert len(rows)==count and len({r['prompt_sha256'] for r in rows})==count
        for shard,offset in enumerate(range(0,count,size)):
            promptfile=stage/f'{experiment}-t{t}-queries-{shard}.jsonl'
            queries=[dict(prompt=r['raw_prompt'],prompt_id=r['prompt_id'],split='training',source='existing approved Alpaca16k',source_prompt_sha256=r['prompt_sha256']) for r in rows[offset:offset+size]]
            jsonl(promptfile,queries)
            name=f'REV2-{experiment}-t{t}-data-{shard}';out=stage/name
            j=copy.deepcopy(d['P3-D48-data-self-target-2-1455']);o,i=parts(j)
            targetrow=WS/f'artifacts/P3_D48_20261008_1455/target-{t}.json';target=json.loads(targetrow.read_text())
            for f,v in [('--tag',name),('--code-repo',code),('--base','qwen3' if t==2 else 'llama'),('--prompts',promptfile),('--target',target['path']),('--target-rev',target['revision']),('--seed',7001),('--note',f'D54 {experiment}; exact existing Alpaca subset; cap{cap}; independent new outputs, evaluation forbidden, manual audit before training')]:replace(o,f,v)
            for f,v in [('--target-row',targetrow),('--public-queries',promptfile),('--output',out),('--count',size),('--seed',7001),('--max-new-tokens',cap),('--training-context-budget',4096 if cap==2048 else 2048),('--min-free-gb',350)]:replace(i,f,v)
            if t!=2:
                oo,_=parts(d[f'FIX24-official-t{t}-16k-fc'])
                for f in ['--drafter-model','--drafter-rev']:replace(o,f,oo[oo.index(f)+1])
            j.update(name=name,args=o+['--']+i,allowed_nodes=NODES);jobs.append(j)
            records.append(dict(experiment=experiment,kind='data',target=t,name=name,shard=shard,n=size,cap=cap,run_dir=str(out),prompts=str(promptfile),prompt_sha256=sha(promptfile),source=str(source),source_sha256=sha(source)))
    write(stage/'plan.json',records);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish-initial')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);a=p.parse_args();prepare(a.stage,a.code)
