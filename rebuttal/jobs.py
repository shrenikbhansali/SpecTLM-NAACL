"""Immutable job plans for the existing exclusive-owner dispatcher."""
import json,subprocess,hashlib
from pathlib import Path
from rebuttal.dispatch_exports import write_immutable,append_unique

ROOT=Path('/home/heck2/sbhansali8/ReFit')
FROZEN=ROOT/'rebuttal/worktrees/frozen-6da2e42'
GATE=ROOT/'rebuttal/advance_r1_20261124_1523/gate/results.json'
CANONICAL=ROOT/'rebuttal/preflight_20261124_exactfamily/jobs.jsonl'

def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()

def job(stage,code,name,experiment,target,command,inputs=(),seed=0,metadata=None,env=None):
 stage=Path(stage);code=Path(code);stage.mkdir(parents=True,exist_ok=True)
 targetrow=ROOT/f'rebuttal/inputs/target-{target}.json';t=json.loads(targetrow.read_text())
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=code,text=True).strip()
 if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=code,text=True).strip():raise ValueError('dirty run checkout')
 if not subprocess.check_output(['git','tag','--points-at',commit],cwd=code,text=True).strip():raise ValueError('untagged run commit')
 out=ROOT/'rebuttal/runs'/name
 command=[str(x) for x in command]+['--output',str(out/'cell')]
 files=[targetrow,GATE,*map(Path,inputs)]
 plan=dict(name=name,workspace=str(ROOT),run_dir=str(out),cwd=str(code),command=command,harness_commit=commit,engine_version='0.31.0',gpu='A40',seed=seed,K=4,input_sha256={str(p):digest(p) for p in files},target=target,experiment=experiment,requires_baseline_pass=True,baseline_report=str(GATE)) | (metadata or {})
 path=stage/(name+'.json');write_immutable(path,plan)
 prompts=next((str(p) for p in inputs if str(p).endswith('.jsonl')),str(ROOT/'artifacts/P3_repair_20261008_0305/eval/forbidden.jsonl'))
 args=['--task','REBUTTAL','--base','llama','--drafter','eagle3','--k',str(plan['K']),'--seed',str(seed),'--no-resolve','--tag',name,'--prompts',prompts,'--engine-lock',str(FROZEN/'atlas/env/requirements.lock'),'--python',command[0],'--code-repo',str(code),'--target',t['path'],'--target-rev',t['revision'],'--drafter-model',str(ROOT/f'artifacts/P3_D50_20261009_0200/E1-official-native-v2-t{target}'),'--drafter-rev','ada412b672e293d682423de84a095447bf38a637']
 env={'HF_HUB_OFFLINE':'1','HF_HUB_CACHE':'/home/heck2/sbhansali8/caches/huggingface/hub','VLLM_CACHE_ROOT':'{out_dir}/vllm_cache','CC':'/opt/rh/gcc-toolset-13/root/usr/bin/gcc','CXX':'/opt/rh/gcc-toolset-13/root/usr/bin/g++',**(env or {})}
 for k,v in env.items():args+=['--env',k+'='+v]
 args+=['--note','Owner-approved rebuttal E4/E5; immutable plan and pinned inputs','--',str(ROOT/'.venv-transport/bin/python'),'-u',str(code/'rebuttal/run_recorded.py'),'--plan',str(path)]
 result={'name':name,'args':args};write_immutable(stage/(name+'.job.json'),result)
 return result

def submit(stage,jobs):
 subprocess.run(['pgrep','-af','[q]ueue.py'],check=True)
 print('Stage',stage,'contents',[p.name for p in Path(stage).iterdir()],flush=True)
 print((ROOT/'rebuttal/JOURNAL.md').read_text()[-1000:],flush=True)
 for j in jobs:
  if (ROOT/'rebuttal/runs'/j['name']).exists():
   existing={r['name'] for r in map(json.loads,CANONICAL.read_text().splitlines())}
   if j['name'] not in existing:raise FileExistsError(j['name'])
 added=append_unique(CANONICAL,jobs);print('Appended',added,flush=True);return added
