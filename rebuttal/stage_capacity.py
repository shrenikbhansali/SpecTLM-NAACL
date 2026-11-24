"""Stage the authorized E2/E3b jobs without submitting; all outputs are new."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024**2),b''):h.update(block)
    return h.hexdigest()


def replace(args,key,value):
    args[args.index(key)+1]=str(value)


def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--stage',type=Path,required=True);p.add_argument('--baseline-report',type=Path,required=True)
    a=p.parse_args();root=a.workspace;stage=a.stage;stage.mkdir(parents=True,exist_ok=False)
    code=root/'rebuttal/worktrees/train-capacity-v2-20261124'
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=code,text=True).strip()
    if not subprocess.check_output(['git','tag','--points-at','HEAD'],cwd=code,text=True).strip():raise ValueError('Missing run tag')
    jobs=[];plans=[]
    old=root/'rebuttal/training_20261124'
    for line in (old/'jobs-after-baseline.jsonl').read_text().splitlines():
        job=json.loads(line);oldname=job['name'];plan=json.loads((old/(oldname+'.json')).read_text())
        name=oldname.replace('scratch10ep','scratch20ep');out=root/'rebuttal/runs'/name
        if out.exists():raise FileExistsError(out)
        plan.update(name=name,run_dir=str(out),cwd=str(code),harness_commit=commit,baseline_report=str(a.baseline_report))
        command=plan['command'];replace(command,'--output',out/'cell')
        if plan['experiment']=='E3b':
            replace(command,'--epochs',20);command[command.index('--export-epochs')+1:]=['1','2','5','10','15','20']
        path=stage/(name+'.json');path.write_text(json.dumps(plan,indent=2)+'\n');plans.append(path)
        args=job['args'];replace(args,'--tag',name);replace(args,'--code-repo',code);replace(args,'--plan',path)
        args[args.index('--plan')-1]=str(code/'rebuttal/run_recorded.py');job['name']=name;jobs.append(job)
    rows=[json.loads(x) for x in (root/'rebuttal/E2/prepared.jsonl').read_text().splitlines()]
    refs=[(r['target'],r['seed'],'lora-'+r['mode'],Path(r['export'])) for r in rows]
    inv=json.loads((root/'rebuttal/asset_inventory.json').read_text())['training_runs']
    for r in inv:
        if 'whole-r343' in r['name']:
            refs.append((int(r['name'].split('-t')[1][0]),int(r['name'].split('seed')[1]),'lora-all',Path(r['final_export'])))
    for t in [0,1]:
        for seed,steps in enumerate(([4477,4472,4481] if t==0 else [2625,2615,2621])):
            if seed==0:source=root/f'artifacts/FIX24_20261009_1420/FIX24-official-t{t}-16k-fc'
            elif t==0:source=root/f'artifacts/FIX24_official_seeds_20261009/FIX24-official-t0-16k-fc-seed{seed}'
            else:source=root/f'artifacts/REV2_E8_20261010_0425/REV2-E8-t1-interface-seed{seed}'
            refs.append((t,seed,'interface',source/f'export-{steps}'))
    templatejobs=[json.loads(x) for x in (root/'rebuttal/preflight_20261124_retry1/jobs.jsonl').read_text().splitlines()]
    for t,seed,variant,drafter in refs:
        for bench in ['speed128','math128']:
            original=f'BASELINE_t{t}_full_speed128_s0_cachefix1'
            plan=json.loads((root/'rebuttal/preflight_20261124_retry1'/(original+'.json')).read_text())
            job=copy.deepcopy(next(x for x in templatejobs if x['name']==original))
            name=f'E2_t{t}_{variant}_{bench}_s{seed}';out=root/'rebuttal/runs'/name
            if out.exists():raise FileExistsError(out)
            command=plan['command'];prompts=Path(command[command.index('--prompts')+1])
            if bench=='math128':prompts=root/f'artifacts/REV4_P0_20261011_0240/panels/t{t}-math128.jsonl'
            data=[json.loads(x) for x in prompts.read_text().splitlines()]
            if len(data)!=128 or any('rendered_token_ids' not in x for x in data):raise ValueError('Incorrect held-out panel')
            if not (drafter/'config.json').exists():raise FileNotFoundError(drafter)
            replace(command,'--drafter',drafter);replace(command,'--prompts',prompts);replace(command,'--output',out/'cell')
            # Training seed is a comparison axis; generation stays seed0 in every arm.
            plan.update(name=name,run_dir=str(out),training_seed=seed,target=t,experiment='E2',variant=variant,
                        benchmark=bench,requires_baseline_pass=True,baseline_report=str(a.baseline_report))
            target=Path(command[command.index('--target')+1])
            plan['input_sha256']={str(q):sha(q) for q in [prompts,drafter/'config.json',target/'config.json']}
            plan.pop('source_job',None);plan['purpose']='E2 seed-matched LoRA decomposition; frozen SPEED128/first128 MATH'
            path=stage/(name+'.json');path.write_text(json.dumps(plan,indent=2)+'\n');plans.append(path)
            args=job['args'];replace(args,'--tag',name);replace(args,'--prompts',prompts)
            replace(args,'--drafter-model',drafter);replace(args,'--plan',path)
            args[args.index('--plan')-1]=str(code/'rebuttal/run_recorded.py');job['name']=name;jobs.append(job)
    (stage/'jobs.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in jobs))
    print(json.dumps(dict(plans=len(plans),jobs=len(jobs),stage=str(stage),submitted=False)))


if __name__=='__main__':main()
