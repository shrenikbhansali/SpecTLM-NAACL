import pytest

from atlas.census_summary import paired_acceptance
from atlas.run_cell import metrics


def row(name, accepted, drafted=None):
    return dict(prompt_id=name, per_step_accepted=accepted,
                per_step_drafted=[1] * len(accepted) if drafted is None else drafted,
                completion_token_ids=[9] * 4)


def test_one_sided_zero_removes_both_partners_before_macro_and_pooling():
    base = [row('a', [1, 0]), row('b', [1, 1])]
    child = [row('a', [1, 0]), row('b', [])]
    r = paired_acceptance(base, child, 1, metrics)
    assert r['ids'] == ['a'] and r['excluded_ids'] == ['b']
    assert r['n_total'] == 2 and r['n_paired'] == 1
    assert r['A00']['macro_p1'] == r['A00']['pooled_p1'] == .5
    assert r['retention']['macro_p1'] == r['retention']['pooled_p1'] == 1


def test_prompt_macro_and_pooled_steps_are_distinct_estimands():
    r = paired_acceptance([row('a', [1]), row('b', [0] * 9)],
                          [row('a', [1]), row('b', [1] * 9)], 1, metrics)
    assert r['A00']['macro_p1'] == .5
    assert r['A00']['pooled_p1'] == .1
    assert r['retention']['macro_p1'] == 2
    assert r['retention']['pooled_p1'] == 10
    assert r['retention']['tau'] == pytest.approx(4 / 3)


def test_prompt_ids_are_paired_by_identity_not_row_order():
    base = [row('a', [1]), row('b', [0])]
    child = [row('b', [1]), row('a', [0])]
    r = paired_acceptance(base, child, 1, metrics)
    assert r['ids'] == ['a', 'b']
    assert r['paired'][0]['A00']['p1'] == 1
    assert r['paired'][0]['A10']['p1'] == 0


@pytest.mark.parametrize('other', [[row('different', [1])],
                                  [row('a', [1]), row('a', [1])]])
def test_missing_or_duplicate_ids_fail(other):
    with pytest.raises(ValueError):
        paired_acceptance([row('a', [1])], other, 1, metrics)


@pytest.mark.parametrize('bad', [row('a', [2]), row('a', [1], []),
                               row('a', [True]), row('a', [0], [0])])
def test_counters_are_validated_by_the_supplied_frozen_metric_function(bad):
    with pytest.raises(ValueError):
        paired_acceptance([row('a', [1])], [bad], 1, metrics)


def test_all_zero_is_explicitly_undefined_not_a_perfect_retention():
    r = paired_acceptance([row('a', [])], [row('a', [])], 1, metrics)
    assert r['n_paired'] == 0 and r['excluded_ids'] == ['a']
    assert r['A00'] is None and r['A10'] is None and r['retention'] is None


def test_zero_parent_acceptance_has_undefined_ratio():
    r = paired_acceptance([row('a', [0])], [row('a', [1])], 1, metrics)
    assert r['retention']['macro_p1'] is None
    assert r['retention']['pooled_p1'] is None
    assert r['retention']['tau'] == 2
