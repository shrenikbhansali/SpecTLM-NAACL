import copy
import json
import pytest
import torch
from safetensors import safe_open
from safetensors.torch import save_file,load_file
from followspec.adapter_views import canonical_bank,validate_view
from followspec.tests.test_mixture_targets import registry_fixture
from atlas.run_cell import sha256


def test_explicit_vllm_view_retains_all_lora_factors_and_originals(tmp_path):
    reg=registry_fixture(tmp_path);reg.pop('mixed');source=tmp_path/'a/adapter_model.safetensors'
    tensors=load_file(str(source));tensors['base_model.model.lm_head.base_layer.weight']=torch.ones(4,3)
    save_file(tensors,str(source));reg['a']['files_sha256']['adapter_model.safetensors']=sha256(source)
    before=source.read_bytes();result=canonical_bank(reg,tmp_path/'views')
    assert result['b']==reg['b'] and source.read_bytes()==before
    actual=load_file(str(__import__('pathlib').Path(result['a']['path'])/'adapter_model.safetensors'))
    assert set(actual)==set(tensors)-{'base_model.model.lm_head.base_layer.weight'}
    assert all(torch.equal(v,actual[k]) for k,v in tensors.items() if k in actual)
    validate_view(result['a'])
    assert result['a']['revision']==reg['a']['revision']
    assert result['a']['normalization']['policy']=='vllm_0.31.0_base_embedding_skip'
    bad=copy.deepcopy(result['a']);bad['normalization']['policy']='ignore-arbitrary-weights'
    with pytest.raises(ValueError,match='policy'):validate_view(bad)


def test_unknown_non_lora_parameters_cannot_be_dropped(tmp_path):
    reg=registry_fixture(tmp_path);reg.pop('mixed');source=tmp_path/'a/adapter_model.safetensors'
    tensors=load_file(str(source));tensors['base_model.model.arbitrary.weight']=torch.ones(4,3)
    save_file(tensors,str(source));reg['a']['files_sha256']['adapter_model.safetensors']=sha256(source)
    with pytest.raises(ValueError,match='unsupported'):canonical_bank(reg,tmp_path/'views')
