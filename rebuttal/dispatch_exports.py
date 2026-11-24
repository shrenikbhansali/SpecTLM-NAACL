"""Append frozen evaluations when native training commits an immutable export.

This CPU watcher does not launch GPU processes or start another dispatcher.
"""
import argparse
import copy
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def write_immutable(path, value):
    path = Path(path)
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError('Existing plan differs: ' + str(path))
        return
    with path.open('x') as f:
        f.write(json.dumps(value, indent=2) + '\n')


def append_unique(path, jobs):
    path = Path(path)
    with (path.parent / 'append.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        old = [json.loads(x) for x in path.read_text().splitlines()]
        known = {x['name']: x for x in old}
        added = []
        for job in jobs:
            if job['name'] in known:
                if known[job['name']] != job:
                    raise ValueError('Changed queue identity: ' + job['name'])
                continue
            added.append(job)
            known[job['name']] = job
        if added:
            temporary = path.with_name(f'jobs.append-{os.getpid()}.tmp')
            temporary.write_text(''.join(json.dumps(x) + '\n' for x in old + added))
            os.replace(temporary, path)
        return [x['name'] for x in added]


def completed_exports(cell):
    return sorted((p for p in Path(cell).glob('export-*')
                   if (p / 'repair_provenance.json').exists()
                   and (p / 'config.json').exists()),
                  key=lambda p: int(p.name.split('-')[-1]))


def replace(args, key, value):
    args[args.index(key) + 1] = str(value)


def evaluation(root, output, template_stage, source_plan, export, variant, bench):
    t, seed = source_plan['target'], source_plan['seed']
    template_name = f'E2_t{t}_interface_{bench}_s0'
    templates = [json.loads(x) for x in (template_stage / 'jobs.jsonl').read_text().splitlines()]
    job = copy.deepcopy(next(x for x in templates if x['name'] == template_name))
    plan = json.loads((template_stage / (template_name + '.json')).read_text())
    step = int(export.name.split('-')[-1]) if export.name.startswith('export-') else int(
        json.loads((export / 'ablation_provenance.json').read_text())['trained'].split('export-')[-1])
    name = f"{source_plan['name']}_{variant}_step{step}_{bench}"
    old_drafter = plan['command'][plan['command'].index('--drafter') + 1]
    plan['input_sha256'].pop(old_drafter + '/config.json')
    plan['input_sha256'][str(export / 'config.json')] = hashlib.sha256((export / 'config.json').read_bytes()).hexdigest()
    gate = Path(source_plan['baseline_report'])
    plan['input_sha256'][str(gate)] = hashlib.sha256(gate.read_bytes()).hexdigest()
    plan.update(name=name, run_dir=str(root / 'rebuttal/runs' / name),
                baseline_report=str(gate), training_seed=seed, experiment=source_plan['experiment'],
                variant=variant, training_run=source_plan['name'], export_step=step,
                drafter_revision=source_plan['harness_commit'])
    replace(plan['command'], '--drafter', export)
    replace(plan['command'], '--drafter-revision', source_plan['harness_commit'])
    replace(plan['command'], '--output', Path(plan['run_dir']) / 'cell')
    plan['purpose'] = 'Frozen evaluation of a completed native export; existing held-out rendered IDs'
    path = output / (name + '.json')
    if Path(plan['run_dir']).exists() and not path.exists():
        raise FileExistsError(plan['run_dir'])
    write_immutable(path, plan)
    job['name'] = name
    replace(job['args'], '--tag', name)
    replace(job['args'], '--drafter-model', export)
    replace(job['args'], '--drafter-rev', source_plan['harness_commit'])
    replace(job['args'], '--plan', path)
    return job


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--runs', nargs='+', required=True)
    p.add_argument('--poll', type=int, default=60)
    p.add_argument('--once', action='store_true')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    root = a.workspace
    canonical = root / 'rebuttal/preflight_20261124_exactfamily/jobs.jsonl'
    template = root / 'rebuttal/ready_20261124_1504'
    log = root / 'artifacts/M2_D28_20261006/response_queue.log'
    # A separate process lock prevents redundant export work if resumed twice.
    with (a.output / 'watcher.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        seen = set()
        alerts = set()
        offset = log.stat().st_size
        while True:
            all_finished = True
            for name in a.runs:
                run = root / 'rebuttal/runs' / name
                if not (run / 'metrics.json').exists():
                    all_finished = False
                elif json.loads((run / 'metrics.json').read_text())['status'] == 'failed' and name not in alerts:
                    message = {'time': datetime.datetime.now().astimezone().isoformat(), 'event': 'run_failed', 'name': name}
                    with (a.output / 'alerts.jsonl').open('a') as f:
                        f.write(json.dumps(message) + '\n')
                    print('ALERT', json.dumps(message), flush=True)
                    alerts.add(name)
                if not (run / 'config.yaml').exists():
                    continue
                plan = json.loads((run / 'config.yaml').read_text())
                for export in completed_exports(run / 'cell'):
                    key = (name, str(export))
                    if key in seen:
                        continue
                    variants = [('all', export)]
                    if '--variant' in plan['command'] and plan['command'][plan['command'].index('--variant') + 1] == 'whole_lora':
                        from rebuttal.ablate_lora import ablate
                        proof = json.loads((run / 'cell/parameters.json').read_text())
                        adapted = {n.rsplit('.', 1)[0] + '.weight' for n in proof['trainable_names']}
                        base = Path(plan['command'][plan['command'].index('--drafter') + 1])
                        for mode in ['no_fc', 'fc_only']:
                            out = a.output / f'{name}_{export.name}_{mode}'
                            if not out.exists():
                                ablate(export, base, out, mode, adapted)
                            elif not (out / 'ablation_provenance.json').exists():
                                raise RuntimeError('Partial ablation export: ' + str(out))
                            variants.append((mode, out))
                    jobs = [evaluation(root, a.output, template, plan, path, variant, bench)
                            for variant, path in variants for bench in ['speed128', 'math128']]
                    # Inspect the sole dispatcher, journal and stage before each append.
                    subprocess.run(['pgrep', '-af', '[q]ueue.py'], check=True)
                    print('Stage:', a.output, 'files:', len(list(a.output.iterdir())), flush=True)
                    print((root / 'rebuttal/JOURNAL.md').read_text()[-1000:], flush=True)
                    added = append_unique(canonical, jobs)
                    with (a.output / 'submitted.jsonl').open('a') as f:
                        f.write(json.dumps({'export': str(export), 'jobs': added}) + '\n')
                    print('APPENDED', added, flush=True)
                    seen.add(key)
            with log.open() as f:
                f.seek(offset)
                for line in f:
                    event = json.loads(line)
                    if event.get('event') == 'launch_failed':
                        with (a.output / 'alerts.jsonl').open('a') as out:
                            out.write(json.dumps(event) + '\n')
                        print('ALERT', json.dumps(event), flush=True)
                offset = f.tell()
            if a.once or all_finished:
                return
            time.sleep(a.poll)


if __name__ == '__main__':
    main()
