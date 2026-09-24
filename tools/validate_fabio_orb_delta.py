"""Offline Fabio-style MNQ ORB + candle-delta approximation validation."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.prop_futures import FabioORBDeltaModel
from core.config import DEFAULT_GATE_CFG
from core.validation.battery import run_gate
from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many


DATA_PATH = ROOT / "data" / "MNQ_1m.parquet"
OUT_DIR = ROOT / "data" / "prop_futures"
STARTING_BALANCE = 50_000.0


def main() -> int:
    if not DATA_PATH.exists():
        print("BLOCKED: data/MNQ_1m.parquet is missing.")
        print("Do not pull data yet. First run:")
        print("  .venv/bin/python tools/quote_databento_fabio.py --phase-b")
        print("Then wait for human approval before any Databento timeseries pull.")
        return 2

    raw = load_mnq(DATA_PATH)
    model = FabioORBDeltaModel(contract="MNQ", delta_threshold=0.0)
    baseline = FabioORBDeltaModel(contract="MNQ", delta_threshold=-float("inf"))
    prepared = model._prepare_5m_frame(raw)
    sessions = sorted(prepared["session"].dropna().unique())
    cut = int(len(sessions) * 0.60)
    train_sessions = set(sessions[:cut])
    holdout_sessions = set(sessions[cut:])
    train = prepared[prepared["session"].isin(train_sessions)].reset_index(drop=True)
    holdout = prepared[prepared["session"].isin(holdout_sessions)].reset_index(drop=True)

    train_result = evaluate(model, train)
    holdout_result = evaluate(model, holdout)
    baseline_holdout = evaluate(baseline, holdout)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trade_path = OUT_DIR / "fabio_orb_delta_MNQ_1m_holdout_trades.csv"
    holdout_result["trades"].to_csv(trade_path, index=False)

    daily_counts = observed_daily_counts(holdout, holdout_result["trades"])
    mc = monte_carlo(holdout_result["trades"], np.sort(daily_counts))
    gate = gate_result(holdout_result, model)

    print("FABIO ORB DELTA OFFLINE VALIDATION")
    print(f"data={DATA_PATH}")
    print(
        f"sessions={len(sessions)} train={len(train_sessions)} holdout={len(holdout_sessions)} "
        f"train_start={sessions[0]} train_end={sessions[cut - 1]} "
        f"holdout_start={sessions[cut]} holdout_end={sessions[-1]}"
    )
    print("model=FabioORBDeltaModel(contract=MNQ, ORB_Dur=30, TP_RR=1.0, delta_threshold=0.0)")
    print("delta=APPROXIMATE candle delta: +volume if 1m close>open, -volume if close<open, 0 otherwise")
    print("limitation=this is not tick/bid-ask volume delta and is not a verbatim appendix port until PDF appendix is supplied")
    print("split=60/40 no_param_tuning=true network_calls=0")
    print()
    print_step0(raw, prepared)
    print_summary("TRAIN_DELTA", train_result)
    print_summary("HOLDOUT_DELTA", holdout_result)
    print_summary("HOLDOUT_BASELINE_NO_DELTA", baseline_holdout)
    print_walk_forward(holdout, holdout_result["trades"])
    print_gate(gate)
    print_mc(mc)
    print(
        "ranked_verdict="
        + ranked_verdict(holdout_result["trades"], baseline_holdout["trades"], holdout)
    )
    print(f"trades_file={trade_path}")
    return 0


def load_mnq(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    return frame[["open", "high", "low", "close", "volume"]].copy()


def evaluate(model: FabioORBDeltaModel, prepared: pd.DataFrame) -> dict[str, object]:
    pnl, pos, market, trades = model._simulate_5m(prepared)
    rows = []
    for trade in trades:
        risk = abs(trade.entry_price - trade.stop_price) * model.point_value
        rows.append(
            {
                "entry_ts": trade.entry_ts,
                "exit_ts": trade.exit_ts,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "stop_price": trade.stop_price,
                "target_price": trade.target_price,
                "risk_dollars": risk,
                "pnl": trade.pnl,
                "gross_pnl": trade.pnl + model.commission_rt,
                "r_mult": trade.pnl / risk if risk > 0 else 0.0,
                "reason": trade.reason,
            }
        )
    return {
        "pnl": pnl,
        "pos": pos,
        "market": market,
        "trades": pd.DataFrame(rows),
    }


def gate_result(result: dict[str, object], model: FabioORBDeltaModel):
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
        commission_per_rt=1.0,
        min_trades_per_day=0,
        max_trades_per_day=1,
    )
    return run_empirical_many(params, trades["pnl"].to_numpy(float), daily_counts)


def observed_daily_counts(prepared: pd.DataFrame, trades: pd.DataFrame) -> np.ndarray:
    sessions = sorted(prepared["session"].dropna().unique())
    if trades.empty:
        return np.zeros(len(sessions), dtype=int)
    trade_days = pd.to_datetime(trades["entry_ts"]).dt.tz_convert("America/New_York").dt.date
    counts = trade_days.value_counts()
    return np.array([int(counts.get(session, 0)) for session in sessions], dtype=int)


def print_step0(raw: pd.DataFrame, prepared: pd.DataFrame) -> None:
    idx = pd.DatetimeIndex(raw.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    gaps = idx.to_series().diff().dropna().gt(pd.Timedelta(minutes=1.5)).sum()
    print("STEP_0_DATA_SANITY")
    print(
        f"rows_1m={len(raw)} start_utc={idx[0].isoformat()} end_utc={idx[-1].isoformat()} "
        f"gaps_gt_1m={int(gaps)} nan_ohlcv={int(raw[['open','high','low','close','volume']].isna().sum().sum())}"
    )
    print(
        f"price_min={raw['low'].min():.2f} price_max={raw['high'].max():.2f} "
        f"prepared_5m_rows={len(prepared)} prepared_sessions={prepared['session'].nunique()}"
    )
    print()


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
    friction = len(trades) * 1.0
    rr = avg_win / abs(avg_loss) if avg_loss < 0 else 0.0
    print(
        f"n_trades={len(trades)} win_rate={(pnl > 0).mean():.2%} "
        f"avg_win=${avg_win:.2f} avg_loss=${avg_loss:.2f} RR={rr:.3f} "
        f"mean=${np.mean(pnl):.2f} total=${np.sum(pnl):.2f}"
    )
    print(
        f"avg_risk=${trades['risk_dollars'].mean():.2f} max_risk=${trades['risk_dollars'].max():.2f} "
        f"friction=${friction:.2f} friction_pct_of_abs_gross_pnl="
        f"{(friction / gross_abs if gross_abs else 0.0):.2%} "
        f"skew={finite(stats.skew(pnl, bias=False)):.3f} "
        f"max_consec_losses={max_consecutive_losses(pnl)}"
    )
    print()


def print_walk_forward(prepared: pd.DataFrame, trades: pd.DataFrame) -> None:
    print("WALK_FORWARD_4_BUCKETS_HOLDOUT")
    rows = [["bucket", "start", "end", "n_trades", "mean_pnl", "win_rate"]]
    sessions = sorted(prepared["session"].dropna().unique())
    for idx, bucket in enumerate(np.array_split(np.asarray(sessions, dtype=object), 4), start=1):
        if len(bucket) == 0:
            continue
        if trades.empty:
            bucket_trades = trades
        else:
            trade_days = pd.to_datetime(trades["exit_ts"]).dt.tz_convert("America/New_York").dt.date
            bucket_trades = trades.loc[trade_days.isin(set(bucket))]
        pnl = bucket_trades["pnl"].to_numpy(float) if not bucket_trades.empty else np.array([], dtype=float)
        rows.append(
            [
                str(idx),
                str(bucket[0]),
                str(bucket[-1]),
                str(len(bucket_trades)),
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


def ranked_verdict(delta_trades: pd.DataFrame, baseline_trades: pd.DataFrame, prepared: pd.DataFrame) -> str:
    delta_mean = trade_mean(delta_trades)
    base_mean = trade_mean(baseline_trades)
    same_signed = walk_forward_same_signed(prepared, delta_trades)
    beats = delta_mean > base_mean
    if beats and same_signed:
        return "candidate_survives_approximation"
    return f"fail beats_baseline={beats} walk_forward_same_signed={same_signed}"


def walk_forward_same_signed(prepared: pd.DataFrame, trades: pd.DataFrame) -> bool:
    if trades.empty:
        return False
    sessions = sorted(prepared["session"].dropna().unique())
    signs: list[int] = []
    trade_days = pd.to_datetime(trades["exit_ts"]).dt.tz_convert("America/New_York").dt.date
    for bucket in np.array_split(np.asarray(sessions, dtype=object), 4):
        bucket_trades = trades.loc[trade_days.isin(set(bucket))]
        if bucket_trades.empty:
            return False
        mean = float(bucket_trades["pnl"].mean())
        signs.append(1 if mean > 0 else -1 if mean < 0 else 0)
    return all(sign > 0 for sign in signs) or all(sign < 0 for sign in signs)


def trade_mean(trades: pd.DataFrame) -> float:
    return 0.0 if trades.empty else float(trades["pnl"].mean())


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


if __name__ == "__main__":
    sys.exit(main())
