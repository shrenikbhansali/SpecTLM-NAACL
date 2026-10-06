import json
import pytest
import torch
from followspec.verify_mixture import compare_logits, ensure_unpaused, cases


def test_acceptance_matrix_has_onehot_zero_and_three_scales():
    matrix=cases(0)
    assert len(matrix)==7
    assert [r['scale'] for r in matrix if r['kind']=='random']==[.5,1.,1.5]
    assert all(abs(sum(r['weights'])-1)<1e-6 for r in matrix)


def test_logit_report_exposes_max_errors_and_failures():
    report=compare_logits(torch.tensor([[1.,2.]]),torch.tensor([[1.,2.1]]),atol=.01,rtol=.01)
    assert not report['passed'] and report['max_absolute_difference']==pytest.approx(.1)
    assert report['max_relative_difference']==pytest.approx(.1/2.1)
    assert compare_logits(torch.zeros(1),torch.zeros(1),atol=0.,rtol=0.)['passed']
    with pytest.raises(ValueError):compare_logits(torch.tensor([float('nan')]),torch.zeros(1),atol=.1,rtol=.1)


def test_nested_historical_marker_blocks_real_acceptance(tmp_path):
    (tmp_path/'tlm-spec-maintenance').mkdir()
    (tmp_path/'tlm-spec-maintenance/EXPERIMENTS_PAUSED.json').write_text('{}')
    with pytest.raises(RuntimeError,match='paused'):ensure_unpaused(tmp_path/'worktree')
