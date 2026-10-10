import pytest
import torch
from followspec.family_repair import configure_variant, supervision_source
from followspec.tests.test_family_repair import Tiny


def test_default_supervision_unchanged_and_generation_provenance_enforced():
    child = dict(id='child', revision='c', path='/child')
    parent = dict(id='parent', revision='p', path='/parent')
    rows = [dict(generation_target='child', generation_revision='c')]
    assert supervision_source(child, rows, None) == child
    assert supervision_source(child, rows, parent) == parent
    with pytest.raises(ValueError):
        supervision_source(parent, rows, None)
    with pytest.raises(ValueError):
        supervision_source(child, rows, dict(id='parent'))


@pytest.mark.parametrize('variant', ['decoder_dense', 'decoder_qo'])
def test_full_rank_decoder_freezes_interface_head_and_embeddings(variant):
    m = Tiny()
    m.layers[0]['o_proj'] = torch.nn.Linear(2, 2, bias=False)
    proof = configure_variant(m, variant)
    names = proof['trainable_names']
    assert names and all(n.startswith('layers.') for n in names)
    if variant == 'decoder_qo':
        assert all('.q_proj.' in n or '.o_proj.' in n for n in names)
    assert not m.fc.weight.requires_grad
    assert not m.lm_head.weight.requires_grad
    assert not m.embed_tokens.weight.requires_grad
