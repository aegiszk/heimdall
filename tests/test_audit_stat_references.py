"""V3 validation audit: battery math vs independent references.

References:
  PSR  - Bailey & Lopez de Prado (2012) "The Sharpe Ratio Efficient Frontier", eq. for PSR(SR*)
         with sqrt(n-1) and non-excess kurtosis gamma4.
  DSR  - Bailey & Lopez de Prado (2014) "The Deflated Sharpe Ratio", SR0 expected-max formula.
  NW   - Newey & West (1987) Bartlett kernel; lag rule floor(4 (T/100)^(2/9)) (Newey-West 1994).
         Cross-checked against statsmodels OLS HAC (installed out-of-venv for the audit only).
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest
from scipy import stats

from core.validation import metrics as m

# statsmodels is NOT a Heimdall dependency; point HEIMDALL_AUDIT_REFS at an out-of-venv install to run the check.
_REF = os.environ.get("HEIMDALL_AUDIT_REFS", "")


def _ref_psr(r, sr_star):
    r = np.asarray(r, float)
    n = len(r)
    sr = r.mean() / r.std(ddof=1)
    g3 = stats.skew(r)
    g4 = stats.kurtosis(r, fisher=False)
    return stats.norm.cdf((sr - sr_star) * np.sqrt(n - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr**2))


@pytest.mark.parametrize("seed", range(5))
def test_psr_matches_reference_formula(seed):
    r = np.random.default_rng(seed).standard_t(4, 250) * 0.01 + 0.001
    for sr_star in (0.0, 0.05, 0.2):
        assert m.probabilistic_sharpe_ratio(r, sr_star) == pytest.approx(_ref_psr(r, sr_star), abs=1e-12)


def test_expected_max_sharpe_matches_monte_carlo_order_statistic():
    # E[max of N iid N(0, v)] ~= SR0 formula; check within 3% for N = 10, 100, 1000
    rng = np.random.default_rng(0)
    for n in (10, 100, 1000):
        mc = rng.standard_normal((4000, n)).max(axis=1).mean()
        assert m.expected_max_sharpe(1.0, n) == pytest.approx(mc, rel=0.03)


def test_dsr_with_one_trial_equals_undeflated_psr():
    # Convention A (nb_trials=1, var=0) applies NO multiple-testing deflation.
    r = np.random.default_rng(1).normal(0.001, 0.01, 100)
    assert m.deflated_sharpe_ratio(r, 0.0, 1) == pytest.approx(m.probabilistic_sharpe_ratio(r, 0.0))


def test_convention_B_benchmark_is_implausibly_high():
    # validate_research_candidates passes nb_trials=2, sr_trials_var=1.0 in PER-TRADE Sharpe units.
    # SR0 = 0.52 per trade; a 60%-win 1:1 strategy has per-trade SR ~0.20.
    sr0 = m.expected_max_sharpe(1.0, 2)
    assert sr0 == pytest.approx(0.5198, abs=1e-3)
    assert sr0 > 2.5 * 0.2041  # 60% / 1:1 true per-trade SR = 0.2/sqrt(0.96)


def test_newey_west_lag_rule_and_value_vs_statsmodels():
    if _REF:
        sys.path.append(_REF)
    sm = pytest.importorskip("statsmodels.api")
    rng = np.random.default_rng(3)
    e = rng.standard_normal(300)
    r = np.empty(300)
    r[0] = e[0]
    for i in range(1, 300):
        r[i] = 0.4 * r[i - 1] + e[i]
    r = r * 0.01 + 0.002
    lags = int(np.floor(4 * (300 / 100) ** (2 / 9)))
    fit = sm.OLS(r, np.ones_like(r)).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
    assert m.newey_west_tstat(r) == pytest.approx(float(fit.tvalues[0]), rel=1e-9)


def test_walk_forward_is_subperiod_consistency_not_refit():
    # metrics.walk_forward splits into n+1 chunks and DISCARDS the first; nothing is re-fit.
    r = np.arange(12, dtype=float)
    folds = np.array_split(r, 6)
    assert m.walk_forward(r, 5) == [m.sharpe(f) for f in folds[1:]]


def test_pbo_sanity_noise_vs_one_real_edge():
    rng = np.random.default_rng(7)
    noise = rng.standard_normal((800, 10)) * 0.01
    assert m.cscv_pbo(noise, 8) > 0.3
    edge = noise.copy()
    edge[:, 0] += 0.004
    assert m.cscv_pbo(edge, 8) < 0.1
