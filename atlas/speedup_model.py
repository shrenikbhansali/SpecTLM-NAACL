"""Descriptive fixed-K serving-cost fit; never computes acceptance metrics.

At fixed hardware, batch, target, workload and drafter architecture, fit
seconds/output-token = intercept + step_cost / macro_tau. This is an empirical
conversion, not a causal model: lengths and scheduling can break it. K is fixed
by the observations and cannot be extrapolated. Validate on held-out timing
conditions before interpreting predictions as measured speedups.
"""
from __future__ import annotations

import numpy as np


def fit_cost_model(tau, seconds_per_token, *, k: int) -> dict:
    tau = np.asarray(tau, dtype=float)
    y = np.asarray(seconds_per_token, dtype=float)
    if (tau.ndim != 1 or tau.shape != y.shape or len(tau) < 2
            or not np.all(np.isfinite(tau)) or not np.all(np.isfinite(y))
            or not isinstance(k, int) or k < 1
            or np.any(tau < 1) or np.any(tau > k + 1) or np.any(y <= 0)):
        raise ValueError('Require finite positive costs and 1 <= tau <= K+1')
    if np.ptp(1 / tau) < 1e-10:
        raise ValueError('Two cost coefficients require distinct acceptance values')
    x = np.column_stack([np.ones(len(tau)), 1 / tau])
    # Exact two-variable nonnegative least squares: feasible interior or either
    # nonnegative axis. No unconstrained negative physical costs are retained.
    candidates = [np.array([y.mean(), 0.]),
                  np.array([0., np.dot(x[:, 1], y) / np.dot(x[:, 1], x[:, 1])])]
    interior = np.linalg.lstsq(x, y, rcond=None)[0]
    if np.all(interior >= 0):
        candidates.append(interior)
    coef = min(candidates, key=lambda c: np.sum((x @ c - y) ** 2))
    residual = y - x @ coef
    return dict(k=k, intercept_s=float(coef[0]), step_s=float(coef[1]),
                tau_min=float(tau.min()), tau_max=float(tau.max()),
                boundary_fit=bool(np.any(coef == 0)), n_conditions=len(tau),
                residual_rmse_s=float(np.sqrt(np.mean(residual ** 2))),
                residuals_s=residual.tolist(),
                formula='seconds_per_output_token = intercept_s + step_s / tau',
                scope='fixed hardware, batch, target, workload, drafter architecture and K')


def predict_cost(model: dict, tau: float, *, k: int) -> dict:
    if k != model['k']:
        raise ValueError('K extrapolation is unidentified by this fixed-K fit')
    if not np.isfinite(tau) or not 1 <= tau <= k + 1:
        raise ValueError('Require finite 1 <= tau <= K+1')
    seconds = model['intercept_s'] + model['step_s'] / tau
    return dict(seconds_per_token=float(seconds), tokens_per_second=float(1 / seconds),
                outside_calibration_range=bool(tau < model['tau_min'] or tau > model['tau_max']))
