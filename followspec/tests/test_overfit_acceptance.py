import pytest
from followspec.overfit_acceptance import validate_corpus


def test_fit_acceptance_requires_exactly64_distinct_bounded_training_responses():
    rows=[dict(sample_id=str(i),prompt_sha256=str(i),acceptance_only=True,split='train',
               generation_target='bank',completion_token_ids=[1,2]) for i in range(64)]
    validate_corpus(rows)
    for bad in [rows[:5],rows[:-1]+rows[:1],rows[:-1]+[rows[-1]|dict(acceptance_only=False)],
                rows[:-1]+[rows[-1]|dict(completion_token_ids=[1]*65)],
                rows[:-1]+[rows[-1]|dict(split='test')]]:
        with pytest.raises(ValueError):validate_corpus(bad)


def test_full_response_capacity_requires_explicit_source_scope_and_capped64_samples():
    from followspec.overfit_acceptance import validate_capacity
    rows=[dict(sample_id=str(i),prompt_sha256=str(i),acceptance_only=True,split='train',
        completion_token_ids=[1]*512,input_ids=[2,3]+[1]*512) for i in range(64)]
    source=dict(acceptance_only=True,capacity_smoke=True,max_new_tokens=512)
    validate_corpus(rows,capacity=True);validate_capacity(rows,source)
    with pytest.raises(ValueError):validate_corpus(rows)
    with pytest.raises(ValueError):validate_capacity(rows,source|dict(capacity_smoke=False))
    with pytest.raises(ValueError):validate_capacity(rows,source|dict(acceptance_only=False))
    with pytest.raises(ValueError):validate_corpus(rows+[rows[0]],capacity=True)
    short=[r|dict(completion_token_ids=[1]*64,input_ids=[2,3]+[1]*64) for r in rows]
    with pytest.raises(ValueError,match='512'):validate_capacity(short,source)


def test_acceptance_mixture_registry_requires_bounded_acceptance_rows(tmp_path):
    from followspec.overfit_acceptance import validate_acceptance_registry
    from followspec.tests.test_mixture_targets import registry_fixture
    from followspec.mixture_targets import validate_registry
    registry=registry_fixture(tmp_path)
    rows=[dict(sample_id=str(i),prompt_sha256=str(i),acceptance_only=True,split='train',
               generation_target='mixed',completion_token_ids=[1,2]) for i in range(64)]
    with pytest.raises(ValueError,match='acceptance'):validate_registry(registry)
    validate_acceptance_registry(registry,rows)
    for bad in [rows[:5],rows[:-1]+[rows[-1]|dict(acceptance_only=False)]]:
        with pytest.raises(ValueError):validate_acceptance_registry(registry,bad)
    registry['mixed']['files_sha256']['adapter_config.json']='bad'
    with pytest.raises(ValueError,match='hash'):validate_acceptance_registry(registry,rows)
