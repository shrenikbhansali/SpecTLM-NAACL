import json
import pytest
from followspec.train_eagle3 import ensure_unpaused,resolve_plan
from followspec.configs import load_presets


def test_pause_recognizes_historical_marker(tmp_path):
    (tmp_path/'tlm-spec-maintenance').mkdir();(tmp_path/'tlm-spec-maintenance/EXPERIMENTS_PAUSED.json').write_text('{}')
    with pytest.raises(RuntimeError,match='paused'):ensure_unpaused(tmp_path/'nested')


def test_draft_configs_cannot_silently_supply_training_budget(tmp_path):
    config=load_presets()['FS'];manifest={'schema':'followspec_paired_features_v1','arm':'FS','token_budget':100,'optimizer_steps':1}
    with pytest.raises(ValueError,match='resolved'):resolve_plan(config,manifest,0)
    config|={'initialization_revision':'a'*40,'token_budget':100,'optimizer_steps':1}
    manifest['initialization_revision']='a'*40
    plan=resolve_plan(config,manifest,0)
    assert plan['training_config']['lr']==2e-5 and plan['training_config']['epochs']==1
    manifest['token_budget']=101
    with pytest.raises(ValueError,match='token_budget'):resolve_plan(config,manifest,0)
