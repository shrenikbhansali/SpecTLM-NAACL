import pytest
from followspec.configs import load_presets, check_matched, validate_eagle_family


def test_qwen_eagle_presets_change_initialization_only():
    llama=load_presets();qwen=load_presets(family='qwen3')
    assert check_matched(qwen)==check_matched(llama)
    for arm in llama:
        assert qwen[arm]['initialization']=='RedHatAI/Qwen3-8B-speculator.eagle3'
        assert {k:v for k,v in qwen[arm].items() if k!='initialization'}=={k:v for k,v in llama[arm].items() if k!='initialization'}


def test_unknown_family_is_not_silently_treated_as_llama():
    with pytest.raises(ValueError,match='family'):load_presets(family='unknown')


def test_qwen_target_and_checkpoint_verifier_family_must_match():
    base={'model_type':'qwen3'}
    draft={'speculators_config':{'algorithm':'eagle3','verifier':{'architectures':['Qwen3ForCausalLM']}}}
    validate_eagle_family('qwen3',base,draft)
    with pytest.raises(ValueError,match='family'):validate_eagle_family('llama',base,draft)
    draft['speculators_config']['verifier']['architectures']=['LlamaForCausalLM']
    with pytest.raises(ValueError,match='family'):validate_eagle_family('qwen3',base,draft)
