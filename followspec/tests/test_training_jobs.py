import json
import subprocess
import pytest
from atlas.run_cell import sha256,write_new
from followspec.configs import load_presets
from followspec.production_pipeline import finish,read

def final_stage(tmp_path, *, ready=True, alter=None):
    repo=tmp_path/'code';repo.mkdir();(repo/'atlas/env').mkdir(parents=True)
    (repo/'atlas/env/requirements.lock').write_text('vllm==0.31.0\n')
    for cmd in [['init','-q','-b','main'],['add','.'],['-c','user.name=test','-c','user.email=t@t','commit','-qm','fixture']]:
        subprocess.run(['git',*cmd],cwd=repo,check=True)
    stage=tmp_path/'final';stage.mkdir()
    spec=dict(code_repo=str(repo),python='generation-python',seed=20261006,base_id='meta-llama/Llama-3.1-8B-Instruct',
        base_revision='a'*40,base_snapshot=str(tmp_path/('a'*40)),drafter_revision='d'*40,drafter_snapshot=str(tmp_path/('d'*40)))
    for arm,cfg in load_presets().items():
        p=stage/arm;p.mkdir();mask=p/'decoded_masks.jsonl';mask.write_text('reviewed fixture\n')
        cfg.update(initialization_revision='d'*40,token_budget=1000,optimizer_steps=1)
        if alter:alter(arm,cfg)
        write_new(p/'training_config.json',cfg)
        write_new(p/'manifest.json',dict(schema='followspec_online_tokens_v1',arm=arm,base_revision='a'*40,
            initialization_revision='d'*40,token_budget=1000,optimizer_steps=1,data_acceptance_passed=True,
            acceptance_only=False,sample_mask_audit=dict(path=str(mask),sha256=sha256(mask))))
    finish(stage,dict(stage='finalize',spec=spec),dict(production_ready=ready,data_ready=True,training_capacity_verified=True,blockers=[]))
    return stage

def test_twelve_jobs_keep_controls_seeds_pins_and_memory_flags(tmp_path):
    from followspec.training_jobs import training_jobs
    stage=final_stage(tmp_path);out=training_jobs(stage,tmp_path/'jobs',python='/native/bin/python')
    jobs=[json.loads(s) for s in (out/'jobs.jsonl').read_text().splitlines()];assert len(jobs)==12;seen=[]
    for j in jobs:
        a=j['args'];i=a.index('--');launch=a[:i];cmd=a[i+1:];arm=cmd[cmd.index('--arm')+1];seed=int(cmd[cmd.index('--seed')+1]);seen.append((seed,arm))
        assert launch[launch.index('--seed')+1]==str(seed) and '--allow-h200-training' in launch
        assert cmd[0]=='/native/bin/python' and cmd[cmd.index('--manifest')+1]==str(stage/arm/'manifest.json')
        assert '--release-grad-before-forward' in cmd and '--offload-saved-tensors' in cmd and '--allow-a40-production' in cmd
        assert 'TORCH_COMPILE_DISABLE=0' in launch
        assert cmd[cmd.index('--configs')+1:cmd.index('--configs')+5]==[str(stage/a/'training_config.json') for a in ('FS','MVD','PO-D','PO-T')]
    assert seen==[(s,a) for s in range(3) for a in ('FS','MVD','PO-D','PO-T')]
    assert read(out/'results.json')['n_jobs']==12

def test_unready_stage_is_rejected_without_output(tmp_path):
    from followspec.training_jobs import training_jobs
    stage=final_stage(tmp_path,ready=False)
    with pytest.raises(ValueError,match='readiness'):training_jobs(stage,tmp_path/'jobs',python='/native/bin/python')
    assert not (tmp_path/'jobs').exists()

def test_unintended_control_change_is_rejected(tmp_path):
    from followspec.training_jobs import training_jobs
    stage=final_stage(tmp_path,alter=lambda a,c:c.update(lr=.01) if a=='PO-T' else None)
    with pytest.raises(ValueError,match='unintended'):training_jobs(stage,tmp_path/'jobs',python='/native/bin/python')
    assert not (tmp_path/'jobs').exists()

def test_changed_manifest_is_rejected(tmp_path):
    from followspec.training_jobs import training_jobs
    stage=final_stage(tmp_path);(stage/'FS/manifest.json').write_text('{}')
    with pytest.raises(ValueError,match='stage changed'):training_jobs(stage,tmp_path/'jobs',python='/native/bin/python')
    assert not (tmp_path/'jobs').exists()

def test_existing_output_is_preserved(tmp_path):
    from followspec.training_jobs import training_jobs
    stage=final_stage(tmp_path);out=tmp_path/'jobs';out.mkdir();(out/'sentinel').write_text('keep')
    with pytest.raises(FileExistsError):training_jobs(stage,out,python='/native/bin/python')
    assert [p.name for p in out.iterdir()]==['sentinel']
