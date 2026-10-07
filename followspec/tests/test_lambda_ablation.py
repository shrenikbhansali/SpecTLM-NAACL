import copy
import json
import pytest
from followspec.configs import load_presets,check_matched
from followspec.tests.test_training_jobs import final_stage
from followspec.production_pipeline import read,lines,checked_stage
from followspec.training_jobs import training_jobs

@pytest.mark.parametrize('value',[0.,.03,.1,.3])
def test_explicit_approved_grid_and_default_unchanged(value):
    arms=load_presets();arms['FS']['delta_lambda']=value
    if value != .1:
        with pytest.raises(ValueError):check_matched(arms)
    check_matched(arms,fs_delta_lambda=value,ablation_decision='D-39')
    arms['PO-T']['lr']=.01
    with pytest.raises(ValueError,match='unintended'):check_matched(arms,fs_delta_lambda=value,ablation_decision='D-39')

@pytest.mark.parametrize('value,decision',[(.2,'D-39'),(float('nan'),'D-39'),(.3,None),(None,'D-39'),(.3,'D-38')])
def test_unapproved_override_rejected(value,decision):
    with pytest.raises(ValueError):check_matched(load_presets(),fs_delta_lambda=value,ablation_decision=decision)


def pilot(tmp_path):
    stage=final_stage(tmp_path,alter=lambda a,c:c.update(seeds=[0],pilot={'decision_id':'D-38','scope':'exploratory'}))
    return training_jobs(stage,tmp_path/'source',python='/native/python',training_seeds=[0],job_prefix='pilot')


def test_ablation_reuses_exact_data_controls_and_only_three_new_jobs(tmp_path):
    from followspec.lambda_ablation import build
    source=pilot(tmp_path);original={j['name']:j for j in lines(source/'jobs.jsonl')}
    out=build(source,tmp_path/'ablation',code_repo=tmp_path/'code')
    new=lines(out/'dispatch.jsonl');assert len(new)==3 and len({j['name'] for j in new})==3
    info=read(out/'config.json');assert info['reused_lambda']==.1
    for variant in info['variants']:
        training,cfg=checked_stage(variant['training']);final,_=checked_stage(cfg['finalized'])
        jobs=lines(training/'jobs.jsonl');assert len(jobs)==4
        source_final=read(source/'config.json')['finalized']
        from pathlib import Path
        for arm in ('FS','MVD','PO-D','PO-T'):
            expected=read(Path(source_final)/arm/'training_config.json')
            if arm=='FS':expected['delta_lambda']=variant['value']
            assert read(final/arm/'training_config.json')==expected
            assert read(final/arm/'manifest.json')==read(Path(source_final)/arm/'manifest.json')
        fs=next(j for j in jobs if j['name'] not in original)
        assert fs in new and '--ablation-decision' in fs['args'] and '--offload-saved-tensors' in fs['args']
        assert all(j==original[j['name']] for j in jobs if j!=fs)
        assert read(final/'FS/training_config.json')['optimizer_steps']==1


def test_source_tampering_rejected(tmp_path):
    from followspec.lambda_ablation import build
    source=pilot(tmp_path);(source/'jobs.jsonl').write_text('')
    with pytest.raises(ValueError,match='stage changed'):build(source,tmp_path/'ablation',code_repo=tmp_path/'code')
    assert not (tmp_path/'ablation').exists()
