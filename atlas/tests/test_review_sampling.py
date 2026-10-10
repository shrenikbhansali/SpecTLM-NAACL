import pytest
from atlas.run_cell import sampling_options
from types import SimpleNamespace

def test_greedy_default_and_explicit_sampled_setting():
    a=SimpleNamespace(max_new_tokens=2048,seed=0)
    assert sampling_options(a)==dict(temperature=0.,top_p=1.,max_tokens=2048,seed=0)
    a.temperature=.6;a.top_p=.95
    assert sampling_options(a)==dict(temperature=.6,top_p=.95,max_tokens=2048,seed=0)
    a.temperature=-.1
    with pytest.raises(ValueError):sampling_options(a)
    a.temperature=float('nan')
    with pytest.raises(ValueError):sampling_options(a)
    a.temperature=.6;a.top_p=0
    with pytest.raises(ValueError):sampling_options(a)
