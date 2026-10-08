import pytest
from followspec.independent_probe import agreement_counts, validate_probe, transfer_candidates


def test_greedy_probe_causal_alignment_and_answer_mask():
    row=dict(input_ids=[10,11,12,13,14],response_start=3,loss_mask=[False,False,False,True,True])
    assert agreement_counts([0,0,13,99],row)==(1,2)
    assert agreement_counts([0,0,13,14],row)==(2,2)
    with pytest.raises(ValueError):agreement_counts([13,14],row)


def test_probe_is_reserved_and_precutoff():
    rows=[dict(prompt_sha256='abc',source_pool='bank')]
    validate_probe(rows,[dict(prompt_sha256='def')])
    with pytest.raises(ValueError):validate_probe(rows,[dict(prompt_sha256='abc')])
    with pytest.raises(ValueError):validate_probe([dict(prompt_sha256='abc',source_pool='test')],[])


def test_transfer_donor_cannot_be_target():
    donors=[dict(id='a',source_model='child-a'),dict(id='b',source_model='child-b')]
    assert transfer_candidates(donors,'child-a')==[donors[1]]
