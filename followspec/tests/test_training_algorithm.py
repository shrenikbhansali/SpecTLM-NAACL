import pytest
from followspec.configs import load_presets,check_matched
from followspec.train_eagle3 import validate_training_layout


def test_dflash_profiles_keep_matched_controls_and_native_block_settings():
    arms=load_presets(algorithm='dflash');check_matched(arms)
    for cfg in arms.values():
        assert cfg['initialization']=='z-lab/LLaMA3.1-8B-Instruct-DFlash-UltraChat'
        assert cfg['block_size']==10 and cfg['max_anchors']==512 and cfg['gamma']==4.
        assert cfg['total_seq_len']==8192 and cfg['lr']==2e-5
        assert 'ttt_steps' not in cfg
        validate_training_layout(cfg,dict(schema='followspec_online_tokens_v1',sequence_layout='dflash_raw',token_budget_unit='raw sequence tokens'))


def test_dflash_cannot_consume_shifted_eagle_data_or_untested_offline_shards():
    cfg=load_presets(algorithm='dflash')['FS']
    with pytest.raises(ValueError,match='layout'):
        validate_training_layout(cfg,dict(schema='followspec_online_tokens_v1',sequence_layout='eagle_shift',token_budget_unit='shifted sequence tokens'))
    with pytest.raises(ValueError,match='online'):
        validate_training_layout(cfg,dict(schema='followspec_paired_features_v1',sequence_layout='dflash_raw',token_budget_unit='raw sequence tokens'))


def test_legacy_eagle_manifest_stays_compatible_and_unknown_algorithm_is_rejected():
    validate_training_layout(load_presets()['FS'],dict(schema='followspec_online_tokens_v1',token_budget_unit='shifted sequence tokens'))
    with pytest.raises(ValueError,match='algorithm'):load_presets(algorithm='unknown')
