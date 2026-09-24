"""Offline target-width sweep for MES/ES prop futures candidates.

Uses only data/MES_1m.parquet and data/ES_1m.parquet. No Databento import and
no network calls. The grid is intentionally small: target ticks
10/15/20/25/30, with stop ticks set for a fixed intended 1.25:1 target:stop
ratio, the midpoint of the requested 1:1..1.5:1 band.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many


DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "target_sweep"
EASTERN = "America/New_York"
TICK_SIZE = 0.25
TARGET_TICKS = [10, 15, 20, 25, 30]
INTENDED_RR = 1.25
TRAIN_FRAC = 0.60
CONTRACTS = {
    "MES": {"point_value": 5.0, "tick_value": 1.25, "commission": 1.0},
    "ES": {"point_value": 50.0, "tick_value": 12.50, "commission": 3.50},
}
STRATEGIES = ("vwap_reversion", "trend_pullback", "time_scalp")


@dataclass(frozen=True)
class Config:
    strategy: str
    instrument: str
    target_ticks: int
    stop_ticks: int


def main() -> int:
    ensure_data_present()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    frames = {instrument: load_features(instrument) for instrument in CONTRACTS}
    results = []
    trades_by_key: dict[tuple[str, str, int], pd.DataFrame] = {}
    for instrument, frame in frames.items():
        split_day = split_session(frame)
        for strategy in STRATEGIES:
            for target_ticks in TARGET_TICKS:
                config = Config(
                    strategy=strategy,
                    instrument=instrument,
                    target_ticks=target_ticks,
                    stop_ticks=max(1, int(round(target_ticks / INTENDED_RR))),
                )
                trades = simulate(frame, config)
                trades_by_key[(strategy, instrument, target_ticks)] = trades
                train = trades[trades["session"] <= split_day]
                holdout = trades[trades["session"] > split_day]
                results.append({**config.__dict__, "split": "train", **metrics(train, config)})
                results.append({**config.__dict__, "split": "holdout", **metrics(holdout, config)})

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUT_DIR / "target_sweep_grid.csv", index=False)
    print_grid(results_df)

    selected = select_by_train(results_df)
    selected_rows = []
    wf_rows = []
    for row in selected.itertuples(index=False):
        trades = trades_by_key[(row.strategy, row.instrument, int(row.target_ticks))]
        split_day = split_session(frames[row.instrument])
        holdout = trades[trades["session"] > split_day].copy()
        holdout.to_csv(
            OUT_DIR / f"{row.strategy}_{row.instrument}_target{int(row.target_ticks)}_holdout_trades.csv",
            index=False,
        )
        daily_counts = observed_daily_counts(frames[row.instrument], holdout, after_day=split_day)
        mc = monte_carlo(holdout, daily_counts)
        holdout_metrics = metrics(holdout, Config(row.strategy, row.instrument, int(row.target_ticks), int(row.stop_ticks)))
        selected_rows.append(
            {
                "strategy": row.strategy,
                "instrument": row.instrument,
                "target_ticks": int(row.target_ticks),
                "stop_ticks": int(row.stop_ticks),
                **holdout_metrics,
                "pass_rate": 0.0 if mc is None else mc.pass_rate,
                "ev_per_eval": -99.0 if mc is None else ev_per_eval(mc.pass_rate, 2400.0, 99.0),
                "fail_died_mll": 0.0 if mc is None else mc.fail_died_mll,
                "fail_never_target": 1.0 if mc is None else mc.fail_no_target,
                "fail_failed_5day": 0.0 if mc is None else mc.fail_target_min_days,
            }
        )
        wf_rows.extend(walk_forward_rows(trades, Config(row.strategy, row.instrument, int(row.target_ticks), int(row.stop_ticks))))

    selected_df = pd.DataFrame(selected_rows).sort_values("ev_per_eval", ascending=False)
    wf_df = pd.DataFrame(wf_rows)
    selected_df.to_csv(OUT_DIR / "selected_holdout_ranked.csv", index=False)
    wf_df.to_csv(OUT_DIR / "selected_walk_forward.csv", index=False)

    print_selected(selected_df)
    print_walk_forward(wf_df)
    print_verdict(selected_df)
    return 0


def ensure_data_present() -> None:
    missing = [str(DATA_DIR / f"{instrument}_1m.parquet") for instrument in CONTRACTS if not (DATA_DIR / f"{instrument}_1m.parquet").exists()]
    if missing:
        raise FileNotFoundError(f"Required local parquet missing; refusing to pull data: {missing}")


def load_features(instrument: str) -> pd.DataFrame:
    raw = pd.read_parquet(DATA_DIR / f"{instrument}_1m.parquet")
    raw = raw[["open", "high", "low", "close", "volume"]].copy()
    raw.index = pd.DatetimeIndex(raw.index)
    if raw.index.tz is None:
        raw.index = raw.index.tz_localize("UTC")
    else:
        raw.index = raw.index.tz_convert("UTC")
    et_index = raw.index.tz_convert(EASTERN)
    rth_mask = (
        (et_index.weekday < 5)
        & (et_index.time >= time(9, 30))
        & (et_index.time <= time(16, 0))
    )
    rth = raw.loc[rth_mask].copy()
    rth["ts"] = rth.index
    rth["session"] = pd.Series(rth.index.tz_convert(EASTERN).date, index=rth.index)
    typical = (rth["high"] + rth["low"] + rth["close"]) / 3.0
    vol = rth["volume"].clip(lower=0)
    pv = typical * vol
    cum_pv = pv.groupby(rth["session"]).cumsum()
    cum_vol = vol.groupby(rth["session"]).cumsum()
    fallback = typical.groupby(rth["session"]).expanding().mean().reset_index(level=0, drop=True)
    rth["vwap"] = (cum_pv / cum_vol.replace(0, np.nan)).fillna(fallback)
    prior_close = rth.groupby("session")["close"].last().shift(1)
    rth["prior_close"] = rth["session"].map(prior_close)
    return rth.dropna(subset=["prior_close", "vwap"]).copy()


def split_session(frame: pd.DataFrame):
    sessions = np.array(sorted(frame["session"].unique()))
    return sessions[int(len(sessions) * TRAIN_FRAC) - 1]


def simulate(frame: pd.DataFrame, config: Config) -> pd.DataFrame:
    rows = []
    spec = CONTRACTS[config.instrument]
    for session, day in frame.groupby("session", sort=True):
        open_trade = None
        trades_today = 0
        last_i = day.index[-1]
        for ts, bar in day.iterrows():
            clock = ts.tz_convert(EASTERN).time()
            if open_trade is not None:
                exit_price, reason = exit_price_for(open_trade, bar, ts == last_i)
                if exit_price is not None:
                    rows.append(close_trade(open_trade, bar, exit_price, reason, spec))
                    open_trade = None
                    continue
            if open_trade is None and trades_today < max_trades_day(config.strategy) and entry_window(config.strategy, clock):
                plan = entry_plan(config, day, ts)
                if plan is None:
                    continue
                side, signal_price = plan
                entry_price = signal_price + side * TICK_SIZE
                open_trade = {
                    "strategy": config.strategy,
                    "instrument": config.instrument,
                    "session": session,
                    "entry_ts": ts,
                    "side": side,
                    "signal_price": signal_price,
                    "entry_price": entry_price,
                    "target_price": signal_price + side * config.target_ticks * TICK_SIZE,
                    "stop_price": signal_price - side * config.stop_ticks * TICK_SIZE,
                    "target_ticks": config.target_ticks,
                    "stop_ticks": config.stop_ticks,
                }
                trades_today += 1
    return pd.DataFrame(rows)


def entry_window(strategy: str, clock: time) -> bool:
    if strategy == "time_scalp":
        return (time(10, 0) <= clock <= time(11, 30)) or (time(13, 30) <= clock <= time(15, 30))
    return time(9, 45) <= clock <= time(15, 30)


def max_trades_day(strategy: str) -> int:
    return 6 if strategy == "time_scalp" else 3


def entry_plan(config: Config, day: pd.DataFrame, ts: pd.Timestamp) -> tuple[int, float] | None:
    i = day.index.get_loc(ts)
    bar = day.loc[ts]
    close = float(bar["close"])
    if config.strategy == "vwap_reversion":
        threshold = config.target_ticks * TICK_SIZE
        anchors = [float(bar["vwap"]), float(bar["prior_close"])]
        candidates = [(abs(close - anchor), anchor) for anchor in anchors if np.isfinite(anchor) and abs(close - anchor) >= threshold]
        if not candidates:
            return None
        _, anchor = min(candidates, key=lambda item: item[0])
        return (-1 if close > anchor else 1), close

    if config.strategy == "trend_pullback":
        lookback = 12
        pullback_ticks = 8
        if i < lookback:
            return None
        window = day.iloc[i - lookback : i]
        if len(window) < lookback:
            return None
        open_ = float(bar["open"])
        vwap = float(bar["vwap"])
        prior_close = float(window["close"].iloc[-1])
        trend_move = prior_close - float(window["close"].iloc[0])
        trend_threshold = 2.0 * pullback_ticks * TICK_SIZE
        pullback_distance = pullback_ticks * TICK_SIZE
        if prior_close > vwap and trend_move >= trend_threshold:
            if float(window["high"].max()) - float(bar["low"]) >= pullback_distance and close > open_ and close >= vwap:
                return 1, close
        if prior_close < vwap and trend_move <= -trend_threshold:
            if float(bar["high"]) - float(window["low"].min()) >= pullback_distance and close < open_ and close <= vwap:
                return -1, close
        return None

    if config.strategy == "time_scalp":
        if ts.minute not in (0, 30) or i == 0:
            return None
        prior_close = float(day["close"].iloc[i - 1])
        vwap = float(bar["vwap"])
        if close > vwap and close > prior_close:
            return 1, close
        if close < vwap and close < prior_close:
            return -1, close
        return None

    raise ValueError(f"unknown strategy {config.strategy}")


def exit_price_for(open_trade: dict, bar: pd.Series, is_last_bar: bool) -> tuple[float | None, str]:
    side = int(open_trade["side"])
    stop = float(open_trade["stop_price"])
    target = float(open_trade["target_price"])
    open_ = float(bar["open"])
    high = float(bar["high"])
    low = float(bar["low"])
    if side > 0:
        if open_ <= stop:
            return min(open_, stop - TICK_SIZE), "gap_stop"
        if low <= stop:
            return stop - TICK_SIZE, "stop"
        if high >= target:
            return target, "target"
    else:
        if open_ >= stop:
            return max(open_, stop + TICK_SIZE), "gap_stop"
        if high >= stop:
            return stop + TICK_SIZE, "stop"
        if low <= target:
            return target, "target"
    if is_last_bar:
        return float(bar["close"]) - side * TICK_SIZE, "session_flatten"
    return None, ""


def close_trade(open_trade: dict, bar: pd.Series, exit_price: float, reason: str, spec: dict) -> dict:
    side = int(open_trade["side"])
    entry = float(open_trade["entry_price"])
    gross = side * (exit_price - entry) * spec["point_value"]
    pnl = gross - spec["commission"]
    theoretical_gross_win = open_trade["target_ticks"] * spec["tick_value"]
    return {
        **open_trade,
        "exit_ts": bar.name,
        "exit_price": float(exit_price),
        "reason": reason,
        "gross_pnl": float(gross),
        "pnl": float(pnl),
        "theoretical_gross_win": float(theoretical_gross_win),
    }


def metrics(trades: pd.DataFrame, config: Config) -> dict[str, float | int]:
    if trades.empty:
        return empty_metrics(config)
    pnl = trades["pnl"].to_numpy(float)
    gross = trades["gross_pnl"].to_numpy(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_wins = gross[pnl > 0]
    avg_win = mean_or_zero(wins)
    avg_loss = mean_or_zero(losses)
    avg_gross_win = mean_or_zero(gross_wins)
    friction = friction_dollars(config)
    return {
        "n_trades": int(len(trades)),
        "win_rate": float((pnl > 0).mean()),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "realized_rr": avg_win / abs(avg_loss) if avg_loss < 0 else 0.0,
        "mean_pnl": float(np.mean(pnl)),
        "skew": finite(stats.skew(pnl, bias=False)) if len(pnl) >= 3 else 0.0,
        "kurtosis": finite(stats.kurtosis(pnl, fisher=True, bias=False)) if len(pnl) >= 4 else 0.0,
        "max_consec_losses": max_consecutive_losses(pnl),
        "friction_pct_avg_gross_win": friction / avg_gross_win if avg_gross_win > 0 else 0.0,
    }


def empty_metrics(config: Config) -> dict[str, float | int]:
    return {
        "n_trades": 0,
        "win_rate": 0.0,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "realized_rr": 0.0,
        "mean_pnl": 0.0,
        "skew": 0.0,
        "kurtosis": 0.0,
        "max_consec_losses": 0,
        "friction_pct_avg_gross_win": 0.0,
    }


def friction_dollars(config: Config) -> float:
    spec = CONTRACTS[config.instrument]
    return float(spec["commission"] + 2.0 * spec["tick_value"])


def select_by_train(results: pd.DataFrame) -> pd.DataFrame:
    train = results[results["split"] == "train"].copy()
    train["score"] = train["mean_pnl"]
    train = train.sort_values(["strategy", "instrument", "score", "n_trades"], ascending=[True, True, False, False])
    return train.groupby(["strategy", "instrument"], as_index=False).head(1).reset_index(drop=True)


def observed_daily_counts(frame: pd.DataFrame, trades: pd.DataFrame, *, after_day) -> np.ndarray:
    days = np.array(sorted(day for day in frame["session"].unique() if day > after_day))
    if trades.empty:
        return np.zeros(len(days), dtype=int)
    counts = trades["session"].value_counts()
    return np.array([int(counts.get(day, 0)) for day in days], dtype=int)


def monte_carlo(trades: pd.DataFrame, daily_counts: np.ndarray):
    if trades.empty:
        return None
    params = SimParams(n_sims=10_000, daily_buffer=325.0)
    return run_empirical_many(params, trades["pnl"].to_numpy(float), daily_counts)


def walk_forward_rows(trades: pd.DataFrame, config: Config) -> list[dict[str, object]]:
    if trades.empty:
        return []
    out = []
    start = pd.Timestamp(trades["entry_ts"].min()).tz_convert(EASTERN).normalize()
    end = pd.Timestamp(trades["entry_ts"].max()).tz_convert(EASTERN)
    bucket_start = start
    idx = 1
    while bucket_start <= end:
        bucket_end = bucket_start + pd.DateOffset(months=6)
        mask = (pd.to_datetime(trades["entry_ts"]) >= bucket_start) & (pd.to_datetime(trades["entry_ts"]) < bucket_end)
        chunk = trades.loc[mask]
        row = {
            "strategy": config.strategy,
            "instrument": config.instrument,
            "target_ticks": config.target_ticks,
            "bucket": idx,
            "start": bucket_start.date().isoformat(),
            "end": (bucket_end - pd.Timedelta(days=1)).date().isoformat(),
        }
        row.update(metrics(chunk, config))
        out.append(row)
        bucket_start = bucket_end
        idx += 1
    return out


def print_grid(results: pd.DataFrame) -> None:
    print("TRAIN/HOLDOUT GRID")
    rows = [["split", "strategy", "inst", "target", "stop", "trades", "win", "avg_win", "avg_loss", "RR", "mean", "fric%"]]
    for row in results.sort_values(["split", "strategy", "instrument", "target_ticks"]).itertuples(index=False):
        rows.append(format_metric_row(row))
    print_table(rows)
    print()


def format_metric_row(row) -> list[str]:
    return [
        row.split,
        row.strategy,
        row.instrument,
        str(int(row.target_ticks)),
        str(int(row.stop_ticks)),
        str(int(row.n_trades)),
        pct(row.win_rate),
        money(row.avg_win),
        money(row.avg_loss),
        f"{row.realized_rr:.3f}",
        money(row.mean_pnl),
        pct(row.friction_pct_avg_gross_win),
    ]


def print_selected(selected: pd.DataFrame) -> None:
    print("RANKED HOLDOUT TABLE")
    rows = [[
        "strategy",
        "inst",
        "target",
        "stop",
        "trades",
        "win",
        "avg_win",
        "avg_loss",
        "RR",
        "skew",
        "fric%",
        "pass",
        "EV",
        "died",
        "never",
        "5day",
    ]]
    for row in selected.itertuples(index=False):
        rows.append(
            [
                row.strategy,
                row.instrument,
                str(int(row.target_ticks)),
                str(int(row.stop_ticks)),
                str(int(row.n_trades)),
                pct(row.win_rate),
                money(row.avg_win),
                money(row.avg_loss),
                f"{row.realized_rr:.3f}",
                f"{row.skew:.3f}",
                pct(row.friction_pct_avg_gross_win),
                pct(row.pass_rate),
                money(row.ev_per_eval),
                pct(row.fail_died_mll),
                pct(row.fail_never_target),
                pct(row.fail_failed_5day),
            ]
        )
    print_table(rows)
    print()


def print_walk_forward(wf: pd.DataFrame) -> None:
    print("WALK-FORWARD 6M STABILITY FOR TRAIN-SELECTED TARGETS")
    rows = [["strategy", "inst", "target", "bucket", "start", "end", "trades", "win", "RR", "mean"]]
    for row in wf.sort_values(["strategy", "instrument", "bucket"]).itertuples(index=False):
        rows.append(
            [
                row.strategy,
                row.instrument,
                str(int(row.target_ticks)),
                str(int(row.bucket)),
                row.start,
                row.end,
                str(int(row.n_trades)),
                pct(row.win_rate),
                f"{row.realized_rr:.3f}",
                money(row.mean_pnl),
            ]
        )
    print_table(rows)
    print()


def print_verdict(selected: pd.DataFrame) -> None:
    positive = selected[selected["ev_per_eval"] > 0]
    if positive.empty:
        print("VERDICT: NO positive-EV holdout config. Wider targets did not clear friction on MES or ES.")
    else:
        best = positive.sort_values("ev_per_eval", ascending=False).iloc[0]
        print(
            "VERDICT: POSITIVE-EV holdout config found: "
            f"{best.strategy} {best.instrument} target={int(best.target_ticks)} "
            f"pass={best.pass_rate:.4%} EV=${best.ev_per_eval:.2f}"
        )


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


def mean_or_zero(values: np.ndarray) -> float:
    return float(np.mean(values)) if len(values) else 0.0


def finite(value: float) -> float:
    value = float(value)
    return value if np.isfinite(value) else 0.0


def money(value: float) -> str:
    return f"${value:.2f}"


def pct(value: float) -> str:
    return f"{100.0 * float(value):.2f}%"


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(row[i]).rjust(widths[i]) for i in range(len(row))))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


if __name__ == "__main__":
    sys.exit(main())
