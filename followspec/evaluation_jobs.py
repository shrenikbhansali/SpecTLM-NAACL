"""Immutable M4 launch handoff from all twelve completed matched M3 runs.

Uses B7's scheduler without changing historical cell defaults or statistics.
K4 is the complete comparison matrix; K2/8 contain FS and Frozen only.
"""
import argparse
import importlib.metadata
import re
import shutil
from pathlib import Path
from atlas.run_cell import sha256, write_new
from followspec.evaluate import schedule, pin
from followspec.production import ARMS, launcher_job
from followspec.production_pipeline import checked_stage, execution_spec, finish, jsonl, lines, new_output, read


def immutable_export(source, output):
    """Copy inference files once; validation/optimizer metadata stays native."""
    source=Path(source);out=Path(output)
    files=[source/name for name in ('config.json','model.safetensors','config.py') if (source/name).is_file()]
    hashes={p.name:sha256(p) for p in files}
    if not {'config.json','model.safetensors'}<=set(hashes):raise ValueError('inference export files missing')
    if out.exists():
        if not (out/'export_proof.json').is_file() or read(out/'export_proof.json')!=dict(source=str(source),files_sha256=hashes):
            raise ValueError('inference export changed or incomplete')
        if {p.name for p in out.iterdir()}!=set(hashes)|{'export_proof.json'} or any(sha256(out/name)!=digest for name,digest in hashes.items()):
            raise ValueError('inference export changed')
        return out
    out.mkdir(parents=True)
    for p in files:shutil.copyfile(p,out/p.name)
    if any(sha256(out/name)!=digest or sha256(source/name)!=digest for name,digest in hashes.items()):
        raise ValueError('source changed during inference export')
    write_new(out/'export_proof.json',dict(source=str(source),files_sha256=hashes))
    return out


def evaluation_jobs(training, targets, output, *, python, code_repo=None, completed_only=False, previous=None, training_seeds=None, allow_validation_pending=False, reuse_frozen=None, job_prefix=None):
    root, cfg = checked_stage(training)
    declared=cfg.get("training_seeds",[0,1,2])
    selected = list(declared) if training_seeds is None else list(training_seeds)
    if not selected or any(type(s) is not int or s not in range(3) for s in selected) or len(set(selected)) != len(selected):
        raise ValueError('training seeds must be a nonempty unique subset of 0,1,2')
    selected = sorted(selected)
    if not declared or len(set(declared))!=len(declared) or any(type(s) is not int or s not in range(3) for s in declared) or not set(selected)<=set(declared):
        raise ValueError('invalid declared training seeds')
    if cfg['stage'] != 'training-jobs' or read(root/'results.json').get('n_jobs') != 4*len(declared):
        raise ValueError('complete declared M3 plan required')
    if job_prefix is not None and not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',job_prefix):
        raise ValueError('invalid evaluation job prefix')
    if previous is not None and reuse_frozen is not None:
        raise ValueError('choose previous continuation or Frozen reference reuse')
    final, _ = checked_stage(cfg['finalized'])
    if sha256(final/'stage_files.json') != cfg['finalized_stage_sha256']:
        raise ValueError('finalized data stage changed')
    spec = execution_spec(cfg['spec'], code_repo or cfg['spec']['code_repo'])
    checkpoints = []; evidence = {}; seen = set(); pending = []; excluded = []; validation_pending = []
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
        expected = read(final/arm/'training_config.json')
        checkpoint = run/'checkpoints'/str(expected['epochs']-1)
        state=checkpoint/'training_state.json';seal=checkpoint.parent/f"epoch{expected['epochs']-1}_end"
        final_sealed=state.is_file() and seal.is_symlink() and seal.resolve()==checkpoint.resolve()
        validation_open=not (run/'results.json').is_file()
        if validation_open and not (allow_validation_pending and final_sealed):
            if completed_only:
                pending.append(dict(arm=arm,seed=seed,run=str(run)));continue
            raise ValueError(f'completed M3 run required: {run}')
        actual = read(run/'config.json')
        result = read(run/'results.json') if not validation_open else None
        if allow_validation_pending and final_sealed:
            native_state=read(state)
            if expected['epochs']!=1 or native_state.get('epoch')!=0 or native_state.get('global_step')!=expected['optimizer_steps'] or native_state.get('local_step')!=0:
                raise ValueError('sealed final checkpoint must prove exact complete training steps')
            evidence[str(state)]=sha256(state)
        if validation_open:
            validation_pending.append(dict(arm=arm,seed=seed,run=str(run),checkpoint=str(checkpoint),proof=str(state)))
        if actual.get('dry_run') is not False or actual.get('training_config') != expected or actual.get('seed') != seed:
            raise ValueError('actual training config differs from matched plan')
        if actual.get('base_revision') != spec['base_revision'] or actual.get('backend_revision') != expected['backend_revision']:
            raise ValueError('actual training model/backend pins differ')
        if actual.get('release_grad_before_forward') is not True or actual.get('offload_saved_tensors') is not True or actual.get('torch_compile_disable') != '0':
            raise ValueError('actual training memory controls differ')
        if result is not None and (result.get('status') != 'trained_pending_vllm_acceptance' or any(result.get(k) != expected[k] for k in ('optimizer_steps','token_budget'))):
            raise ValueError('completed M3 budget/step verification required')
        checkpoint = run/'checkpoints'/str(expected['epochs']-1)
        files = [checkpoint/'config.json', checkpoint/'model.safetensors']
        if any(not p.is_file() or not p.stat().st_size for p in files):
            raise ValueError('nonempty native checkpoint export required')
        if read(files[0]).get('speculators_config',{}).get('algorithm') != 'eagle3':
            raise ValueError('M3 EAGLE-3 export required')
        pin(actual['code_commit'])
        inference=immutable_export(checkpoint,root/'evaluation_exports'/f'{arm}-s{seed}') if allow_validation_pending else checkpoint
        if allow_validation_pending:evidence.update({str(p):sha256(p) for p in inference.iterdir() if p.is_file()})
        checkpoints.append(dict(arm=arm,seed=seed,model_id=str(inference),revision=actual['code_commit']))
        evidence.update({str(p):sha256(p) for p in [run/'config.json',*([run/'results.json'] if result is not None else []),*files]})
    if seen != {(a,s) for a in ARMS for s in declared}:
        raise ValueError('complete declared M3 matrix required')
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
    if previous is not None or reuse_frozen is not None:
        previous_path, previous_cfg = checked_stage(previous or reuse_frozen)
        if previous_cfg['stage'] != 'evaluation-jobs' or (previous is not None and previous_cfg['training'] != str(root)):
            raise ValueError('previous evaluation stage must use this training plan')
        if previous is not None:
            if previous_cfg['targets_sha256'] != sha256(targets) or previous_cfg['prompt_sha256'] != prompt_hashes or previous_cfg.get('job_prefix')!=job_prefix:
                raise ValueError('previous targets, prompt files or job prefix changed')
            for path,digest in read(previous_path/'checkpoint_inputs_sha256.json').items():
                if evidence.get(path) != digest:
                    raise ValueError('previous checkpoint changed or is no longer complete')
        elif any(previous_cfg['prompt_sha256'].get(path)!=digest for path,digest in prompt_hashes.items()):
            raise ValueError('Frozen reference prompt files changed')
        prior_records = {r['run_id']:r for name in ('index_k4.json','index_k2_k8.json') for r in read(previous_path/name) if r['seed'] in selected and (reuse_frozen is None or (r['arm']=='Frozen' and r['derivative_id'] in target_by_id and r['workload'] in target_by_id[r['derivative_id']]['workloads']))}
        prior_jobs = [j for j in lines(previous_path/('effective_jobs.jsonl' if (previous_path/'effective_jobs.jsonl').exists() else 'jobs.jsonl')) if j['name'] in prior_records]
    # Do not choose workloads/targets based on observed checkpoint results.
    plan_spec = dict(base_id=spec['base_id'],base_revision=spec['base_revision'],targets=target_rows,
                     checkpoints=checkpoints,K=[4],evaluation_seed=0,max_new_tokens=512)
    out = Path(output).resolve()
    primary = schedule(plan_spec, out/'runs')
    secondary = schedule(plan_spec | dict(K=[2,8],checkpoints=[c for c in checkpoints if c['arm'] in ('FS','Frozen')]),out/'runs')
    jobs = []
    for record in primary+secondary:
        if job_prefix and record['arm']!='Frozen':
            record['run_id']=job_prefix+'-'+record['run_id']
            record['run_dir']=str(out/'runs'/record['run_id'])
            record['argv'][record['argv'].index('--output')+1]=record['run_dir']
            record['env']['VLLM_CACHE_ROOT']=str(Path(record['run_dir'])/'vllm_cache')
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
        completed_only=completed_only,previous=str(previous_path) if previous is not None else None,training_seeds=selected,
        reuse_frozen=str(previous_path) if reuse_frozen is not None else None,job_prefix=job_prefix,allow_validation_pending=allow_validation_pending,
        analysis_versions={p:importlib.metadata.version(p) for p in ('numpy','scipy')}),
        dict(n_jobs=len(jobs),n_effective_jobs=len(prior_jobs)+len(jobs),n_primary=len(primary),n_secondary=len(secondary),submitted=False,
             training_complete=not pending and not validation_pending,checkpoints_ready=not pending,n_pending_training=len(pending),pending_training=pending,
             n_validation_pending=len(validation_pending),validation_pending=validation_pending,
             n_excluded_training=len(excluded),excluded_training=excluded,exploratory_single_seed=len(selected)==1,
             checkpoint_loadability='pending first vLLM cells',owner_gate_decision='pending',
             next=('Preflight K4 only; use followspec.pilot_report for descriptive single-seed evidence, not Gate3.' if len(selected)==1 else 'Preflight and dispatch to free A40s. Aggregate index_k4 with B7; K2/8 are separate FS/Frozen diagnostics.')))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('training','targets','output','python'):p.add_argument('--'+name,required=True)
    p.add_argument('--code-repo');p.add_argument('--completed-only',action='store_true');p.add_argument('--previous')
    p.add_argument('--training-seeds',type=int,nargs='+',help='explicit exploratory seed scope; defaults to all three seeds')
    p.add_argument('--allow-validation-pending',action='store_true');p.add_argument('--reuse-frozen');p.add_argument('--job-prefix')
    a=p.parse_args()
    print(evaluation_jobs(a.training,a.targets,a.output,python=a.python,code_repo=a.code_repo,completed_only=a.completed_only,previous=a.previous,training_seeds=a.training_seeds,allow_validation_pending=a.allow_validation_pending,reuse_frozen=a.reuse_frozen,job_prefix=a.job_prefix))


if __name__=='__main__':main()
