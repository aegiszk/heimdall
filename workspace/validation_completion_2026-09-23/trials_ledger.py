"""Empirical per-trade Sharpe of every trial with a surviving trade log that overlaps the index-futures
60/40 holdout window (2025-09-11 .. 2026-06-30 on MNQ/MES/ES_1m). Read-only. Produces the candidate
sr_trials_var and nb_trials inputs for a trial-count-aware DSR."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
H0, H1 = pd.Timestamp("2025-09-11").date(), pd.Timestamp("2026-06-30").date()

LOGS = {
    # name: (path, instrument file, family)
    "inversion_v2_MNQ": ("data/prop_futures/inversion_model_MNQ_1m_trades.csv", "MNQ", "dhesi"),
    "inversion_v2_MES": ("data/prop_futures/inversion_model_MES_1m_trades.csv", "MES", "dhesi"),
    "fabio_orb_delta_MNQ": ("data/prop_futures/fabio_orb_delta_MNQ_1m_holdout_trades.csv", "MNQ", "fabio"),
    "luxalgo_poc_MNQ": ("data/strategy_research/luxalgo_poc_sweep_reclaim_trades.csv", "MNQ", "poc"),
    "casper_fvg_MNQ": ("data/strategy_research/youtube_opening_fvg_scalp_trades.csv", "MNQ", "fvg"),
    "intraday_mom_MNQ": ("data/strategy_research/intraday_momentum_MNQ_databento_trades.csv", "MNQ", "imom"),
    "intraday_mom_MES": ("data/strategy_research/intraday_momentum_MES_databento_trades.csv", "MES", "imom"),
    "intraday_mom_ES": ("data/strategy_research/intraday_momentum_ES_databento_trades.csv", "ES", "imom"),
    "vwap_rev_MES_full": ("data/prop_futures/vwap_reversion_hard_stop_MES_1m_trades.csv", "MES", "vwap"),
    "time_scalp_MES_full": ("data/prop_futures/time_structured_scalp_MES_1m_trades.csv", "MES", "tscalp"),
    "trend_pullback_MES_full": ("data/prop_futures/trend_pullback_continuation_MES_1m_trades.csv", "MES", "tpull"),
    "swing_ES": ("data/prop_futures/swing_trend_ES_1m_holdout_trades.csv", "ES", "swing"),
}
for p in sorted((ROOT / "data" / "target_sweep").glob("*_holdout_trades.csv")):
    LOGS[f"tsweep_{p.stem.replace('_holdout_trades', '')}"] = (str(p.relative_to(ROOT)), p.stem.split("_")[-2], "tsweep")
for p in sorted((ROOT / "data" / "quality_filter_sweep").glob("*_trades.csv")):
    LOGS[f"qfilter_{p.stem.replace('_trades', '')}"] = (str(p.relative_to(ROOT)), "ES", "qfilter")


def session_dates(t: pd.DataFrame) -> pd.Series:
    if "session" in t:
        return pd.to_datetime(t["session"]).dt.date
    ts = pd.to_datetime(t["entry_ts"], utc=False)
    if getattr(ts.dt, "tz", None) is not None:
        ts = ts.dt.tz_convert("America/New_York")
    return ts.dt.date


rows = []
for name, (path, inst, fam) in LOGS.items():
    t = pd.read_csv(ROOT / path)
    if "traded" in t:
        t = t[t["traded"].astype(str).str.lower().isin(["true", "1"])]
    d = session_dates(t)
    h = t[(d >= H0) & (d <= H1)]
    p = h["pnl"].to_numpy(float)
    n = len(p)
    sr = float(p.mean() / p.std(ddof=1)) if n > 2 and p.std(ddof=1) > 0 else float("nan")
    rows.append({"trial": name, "family": fam, "instrument": inst, "n_holdout": n,
                 "mean_pnl": float(p.mean()) if n else float("nan"), "sr_per_trade": sr})

df = pd.DataFrame(rows).sort_values("trial")
ok = df[(df["n_holdout"] >= 30) & df["sr_per_trade"].notna()]
fam_best = ok.sort_values("n_holdout").groupby("family").tail(1)
res = {
    "window": [str(H0), str(H1)],
    "trials_with_logs": len(df),
    "trials_n_ge_30": len(ok),
    "var_sr_all_n_ge_30": float(ok["sr_per_trade"].var(ddof=1)),
    "mean_sampling_var_1_over_n": float((1.0 / ok["n_holdout"]).mean()),
    "var_sr_one_per_family": float(fam_best["sr_per_trade"].var(ddof=1)),
    "families_n_ge_30": int(fam_best["family"].nunique()),
    "max_sr_observed": float(ok["sr_per_trade"].max()),
}
res["var_sr_excess_over_sampling"] = max(res["var_sr_all_n_ge_30"] - res["mean_sampling_var_1_over_n"], 0.0)
df.to_csv(HERE / "trials_ledger_empirical.csv", index=False)
(HERE / "trials_ledger_empirical.json").write_text(json.dumps(res, indent=1))
print(df.to_string(index=False))
print(json.dumps(res, indent=1))
