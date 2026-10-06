import copy
import pytest
from followspec.tests.test_paired_trimming import fixture, assemble
from followspec.paired_responses import pair_runs
from followspec.token_data import validate_paired_arms, validate_arm_set


def test_mixture_pair_scope_does_not_require_fabricating_an_mvd_mixture(tmp_path):
    child, base = fixture(tmp_path)
    arms = assemble(pair_runs(child, base, child_id='c'))
    pair = {k: v for k, v in arms.items() if k != 'MVD'}
    assert validate_paired_arms(pair)['shifted_sequence_tokens'] == 4
    with pytest.raises(ValueError, match='four arms'):
        validate_arm_set(pair)
    with pytest.raises(ValueError, match='three paired arms'):
        validate_paired_arms(arms)


@pytest.mark.parametrize('field', ['context_token_ids', 'response_view', 'token_budget'])
def test_partial_pair_validation_still_rejects_tampered_controls(tmp_path, field):
    child, base = fixture(tmp_path)
    arms = assemble(pair_runs(child, base, child_id='c'))
    pair = copy.deepcopy({k: v for k, v in arms.items() if k != 'MVD'})
    if field == 'token_budget':
        pair['PO-D'][field] += 1
    elif field == 'response_view':
        pair['PO-D']['samples'][0][field]['peer_record_index'] += 1
    else:
        pair['PO-D']['samples'][0][field][0] += 1
    with pytest.raises(ValueError):
        validate_paired_arms(pair)
