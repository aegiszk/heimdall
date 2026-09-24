"""Validation math, self-implemented (permissive, auditable). All in PER-PERIOD return units.
References: Bailey & Lopez de Prado (PSR/DSR 2014; CSCV/PBO 2016); Newey-West (1987)."""
from __future__ import annotations
import numpy as np
from scipy import stats

def sharpe(returns: np.ndarray) -> float:
    r = np.asarray(returns, float)
    sd = r.std(ddof=1)
    return 0.0 if sd == 0 else r.mean() / sd

def max_drawdown(returns: np.ndarray) -> float:
    eq = np.cumprod(1.0 + np.asarray(returns, float))
    peak = np.maximum.accumulate(eq)
    return float((eq / peak - 1.0).min())  # negative number

def newey_west_tstat(returns: np.ndarray, lags: int | None = None) -> float:
    r = np.asarray(returns, float); T = len(r)
    if T < 3: return 0.0
    mu = r.mean(); e = r - mu
    if lags is None: lags = int(np.floor(4 * (T / 100.0) ** (2/9)))
    g0 = (e @ e) / T
    lrv = g0
    for L in range(1, lags + 1):
        w = 1.0 - L / (lags + 1)
        cov = (e[L:] @ e[:-L]) / T
        lrv += 2 * w * cov
    se = np.sqrt(max(lrv, 1e-18) / T)
    return float(mu / se)

def probabilistic_sharpe_ratio(returns: np.ndarray, sr_benchmark: float = 0.0) -> float:
    """P(true per-period SR > sr_benchmark). Adjusts for skew/kurtosis of returns."""
    r = np.asarray(returns, float); T = len(r)
    sr = sharpe(r)
    sk = float(stats.skew(r)); ku = float(stats.kurtosis(r, fisher=False))  # normal kurt = 3
    denom = np.sqrt(max(1.0 - sk * sr + ((ku - 1.0) / 4.0) * sr ** 2, 1e-12))
    z = (sr - sr_benchmark) * np.sqrt(T - 1) / denom
    return float(stats.norm.cdf(z))

def expected_max_sharpe(sr_trials_var: float, n_trials: int) -> float:
    """SR0: expected max per-period Sharpe under the null across n_trials (Bailey-LdP)."""
    if n_trials <= 1: return 0.0
    g = 0.5772156649  # Euler-Mascheroni
    z1 = stats.norm.ppf(1 - 1.0 / n_trials)
    z2 = stats.norm.ppf(1 - 1.0 / (n_trials * np.e))
    return float(np.sqrt(max(sr_trials_var, 0.0)) * ((1 - g) * z1 + g * z2))

def deflated_sharpe_ratio(returns: np.ndarray, sr_trials_var: float, n_trials: int) -> float:
    """DSR = PSR benchmarked against the expected max Sharpe from n_trials. Pass if > 0.95."""
    sr0 = expected_max_sharpe(sr_trials_var, n_trials)
    return probabilistic_sharpe_ratio(returns, sr_benchmark=sr0)

def bootstrap_sharpe_ci(returns: np.ndarray, B: int = 2000, alpha: float = 0.05, seed: int = 0):
    r = np.asarray(returns, float); T = len(r); rng = np.random.default_rng(seed)
    srs = np.array([sharpe(r[rng.integers(0, T, T)]) for _ in range(B)])
    lo, hi = np.quantile(srs, [alpha/2, 1 - alpha/2])
    return float(lo), float(hi)

def monte_carlo_permutation(positions: np.ndarray, market_returns: np.ndarray,
                            n: int = 2000, seed: int = 0) -> float:
    """Null: positions carry no timing edge. p = frac of random-timing Sharpes >= observed."""
    pos = np.asarray(positions, float); mkt = np.asarray(market_returns, float)
    obs = sharpe(pos * mkt); rng = np.random.default_rng(seed)
    cnt = sum(sharpe(rng.permutation(pos) * mkt) >= obs for _ in range(n))
    return float(cnt / n)

def cscv_pbo(returns_matrix: np.ndarray, S: int = 8) -> float:
    """Probability of Backtest Overfitting via CSCV across a matrix (T x N strategies)."""
    from itertools import combinations
    M = np.asarray(returns_matrix, float); T, N = M.shape
    S -= S % 2
    rows = np.array_split(np.arange(T), S)
    idx = list(range(S)); lam = []
    for tr in combinations(idx, S // 2):
        is_rows = np.concatenate([rows[i] for i in tr])
        oos_rows = np.concatenate([rows[i] for i in idx if i not in tr])
        is_sr = np.array([sharpe(M[is_rows, j]) for j in range(N)])
        oos_sr = np.array([sharpe(M[oos_rows, j]) for j in range(N)])
        best = int(np.argmax(is_sr))
        rank = (np.sum(oos_sr <= oos_sr[best]) ) / (N + 1)  # relative rank in OOS
        rank = min(max(rank, 1e-6), 1 - 1e-6)
        lam.append(np.log(rank / (1 - rank)))
    lam = np.array(lam)
    return float(np.mean(lam <= 0))  # frac where IS-best is below OOS median

def walk_forward(returns: np.ndarray, n_splits: int = 5):
    r = np.asarray(returns, float); folds = np.array_split(r, n_splits + 1)
    return [sharpe(folds[i + 1]) for i in range(n_splits)]  # OOS sharpe per forward fold
