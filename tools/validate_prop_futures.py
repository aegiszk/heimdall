"""Validate the three MES prop-futures candidates on Databento 1-minute data."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.prop_futures import (
    TimeStructuredScalpModel,
    TrendPullbackContinuationModel,
    VWAPReversionHardStopModel,
)
from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many


EASTERN = "America/New_York"
DATA_PATH = ROOT / "data" / "MES_1m.parquet"
OUT_DIR = ROOT / "data" / "prop_futures"
POINT_VALUE = 5.0


def main() -> int:
    df = load_mes_features(DATA_PATH)
    models = [
        VWAPReversionHardStopModel(contract="MES"),
        TrendPullbackContinuationModel(contract="MES"),
        TimeStructuredScalpModel(contract="MES"),
    ]

    summaries = []
    for model in models:
        trades = trades_for_model(model, df)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        trade_path = OUT_DIR / f"{model.name}_MES_1m_trades.csv"
        trades.to_csv(trade_path, index=False)
        daily_counts = observed_daily_counts(df, trades)
        mc = monte_carlo(trades["pnl"].to_numpy(float), daily_counts)
        summary = summarize(model.name, trades, mc)
        summaries.append(summary)
        print_strategy(model.name, trades, daily_counts, mc, trade_path)

    print_ranked_summary(summaries)
    return 0


def load_mes_features(path: Path) -> pd.DataFrame:
    raw = pd.read_parquet(path)
    raw = raw[["open", "high", "low", "close", "volume"]].copy()
    raw.index = pd.DatetimeIndex(raw.index)
    if raw.index.tz is None:
        raw.index = raw.index.tz_localize("UTC")
    else:
        raw.index = raw.index.tz_convert("UTC")

    et_index = raw.index.tz_convert(EASTERN)
    rth = raw.loc[(et_index.weekday < 5) & (et_index.time >= pd.Timestamp("09:30").time()) & (et_index.time <= pd.Timestamp("16:00").time())].copy()
    rth["ts"] = rth.index
    session = rth.index.tz_convert(EASTERN).date
    typical = (rth["high"] + rth["low"] + rth["close"]) / 3.0
    pv = typical * rth["volume"].clip(lower=0)
    cum_pv = pv.groupby(session).cumsum()
    cum_vol = rth["volume"].clip(lower=0).groupby(session).cumsum()
    fallback = typical.groupby(session).expanding().mean().reset_index(level=0, drop=True)
    rth["vwap"] = (cum_pv / cum_vol.replace(0, np.nan)).fillna(fallback)

    closes = rth.groupby(session)["close"].last()
    prior = closes.shift(1)
    rth["prior_close"] = pd.Series(session, index=rth.index).map(prior)
    rth = rth.dropna(subset=["prior_close", "vwap"]).copy()
    return rth


def trades_for_model(model, df: pd.DataFrame) -> pd.DataFrame:
    frame = model._prepare_frame(df)
    _, _, _, trades = model._simulate(frame)
    rows = []
    for trade in trades:
        risk = abs(trade.entry_price - trade.stop_price) * POINT_VALUE
        rows.append(
            {
                "entry_ts": trade.entry_ts,
                "exit_ts": trade.exit_ts,
                "side": "long" if trade.side > 0 else "short",
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "stop_price": trade.stop_price,
                "target_price": trade.target_price,
                "pnl": trade.pnl,
                "r_mult": trade.pnl / risk if risk > 0 else 0.0,
                "reason": trade.reason,
            }
        )
    return pd.DataFrame(rows)


def observed_daily_counts(df: pd.DataFrame, trades: pd.DataFrame) -> np.ndarray:
    days = pd.DatetimeIndex(df.index).tz_convert(EASTERN).date
    unique_days = sorted(set(days))
    if trades.empty:
        return np.zeros(len(unique_days), dtype=int)
    trade_days = pd.to_datetime(trades["entry_ts"]).dt.date
    counts = trade_days.value_counts()
    return np.array([int(counts.get(day, 0)) for day in unique_days], dtype=int)


def monte_carlo(trade_pnls: np.ndarray, daily_counts: np.ndarray):
    if len(trade_pnls) == 0:
        return None
    params = SimParams(n_sims=10_000, daily_buffer=325.0, commission_per_rt=1.0)
    return run_empirical_many(params, trade_pnls, daily_counts)


def summarize(name: str, trades: pd.DataFrame, mc) -> dict[str, float | str]:
    pnl = trades["pnl"].to_numpy(float) if not trades.empty else np.array([], dtype=float)
    return {
        "strategy": name,
        "skew": finite(stats.skew(pnl, bias=False)) if len(pnl) >= 3 else 0.0,
        "pass_rate": 0.0 if mc is None else mc.pass_rate,
        "ev_per_eval": -99.0 if mc is None else ev_per_eval(mc.pass_rate, 2400.0, 99.0),
    }


def print_strategy(name: str, trades: pd.DataFrame, daily_counts: np.ndarray, mc, trade_path: Path) -> None:
    print(f"STRATEGY {name}")
    print(f"trades_file={trade_path}")
    print(f"daily_trade_counts={daily_count_summary(daily_counts)}")
    if trades.empty:
        print("n_trades=0")
        print()
        return

    pnl = trades["pnl"].to_numpy(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    avg_win = mean_or_zero(wins)
    avg_loss = mean_or_zero(losses)
    rr = avg_win / abs(avg_loss) if avg_loss < 0 else 0.0
    print(
        "distribution "
        f"n_trades={len(trades)} win_rate={(pnl > 0).mean() * 100:.2f}% "
        f"avg_win=${avg_win:.2f} avg_loss=${avg_loss:.2f} realized_RR={rr:.3f} "
        f"skew={finite(stats.skew(pnl, bias=False)):.3f} "
        f"kurtosis={finite(stats.kurtosis(pnl, fisher=True, bias=False)):.3f} "
        f"max_consec_losses={max_consecutive_losses(trades.sort_values('exit_ts')['pnl'].to_numpy(float))}"
    )
    print("worst_5")
    rows = [["entry_ts", "exit_ts", "side", "entry", "exit", "pnl", "r_mult", "reason"]]
    for row in trades.sort_values("pnl").head(5).itertuples(index=False):
        rows.append(
            [
                pd.Timestamp(row.entry_ts).isoformat(),
                pd.Timestamp(row.exit_ts).isoformat(),
                row.side,
                f"{row.entry_price:.2f}",
                f"{row.exit_price:.2f}",
                f"${row.pnl:.2f}",
                f"{row.r_mult:.3f}",
                row.reason,
            ]
        )
    print_table(rows)
    if mc is not None:
        print(
            "monte_carlo "
            f"pass_rate={mc.pass_rate:.4%} "
            f"EV_per_eval=${ev_per_eval(mc.pass_rate, 2400.0, 99.0):.2f} "
            f"fail_died_MLL={mc.fail_died_mll:.4%} "
            f"fail_never_target={mc.fail_no_target:.4%} "
            f"fail_failed_5day={mc.fail_target_min_days:.4%}"
        )
    print()


def print_ranked_summary(summaries: list[dict[str, float | str]]) -> None:
    ranked = sorted(summaries, key=lambda row: float(row["ev_per_eval"]), reverse=True)
    print("RANKED SUMMARY")
    rows = [["strategy", "skew", "pass_rate", "EV_per_eval"]]
    for row in ranked:
        rows.append(
            [
                str(row["strategy"]),
                f"{float(row['skew']):.3f}",
                f"{float(row['pass_rate']) * 100:.4f}%",
                f"${float(row['ev_per_eval']):.2f}",
            ]
        )
    print_table(rows)


def max_consecutive_losses(pnl: np.ndarray) -> int:
    max_run = 0
    run = 0
    for value in pnl:
        if value < 0:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
    return max_run


def daily_count_summary(counts: np.ndarray) -> str:
    unique, freq = np.unique(counts, return_counts=True)
    return "{" + ", ".join(f"{int(k)}:{int(v)}" for k, v in zip(unique, freq)) + "}"


def mean_or_zero(values: np.ndarray) -> float:
    return float(np.mean(values)) if len(values) else 0.0


def finite(value: float) -> float:
    value = float(value)
    return value if np.isfinite(value) else 0.0


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(row[i]).rjust(widths[i]) for i in range(len(row))))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


if __name__ == "__main__":
    sys.exit(main())
