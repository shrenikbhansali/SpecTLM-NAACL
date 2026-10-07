"""Emit immutable M3 jobs only after matched M2 data and capacity checks pass."""
import argparse
import re
from pathlib import Path
from atlas.run_cell import sha256, write_new
from followspec.configs import check_matched
from followspec.production import ARMS, launcher_job
from followspec.production_pipeline import checked_stage, execution_spec, finish, jsonl, new_output, read
from followspec.train_eagle3 import resolve_plan


def training_jobs(finalized, output, *, python, code_repo=None, training_seeds=None, job_prefix="m3"):
    selected=[0,1,2] if training_seeds is None else list(training_seeds)
    if not selected or len(set(selected))!=len(selected) or any(type(s) is not int or s not in range(3) for s in selected):raise ValueError("invalid training seeds")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",job_prefix):raise ValueError("invalid job prefix")
    root, cfg = checked_stage(finalized)
    ready = read(root/'results.json')
    if cfg['stage'] != 'finalize' or not all(ready.get(k) is True for k in
            ('production_ready', 'data_ready', 'training_capacity_verified')) or ready.get('blockers'):
        raise ValueError('M2 data and training capacity readiness required')
    spec = execution_spec(cfg['spec'], code_repo or cfg['spec']['code_repo'])
    configs = {a: read(root/a/'training_config.json') for a in ARMS}
    differences = check_matched(configs)
    plans = []
    for arm, config in configs.items():
        manifest = read(root/arm/'manifest.json')
        if manifest.get('data_acceptance_passed') is not True or manifest.get('acceptance_only'):
            raise ValueError('audited production data required')
        if manifest.get('base_revision') != spec['base_revision'] or config['initialization_revision'] != spec['drafter_revision']:
            raise ValueError('model pins differ from production specification')
        audit = manifest.get('sample_mask_audit', {})
        if not audit.get('path') or sha256(audit['path']) != audit.get('sha256'):
            raise ValueError('reviewed sample masks changed')
        if (config['seeds'] != [0, 1, 2] and not (config['seeds']==[0] and selected==[0] and config.get('pilot',{}).get('decision_id'))) or not set(selected)<=set(config['seeds']):
            raise ValueError('approved M3 seeds required')
        for seed in selected:
            plans.append(resolve_plan(config, manifest, seed))
    out = new_output(output)
    jobs = []
    for seed in selected:
        for arm in ARMS:
            name = f'{job_prefix}-{arm.lower()}-s{seed}'
            command = ['-m', 'followspec.train_eagle3', '--configs',
                *[str(root/a/'training_config.json') for a in ARMS], '--arm', arm,
                '--manifest', str(root/arm/'manifest.json'), '--base-snapshot', spec['base_snapshot'],
                '--drafter-snapshot', spec['drafter_snapshot'], '--seed', str(seed),
                '--output', str(out/'runs'/name), '--allow-a40-production',
                '--release-grad-before-forward', '--offload-saved-tensors']
            job = launcher_job(spec | dict(seed=seed), name, 'M3', root/arm/'manifest.json', command, python=python)
            args = job['args']; args[args.index('--drafter')+1] = 'fs-eagle3'
            split = args.index('--')
            args[split:split] = ['--allow-h200-training', '--env', 'TORCH_COMPILE_DISABLE=0',
                '--drafter-model', configs[arm]['initialization'], '--drafter-rev', spec['drafter_revision']]
            jobs.append(job)
    jsonl(out/'jobs.jsonl', jobs)
    write_new(out/'resolved_plans.json', plans)
    write_new(out/'config_diff.json', differences)
    finish(out, dict(stage='training-jobs', finalized=str(root), spec=spec, python=python,
        finalized_stage_sha256=sha256(root/'stage_files.json'),training_seeds=selected,job_prefix=job_prefix),
        dict(n_jobs=len(jobs), production_ready=True, submitted=False,
             next='Run actual trainer and launcher dry runs, then dispatch to free A40/H200 GPUs'))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--finalized', required=True); p.add_argument('--output', required=True)
    p.add_argument('--python', required=True); p.add_argument('--code-repo')
    p.add_argument('--training-seeds',type=int,nargs='+');p.add_argument('--job-prefix',default='m3')
    a = p.parse_args()
    print(training_jobs(a.finalized, a.output, python=a.python, code_repo=a.code_repo,training_seeds=a.training_seeds,job_prefix=a.job_prefix))


if __name__ == '__main__':
    main()
