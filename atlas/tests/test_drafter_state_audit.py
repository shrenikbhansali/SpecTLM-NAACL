import torch
from types import SimpleNamespace
import pytest
from atlas.drafter_state_audit import tensor_fingerprint, inspect_worker


def test_fingerprint_covers_values_shape_and_dtype():
    x = torch.arange(6, dtype=torch.bfloat16).reshape(2, 3)
    assert tensor_fingerprint(x) == tensor_fingerprint(x.clone())
    assert tensor_fingerprint(x) != tensor_fingerprint(x + 1)
    assert tensor_fingerprint(x) != tensor_fingerprint(x.reshape(3, 2))
    assert tensor_fingerprint(x) != tensor_fingerprint(x.float())


def test_scalar_fingerprint():
    assert tensor_fingerprint(torch.tensor(1.))['shape']==[]


@pytest.mark.parametrize('field',['speculator','drafter'])
def test_both_pinned_runner_layouts(field):
    model=torch.nn.Linear(2,2,bias=False)
    model.config=SimpleNamespace(to_dict=lambda:dict(hidden_size=2))
    target=SimpleNamespace(model=SimpleNamespace(aux_hidden_state_layers=(2,16,29)))
    runner=SimpleNamespace(**{field:SimpleNamespace(model=model)},get_model=lambda:target)
    result=inspect_worker(SimpleNamespace(model_runner=runner))
    assert result['taps']==[2,16,29]
    assert result['weights']['weight']==tensor_fingerprint(model.weight)
