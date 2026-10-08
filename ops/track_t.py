"""D-40 operational preparation and raw-counter audit; never alters the frozen engine."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

WS = Path('/home/heck2/sbhansali8/SpecTLM')
CODE = WS / '.worktrees/run-FIX15-pilot-eval-20261007'
COMMIT = '6da2e4265c0398ec0de5affaf23b0bd1df0be445'
PY = str(WS / '.venv-atlas-031-clean/bin/python')
HUB = Path('/home/heck2/sbhansali8/HFcache/hub')
SPEED = WS / 'artifacts/B4_public_resolved_20261005/speed128.jsonl'
MANIFEST = WS / 'artifacts/T1_models_20261007/manifest.jsonl'
DISPATCH = WS / 'artifacts/FIX16_operations_20261007/dispatch.jsonl'
QUEUE_LOG = WS / 'artifacts/M2_D28_20261006/response_queue.log'
BASE = {
    'llama': ('meta-llama/Llama-3.1-8B-Instruct', '0e9e39f249a16976918f6564b8830bc894c89659'),
    'qwen3': ('Qwen/Qwen3-8B', 'b968826d9c46dd6066d109eabc6255188de91218'),
}
DRAFT = {
    ('llama','eagle3'): ('RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3', 'f4fa34a8f803a0ba75d048d6b3dbc1ad5149e9ac', 4),
    ('qwen3','eagle3'): ('RedHatAI/Qwen3-8B-speculator.eagle3', '08610ffa01dd9f16731fe8f627b85905b6aa51c4', 4),
    ('llama','dflash'): ('z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat', 'd3af30def9601abdd10810aba220d692f0e803f0', 10),
    ('qwen3','dflash'): ('z-lab/Qwen3-8B-DFlash-b16', '9b41424b7109f9c5413454f481b09a82b85333f4', 16),
}


def read(path): return json.loads(Path(path).read_text())
def lines(path): return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, obj):
    with Path(path).open('x') as f: json.dump(obj, f, indent=2, allow_nan=False); f.write('\n')
def snapshot(model, revision): return HUB / ('models--' + model.replace('/', '--')) / 'snapshots' / revision
def slug(model): return re.sub('[^a-z0-9]+', '-', model.lower())[:80]


def frozen_check():
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=CODE,text=True).strip() != COMMIT:
        raise ValueError('wrong frozen commit')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=CODE,text=True).strip():
        raise ValueError('dirty frozen code')


def validate_render(rows, raw, tok, vocab_size):
    if len(rows) != len(raw) or len({r['prompt_id'] for r in rows}) != len(raw):
        raise ValueError('wrong count or duplicate prompt IDs')
    bos_counts = set()
    for row, source in zip(rows, raw):
        if row['prompt_id'] != source['prompt_id'] or row.get('raw_prompt') != source['prompt']:
            raise ValueError('raw query or order changed')
        ids = row.get('rendered_token_ids')
        if not isinstance(ids, list) or not ids or any(type(i) is not int or not 0 <= i < vocab_size for i in ids):
            raise ValueError('missing/invalid/out-of-vocabulary token IDs')
        if ids != tok.encode(row['prompt'], add_special_tokens=False): raise ValueError('tokens differ from rendered text')
        n = ids.count(tok.bos_token_id) if tok.bos_token_id is not None else 0
        if n > 1 or (n == 1 and ids[0] != tok.bos_token_id): raise ValueError('multiple or misplaced BOS')
        bos_counts.add(n)
    return dict(n=len(rows), bos_counts=sorted(bos_counts),
                bos_policy='exact template tokens; one leading BOS when template includes BOS, none otherwise',
                decoded_samples=[dict(prompt_id=r['prompt_id'], decoded=tok.decode(r['rendered_token_ids'], skip_special_tokens=False),
                                      token_ids=r['rendered_token_ids']) for r in rows[:5]])


def render_all(out):
    from transformers import AutoTokenizer
    frozen_check(); out.mkdir(parents=True, exist_ok=False)
    raw = lines(SPEED); models = lines(MANIFEST)
    if len(models) != 18 or any(r['status'] != 'ok' for r in models): raise ValueError('18 successful models required')
    def one(r):
        target = Path(r['path']); tokpath = target; revision = r['revision']; template = 'own'
        cfg = read(target/'tokenizer_config.json')
        if not cfg.get('chat_template') and not (target/'chat_template.jinja').exists():
            tokpath = snapshot(*BASE[r['base']]); revision = BASE[r['base']][1]; template = 'D-30 official template fallback'
        dest = out/r['base']/slug(r['id']); dest.parent.mkdir(exist_ok=True)
        cmd = [str(WS/'.venv-magpie/bin/python'), '-m', 'atlas.workloads', 'render-evaluation', '--input', str(SPEED),
               '--tokenizer', str(tokpath), '--tokenizer-revision', revision, '--family', r['base'], '--output', str(dest), '--capture-rendered-token-ids']
        log = out/(slug(r['id'])+'.log')
        with log.open('x') as f:
            result = subprocess.run(cmd, cwd=CODE, env=dict(os.environ,HF_HUB_OFFLINE='1',HF_HUB_CACHE=str(HUB)), stdout=f, stderr=subprocess.STDOUT)
        if result.returncode: raise ValueError(f'render failed: {log}')
        tok = AutoTokenizer.from_pretrained(tokpath, local_files_only=True, trust_remote_code=False)
        rows = lines(dest/'prompts.jsonl'); config = read(dest/'config.json')
        vocab = min(read(target/'config.json')['vocab_size'], read(snapshot(*BASE[r['base']])/'config.json')['vocab_size'])
        audit = validate_render(rows, raw, tok, vocab)
        if config['input_sha256'] != sha(SPEED) or config['prompts_sha256'] != sha(dest/'prompts.jsonl') or config['n'] != 128:
            raise ValueError('render provenance mismatch')
        expected = [tok.apply_chat_template([{'role':'user','content':r['prompt']}],tokenize=False,add_generation_prompt=True,enable_thinking=False) for r in raw]
        if expected != [r['prompt'] for r in rows]: raise ValueError('chat template mismatch')
        write(dest/'verification.json',audit|dict(template=template,config=config,model=r,frozen_commit=COMMIT))
        print(r['id'], 'verified', audit['n'], 'BOS',audit['bos_counts'],flush=True)
        return r['id'], dict(rendered=str(dest/'prompts.jsonl'),template=template,verification=str(dest/'verification.json'))
    with ThreadPoolExecutor(max_workers=3) as pool: index = dict(pool.map(one, models))
    write(out/'index.json',index)


def build_jobs(models, index, out):
    jobs=[]; records=[]
    for r in models:
        b=r['base']; prompts=index[r['id']]['rendered']
        for method in ('eagle3','dflash'):
            dr,drrev,k=DRAFT[b,method]
            for cell in ('A00','A10'):
                name=f'T1-{b}-{method}-{cell}-'+hashlib.sha256(r['id'].encode()).hexdigest()[:12]
                run=out/'runs'/name
                target,trev=(str(snapshot(*BASE[b])), BASE[b][1]) if cell=='A00' else (r['path'],r['revision'])
                cmd=[PY,'-m','atlas.run_cell','--target',target,'--target-revision',trev,'--drafter',dr,'--drafter-revision',drrev,
                     '--method',method,'--K',str(k),'--prompts',prompts,'--seed','0','--max-new-tokens','512','--batch-size','8',
                     '--max-model-len','4096','--gpu-memory-utilization','.70','--use-prompt-token-ids','--output',str(run)]
                args=['--task','T1','--base',b,'--drafter',method,'--k',str(k),'--seed','0','--no-resolve','--tag',name,
                      '--prompts',prompts,'--engine-lock',str(CODE/'atlas/env/requirements.lock'),'--python',PY,'--code-repo',str(CODE),
                      '--env','HF_HUB_OFFLINE=1','--env',f'HF_HUB_CACHE={HUB}','--env','VLLM_CACHE_ROOT={out_dir}/vllm_cache',
                      '--target',target,'--target-rev',trev,'--drafter-model',dr,'--drafter-rev',drrev,
                      '--note',f'D-40 {r["hypothesis"]} {r["id"]} {cell}; same model-own rendered IDs', '--',cmd[0],'-u',*cmd[1:]]
                jobs.append(dict(name=name,args=args,allowed_nodes=['heck-srv1','heck-srv3']))
                records.append(dict(run_id=name,run_dir=str(run),argv=cmd,env={'VLLM_CACHE_ROOT':'{out_dir}/vllm_cache'},
                                    prompt_file=prompts,K=k,base=b,method=method,cell=cell,model_id=r['id'],hypothesis=r['hypothesis'],model=r))
    if len({j['name'] for j in jobs}) != len(jobs): raise ValueError('duplicate job identity')
    return jobs,records


def conditional_counts(accepted,drafted,k):
    if len(accepted)!=len(drafted) or any(type(a)!=int or type(d)!=int or not 0<=a<=d<=k or d==0 for a,d in zip(accepted,drafted)):
        raise ValueError('invalid counters')
    return ([sum(a>=i+1 for a in accepted) for i in range(k)],
            [sum(a>=i and d>=i+1 for a,d in zip(accepted,drafted)) for i in range(k)])


def launch_guard(stage):
    # Required operator check before every handoff; never starts another queue.
    proc=subprocess.run(['pgrep','-af','[q]ueue.py'],capture_output=True,text=True)
    print(proc.stdout,flush=True)
    subprocess.run(['ls','-la',str(stage)],check=True)
    if len(proc.stdout.strip().splitlines())!=1:raise ValueError('exactly one canonical queue required')
    if str(DISPATCH) not in proc.stdout:raise ValueError('unexpected queue')
    for parent in [WS,*WS.parents]:
        for rel in ['EXPERIMENTS_PAUSED.json','tlm-spec-maintenance/EXPERIMENTS_PAUSED.json']:
            if (parent/rel).exists():raise ValueError('pause marker present')


def publish(jobs,stage):
    launch_guard(stage);old=lines(DISPATCH);before=sha(DISPATCH);known={j['name']:j for j in old};add=[]
    for j in jobs:
        if j['name'] in known:
            if known[j['name']]!=j:raise ValueError('existing job changed')
            continue
        if j['allowed_nodes']!=['heck-srv1','heck-srv3']:raise ValueError('T1 placement changed')
        add.append(j);known[j['name']]=j
    if not add:return 0
    tmp=DISPATCH.with_name(DISPATCH.name+f'.T1-{os.getpid()}.tmp')
    with tmp.open('x') as f:
        for j in old+add:f.write(json.dumps(j)+'\n')
        f.flush();os.fsync(f.fileno())
    if sha(DISPATCH)!=before:raise ValueError('concurrent dispatch update; retry without replacing it')
    os.replace(tmp,DISPATCH);return len(add)


def watch(stage):
    import fcntl
    from ops.method_recovery import retry_plan,preflight,apply_overlay
    from ops.raw_acceptance_audit import t1
    frozen_check();handle=(stage/'watch.lock').open('a+')
    fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    records=read(stage/'index.json');jobs={j['name']:j for j in lines(stage/'jobs.jsonl')}
    overlays={read(p)['record']['retry_of']:read(p) for p in stage.glob('overlay-*.json')}
    blocked={};last=-1
    def event(**kw):
        with (stage/'events.jsonl').open('a') as f:f.write(json.dumps(dict(time=time.strftime('%Y-%m-%dT%H:%M:%S%z'),**kw))+'\n')
    while True:
        launches={r['name']:r for r in lines(QUEUE_LOG) if r.get('event')=='launched'}
        effective=apply_overlay(records,overlays)
        for original,active in zip(records,effective):
            name=original['run_id'];launch=launches.get(active['run_id'])
            if name in blocked or not launch or not (Path(launch['out_dir'])/'exit_code').exists():continue
            exit_code=(Path(launch['out_dir'])/'exit_code').read_text().strip()
            if exit_code=='0':continue
            try:
                r,j,proof=retry_plan(active,jobs[name],launch['out_dir'],stage/'retries',attempt=2 if name in overlays else 1,
                    expected_prompt_sha=sha(original['prompt_file']),expected_source_sha=sha(CODE/'atlas/run_cell.py'))
                j['allowed_nodes']=['heck-srv1','heck-srv3']
                launch_guard(stage);preflight([j],CODE,stage/f'retry-preflight-{time.time_ns()}')
                overlay=dict(record=r,job=j,proof=proof);write(stage/f'overlay-{name}.json',overlay);overlays[name]=overlay
                publish([j],stage);event(event='collision_retry',original=name,retry=r['run_id'])
            except ValueError as e:blocked[name]=str(e);event(event='blocked',run=name,reason=str(e))
        effective=apply_overlay(records,overlays)
        done=sum((Path(r['run_dir'])/'results.json').is_file() for r in effective)
        if done!=last:
            effective_path=stage/f'effective-{time.time_ns()}.json';write(effective_path,effective)
            if done:
                report=stage/('report' if done==len(records) else f'partial-{done}-{time.time_ns()}')
                result=t1(effective_path,report,partial=done<len(records))
                event(event='report',complete=done,total=len(records),report=str(report),blocked=blocked)
            last=done
        if done==len(records):return
        time.sleep(60)


def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['render','plan','dispatch','watch']);p.add_argument('--output',required=True);p.add_argument('--render-index');a=p.parse_args()
    out=Path(a.output).resolve()
    if a.command=='render':render_all(out);return
    if a.command=='watch':watch(out);return
    if a.command=='dispatch':
        checks=read(out/'preflight/results.json')
        if not checks['passed'] or len(checks['checks'])!=144:raise ValueError('72 cell and launcher preflights required')
        print(publish(lines(out/'jobs.jsonl'),out),'jobs handed to existing queue');return
    frozen_check();out.mkdir(parents=True,exist_ok=False)
    jobs,records=build_jobs(lines(MANIFEST),read(a.render_index),out)
    write(out/'index.json',records)
    with (out/'jobs.jsonl').open('x') as f:
        for job in jobs:f.write(json.dumps(job)+'\n')
    write(out/'config.json',dict(frozen_commit=COMMIT,render_index=a.render_index,render_index_sha256=sha(a.render_index),manifest_sha256=sha(MANIFEST),n_cells=len(records)))
    print(len(jobs),'cells prepared')


if __name__=='__main__':main()
