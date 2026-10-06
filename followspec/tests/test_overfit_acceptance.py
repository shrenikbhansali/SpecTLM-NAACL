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
