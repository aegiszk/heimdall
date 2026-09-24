"""Offline validation for the Okala 80/20 Nasdaq model.

Uses only local data/MNQ_1m.parquet. No network calls, no new data pulls, and
no parameter sweeps. The mechanical proxies are fixed in core.alpha.okala8020.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.okala8020 import Okala8020Model, SETUP_A, SETUP_B, SETUP_C, STARTING_BALANCE
from core.config import DEFAULT_GATE_CFG
from core.validation.battery import run_gate
from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many


DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "prop_futures"
INSTRUMENT = "MNQ"
TRAIN_FRAC = 0.60
ALL = "ALL"
SETUPS = (ALL, SETUP_A, SETUP_B, SETUP_C)


def main() -> int:
    ensure_data_present()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_parquet(DATA_DIR / "MNQ_1m.parquet")
    raw = raw[["open", "high", "low", "close", "volume"]].copy()

    print("OKALA 80/20 NASDAQ OFFLINE VALIDATION")
    print("network_calls=0 data_sources=data/MNQ_1m.parquet")
    print("market=MNQ split=60/40_by_RTH_session walk_forward=4_buckets no_tuning=true")
    print("resample_200s=pandas resample('200s', label='right', closed='right') from 1m OHLCV")
    print("resample_10m=pandas resample('10min', label='right', closed='right') from 1m OHLCV")
    print("C_h_pattern_status=dropped_ambiguous")
    print()
    print_data_sanity(raw)

    model = Okala8020Model()
    result = model._run_backtest(raw)
    trades = model.trades_frame(result.trades)
    trade_path = OUT_DIR / "okala8020_MNQ_1m_trades.csv"
    trades.to_csv(trade_path, index=False)

    sessions = np.asarray(sorted(result.frame["session"].dropna().unique()), dtype=object)
    cut = int(len(sessions) * TRAIN_FRAC)
    train_sessions = set(sessions[:cut])
    holdout_sessions = set(sessions[cut:])
    train_trades = subset_sessions(trades, train_sessions)
    holdout_trades = subset_sessions(trades, holdout_sessions)

    summary_rows: list[dict[str, Any]] = []
    for split, split_trades in (("train", train_trades), ("holdout", holdout_trades), ("full", trades)):
        for setup in SETUPS:
            summary_rows.append(
                {
                    "instrument": INSTRUMENT,
                    "split": split,
                    "setup": setup,
                    **metrics(subset_setup(split_trades, setup)),
                }
            )

    wf_rows = walk_forward_rows(sessions[cut:], holdout_trades)

    mc_rows: list[dict[str, Any]] = []
    for setup in SETUPS:
        setup_trades = subset_setup(holdout_trades, setup)
        daily_counts = observed_daily_counts(sessions[cut:], setup_trades)
        mc_rows.append(mc_row(setup, monte_carlo(setup_trades, daily_counts)))

    gate = gate_result(model, result, holdout_sessions, holdout_trades)
    gate_row = {
        "instrument": INSTRUMENT,
        "setup": ALL,
        "passed": gate.passed,
        "reasons": ",".join(gate.reasons),
        "n_trades": gate.n_trades,
        "dsr": gate.dsr,
        "nw_t": gate.nw_t,
        "boot_lo": gate.boot_lo,
        "max_dd": gate.max_dd,
        "wf_min": gate.wf_min,
        "mc_p": gate.mc_p,
        "trade_log": str(trade_path.relative_to(ROOT)),
    }

    print_summary_table(pd.DataFrame(summary_rows))
    print_walk_forward(pd.DataFrame(wf_rows))
    print_mc(pd.DataFrame(mc_rows))
    print_gate(pd.DataFrame([gate_row]))
    print_frequency_diagnostic(trades, result.diagnostics)
    print_discretion_gaps(model)
    print_verdict(pd.DataFrame(summary_rows), pd.DataFrame(mc_rows), pd.DataFrame([gate_row]))
    return 0


def ensure_data_present() -> None:
    path = DATA_DIR / "MNQ_1m.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Required local parquet missing; refusing to pull data: {path}")


def print_data_sanity(raw: pd.DataFrame) -> None:
    idx = pd.DatetimeIndex(raw.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    gaps = int(idx.to_series().diff().dropna().gt(pd.Timedelta(minutes=1.5)).sum())
    print("STEP_0_DATA_SANITY_MNQ")
    print(
        f"rows_1m={len(raw)} start_utc={idx[0].isoformat()} end_utc={idx[-1].isoformat()} "
        f"gaps_gt_1m={gaps} nan_ohlcv={int(raw[['open','high','low','close','volume']].isna().sum().sum())}"
    )
    print(f"price_min={raw['low'].min():.2f} price_max={raw['high'].max():.2f}")
    print()


def subset_sessions(trades: pd.DataFrame, sessions: set[object]) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    return trades[trades["session"].isin(sessions)].copy()


def subset_setup(trades: pd.DataFrame, setup: str) -> pd.DataFrame:
    if setup == ALL or trades.empty:
        return trades.copy()
    return trades[trades["setup"] == setup].copy()


def metrics(trades: pd.DataFrame) -> dict[str, Any]:
    if trades.empty:
        return {
            "n_trades": 0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "realized_rr": 0.0,
            "mean_pnl": 0.0,
            "total_pnl": 0.0,
            "skew": 0.0,
            "tp1_hit_rate": 0.0,
            "runner_contribution_pct": 0.0,
            "worst_5": "",
            "max_consec_losses": 0,
        }
    pnl = trades["pnl"].to_numpy(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    avg_win = mean_or_zero(wins)
    avg_loss = mean_or_zero(losses)
    tp1_abs = float(trades["tp1_gross_pnl"].abs().sum())
    runner_abs = float(trades["runner_gross_pnl"].abs().sum())
    return {
        "n_trades": int(len(trades)),
        "win_rate": float((pnl > 0).mean()),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "realized_rr": avg_win / abs(avg_loss) if avg_loss < 0 else 0.0,
        "mean_pnl": float(np.mean(pnl)),
        "total_pnl": float(np.sum(pnl)),
        "skew": finite(stats.skew(pnl, bias=False)) if len(pnl) >= 3 else 0.0,
        "tp1_hit_rate": float(trades["tp1_hit"].mean()),
        "runner_contribution_pct": runner_abs / (tp1_abs + runner_abs) if (tp1_abs + runner_abs) > 1e-12 else 0.0,
        "worst_5": ",".join(f"{value:.2f}" for value in np.sort(pnl)[:5]),
        "max_consec_losses": max_consecutive_losses(pnl),
    }


def walk_forward_rows(sessions: np.ndarray, trades: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, bucket in enumerate(np.array_split(sessions, 4), start=1):
        if len(bucket) == 0:
            continue
        bucket_trades = subset_sessions(trades, set(bucket))
        for setup in SETUPS:
            rows.append(
                {
                    "instrument": INSTRUMENT,
                    "bucket": idx,
                    "setup": setup,
                    "start": str(bucket[0]),
                    "end": str(bucket[-1]),
                    **metrics(subset_setup(bucket_trades, setup)),
                }
            )
    return rows


def observed_daily_counts(sessions: np.ndarray, trades: pd.DataFrame) -> np.ndarray:
    if len(sessions) == 0:
        return np.zeros(0, dtype=int)
    if trades.empty:
        return np.zeros(len(sessions), dtype=int)
    counts = trades["session"].value_counts()
    return np.asarray([int(counts.get(session, 0)) for session in sessions], dtype=int)


def monte_carlo(trades: pd.DataFrame, daily_counts: np.ndarray):
    if trades.empty:
        return None
    params = SimParams(
        n_sims=10_000,
        daily_buffer=325.0,
        min_trades_per_day=0,
        max_trades_per_day=max(1, int(daily_counts.max()) if len(daily_counts) else 1),
        commission_per_rt=1.0,
    )
    return run_empirical_many(params, trades["pnl"].to_numpy(float), daily_counts)


def mc_row(setup: str, mc) -> dict[str, Any]:
    if mc is None:
        return {
            "instrument": INSTRUMENT,
            "setup": setup,
            "pass_rate": 0.0,
            "ev_per_eval": -99.0,
            "fail_died_mll": 0.0,
            "fail_never_target": 1.0,
            "fail_failed_5day": 0.0,
            "avg_final_balance": 50_000.0,
            "avg_trades": 0.0,
        }
    return {
        "instrument": INSTRUMENT,
        "setup": setup,
        "pass_rate": mc.pass_rate,
        "ev_per_eval": ev_per_eval(mc.pass_rate, 2400.0, 99.0),
        "fail_died_mll": mc.fail_died_mll,
        "fail_never_target": mc.fail_no_target,
        "fail_failed_5day": mc.fail_target_min_days,
        "avg_final_balance": mc.avg_final_balance,
        "avg_trades": mc.avg_trades,
    }


def gate_result(model: Okala8020Model, result, holdout_sessions: set[object], holdout_trades: pd.DataFrame):
    mask = result.frame["session"].isin(holdout_sessions).to_numpy()
    returns = result.pnl[mask] / STARTING_BALANCE
    positions = result.pos[mask]
    market_returns = result.market[mask] / STARTING_BALANCE
    active_returns = holdout_trades["pnl"].to_numpy(float) / STARTING_BALANCE if not holdout_trades.empty else np.array([], dtype=float)
    cfg = DEFAULT_GATE_CFG.copy()
    cfg["wf_splits"] = 4
    return run_gate(
        returns,
        cfg,
        nb_trials=1,
        sr_trials_var=0.0,
        positions=positions,
        active_returns=active_returns,
        market_returns=market_returns,
        n_params=len(model.strategy_params),
    )


def print_summary_table(summary: pd.DataFrame) -> None:
    print("PER_SETUP_STATS")
    rows = [[
        "instrument",
        "split",
        "setup",
        "trades",
        "win",
        "avg_win",
        "avg_loss",
        "RR",
        "mean",
        "skew",
        "TP1",
        "runner%",
        "maxCL",
        "worst5",
    ]]
    for row in summary.sort_values(["split", "setup"]).itertuples(index=False):
        rows.append(
            [
                row.instrument,
                row.split,
                row.setup,
                str(int(row.n_trades)),
                pct(row.win_rate),
                money(row.avg_win),
                money(row.avg_loss),
                f"{row.realized_rr:.3f}",
                money(row.mean_pnl),
                f"{row.skew:.3f}",
                pct(row.tp1_hit_rate),
                pct(row.runner_contribution_pct),
                str(int(row.max_consec_losses)),
                row.worst_5,
            ]
        )
    print_table(rows)
    print()


def print_walk_forward(wf: pd.DataFrame) -> None:
    print("WALK_FORWARD_4_BUCKETS_HOLDOUT")
    rows = [["instrument", "bucket", "setup", "start", "end", "trades", "win", "RR", "mean", "TP1", "maxCL"]]
    for row in wf.sort_values(["bucket", "setup"]).itertuples(index=False):
        rows.append(
            [
                row.instrument,
                str(int(row.bucket)),
                row.setup,
                row.start,
                row.end,
                str(int(row.n_trades)),
                pct(row.win_rate),
                f"{row.realized_rr:.3f}",
                money(row.mean_pnl),
                pct(row.tp1_hit_rate),
                str(int(row.max_consec_losses)),
            ]
        )
    print_table(rows)
    print()


def print_mc(mc: pd.DataFrame) -> None:
    print("PROP_MONTECARLO_BUFFER_325")
    rows = [["instrument", "setup", "pass", "EV", "died", "never", "5day", "avg_final", "avg_trades"]]
    for row in mc.sort_values("setup").itertuples(index=False):
        rows.append(
            [
                row.instrument,
                row.setup,
                pct(row.pass_rate),
                money(row.ev_per_eval),
                pct(row.fail_died_mll),
                pct(row.fail_never_target),
                pct(row.fail_failed_5day),
                money(row.avg_final_balance),
                f"{row.avg_trades:.2f}",
            ]
        )
    print_table(rows)
    print()


def print_gate(gates: pd.DataFrame) -> None:
    print("FUNNEL_GATE_HOLDOUT")
    rows = [["instrument", "setup", "passed", "reasons", "n", "dsr", "nw_t", "boot_lo", "max_dd", "wf_min", "mc_p", "trade_log"]]
    for row in gates.itertuples(index=False):
        rows.append(
            [
                row.instrument,
                row.setup,
                "YES" if row.passed else "NO",
                row.reasons,
                str(int(row.n_trades)),
                f"{row.dsr:.4f}",
                f"{row.nw_t:.4f}",
                f"{row.boot_lo:.4f}",
                f"{row.max_dd:.4f}",
                f"{row.wf_min:.4f}",
                f"{row.mc_p:.4f}" if row.mc_p is not None else "n/a",
                row.trade_log,
            ]
        )
    print_table(rows)
    print()


def print_frequency_diagnostic(trades: pd.DataFrame, diagnostics) -> None:
    print("FREQUENCY_DIAGNOSTIC")
    print(f"full_period_trades={len(trades)} expected_daily_scale_min=100")
    keys = [
        "A_strong_move",
        "A_wick_level_miss",
        "A_second_candle_confirm",
        f"{SETUP_A}_entries",
        "B_large_body_pair",
        "B_gap_imbalance",
        "B_zone_has_8020",
        "B_zone_touch",
        f"{SETUP_B}_entries",
    ]
    rows = [["condition", "count"]]
    for key in keys:
        rows.append([key, str(int(diagnostics.get(key, 0)))])
    print_table(rows)
    if len(trades) < 100:
        label, drop = largest_drop(diagnostics)
        print(f"under_100_trades=true likely_over_strict_condition={label} conditional_keep={pct(drop)}")
    else:
        print("under_100_trades=false")
    print()


def largest_drop(diagnostics) -> tuple[str, float]:
    edges = []
    chains = [
        ["A_strong_move", "A_wick_level_miss", "A_second_candle_confirm", f"{SETUP_A}_entries"],
        ["B_large_body_pair", "B_gap_imbalance", "B_zone_has_8020", "B_zone_touch", f"{SETUP_B}_entries"],
    ]
    for chain in chains:
        for left, right in zip(chain, chain[1:]):
            left_count = int(diagnostics.get(left, 0))
            right_count = int(diagnostics.get(right, 0))
            if left_count > 0:
                edges.append((f"{left}->{right}", right_count / left_count))
    if not edges:
        return "no_candidates", 0.0
    return min(edges, key=lambda item: item[1])


def print_discretion_gaps(model: Okala8020Model) -> None:
    print("DISCRETION_GAP_LIST")
    for idx, item in enumerate(model.discretion_gaps(), start=1):
        print(f"{idx}. {item}")
    print()


def print_verdict(summary: pd.DataFrame, mc: pd.DataFrame, gates: pd.DataFrame) -> None:
    holdout_all = summary[(summary["split"] == "holdout") & (summary["setup"] == ALL)].iloc[0]
    mc_all = mc[mc["setup"] == ALL].iloc[0]
    gate = gates.iloc[0]
    print("FUNNEL_VERDICT")
    if bool(gate.passed) and float(mc_all.ev_per_eval) > 0.0:
        print(
            "SURVIVES: "
            f"holdout_n={int(holdout_all.n_trades)} win={pct(holdout_all.win_rate)} "
            f"MC_pass={pct(mc_all.pass_rate)} EV={money(mc_all.ev_per_eval)}"
        )
    else:
        print(
            "FAIL: "
            f"gate_pass={bool(gate.passed)} reasons={gate.reasons} holdout_n={int(holdout_all.n_trades)} "
            f"MC_pass={pct(mc_all.pass_rate)} EV={money(mc_all.ev_per_eval)}"
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


def mean_or_zero(values) -> float:
    arr = np.asarray(values, dtype=float)
    return float(np.mean(arr)) if len(arr) else 0.0


def finite(value: float) -> float:
    value = float(value)
    return value if np.isfinite(value) else 0.0


def money(value: float) -> str:
    return f"${float(value):.2f}"


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
