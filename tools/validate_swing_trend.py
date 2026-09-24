"""Offline ES swing-trend validation on local 1-minute parquet data only."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.prop_futures import SwingTrendModel
from core.config import DEFAULT_GATE_CFG
from core.validation.battery import run_gate
from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many


DATA_PATH = ROOT / "data" / "ES_1m.parquet"
OUT_DIR = ROOT / "data" / "prop_futures"
STARTING_BALANCE = 50_000.0


def main() -> int:
    model = SwingTrendModel(contract="ES")
    raw = load_es(DATA_PATH)
    daily = model._prepare_daily_frame(raw)
    cut = int(len(daily) * 0.60)
    train_daily = daily.iloc[:cut].reset_index(drop=True)
    holdout_daily = daily.iloc[cut:].reset_index(drop=True)

    train = evaluate_daily(model, train_daily)
    holdout = evaluate_daily(model, holdout_daily)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trade_path = OUT_DIR / "swing_trend_ES_1m_holdout_trades.csv"
    holdout["trades"].to_csv(trade_path, index=False)

    daily_counts = observed_daily_counts(holdout_daily, holdout["trades"])
    mc = monte_carlo(holdout["trades"], np.sort(daily_counts))
    gate = gate_result(holdout, model)

    print("SWING TREND OFFLINE VALIDATION")
    print(f"data={DATA_PATH}")
    print(
        f"daily_sessions={len(daily)} train={len(train_daily)} holdout={len(holdout_daily)} "
        f"train_start={daily['_session'].iloc[0].date()} train_end={train_daily['_session'].iloc[-1].date()} "
        f"holdout_start={holdout_daily['_session'].iloc[0].date()} holdout_end={holdout_daily['_session'].iloc[-1].date()}"
    )
    print("model=SwingTrendModel(contract=ES, breakout_days=20, atr_days=14, reward_r=2.5)")
    print("split=60/40 no_param_tuning=true network_calls=0")
    print()
    print_summary("TRAIN", train)
    print_summary("HOLDOUT", holdout)
    print(f"holdout_daily_trade_counts={daily_count_summary(daily_counts)}")
    print()
    print_walk_forward(holdout_daily, holdout["trades"])
    print_gate(gate)
    print_mc(mc)
    print(f"trades_file={trade_path}")
    return 0


def load_es(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    return frame[["open", "high", "low", "close", "volume"]].copy()


def evaluate_daily(model: SwingTrendModel, daily: pd.DataFrame) -> dict[str, object]:
    pnl, pos, market, trades = model._simulate_daily(daily)
    rows = []
    for trade in trades:
        risk = abs(trade.entry_price - trade.stop_price) * model.point_value
        gross_pnl = trade.pnl + model.commission_rt
        rows.append(
            {
                "entry_ts": trade.entry_ts,
                "exit_ts": trade.exit_ts,
                "side": "long" if trade.side > 0 else "short",
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "stop_price": trade.stop_price,
                "target_price": trade.target_price,
                "risk_dollars": risk,
                "pnl": trade.pnl,
                "gross_pnl": gross_pnl,
                "r_mult": trade.pnl / risk if risk > 0 else 0.0,
                "hold_days": max(1, business_day_span(trade.entry_ts, trade.exit_ts)),
                "reason": trade.reason,
            }
        )
    return {
        "pnl": pnl,
        "pos": pos,
        "market": market,
        "trades": pd.DataFrame(rows),
    }


def gate_result(result: dict[str, object], model: SwingTrendModel):
    pnl = np.asarray(result["pnl"], dtype=float)
    pos = np.asarray(result["pos"], dtype=float)
    market = np.asarray(result["market"], dtype=float)
    returns = pnl / STARTING_BALANCE
    active_returns = returns[pnl != 0.0]
    cfg = DEFAULT_GATE_CFG.copy()
    cfg["wf_splits"] = 4
    return run_gate(
        returns,
        cfg,
        nb_trials=1,
        sr_trials_var=0.0,
        positions=pos,
        active_returns=active_returns,
        market_returns=market / STARTING_BALANCE,
        n_params=len(model.strategy_params),
    )


def monte_carlo(trades: pd.DataFrame, daily_counts: np.ndarray):
    if trades.empty:
        return None
    params = SimParams(
        n_sims=10_000,
        daily_buffer=325.0,
        commission_per_rt=3.5,
        min_trades_per_day=0,
        max_trades_per_day=1,
    )
    return run_empirical_many(params, trades["pnl"].to_numpy(float), daily_counts)


def observed_daily_counts(daily: pd.DataFrame, trades: pd.DataFrame) -> np.ndarray:
    days = [ts.date() for ts in daily["_session"]]
    if trades.empty:
        return np.zeros(len(days), dtype=int)
    trade_days = cme_session_dates(pd.to_datetime(trades["entry_ts"])).dt.date
    counts = trade_days.value_counts()
    return np.array([int(counts.get(day, 0)) for day in days], dtype=int)


def cme_session_dates(ts: pd.Series) -> pd.Series:
    if getattr(ts.dt, "tz", None) is None:
        ts = ts.dt.tz_localize("UTC")
    else:
        ts = ts.dt.tz_convert("UTC")
    et = ts.dt.tz_convert("America/New_York").dt.tz_localize(None)
    session = et.dt.normalize()
    evening = et.dt.time >= pd.Timestamp("18:00").time()
    return session + pd.to_timedelta(evening.astype(int), unit="D")


def print_summary(label: str, result: dict[str, object]) -> None:
    trades = result["trades"]
    print(label)
    if trades.empty:
        print("n_trades=0")
        print()
        return
    pnl = trades["pnl"].to_numpy(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    avg_win = mean_or_zero(wins)
    avg_loss = mean_or_zero(losses)
    gross_abs = np.abs(trades["gross_pnl"].to_numpy(float)).sum()
    friction = len(trades) * 3.5
    rr = avg_win / abs(avg_loss) if avg_loss < 0 else 0.0
    print(
        f"n_trades={len(trades)} win_rate={(pnl > 0).mean():.2%} "
        f"avg_win=${avg_win:.2f} avg_loss=${avg_loss:.2f} RR={rr:.3f} "
        f"mean=${np.mean(pnl):.2f} median=${np.median(pnl):.2f} "
        f"total=${np.sum(pnl):.2f}"
    )
    print(
        f"avg_risk=${trades['risk_dollars'].mean():.2f} max_risk=${trades['risk_dollars'].max():.2f} "
        f"avg_hold_days={trades['hold_days'].mean():.2f} max_hold_days={trades['hold_days'].max()}"
    )
    print(
        f"friction=${friction:.2f} friction_pct_of_abs_gross_pnl="
        f"{(friction / gross_abs if gross_abs else 0.0):.2%} "
        f"max_consec_losses={max_consecutive_losses(pnl)} "
        f"skew={finite(stats.skew(pnl, bias=False)):.3f}"
    )
    print()


def print_walk_forward(daily: pd.DataFrame, trades: pd.DataFrame) -> None:
    print("WALK_FORWARD_4_BUCKETS_HOLDOUT")
    rows = [["bucket", "start", "end", "n_trades", "mean_pnl", "win_rate"]]
    if trades.empty:
        print_table(rows + [["1", "-", "-", "0", "$0.00", "0.00%"]])
        print()
        return
    sessions = daily["_session"].reset_index(drop=True)
    cuts = np.array_split(np.arange(len(sessions)), 4)
    exit_ts = pd.to_datetime(trades["exit_ts"])
    for idx, locs in enumerate(cuts, start=1):
        start = sessions.iloc[locs[0]]
        end = sessions.iloc[locs[-1]]
        mask = (exit_ts.dt.date >= start.date()) & (exit_ts.dt.date <= end.date())
        bucket = trades.loc[mask]
        pnl = bucket["pnl"].to_numpy(float) if not bucket.empty else np.array([], dtype=float)
        rows.append(
            [
                str(idx),
                str(start.date()),
                str(end.date()),
                str(len(bucket)),
                f"${mean_or_zero(pnl):.2f}",
                f"{((pnl > 0).mean() if len(pnl) else 0.0):.2%}",
            ]
        )
    print_table(rows)
    print()


def print_gate(gate) -> None:
    print("FUNNEL_GATE_HOLDOUT")
    print(
        f"passed={gate.passed} reasons={gate.reasons} n_trades={gate.n_trades} "
        f"n_params={gate.n_params} dsr={gate.dsr:.4f} nw_t={gate.nw_t:.4f} "
        f"boot_lo={gate.boot_lo:.4f} max_dd={gate.max_dd:.4f} "
        f"wf_min={gate.wf_min:.4f} mc_p={gate.mc_p:.4f}"
    )
    print()


def print_mc(mc) -> None:
    print("PROP_MONTECARLO_BUFFER_325")
    if mc is None:
        print("no trades")
        print()
        return
    print(
        f"pass_rate={mc.pass_rate:.4%} EV_per_eval=${ev_per_eval(mc.pass_rate, 2400.0, 99.0):.2f} "
        f"fail_died_mll={mc.fail_died_mll:.4%} fail_never_target={mc.fail_no_target:.4%} "
        f"fail_failed_5day={mc.fail_target_min_days:.4%} avg_final_balance=${mc.avg_final_balance:.2f} "
        f"avg_trades={mc.avg_trades:.2f}"
    )
    print()


def business_day_span(start, end) -> int:
    start_date = pd.Timestamp(start).date()
    end_date = pd.Timestamp(end).date()
    return int(np.busday_count(start_date, end_date) + 1)


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


def mean_or_zero(values) -> float:
    arr = np.asarray(values, dtype=float)
    return float(np.mean(arr)) if len(arr) else 0.0


def finite(value: float) -> float:
    value = float(value)
    return value if np.isfinite(value) else 0.0


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(row[i]).rjust(widths[i]) for i in range(len(row))))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


def daily_count_summary(counts: np.ndarray) -> str:
    unique, freq = np.unique(counts, return_counts=True)
    return ",".join(f"{int(k)}:{int(v)}" for k, v in zip(unique, freq))


if __name__ == "__main__":
    sys.exit(main())
