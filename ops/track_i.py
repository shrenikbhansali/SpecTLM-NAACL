"""Owner D-42: outcome-independent 60-target census, standalone draft models."""
import argparse
from collections import defaultdict, Counter
import copy
import csv
import hashlib
import json
from pathlib import Path
from ops.track_t import WS, BASE, snapshot, build_jobs, read, lines, write, sha


def select_targets(rows, per_base=30):
    selected=[]
    for base in ['llama','qwen3']:
        strata=defaultdict(list)
        for r in rows:
            if r['base']==base:strata[r['type'],r['pool']].append(r)
        for key in strata:
            strata[key].sort(key=lambda r:hashlib.sha256(('I1-D41-20261007/'+base+'/'+r['model_id']).encode()).hexdigest())
        if sum(map(len,strata.values()))<per_base:raise ValueError('insufficient targets')
        n=0
        while n<per_base:
            for key in sorted(strata):
                if strata[key] and n<per_base:selected.append(strata[key].pop(0));n+=1
    return selected


def replace(args,flag,value): args[args.index(flag)+1]=str(value)


def independent_pair(r,d,prompts,out,code,commit):
    model=dict(id=r['model_id'],base=r['base'],revision=r['revision'],path=r['staged_path'],hypothesis=r['type'],license=r['license'])
    oldjobs,oldrecords=build_jobs([model],{model['id']:dict(rendered=prompts)},out)
    jobs=[];records=[]
    for j,record in zip(oldjobs[:2],oldrecords[:2]):
        j=copy.deepcopy(j);record=copy.deepcopy(record);args=j['args'];split=args.index('--');outer=args[:split];cmd=args[split+1:]
        tag=d['id'].split('/')[-1].lower();name=record['run_id'].replace('T1-','I1-').replace('eagle3',tag);run=out/'runs'/name
        replace(outer,'--task','I1');replace(outer,'--tag',name);replace(outer,'--drafter','draft_model');replace(outer,'--drafter-model',d['path']);replace(outer,'--drafter-rev',d['revision'])
        replace(outer,'--code-repo',code);replace(outer,'--engine-lock',code/'atlas/env/requirements.lock')
        replace(outer,'--note',f'D-42 stratified independent census: {r["model_id"]}; drafter {d["id"]}; {record["cell"]}')
        replace(cmd,'--method','draft_model');replace(cmd,'--drafter',d['path']);replace(cmd,'--drafter-revision',d['revision']);replace(cmd,'--output',run)
        cmd.append('--draft-vocab-mapping')
        if r['type']=='lora_adapter':
            base,rev=BASE[r['base']];target=str(snapshot(base,rev))
            for group,flag,revflag in [(cmd,'--target','--target-revision'),(outer,'--target','--target-rev')]:
                replace(group,flag,target);replace(group,revflag,rev)
            rank=next(v for v in [8,16,32,64,128,256,320,512] if v>=int(float(r['r'])))
            cmd+=['--max-lora-rank',str(rank)]
            if record['cell']=='A10':
                cmd+=['--adapter',r['staged_path'],'--adapter-revision',r['revision']]
                outer+=['--adapter',r['staged_path'],'--adapter-rev',r['revision']]
            else:cmd+=['--enable-lora']
        j.update(name=name,args=outer+['--']+cmd,allowed_nodes=['heck-srv4','heck-srv2'])
        record.update(run_id=name,run_dir=str(run),argv=[v for i,v in enumerate(cmd) if not (i==1 and v=='-u')],
                      method=tag,drafter_model=d['id'],frozen_commit=commit,selection_stratum=[r['base'],r['type'],r['pool']],atlas_model=r)
        jobs.append(j);records.append(record)
    return jobs,records


def prepare(out,code,commit,smoke=False):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for base in ['llama','qwen3']:
        rows += [dict(r,base=base) for r in csv.DictReader(open(WS/f'artifacts/atlas/pool_manifest_{base}.csv')) if r['in_atlas']=='True']
    if len(rows)!=174:raise ValueError('atlas census changed')
    chosen=select_targets(rows);write(out/'selection.json',dict(n_universe=len(rows),n_selected=len(chosen),seed='I1-D41-20261007',
        procedure='30/base; round-robin (type,pool) strata, SHA256 model ordering within each; no outcome values used',
        strata_counts=dict(Counter('|'.join((r['base'],r['type'],r['pool'])) for r in chosen)),targets=chosen))
    if smoke:
        chosen=[next(r for r in chosen if r['base']==b and r['type']=='lora_adapter') for b in ['llama','qwen3']]
    drafts=lines(WS/'artifacts/I1_models_20261007/verified_manifest.jsonl')
    if len(drafts)!=3 or any(r['status']!='ok' for r in drafts):raise ValueError('all three pinned drafters required')
    own=read(WS/'artifacts/A3_rendered_20261006/index.json');general=read(WS/'artifacts/A3_rendered_20261006/index_speed128.json')
    jobs=[];records=[]
    for r in chosen:
        key=f'{r["base"]}:{r["model_id"]}';prompt=own[key]['rendered'] if key in own else general[key]['rendered']
        if smoke:
            dest=out/(r['base']+'-five-prompts.jsonl')
            with dest.open('x') as f:
                for row in lines(prompt)[:5]:f.write(json.dumps(row)+'\n')
            prompt=str(dest)
        for d in drafts:
            if (r['base']=='llama')!=d['id'].startswith('meta-llama/'):continue
            jj,rr=independent_pair(r,d,prompt,out,code,commit)
            if smoke:
                for j,rec in zip(jj,rr):
                    replace(j['args'],'--max-new-tokens',64);replace(rec['argv'],'--max-new-tokens',64)
                    j['name']+='-smoke';replace(j['args'],'--tag',j['name']);rec['run_id']=j['name']
            jobs+=jj;records+=rr
    write(out/'index.json',records)
    with (out/'jobs.jsonl').open('x') as f:
        for j in jobs:f.write(json.dumps(j)+'\n')
    write(out/'config.json',dict(frozen_commit=commit,code_repo=str(code),n_cells=len(records),smoke=smoke,
        drafter_manifest_sha256=sha(WS/'artifacts/I1_models_20261007/verified_manifest.jsonl'),selection_sha256=sha(out/'selection.json'),
        prompt_sha256={r['prompt_file']:sha(r['prompt_file']) for r in records},K=4,engine_version='0.31.0',
        placement='heck-srv4,heck-srv2:0-3; queue slots MUST exclude heck-srv2:4-7 before dispatch'))
    print(len(records),'cells prepared',flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--code',required=True);p.add_argument('--commit',required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args()
    prepare(Path(a.output).resolve(),Path(a.code).resolve(),a.commit,a.smoke)


if __name__=='__main__':main()
