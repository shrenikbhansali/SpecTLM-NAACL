"""Immutable M4 launch handoff from all twelve completed matched M3 runs.

Uses B7's scheduler without changing historical cell defaults or statistics.
K4 is the complete comparison matrix; K2/8 contain FS and Frozen only.
"""
import argparse
import importlib.metadata
from pathlib import Path
from atlas.run_cell import sha256, write_new
from followspec.evaluate import schedule, pin
from followspec.production import ARMS, launcher_job
from followspec.production_pipeline import checked_stage, execution_spec, finish, jsonl, lines, new_output, read


def evaluation_jobs(training, targets, output, *, python, code_repo=None, completed_only=False, previous=None, training_seeds=None):
    selected = [0, 1, 2] if training_seeds is None else list(training_seeds)
    if not selected or any(type(s) is not int or s not in range(3) for s in selected) or len(set(selected)) != len(selected):
        raise ValueError('training seeds must be a nonempty unique subset of 0,1,2')
    selected = sorted(selected)
    root, cfg = checked_stage(training)
    if cfg['stage'] != 'training-jobs' or read(root/'results.json').get('n_jobs') != 12:
        raise ValueError('complete twelve-job M3 plan required')
    final, _ = checked_stage(cfg['finalized'])
    if sha256(final/'stage_files.json') != cfg['finalized_stage_sha256']:
        raise ValueError('finalized data stage changed')
    spec = execution_spec(cfg['spec'], code_repo or cfg['spec']['code_repo'])
    checkpoints = []; evidence = {}; seen = set(); pending = []; excluded = []
    for job in lines(root/'jobs.jsonl'):
        argv = job['args']; cmd = argv[argv.index('--')+1:]
        arm = cmd[cmd.index('--arm')+1]; seed = int(cmd[cmd.index('--seed')+1])
        if (arm, seed) in seen or arm not in ARMS or seed not in range(3):
            raise ValueError('duplicate or invalid M3 arm/seed')
        seen.add((arm, seed)); run = Path(cmd[cmd.index('--output')+1])
        if seed not in selected:
            excluded.append(dict(arm=arm,seed=seed,run=str(run),reason='outside explicit training seed scope'))
            continue
        if list(run.glob('failure*.json')):
            raise ValueError(f'completed M3 run required, failed run: {run}')
        if not (run/'results.json').is_file():
            if completed_only:
                pending.append(dict(arm=arm,seed=seed,run=str(run)));continue
            raise ValueError(f'completed M3 run required: {run}')
        actual = read(run/'config.json'); result = read(run/'results.json')
        expected = read(final/arm/'training_config.json')
        if actual.get('dry_run') is not False or actual.get('training_config') != expected or actual.get('seed') != seed:
            raise ValueError('actual training config differs from matched plan')
        if actual.get('base_revision') != spec['base_revision'] or actual.get('backend_revision') != expected['backend_revision']:
            raise ValueError('actual training model/backend pins differ')
        if actual.get('release_grad_before_forward') is not True or actual.get('offload_saved_tensors') is not True or actual.get('torch_compile_disable') != '0':
            raise ValueError('actual training memory controls differ')
        if result.get('status') != 'trained_pending_vllm_acceptance' or any(result.get(k) != expected[k] for k in ('optimizer_steps','token_budget')):
            raise ValueError('completed M3 budget/step verification required')
        checkpoint = run/'checkpoints'/str(expected['epochs']-1)
        files = [checkpoint/'config.json', checkpoint/'model.safetensors']
        if any(not p.is_file() or not p.stat().st_size for p in files):
            raise ValueError('nonempty native checkpoint export required')
        if read(files[0]).get('speculators_config',{}).get('algorithm') != 'eagle3':
            raise ValueError('M3 EAGLE-3 export required')
        pin(actual['code_commit'])
        checkpoints.append(dict(arm=arm,seed=seed,model_id=str(checkpoint),revision=actual['code_commit']))
        evidence.update({str(p):sha256(p) for p in [run/'config.json',run/'results.json',*files]})
    if seen != {(a,s) for a in ARMS for s in range(3)}:
        raise ValueError('complete twelve-job M3 matrix required')
    checkpoints += [dict(arm='Frozen',seed=s,model_id=spec['drafter_snapshot'],revision=spec['drafter_revision']) for s in selected]
    target_spec = read(targets); target_rows = target_spec['targets']
    bank_ids = set(read(final/'FS/manifest.json').get('registry',{}))
    names = [t['model_id'] for t in target_rows]
    if len(names) != len(set(names)) or names.count('base') != 1 or not any(t['pool']=='test' for t in target_rows):
        raise ValueError('unique held-out targets plus explicit base required')
    workload_labels = set(next(t for t in target_rows if t['model_id']=='base')['workloads'])
    if any(not set(t['workloads']) <= workload_labels for t in target_rows):
        raise ValueError('matched workload labels including parent-retention cells required')
    prompt_hashes = {}; target_by_id = {}
    for target in target_rows:
        name = target['model_id']; target_by_id[name] = target
        if name in bank_ids or target['pool'] not in ('test','base') or (name=='base') != (target['pool']=='base'):
            raise ValueError('held-out evaluation excludes training bank/mixtures')
        pin(target['revision'])
        if name=='base' and target['revision'] != spec['base_revision']:
            raise ValueError('base target pin differs')
        if target.get('adapter') and target.get('max_lora_rank') not in (8,16,32,64,128,256,320,512):
            raise ValueError('explicit paired LoRA rank capacity required')
        if not target['workloads']:
            raise ValueError('target workloads required')
        for path in target['workloads'].values():
            rows=lines(path)
            if not rows or len({r['prompt_id'] for r in rows}) != len(rows) or any(
                    not r.get('rendered_token_ids') or any(type(t) is not int or t<0 for t in r['rendered_token_ids']) for r in rows):
                raise ValueError('unique exact rendered prompt tokens required')
            prompt_hashes[str(Path(path).resolve())] = sha256(path)
    prior_records = {}; prior_jobs = []; previous_path = None
    if previous is not None:
        previous_path, previous_cfg = checked_stage(previous)
        if previous_cfg['stage'] != 'evaluation-jobs' or previous_cfg['training'] != str(root):
            raise ValueError('previous evaluation stage must use this training plan')
        if previous_cfg['targets_sha256'] != sha256(targets) or previous_cfg['prompt_sha256'] != prompt_hashes:
            raise ValueError('previous targets or prompt files changed')
        for path,digest in read(previous_path/'checkpoint_inputs_sha256.json').items():
            if evidence.get(path) != digest:
                raise ValueError('previous checkpoint changed or is no longer complete')
        prior_records = {r['run_id']:r for name in ('index_k4.json','index_k2_k8.json') for r in read(previous_path/name) if r['seed'] in selected}
        prior_jobs = [j for j in lines(previous_path/('effective_jobs.jsonl' if (previous_path/'effective_jobs.jsonl').exists() else 'jobs.jsonl')) if j['name'] in prior_records]
    # Do not choose workloads/targets based on observed checkpoint results.
    plan_spec = dict(base_id=spec['base_id'],base_revision=spec['base_revision'],targets=target_rows,
                     checkpoints=checkpoints,K=[4],evaluation_seed=0,max_new_tokens=512)
    out = Path(output).resolve()
    primary = schedule(plan_spec, out/'runs')
    secondary = schedule(plan_spec | dict(K=[2,8],checkpoints=[c for c in checkpoints if c['arm'] in ('FS','Frozen')]),out/'runs')
    jobs = []
    for record in primary+secondary:
        command = record['argv'][1:]
        target = target_by_id[record['derivative_id']]
        ti=command.index('--target')+1
        command[ti] = spec['base_snapshot'] if record['cell'] in ('A00','A01') or target.get('adapter') else target.get('snapshot',command[ti])
        command += ['--use-prompt-token-ids','--batch-size','8','--gpu-memory-utilization','0.70']
        if target.get('adapter'):
            command += ['--enable-lora','--max-lora-rank',str(target['max_lora_rank'])]
        prior = prior_records.get(record['run_id'])
        if prior is not None:
            # Only the immutable stage's output directory may differ.
            wanted = [python,*command]; old = list(prior['argv'])
            wanted[wanted.index('--output')+1] = old[old.index('--output')+1]
            if wanted != old:
                raise ValueError('previous cell controls or checkpoint identity changed')
            record.clear();record.update(prior)
            continue
        job = launcher_job(spec | dict(seed=0),record['run_id'],'M4',record['prompt_file'],command,python=python)
        job['allowed_nodes']=[f'heck-srv{i}' for i in range(1,6)]
        args=job['args'];args[args.index('--drafter')+1]='eagle3';args[args.index('--k')+1]=str(record['K'])
        args[args.index('--target')+1]=command[ti];args[args.index('--target-rev')+1]=command[command.index('--target-revision')+1]
        extra=['--drafter-model',command[command.index('--drafter')+1],'--drafter-rev',command[command.index('--drafter-revision')+1]]
        if '--adapter' in command:extra += ['--adapter',target['adapter'],'--adapter-rev',target['revision']]
        split=args.index('--');args[split:split]=extra
        record['argv']=[python,*command]
        # The actual launcher path carries its own timestamp; per-cell artifacts retain B7 IDs.
        record['hardware_policy']='A40 only; D-26 training exemption does not apply'
        jobs.append(job)
    if not set(prior_records) <= {r['run_id'] for r in primary+secondary}:
        raise ValueError('previous evaluation cells lost from continuation')
    out=new_output(out)
    jsonl(out/'effective_jobs.jsonl',prior_jobs+jobs)
    jsonl(out/'jobs.jsonl',jobs);write_new(out/'index_k4.json',primary);write_new(out/'index_k2_k8.json',secondary)
    write_new(out/'checkpoint_inputs_sha256.json',evidence)
    finish(out,dict(stage='evaluation-jobs',training=str(root),spec=spec,targets=str(Path(targets).resolve()),
        targets_sha256=sha256(targets),prompt_sha256=prompt_hashes,python=python,
        completed_only=completed_only,previous=str(previous_path) if previous_path else None,training_seeds=selected,
        analysis_versions={p:importlib.metadata.version(p) for p in ('numpy','scipy')}),
        dict(n_jobs=len(jobs),n_effective_jobs=len(prior_jobs)+len(jobs),n_primary=len(primary),n_secondary=len(secondary),submitted=False,
             training_complete=not pending,n_pending_training=len(pending),pending_training=pending,
             n_excluded_training=len(excluded),excluded_training=excluded,exploratory_single_seed=len(selected)==1,
             checkpoint_loadability='pending first vLLM cells',owner_gate_decision='pending',
             next='Preflight and dispatch to free A40s. Aggregate index_k4 with B7; K2/8 are separate FS/Frozen diagnostics.'))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('training','targets','output','python'):p.add_argument('--'+name,required=True)
    p.add_argument('--code-repo');p.add_argument('--completed-only',action='store_true');p.add_argument('--previous')
    p.add_argument('--training-seeds',type=int,nargs='+',help='explicit exploratory seed scope; defaults to all three seeds')
    a=p.parse_args()
    print(evaluation_jobs(a.training,a.targets,a.output,python=a.python,code_repo=a.code_repo,completed_only=a.completed_only,previous=a.previous,training_seeds=a.training_seeds))


if __name__=='__main__':main()
