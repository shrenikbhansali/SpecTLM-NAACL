"""Single-dispatcher I1 smoke-to-census handoff and immutable collision retries."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
from ops.track_t import DISPATCH,QUEUE_LOG,read,lines,sha,write,launch_guard
from ops.method_recovery import apply_overlay,retry_plan,preflight
from ops.raw_acceptance_audit import load,matched_configs,t1


def validate_slots(slots):
    for slot in slots.split(','):
        node,gpu=slot.split(':')
        if node=='heck-srv5' or (node=='heck-srv2' and int(gpu)>3):raise ValueError('unsafe I1 queue slots')


def publish(jobs,stage):
    launch_guard(stage)
    pid=int(subprocess.check_output(['pgrep','-f','[q]ueue.py'],text=True).strip())
    argv=Path(f'/proc/{pid}/cmdline').read_bytes().decode().strip('\0').split('\0');validate_slots(argv[argv.index('--slots')+1])
    old=lines(DISPATCH);before=sha(DISPATCH);known={j['name']:j for j in old};add=[]
    for j in jobs:
        if j['allowed_nodes']!=['heck-srv4','heck-srv2']:raise ValueError('I1 placement changed')
        if j['name'] in known:
            if known[j['name']]!=j:raise ValueError('dispatch identity changed')
        else:add.append(j);known[j['name']]=j
    if not add:return 0
    tmp=DISPATCH.with_name(DISPATCH.name+f'.I1-{os.getpid()}.tmp')
    with tmp.open('x') as f:
        for j in old+add:f.write(json.dumps(j)+'\n')
        f.flush();os.fsync(f.fileno())
    if sha(DISPATCH)!=before:raise ValueError('concurrent dispatch update')
    os.replace(tmp,DISPATCH);return len(add)


def check_preflight(stage):
    p=stage/'preflight/results.json'
    if not p.exists():return False
    r=read(p)
    if not r['passed'] or len(r['checks'])!=2*len(lines(stage/'jobs.jsonl')):raise ValueError('preflight failed')
    return True


def observe(stage):
    cfg=read(stage/'config.json');code=Path(cfg['code_repo']);records=read(stage/'index.json');jobs={j['name']:j for j in lines(stage/'jobs.jsonl')}
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=code,text=True).strip()!=cfg['frozen_commit']:raise ValueError('wrong I1 code')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=code,text=True).strip():raise ValueError('I1 code dirty')
    overlays={read(p)['proof']['retry_of']:read(p) for p in stage.glob('overlay-*.json')}
    launches={r['name']:r for r in lines(QUEUE_LOG) if r.get('event')=='launched'};blocked=[]
    for original,active in zip(records,apply_overlay(records,overlays)):
        name=original['run_id'];launch=launches.get(active['run_id']);exitfile=Path(launch['out_dir'])/'exit_code' if launch else None
        if not exitfile or not exitfile.exists() or exitfile.read_text().strip()=='0':continue
        try:
            rr,jj,proof=retry_plan(active,jobs[name],launch['out_dir'],stage/'retries',attempt=2 if name in overlays else 1,
                                  expected_prompt_sha=sha(original['prompt_file']),expected_source_sha=sha(code/'atlas/run_cell.py'))
            jj['allowed_nodes']=['heck-srv4','heck-srv2'];launch_guard(stage);preflight([jj],code,stage/f'retry-preflight-{time.time_ns()}')
            overlay=dict(record=rr,job=jj,proof=proof);write(stage/f'overlay-{name}.json',overlay);overlays[name]=overlay;publish([jj],stage)
        except ValueError as e:blocked.append(dict(run_id=name,reason=str(e),launcher=launch['out_dir']))
    effective=apply_overlay(records,overlays)
    done=sum((Path(r['run_dir'])/'results.json').is_file() for r in effective)
    return effective,done,blocked


def validate_smoke(records):
    groups={}
    for r in records:
        cfg,rows=load(r['run_dir'])
        if cfg['code_commit']!=r['frozen_commit'] or cfg['method']!='draft_model' or not cfg['draft_vocab_mapping'] or len(rows)!=5:
            raise ValueError('smoke provenance mismatch')
        if any(x['tau'] is None for x in rows.values()):raise ValueError('zero-step smoke')
        groups.setdefault((r['model_id'],r['method']),{})[r['cell']]=(cfg,rows)
    for cells in groups.values():
        if set(cells)!={'A00','A10'}:raise ValueError('unpaired smoke')
        matched_configs(cells['A00'][0],cells['A10'][0])
        if set(cells['A00'][1])!=set(cells['A10'][1]):raise ValueError('smoke prompts differ')
    return dict(passed=True,n_cells=len(records),n_pairs=len(groups),raw_counter_metrics_checked=True,
                scope='Loadability, LoRA configuration and raw-counter validity; not throughput or a repeat-noise estimate.')


def watch(smoke,census):
    handle=(census/'watch.lock').open('a+');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    launched=False;last=-1
    def event(**row):
        with (census/'events.jsonl').open('a') as f:f.write(json.dumps(dict(time=time.strftime('%Y-%m-%dT%H:%M:%S%z'),**row))+'\n')
    while True:
        if not check_preflight(smoke):time.sleep(20);continue
        publish(lines(smoke/'jobs.jsonl'),smoke)
        records,done,blocked=observe(smoke)
        if blocked:
            event(event='smoke_blocked',blocked=blocked);raise RuntimeError('smoke failures require inspection')
        if done!=len(records):time.sleep(30);continue
        proof=validate_smoke(records)
        if not (smoke/'verification.json').exists():write(smoke/'verification.json',proof);event(event='smoke_pass',proof=proof)
        if not check_preflight(census):time.sleep(30);continue
        publish(lines(census/'jobs.jsonl'),census);launched=True;break
    while launched:
        records,done,blocked=observe(census)
        if done!=last:
            index=census/f'effective-{time.time_ns()}.json';write(index,records)
            if done:
                report=census/('report' if done==len(records) else f'partial-{done}-{time.time_ns()}')
                t1(index,report,partial=done<len(records),study='I1');event(event='report',complete=done,total=len(records),report=str(report),blocked=blocked)
            last=done
        if done==len(records):return
        if blocked:event(event='blocked',blocked=blocked)
        time.sleep(60)


def main():
    p=argparse.ArgumentParser();p.add_argument('--smoke',required=True);p.add_argument('--census',required=True);a=p.parse_args()
    watch(Path(a.smoke).resolve(),Path(a.census).resolve())


if __name__=='__main__':main()
