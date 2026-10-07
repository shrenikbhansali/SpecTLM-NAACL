import json
import shutil
from pathlib import Path
import pytest
from atlas.run_cell import write_new
from followspec.production_pipeline import read
from followspec.training_jobs import training_jobs
from followspec.tests.test_evaluation_jobs import completed_training


def pilot(tmp_path):
    old, targets=completed_training(tmp_path)
    new=training_jobs(tmp_path/'final',tmp_path/'pilot_training',python='/native/python',training_seeds=[0],job_prefix='m3-d38')
    for arm in ('fs','mvd','po-d','po-t'):
        shutil.copytree(old/f'runs/m3-{arm}-s0',new/f'runs/m3-d38-{arm}-s0')
    return old,new,targets


def seal(run,step=1,local_step=0):
    (run/'results.json').unlink()
    write_new(run/'checkpoints/0/training_state.json',dict(epoch=0,global_step=step,local_step=local_step))
    (run/'checkpoints/epoch0_end').symlink_to('0')


def test_four_run_plan_names_do_not_collide_with_full_budget(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    old,new,targets=pilot(tmp_path)
    full=evaluation_jobs(old,targets,tmp_path/'full',python='python',training_seeds=[0])
    short=evaluation_jobs(new,targets,tmp_path/'short',python='python',job_prefix='pilot-d38')
    a=read(full/'index_k4.json');b=read(short/'index_k4.json')
    assert {r['run_id'] for r in a if r['arm']!='Frozen'}.isdisjoint({r['run_id'] for r in b if r['arm']!='Frozen'})
    assert {r['run_id'] for r in a if r['arm']=='Frozen'}=={r['run_id'] for r in b if r['arm']=='Frozen'}
    assert len(b)==15 and {r['seed'] for r in b}=={0}
    assert read(short/'results.json')['training_complete'] is True


def test_sealed_final_checkpoint_can_overlap_validation_and_later_complete(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    _,new,targets=pilot(tmp_path);run=new/'runs/m3-d38-fs-s0';saved=(run/'results.json').read_bytes();seal(run)
    first=evaluation_jobs(new,targets,tmp_path/'first',python='python',allow_validation_pending=True,job_prefix='pilot-d38')
    r=read(first/'results.json')
    assert r['checkpoints_ready'] is True and r['training_complete'] is False
    assert r['n_validation_pending']==1 and r['validation_pending'][0]['arm']=='FS'
    (run/'results.json').write_bytes(saved)
    second=evaluation_jobs(new,targets,tmp_path/'second',python='python',allow_validation_pending=True,job_prefix='pilot-d38',previous=first)
    assert read(second/'results.json')['training_complete'] is True
    assert read(second/'results.json')['n_jobs']==0


@pytest.mark.parametrize('step,local_step',[(0,0),(2,0),(1,1)])
def test_interrupted_checkpoint_never_becomes_ready(tmp_path,step,local_step):
    from followspec.evaluation_jobs import evaluation_jobs
    _,new,targets=pilot(tmp_path);seal(new/'runs/m3-d38-fs-s0',step,local_step)
    with pytest.raises(ValueError,match='sealed final'):
        evaluation_jobs(new,targets,tmp_path/'bad',python='python',allow_validation_pending=True)


def test_unsealed_checkpoint_is_pending(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    _,new,targets=pilot(tmp_path);run=new/'runs/m3-d38-fs-s0';seal(run);(run/'checkpoints/epoch0_end').unlink()
    out=evaluation_jobs(new,targets,tmp_path/'out',python='python',allow_validation_pending=True,completed_only=True)
    assert read(out/'results.json')['n_pending_training']==1
    assert 'FS' not in {r['arm'] for r in read(out/'index_k4.json')}


def test_overlap_is_explicit_and_default_still_waits(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    _,new,targets=pilot(tmp_path);seal(new/'runs/m3-d38-fs-s0')
    with pytest.raises(ValueError,match='completed M3'):
        evaluation_jobs(new,targets,tmp_path/'bad',python='python')


def test_reference_reuse_across_training_plans_is_frozen_only(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    old,new,targets=pilot(tmp_path)
    prior=evaluation_jobs(old,targets,tmp_path/'prior',python='python')
    out=evaluation_jobs(new,targets,tmp_path/'out',python='python',reuse_frozen=prior,job_prefix='pilot-d38')
    before={r['run_id']:r['run_dir'] for r in read(prior/'index_k4.json')}
    now=read(out/'index_k4.json')
    assert all(r['run_dir']==before[r['run_id']] for r in now if r['arm']=='Frozen')
    assert all(r['run_dir'].startswith(str(out)) for r in now if r['arm']!='Frozen')
    jobs=[json.loads(s) for s in (out/'jobs.jsonl').read_text().splitlines()]
    assert len(jobs)==18 and all('Frozen' not in j['name'] for j in jobs)


def test_reuse_rejects_changed_external_prompts(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    old,new,targets=pilot(tmp_path);prior=evaluation_jobs(old,targets,tmp_path/'prior',python='python')
    (tmp_path/'eval.jsonl').write_text('{"prompt_id":"eval-1","rendered_token_ids":[9,10]}\n')
    with pytest.raises(ValueError,match='prompt'):
        evaluation_jobs(new,targets,tmp_path/'bad',python='python',reuse_frozen=prior)


def test_reuse_rejects_changed_decoding_python(tmp_path):
    from followspec.evaluation_jobs import evaluation_jobs
    old,new,targets=pilot(tmp_path);prior=evaluation_jobs(old,targets,tmp_path/'prior',python='python')
    with pytest.raises(ValueError,match='controls'):
        evaluation_jobs(new,targets,tmp_path/'bad',python='different-python',reuse_frozen=prior)


def test_evaluation_export_is_immutable_when_native_validation_adds_metadata(tmp_path):
    from followspec.evaluation_jobs import immutable_export
    src=tmp_path/'source';src.mkdir();write_new(src/'config.json',{'model':'fixture'})
    (src/'model.safetensors').write_bytes(b'model');(src/'config.py').write_text('# native config')
    (src/'optimizer_state_dict.pt').write_bytes(b'optimizer')
    out=immutable_export(src,tmp_path/'export')
    before={p.name:p.read_bytes() for p in out.iterdir()}
    write_new(src/'val_metrics.json',{'loss':1})
    assert immutable_export(src,out)==out
    assert {p.name:p.read_bytes() for p in out.iterdir()}==before
    assert 'optimizer_state_dict.pt' not in before and 'val_metrics.json' not in before
    (out/'model.safetensors').write_bytes(b'tampered')
    with pytest.raises(ValueError,match='export changed'):immutable_export(src,out)
