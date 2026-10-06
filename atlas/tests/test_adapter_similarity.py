import pytest
import torch
from atlas.adapter_similarity import cosine_updates


def test_factor_cosine_matches_materialized_union():
    g=torch.Generator().manual_seed(42)
    a={'q':(torch.randn(5,2,generator=g),torch.randn(2,4,generator=g),2.),
       'v':(torch.randn(5,1,generator=g),torch.randn(1,4,generator=g),3.)}
    b={'q':(torch.randn(5,3,generator=g),torch.randn(3,4,generator=g),0.5)}
    av=torch.cat([(s*B@A).flatten() for B,A,s in a.values()])
    bv=torch.cat([(b['q'][2]*b['q'][0]@b['q'][1]).flatten(),torch.zeros(20)])
    assert cosine_updates(a,b)==pytest.approx(torch.nn.functional.cosine_similarity(av,bv,dim=0).item(),abs=1e-7)
    assert cosine_updates(a,a)==pytest.approx(1)


def test_zero_update_is_undefined():
    x={'q':(torch.zeros(5,2),torch.ones(2,4),1.)}
    assert cosine_updates(x,x) is None
