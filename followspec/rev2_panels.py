"""D54 immutable MATH500 target renders and missing seed/target cells."""
import argparse,copy,json
from pathlib import Path
from followspec.rev2_launch import NODES
from followspec.review_followup import parts,replace,publish
from followspec.independent_kd import jsonl
from followspec.repair_data import tokenizer_for,render
from ops.track_t import WS,DISPATCH,lines,write,sha,frozen_check

def value(a,f):return a[a.index(f)+1]
def eval_job(src,name,out,prompts):
    j=copy.deepcopy(src);o,i=parts(j)
    for a in (o,i):replace(a,'--prompts',prompts)
    replace(o,'--tag',name);replace(o,'--note','D54 held-out MATH500 completion; identical per-target rendered IDs; frozen acceptance; pilot')
    replace(i,'--output',out);j.update(name=name,args=o+['--']+i,allowed_nodes=NODES);return j

def prepare(stage):
    frozen_check();stage.mkdir(exist_ok=False);d={j['name']:j for j in lines(DISPATCH)}
    source=WS/'artifacts/P3_D50_20261009_0200/math500/prompts.jsonl';raw=lines(source);assert len(raw)==500
    panels={0:source};proofs={}
    for t in [1,2]:
        row=json.loads((WS/f'artifacts/P3_D48_20261008_1455/target-{t}.json').read_text());tok=tokenizer_for(row['path'])
        old=lines(WS/f'artifacts/P3_repair_20261008_0305/eval/render-{t}/prompts.jsonl')
        for r in old:assert render(tok,r['raw_prompt'])==r['rendered_token_ids'],'existing template mismatch'
        rows=[]
        for r in raw:
            ids=render(tok,r['raw_prompt']);rows.append(r|dict(prompt=tok.decode(ids,skip_special_tokens=False),rendered_token_ids=ids))
        panel=stage/f'math500-t{t}.jsonl';jsonl(panel,rows);panels[t]=panel
        proofs[t]=dict(target=row,source=str(source),source_sha256=sha(source),n=500,sha256=sha(panel),existing_math64_match=True,decoded_five=[r['prompt'] for r in rows[:5]],template_kwargs=dict(enable_thinking=False,add_generation_prompt=True))
    write(stage/'render-audit.json',proofs)
    jobs=[];records=[]
    sources=[(1,'reuse',0,'D50-E1-official-t1-math64'),(1,'fc',0,'FIX24-official-t1-16k-fc-s2625-math64'),(1,'full',0,'FIX24-official-t1-16k-full-s2625-math64'),(1,'independent',0,'D50-E3-t1-draft_model-K4-LNone-math64')]
    for seed,step in [(1,4472),(2,4481)]:
        for arm in ['fc','full']:sources.append((0,arm,seed,f'FIX24-official-t0-16k-{arm}-seed{seed}-s{step}-math64'))
    for t,arm,seed,key in sources:
        name=f'REV2-E14-t{t}-{arm}-seed{seed}-math500';out=stage/'runs'/name
        jobs.append(eval_job(d[key],name,out,panels[t]));records.append(dict(experiment='E14',target=t,arm=arm,seed=seed,workload='math500',name=name,run_dir=str(out)))
    write(stage/'plan.json',records);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish-initial')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);a=p.parse_args();prepare(a.stage)
