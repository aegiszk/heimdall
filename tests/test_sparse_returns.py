import os, sys, numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config import DEFAULT_GATE_CFG
from core.validation.battery import run_gate


def _finite_gate_values(res):
    return [
        value
        for value in [res.dsr, res.mc_p, res.boot_lo, res.nw_t, res.max_dd, res.wf_min]
        if value is not None
    ]


def test_sparse_active_returns_do_not_emit_nan_or_count_flat_bars():
    rng = np.random.default_rng(7)
    returns = np.zeros(1000)
    positions = np.zeros_like(returns)
    active_idx = np.arange(0, len(returns), 20)
    active_returns = rng.normal(0.002, 0.0005, len(active_idx))
    returns[active_idx] = active_returns
    positions[active_idx] = 1.0

    res = run_gate(
        returns,
        DEFAULT_GATE_CFG,
        nb_trials=1,
        sr_trials_var=0.0,
        positions=positions,
        active_returns=returns[positions != 0.0],
        market_returns=returns,
        n_params=1,
    )

    assert res.n_trades == len(active_idx)
    assert res.n_trades != len(returns)
    assert np.isfinite(res.dsr)
    assert all(np.isfinite(value) for value in _finite_gate_values(res))


def test_sparse_active_returns_fail_fast_when_under_min_trades():
    returns = np.zeros(1000)
    positions = np.zeros_like(returns)
    active_idx = np.arange(10)
    returns[active_idx] = 0.001
    positions[active_idx] = 1.0

    res = run_gate(
        returns,
        DEFAULT_GATE_CFG,
        nb_trials=1,
        sr_trials_var=0.0,
        positions=positions,
        active_returns=returns[positions != 0.0],
        market_returns=returns,
        n_params=1,
    )

    assert not res.passed
    assert res.reasons == ["min_trades"]
    assert res.n_trades == len(active_idx)
    assert all(np.isfinite(value) for value in _finite_gate_values(res))
