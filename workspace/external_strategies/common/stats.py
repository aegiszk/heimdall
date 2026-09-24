"""Per-interpretation metrics and program-level multiple-testing tools (research lane; reuses audited core math)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from core.validation.gates import cluster_bootstrap_mean_ci  # noqa: E402
from core.validation.metrics import deflated_sharpe_ratio, newey_west_tstat  # noqa: E402

ET = "America/New_York"


def _day(ts: pd.Series) -> pd.Series:
    e = pd.to_datetime(ts).dt.tz_convert(ET).dt.tz_localize(None) + pd.Timedelta(hours=6)
    return e.dt.normalize()


def summarize(df: pd.DataFrame, years: float | None = None) -> dict:
    """df from harness.trades_frame. All R figures are NET of modelled costs unless named gross."""
    if df is None or len(df) == 0:
        return {"n": 0}
    R = df["R"].to_numpy(float)
    n = len(R)
    day = _day(df["t_entry"])
    wins, losses = R[R > 0], R[R <= 0]
    boot = cluster_bootstrap_mean_ci(R, clusters=day.to_numpy(), n_boot=4000, seed=7, alpha=0.025) if n >= 2 else {}
    eq = np.cumsum(R)
    dd = float((eq - np.maximum.accumulate(np.r_[0.0, eq])[1:]).min()) if n else 0.0
    srt = np.sort(R)[::-1]
    tot = R.sum()
    span_years = years or max((df["t_entry"].max() - df["t_entry"].min()).days / 365.25, 1 / 365.25)
    yr = pd.to_datetime(df["t_entry"]).dt.year
    by_year = df.assign(_y=yr).groupby("_y")["R"].agg(["count", "mean", "sum"]).round(3)
    ym = pd.to_datetime(df["t_entry"]).dt.tz_convert(ET).dt.strftime("%Y-%m")
    by_month = df.assign(_m=ym).groupby("_m")["R"].sum()
    out = {
        "n": n,
        "trades_per_year": n / span_years,
        "win_rate": float((R > 0).mean()),
        "mean_R": float(R.mean()),
        "median_R": float(np.median(R)),
        "mean_gross_R": float(df["gross_R"].mean()),
        "payoff": float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses) and losses.mean() != 0 else np.nan,
        "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else np.inf,
        "sharpe_per_trade": float(R.mean() / R.std(ddof=1)) if n > 2 and R.std(ddof=1) > 0 else np.nan,
        "nw_t": float(newey_west_tstat(R)) if n > 2 else np.nan,
        "p_one_sided": float(1 - st.norm.cdf(newey_west_tstat(R))) if n > 2 else np.nan,
        "boot95_lo": boot.get("ci_lo", np.nan), "boot95_hi": boot.get("ci_hi", np.nan),
        "mean_mfe_R": float(df["mfe_R"].mean()), "mean_mae_R": float(df["mae_R"].mean()),
        "max_dd_R": dd,
        "worst_R": float(R.min()), "best_R": float(R.max()),
        "top1_share": float(srt[:1].sum() / tot) if tot != 0 else np.nan,
        "top5_share": float(srt[:5].sum() / tot) if tot != 0 else np.nan,
        "top10_share": float(srt[:10].sum() / tot) if tot != 0 else np.nan,
        "sum_R": float(tot),
        "mean_net_usd_1lot": float(df["net_usd_1"].mean()),
        "median_net_usd_1lot": float(df["net_usd_1"].median()),
        "long_n": int((df["side"] > 0).sum()), "long_mean_R": float(df.loc[df.side > 0, "R"].mean()) if (df.side > 0).any() else np.nan,
        "short_n": int((df["side"] < 0).sum()), "short_mean_R": float(df.loc[df.side < 0, "R"].mean()) if (df.side < 0).any() else np.nan,
        "pos_years": int((by_year["sum"] > 0).sum()), "n_years": int(len(by_year)),
        "pos_months_frac": float((by_month > 0).mean()) if len(by_month) else np.nan,
        "by_year": by_year.reset_index().rename(columns={"_y": "year"}).to_dict("records"),
        "exit_reasons": df["reason"].value_counts().to_dict(),
    }
    return out


def drop_top(df: pd.DataFrame, k: int | None = None, frac: float | None = None) -> float:
    R = np.sort(df["R"].to_numpy(float))[::-1]
    if frac is not None:
        k = max(1, int(np.ceil(frac * len(R))))
    return float(R[k:].mean()) if len(R) > k else np.nan


def holm(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (m - r) * p[i]))
        adj[i] = run
    return adj


def bh(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    q = np.empty(m)
    prev = 1.0
    for r in range(m - 1, -1, -1):
        i = order[r]
        prev = min(prev, p[i] * m / (r + 1))
        q[i] = prev
    return q


def dsr(R: np.ndarray, sr_trials_var: float, n_trials: int) -> float:
    return float(deflated_sharpe_ratio(np.asarray(R, float), sr_trials_var, n_trials))


def white_reality_check(daily: pd.DataFrame, B: int = 3000, mean_block: float = 5.0, seed: int = 11) -> dict:
    """White (2000) RC with Politis-Romano stationary bootstrap. daily: columns = strategies, rows = session
    days (0 on no-trade days). H0: best strategy has mean <= 0. Returns p-value of max mean statistic."""
    X = daily.fillna(0.0).to_numpy(float)
    T, K = X.shape
    mu = X.mean(0)
    stat = np.sqrt(T) * mu.max()
    rng = np.random.default_rng(seed)
    p = 1.0 / mean_block
    cnt = 0
    for _ in range(B):
        idx = np.empty(T, int)
        idx[0] = rng.integers(T)
        for t in range(1, T):
            idx[t] = rng.integers(T) if rng.random() < p else (idx[t - 1] + 1) % T
        mb = X[idx].mean(0)
        if np.sqrt(T) * (mb - mu).max() >= stat:
            cnt += 1
    return {"stat": float(stat), "p": cnt / B, "T": T, "K": K, "best": str(daily.columns[int(mu.argmax())])}
