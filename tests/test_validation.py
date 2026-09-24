import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.validation import metrics as m

RNG = np.random.default_rng(42)
T = 504  # ~2y daily

def noise():           # pure white noise, zero edge
    return RNG.normal(0, 0.01, T)
def signal(sr_ann=2.0):  # genuine edge, annualized Sharpe ~2
    mu = sr_ann/np.sqrt(252)*0.01
    return RNG.normal(mu, 0.01, T)

def test_noise_is_rejected():
    r = noise()
    assert m.newey_west_tstat(r) < 2.0
    assert m.deflated_sharpe_ratio(r, sr_trials_var=0.002, n_trials=1) < 0.95
    lo, _ = m.bootstrap_sharpe_ci(r)
    assert lo < 0.1   # per-period; not distinguishable from zero

def test_real_signal_passes_when_few_trials():
    r = signal(3.0)
    assert m.newey_west_tstat(r) > 2.0
    assert m.deflated_sharpe_ratio(r, sr_trials_var=0.002, n_trials=1) > 0.95

def test_same_signal_fails_under_heavy_multiple_testing():
    r = signal(2.0)
    dsr_few  = m.deflated_sharpe_ratio(r, sr_trials_var=0.02, n_trials=1)
    dsr_many = m.deflated_sharpe_ratio(r, sr_trials_var=0.02, n_trials=5000)
    assert dsr_few > 0.95 and dsr_many < dsr_few   # trials raise the bar
    print(f"\n  DSR n=1: {dsr_few:.3f}  |  DSR n=5000: {dsr_many:.3f}")

def test_permutation_rejects_random_timing():
    mkt = RNG.normal(0, 0.01, T)
    good_pos = np.sign(mkt)                     # same-bar 'oracle' timing -> strong edge
    rand_pos = RNG.choice([-1, 1], T)
    assert m.monte_carlo_permutation(good_pos, mkt, n=1000) < 0.05
    assert m.monte_carlo_permutation(rand_pos, mkt, n=1000) > 0.05

def test_pbo_high_when_strategies_are_noise():
    M = RNG.normal(0, 0.01, (T, 20))            # 20 pure-noise strategies
    assert m.cscv_pbo(M, S=8) > 0.3             # selecting best-of-noise overfits
