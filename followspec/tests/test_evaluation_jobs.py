import json
from pathlib import Path
import pytest
from atlas.run_cell import write_new
from followspec.production_pipeline import read
from followspec.tests.test_training_jobs import final_stage
from followspec.training_jobs import training_jobs


def completed_training(tmp_path):
    final=final_stage(tmp_path)
    jobs=training_jobs(final,tmp_path/'training',python='/native/python')
    for j in [json.loads(s) for s in (jobs/'jobs.jsonl').read_text().splitlines()]:
        a=j['args'];cmd=a[a.index('--')+1:];arm=cmd[cmd.index('--arm')+1];seed=int(cmd[cmd.index('--seed')+1])
        run=Path(cmd[cmd.index('--output')+1]);run.mkdir(parents=True)
        cfg=read(final/arm/'training_config.json')
        write_new(run/'config.json',dict(training_config=cfg,seed=seed,code_commit='c'*40,
            base_revision='a'*40,backend_revision=cfg['backend_revision'],dry_run=False,
            release_grad_before_forward=True,offload_saved_tensors=True,torch_compile_disable='0'))
        write_new(run/'results.json',dict(status='trained_pending_vllm_acceptance',optimizer_steps=1,
            token_budget=1000,checkpoints=str(run/'checkpoints')))
        ck=run/'checkpoints/0';ck.mkdir(parents=True)
        write_new(ck/'config.json',{'speculators_config':{'algorithm':'eagle3'}})
        (ck/'model.safetensors').write_bytes(b'test fixture only')
    prompts=tmp_path/'eval.jsonl';prompts.write_text(json.dumps(dict(prompt_id='eval-1',prompt='hi',rendered_token_ids=[1,2]))+'\n')
    targets=tmp_path/'targets.json'
    write_new(targets,dict(targets=[dict(model_id='base',revision='a'*40,pool='base',workloads=dict(speed=str(prompts))),
        dict(model_id='heldout',revision='e'*40,pool='test',adapter='/adapter',max_lora_rank=128,workloads=dict(speed=str(prompts)))]))
    return jobs,targets


def test_matched_lora_exact_tokens_and_requested_k_scope(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path)
    out=evaluation_jobs(training,targets,tmp_path/'eval',python='/eval/python')
    jobs=[json.loads(s) for s in (out/'jobs.jsonl').read_text().splitlines()]
    primary=read(out/'index_k4.json');secondary=read(out/'index_k2_k8.json')
    assert len(jobs)==81 and len(primary)==45 and len(secondary)==36
    assert {r['arm'] for r in secondary}=={'FS','Frozen'}
    index={r['run_id']:r for r in primary+secondary}
    for job in jobs:
        assert job['allowed_nodes']==[f'heck-srv{i}' for i in range(1,6)]
        a=job['args'];split=a.index('--');cmd=a[split+1:];record=index[job['name']]
        assert cmd[0]=='/eval/python' and '--use-prompt-token-ids' in cmd
        assert '--allow-h200-training' not in a and a[a.index('--task')+1]=='M4'
        assert cmd[cmd.index('--batch-size')+1]=='8' and cmd[cmd.index('--seed')+1]=='0'
        assert 'VLLM_CACHE_ROOT={out_dir}/vllm_cache' in a
        assert record['run_dir']==cmd[cmd.index('--output')+1]
        if record['derivative_id']=='heldout':
            assert '--enable-lora' in cmd and cmd[cmd.index('--max-lora-rank')+1]=='128'
            assert ('--adapter' in cmd)==(record['cell'] in {'A10','A11'})
    assert read(out/'results.json')['submitted'] is False


def test_missing_training_result_refuses_partial_matrix(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path)
    (training/'runs/m3-fs-s0/results.json').unlink()
    with pytest.raises(ValueError,match='completed M3'):evaluation_jobs(training,targets,tmp_path/'eval',python='python')
    assert not (tmp_path/'eval').exists()


def test_actual_training_controls_must_match(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path);p=training/'runs/m3-po-t-s0/config.json';c=read(p);c['training_config']['lr']=.01;p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='training config'):evaluation_jobs(training,targets,tmp_path/'eval',python='python')


def test_empty_export_refused(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path);(training/'runs/m3-fs-s0/checkpoints/0/model.safetensors').write_bytes(b'')
    with pytest.raises(ValueError,match='export'):evaluation_jobs(training,targets,tmp_path/'eval',python='python')


def test_raw_prompt_input_refused(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path);(tmp_path/'eval.jsonl').write_text('{"prompt_id":"x","prompt":"hi"}\n')
    with pytest.raises(ValueError,match='rendered'):evaluation_jobs(training,targets,tmp_path/'eval',python='python')


def test_failed_training_is_not_a_finished_checkpoint(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path);write_new(training/'runs/m3-fs-s0/failure.rank0.json',{'error':'failed'})
    with pytest.raises(ValueError,match='completed M3'):evaluation_jobs(training,targets,tmp_path/'eval',python='python')


def test_generated_primary_matrix_roundtrips_through_unchanged_b7(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    from followspec.evaluate import aggregate,load_measurements
    from atlas.run_cell import metrics
    training,targets=completed_training(tmp_path)
    out=evaluation_jobs(training,targets,tmp_path/'eval',python='python')
    primary=read(out/'index_k4.json')
    for record in primary:
        cmd=record['argv'];value=lambda k:cmd[cmd.index(k)+1]
        path=Path(record['run_dir']);path.mkdir(parents=True)
        cfg=dict(code_dirty=False,K=4,seed=0,max_new_tokens=512,batch_size=8,max_model_len=4096,
            dtype='bfloat16',temperature=0.,top_p=1.,engine_version='0.31.0',prompt_sha256='same',
            target=value('--target'),target_revision=value('--target-revision'),
            adapter=value('--adapter') if '--adapter' in cmd else None,
            adapter_revision=value('--adapter-revision') if '--adapter' in cmd else None,
            adapter_files_sha256={'weights':'e'*64} if '--adapter' in cmd else None,
            drafter=value('--drafter'),drafter_revision=value('--drafter-revision'),method='eagle3',
            max_lora_rank=int(value('--max-lora-rank')) if '--max-lora-rank' in cmd else 64,
            gpu_memory_utilization=.7,enable_prefix_caching=False,enable_lora='--enable-lora' in cmd,use_prompt_token_ids=True)
        write_new(path/'config.json',cfg)
        write_new(path/'results.json',dict(n=1,macro_acceptance_length=3.,engine_version='0.31.0'))
        (path/'per_prompt.jsonl').write_text(json.dumps(dict(prompt_id='eval-1',**metrics([2,2],[4,4],4)))+'\n')
    summaries,rows=aggregate(load_measurements(primary))
    assert len(rows)==4 and all(c['median_gain_ci95']==[0.,0.] for c in summaries[0]['comparisons'].values())
    assert summaries[0]['owner_gate_decision']=='pending'


def test_workloads_need_parent_retention_cells(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path);spec=read(targets)
    spec['targets'][0]['workloads']={'other':str(tmp_path/'eval.jsonl')};targets.write_text(json.dumps(spec))
    with pytest.raises(ValueError,match='workload labels'):evaluation_jobs(training,targets,tmp_path/'eval',python='python')
    assert not (tmp_path/'eval').exists()


def test_incremental_jobs_reuse_previous_cells_and_finish_full_matrix(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path);saved={}
    for p in (training/'runs').glob('*/results.json'):
        if p.parent.name!='m3-fs-s0':saved[p]=p.read_bytes();p.unlink()
    first=evaluation_jobs(training,targets,tmp_path/'first',python='python',completed_only=True)
    assert len((first/'jobs.jsonl').read_text().splitlines())==36
    assert read(first/'results.json')['n_pending_training']==11
    old={r['run_id']:r['run_dir'] for r in read(first/'index_k4.json')+read(first/'index_k2_k8.json')}
    for p,data in saved.items():p.write_bytes(data)
    second=evaluation_jobs(training,targets,tmp_path/'second',python='python',previous=first)
    assert len((second/'jobs.jsonl').read_text().splitlines())==45
    assert len((second/'effective_jobs.jsonl').read_text().splitlines())==81
    assert read(second/'results.json')['training_complete'] is True
    new={r['run_id']:r['run_dir'] for r in read(second/'index_k4.json')+read(second/'index_k2_k8.json')}
    assert all(new[k]==v for k,v in old.items())


def test_completed_only_can_prepare_frozen_reference_before_training_finishes(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path)
    for p in (training/'runs').glob('*/results.json'):p.unlink()
    out=evaluation_jobs(training,targets,tmp_path/'eval',python='python',completed_only=True)
    assert len((out/'jobs.jsonl').read_text().splitlines())==27
    assert {r['arm'] for r in read(out/'index_k4.json')}=={'Frozen'}
    assert read(out/'results.json')['training_complete'] is False


def test_incremental_mode_does_not_skip_failed_training(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path);run=training/'runs/m3-fs-s0';(run/'results.json').unlink();write_new(run/'failure.rank0.json',{})
    with pytest.raises(ValueError,match='completed M3'):evaluation_jobs(training,targets,tmp_path/'eval',python='python',completed_only=True)


def test_incremental_reuse_refuses_changed_checkpoint(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path)
    first=evaluation_jobs(training,targets,tmp_path/'first',python='python')
    (training/'runs/m3-fs-s0/checkpoints/0/model.safetensors').write_bytes(b'different fixture')
    with pytest.raises(ValueError,match='checkpoint changed'):evaluation_jobs(training,targets,tmp_path/'second',python='python',previous=first)
    assert not (tmp_path/'second').exists()


def test_incremental_reuse_refuses_changed_prompts(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path)
    first=evaluation_jobs(training,targets,tmp_path/'first',python='python')
    (tmp_path/'eval.jsonl').write_text('{"prompt_id":"eval-1","prompt":"hi","rendered_token_ids":[3,4]}\n')
    with pytest.raises(ValueError,match='prompt'):evaluation_jobs(training,targets,tmp_path/'second',python='python',previous=first)


def test_single_seed_feasibility_ignores_only_unselected_runs(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training, targets = completed_training(tmp_path)
    for p in (training/'runs').iterdir():
        if not p.name.endswith('-s0'):
            write_new(p/'failure.rank0.json', {'error': 'owner stopped repetition'})
    out = evaluation_jobs(training, targets, tmp_path/'pilot', python='python', training_seeds=[0])
    primary = read(out/'index_k4.json')
    assert len(primary) == 15
    assert {r['seed'] for r in primary} == {0}
    assert {r['arm'] for r in primary} == {'FS','MVD','PO-D','PO-T','Frozen'}
    assert read(out/'results.json')['n_excluded_training'] == 8
    assert read(out/'results.json')['exploratory_single_seed'] is True
    assert read(out/'results.json')['training_complete'] is True


def test_single_seed_still_refuses_selected_failure(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training, targets = completed_training(tmp_path)
    write_new(training/'runs/m3-fs-s0/failure.rank0.json', {'error':'failed'})
    with pytest.raises(ValueError, match='completed M3'):
        evaluation_jobs(training, targets, tmp_path/'pilot', python='python', training_seeds=[0])


def test_single_seed_reuses_only_selected_prior_frozen_cells(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    training, targets = completed_training(tmp_path)
    saved={}
    for p in (training/'runs').glob('*/results.json'):
        saved[p]=p.read_bytes();p.unlink()
    prior = evaluation_jobs(training, targets, tmp_path/'prior', python='python', completed_only=True)
    for p, data in saved.items():
        if p.parent.name.endswith('-s0'):p.write_bytes(data)
    out = evaluation_jobs(training, targets, tmp_path/'pilot', python='python', previous=prior, training_seeds=[0])
    old = {r['run_id']:r['run_dir'] for r in read(prior/'index_k4.json')}
    assert all(r['run_dir']==old[r['run_id']] for r in read(out/'index_k4.json') if r['arm']=='Frozen')
    assert len(read(out/'index_k4.json'))==15
    jobs=[json.loads(l) for l in (out/'effective_jobs.jsonl').read_text().splitlines()]
    assert len(jobs)==27
    assert len((out/'jobs.jsonl').read_text().splitlines())==18


@pytest.mark.parametrize('seeds', [[],[0,0],[3],[-1],[True]])
def test_invalid_training_seed_scope_rejected(tmp_path,seeds):
    from followspec.evaluation_jobs import evaluation_jobs
    training,targets=completed_training(tmp_path)
    with pytest.raises(ValueError,match='training seeds'):
        evaluation_jobs(training,targets,tmp_path/'bad',python='python',training_seeds=seeds)
    assert not (tmp_path/'bad').exists()
