import copy
import pytest
from followspec.configs import load_presets,check_matched


def test_four_arms_only_intended_fields():
    arms=load_presets();diff=check_matched(arms)
    assert set(arms)=={'FS','MVD','PO-D','PO-T'}
    assert set(diff)<= {'arm','targets','responses','features','labels','delta_lambda','mixtures'}
    for arm in arms.values():
        assert arm['lr']==2e-5 and arm['epochs']==1 and arm['warmup_ratio']==.03
        assert arm['optimizer']=='adamw' and arm['parent_share']==.25
        assert arm['beta']==1 and arm['top_k']==32
        assert arm['seeds']==[0,1,2]


def test_unintended_training_difference_fails():
    arms=copy.deepcopy(load_presets());arms['PO-D']['lr']=1e-4
    with pytest.raises(ValueError,match='lr'):check_matched(arms)


def test_missing_arm_and_mvd_mixtures_fail():
    arms=load_presets();del arms['PO-T']
    with pytest.raises(ValueError):check_matched(arms)
    arms=load_presets();arms['MVD']['mixtures']=True
    with pytest.raises(ValueError):check_matched(arms)
