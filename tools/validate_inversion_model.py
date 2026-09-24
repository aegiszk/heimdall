"""Offline validation for the Dhesi/Chart Fanatics inversion model.

Uses only local data/{MNQ,MES,ES}_1m.parquet. No network calls and no new data
pulls. The thresholds are fixed in core.alpha.inversion_model.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.inversion_model import InversionModel, STARTING_BALANCE
from core.config import DEFAULT_GATE_CFG
from core.validation.battery import run_gate
from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many


DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "prop_futures"
INSTRUMENTS = ("MNQ", "MES", "ES")
TRAIN_FRAC = 0.60


def main() -> int:
    ensure_data_present()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, object]] = []
    wf_rows: list[dict[str, object]] = []
    mc_rows: list[dict[str, object]] = []
    gate_rows: list[dict[str, object]] = []

    print("INVERSION MODEL OFFLINE VALIDATION")
    print("network_calls=0 data_sources=data/MNQ_1m.parquet,data/MES_1m.parquet,data/ES_1m.parquet")
    print("split=60/40_by_RTH_session walk_forward=4_buckets no_tuning=true")
    print()

    for instrument in INSTRUMENTS:
        raw = pd.read_parquet(DATA_DIR / f"{instrument}_1m.parquet")
        raw = raw[["open", "high", "low", "close", "volume"]].copy()
        print_step0(instrument, raw)

        model = InversionModel(contract=instrument)
        result = model._run_backtest(raw)
        trades = model.trades_frame(result.trades)
        trade_path = OUT_DIR / f"inversion_model_{instrument}_1m_trades.csv"
        trades.to_csv(trade_path, index=False)

        sessions = np.asarray(sorted(result.frame["_session"].dropna().unique()), dtype=object)
        cut = int(len(sessions) * TRAIN_FRAC)
        train_sessions = set(sessions[:cut])
        holdout_sessions = set(sessions[cut:])
        train_trades = trades[trades["session"].isin(train_sessions)].copy() if not trades.empty else trades.copy()
        holdout_trades = trades[trades["session"].isin(holdout_sessions)].copy() if not trades.empty else trades.copy()

        summaries.append({"instrument": instrument, "split": "train", **metrics(train_trades)})
        summaries.append({"instrument": instrument, "split": "holdout", **metrics(holdout_trades)})
        wf_rows.extend(walk_forward_rows(instrument, sessions[cut:], holdout_trades))

        daily_counts = observed_daily_counts(sessions[cut:], holdout_trades)
        mc = monte_carlo(holdout_trades, daily_counts)
        mc_rows.append(mc_row(instrument, mc))

        gate = gate_result(model, result, holdout_sessions, holdout_trades)
        gate_rows.append(
            {
                "instrument": instrument,
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
        )

    print_summary_table(pd.DataFrame(summaries))
    print_walk_forward(pd.DataFrame(wf_rows))
    print_mc(pd.DataFrame(mc_rows))
    print_gate(pd.DataFrame(gate_rows))
    print_discretion_gaps()
    print_verdict(pd.DataFrame(summaries), pd.DataFrame(mc_rows), pd.DataFrame(gate_rows))
    return 0


def ensure_data_present() -> None:
    missing = [str(DATA_DIR / f"{instrument}_1m.parquet") for instrument in INSTRUMENTS if not (DATA_DIR / f"{instrument}_1m.parquet").exists()]
    if missing:
        raise FileNotFoundError(f"Required local parquet missing; refusing to pull data: {missing}")


def print_step0(instrument: str, raw: pd.DataFrame) -> None:
    idx = pd.DatetimeIndex(raw.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    gaps = int(idx.to_series().diff().dropna().gt(pd.Timedelta(minutes=1.5)).sum())
    print(f"STEP_0_DATA_SANITY_{instrument}")
    print(
        f"rows_1m={len(raw)} start_utc={idx[0].isoformat()} end_utc={idx[-1].isoformat()} "
        f"gaps_gt_1m={gaps} nan_ohlcv={int(raw[['open','high','low','close','volume']].isna().sum().sum())}"
    )
    print(f"price_min={raw['low'].min():.2f} price_max={raw['high'].max():.2f}")
    print()


def metrics(trades: pd.DataFrame) -> dict[str, object]:
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


def walk_forward_rows(instrument: str, sessions: np.ndarray, trades: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, bucket in enumerate(np.array_split(sessions, 4), start=1):
        if len(bucket) == 0:
            continue
        bucket_set = set(bucket)
        bucket_trades = trades[trades["session"].isin(bucket_set)].copy() if not trades.empty else trades.copy()
        rows.append(
            {
                "instrument": instrument,
                "bucket": idx,
                "start": str(bucket[0]),
                "end": str(bucket[-1]),
                **metrics(bucket_trades),
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
        max_trades_per_day=1,
        commission_per_rt=1.0,
    )
    return run_empirical_many(params, trades["pnl"].to_numpy(float), daily_counts)


def mc_row(instrument: str, mc) -> dict[str, object]:
    if mc is None:
        return {
            "instrument": instrument,
            "pass_rate": 0.0,
            "ev_per_eval": -99.0,
            "fail_died_mll": 0.0,
            "fail_never_target": 1.0,
            "fail_failed_5day": 0.0,
            "avg_final_balance": 50_000.0,
            "avg_trades": 0.0,
        }
    return {
        "instrument": instrument,
        "pass_rate": mc.pass_rate,
        "ev_per_eval": ev_per_eval(mc.pass_rate, 2400.0, 99.0),
        "fail_died_mll": mc.fail_died_mll,
        "fail_never_target": mc.fail_no_target,
        "fail_failed_5day": mc.fail_target_min_days,
        "avg_final_balance": mc.avg_final_balance,
        "avg_trades": mc.avg_trades,
    }


def gate_result(model: InversionModel, result, holdout_sessions: set[object], holdout_trades: pd.DataFrame):
    mask = result.frame["_session"].isin(holdout_sessions).to_numpy()
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
    print("PER_INSTRUMENT_STATS")
    rows = [[
        "instrument",
        "split",
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
    for row in summary.sort_values(["instrument", "split"]).itertuples(index=False):
        rows.append(
            [
                row.instrument,
                row.split,
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
    rows = [["instrument", "bucket", "start", "end", "trades", "win", "RR", "mean", "TP1", "maxCL"]]
    for row in wf.sort_values(["instrument", "bucket"]).itertuples(index=False):
        rows.append(
            [
                row.instrument,
                str(int(row.bucket)),
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
    rows = [["instrument", "pass", "EV", "died", "never", "5day", "avg_final", "avg_trades"]]
    for row in mc.sort_values("instrument").itertuples(index=False):
        rows.append(
            [
                row.instrument,
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
    rows = [["instrument", "passed", "reasons", "n", "dsr", "nw_t", "boot_lo", "max_dd", "wf_min", "mc_p", "trade_log"]]
    for row in gates.sort_values("instrument").itertuples(index=False):
        rows.append(
            [
                row.instrument,
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


def print_discretion_gaps() -> None:
    print("DISCRETION_GAP_LIST")
    for idx, item in enumerate(InversionModel.discretion_gaps(), start=1):
        print(f"{idx}. {item}")
    print()


def print_verdict(summary: pd.DataFrame, mc: pd.DataFrame, gates: pd.DataFrame) -> None:
    holdout = summary[summary["split"] == "holdout"]
    merged = holdout.merge(mc, on="instrument").merge(gates[["instrument", "passed", "reasons"]], on="instrument")
    survivors = merged[(merged["passed"]) & (merged["ev_per_eval"] > 0.0)]
    print("FUNNEL_VERDICT")
    if survivors.empty:
        reasons = []
        for row in merged.sort_values("instrument").itertuples(index=False):
            reasons.append(f"{row.instrument}: gate_pass={row.passed} reasons={row.reasons} EV={row.ev_per_eval:.2f} holdout_n={row.n_trades}")
        print("FAIL: no instrument passed the holdout funnel with positive Monte Carlo EV.")
        print("details=" + " | ".join(reasons))
    else:
        best = survivors.sort_values("ev_per_eval", ascending=False).iloc[0]
        print(
            "SURVIVES: "
            f"{best.instrument} pass_rate={best.pass_rate:.4%} EV={best.ev_per_eval:.2f} "
            f"holdout_n={int(best.n_trades)}"
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
