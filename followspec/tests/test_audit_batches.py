import pytest
from followspec.audit_batches import inspect_batches, inspect_splits


class Sampler:
    def __init__(self, batch_max_length, lengths, num_replicas, rank, seed):
        self.indices = list(range(rank, len(lengths), num_replicas))
    def set_epoch(self, epoch): pass
    def __iter__(self): return iter([self.indices])


def test_exact_coverage_tokens_and_seed_steps_without_loading_models():
    lengths = {arm: [3, 4] for arm in ['FS', 'MVD', 'PO-D', 'PO-T']}
    report = inspect_batches(lengths, factory=Sampler, batch_max_length=8, seeds=[0, 1], epochs=1, replicas=1)
    assert report['optimizer_steps'] == 1
    assert report['token_budget'] == 7
    assert len(report['batches']) == 8


def test_distributed_tail_drop_is_rejected_even_if_nominal_budgets_match():
    class Dropping(Sampler):
        def __iter__(self): return iter([self.indices[:-1]])
    lengths = {arm: [3, 4, 2, 3] for arm in ['FS', 'MVD', 'PO-D', 'PO-T']}
    with pytest.raises(ValueError, match='dropped or duplicated'):
        inspect_batches(lengths, factory=Dropping, batch_max_length=8, seeds=[0], epochs=1, replicas=2)


def test_equal_tokens_do_not_imply_equal_optimizer_steps():
    class ShapeSampler(Sampler):
        def __init__(self, **kwargs):
            super().__init__(**kwargs); self.lengths = kwargs['lengths']
        def __iter__(self):
            return iter([[0], [1]] if self.lengths[0] == 5 else [[0, 1]])
    lengths = {arm: [3, 4] for arm in ['FS', 'MVD', 'PO-D', 'PO-T']}
    lengths['MVD'] = [5, 2]
    with pytest.raises(ValueError, match='optimizer steps'):
        inspect_batches(lengths, factory=ShapeSampler, batch_max_length=8, seeds=[0], epochs=1, replicas=1)


def test_cross_arm_training_validation_overlap_is_rejected():
    arms = {arm: {'samples': [{'prompt_sha256': 'train', 'split': 'train'},
                            {'prompt_sha256': 'val', 'split': 'val'}]}
            for arm in ['FS', 'MVD', 'PO-D', 'PO-T']}
    assert inspect_splits(arms) == {'train': 1, 'val': 1}
    arms['MVD']['samples'][0]['prompt_sha256'] = 'val'
    with pytest.raises(ValueError, match='cross-arm'):
        inspect_splits(arms)


def test_native_truncation_is_refused_before_sampler_construction():
    lengths = {arm: [9] for arm in ['FS', 'MVD', 'PO-D', 'PO-T']}
    with pytest.raises(ValueError, match='truncation'):
        inspect_batches(lengths, factory=Sampler, batch_max_length=8, seeds=[0], epochs=1, replicas=1)
