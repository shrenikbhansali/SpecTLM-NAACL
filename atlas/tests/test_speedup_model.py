import numpy as np
import pytest

from atlas.speedup_model import fit_cost_model, predict_cost


def test_known_cost_recovered_and_holdout_predicted():
    tau = np.array([1.7, 2.0, 2.2, 2.4])
    model = fit_cost_model(tau, .002 + .03 / tau, k=4)
    assert model['intercept_s'] == pytest.approx(.002)
    assert model['step_s'] == pytest.approx(.03)
    prediction = predict_cost(model, 2.6, k=4)
    assert prediction['seconds_per_token'] == pytest.approx(.002 + .03 / 2.6)
    assert prediction['outside_calibration_range']


def test_physical_boundary_not_negative_step_cost():
    model = fit_cost_model([1.5, 2, 2.5], [.01, .02, .03], k=4)
    assert model['step_s'] == 0
    assert model['intercept_s'] == pytest.approx(.02)


def test_negative_intercept_projects_to_nnls_boundary():
    tau = np.array([1.5, 2., 2.5])
    y = -.001 + .02 / tau
    model = fit_cost_model(tau, y, k=4)
    assert model['intercept_s'] == 0
    assert model['step_s'] > 0
    assert model['boundary_fit']


@pytest.mark.parametrize('tau,cost', [([2, 2], [.01,.02]), ([0,2],[.01,.02]),
                                   ([1,2],[-.1,.02]), ([1,np.nan],[.01,.02])])
def test_invalid_or_unidentified_fit_rejected(tau,cost):
    with pytest.raises(ValueError):
        fit_cost_model(tau,cost,k=4)


def test_unknown_k_and_illegal_tau_rejected():
    model=fit_cost_model([1.5,2.], [.02,.016], k=4)
    for tau,k in [(2,6),(6,4),(0,4)]:
        with pytest.raises(ValueError): predict_cost(model,tau,k=k)
