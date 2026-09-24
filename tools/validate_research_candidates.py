"""One-shot validation for the frozen LuxAlgo and YouTube candidates.

The matching pre-registration documents were hashed before this script was
executed on market outcomes. This program contains no search or tuning loop.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import skew


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.research_candidates import OpeningFvgScalpModel, PocSweepReclaimModel
from core.config import DEFAULT_GATE_CFG
from core.validation.battery import run_gate
from tools.prop_montecarlo import SimParams, run_empirical_many


DATA = ROOT / "data" / "MNQ_1m.parquet"
OUT = ROOT / "data" / "strategy_research"
STARTING_CAPITAL = 50_000.0
TRAIN_FRACTION = 0.60


def _max_consecutive_losses(values: np.ndarray) -> int:
    longest = current = 0
    for value in values:
        current = current + 1 if value < 0 else 0
        longest = max(longest, current)
    return longest


def _metrics(trades: pd.DataFrame) -> dict[str, float | int | None]:
    pnl = trades["pnl"].to_numpy(float) if len(trades) else np.array([], dtype=float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    avg_win = float(np.mean(wins)) if len(wins) else None
    avg_loss = float(np.mean(losses)) if len(losses) else None
    payoff = avg_win / abs(avg_loss) if avg_win is not None and avg_loss not in (None, 0.0) else None
    return {
        "trades": int(len(pnl)),
        "win_rate": float(np.mean(pnl > 0)) if len(pnl) else None,
        "mean_pnl": float(np.mean(pnl)) if len(pnl) else None,
        "total_pnl": float(np.sum(pnl)),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "realized_payoff": payoff,
        "skew": float(skew(pnl, bias=False)) if len(pnl) >= 3 else None,
        "max_consecutive_losses": _max_consecutive_losses(pnl),
    }


def _session_split(frame: pd.DataFrame) -> tuple[list[object], list[object]]:
    sessions = sorted(frame["_session"].unique())
    cut = int(len(sessions) * TRAIN_FRACTION)
    return sessions[:cut], sessions[cut:]


def _annotate_sessions(trades: pd.DataFrame) -> pd.DataFrame:
    result = trades.copy()
    if len(result):
        result["session"] = pd.to_datetime(result["entry_ts"]).dt.date
    else:
        result["session"] = pd.Series(dtype=object)
    return result


def _gate(trades: pd.DataFrame) -> dict[str, object]:
    active = trades["pnl"].to_numpy(float) / STARTING_CAPITAL
    result = run_gate(
        active,
        DEFAULT_GATE_CFG,
        nb_trials=2,
        sr_trials_var=1.0,
        active_returns=active,
        n_params=3,
    )
    return asdict(result)


def _monte_carlo(trades: pd.DataFrame, sessions: list[object]) -> dict[str, float | int]:
    pnl = trades["pnl"].to_numpy(float)
    if len(pnl) == 0:
        return {"not_run": 1, "reason": "zero holdout trades"}
    counts = trades.groupby("session").size().reindex(sessions, fill_value=0).to_numpy(int)
    params = SimParams(
        n_sims=10_000,
        seed=20260922,
        max_days=80,
        min_trades_per_day=0,
        max_trades_per_day=1,
        daily_buffer=325.0,
        kill_cushion=400.0,
        protect_green_at=500.0,
        min_profit_day=150.0,
        min_profit_days_required=5,
        commission_per_rt=0.0,
    )
    result = run_empirical_many(params, pnl, counts)
    return {
        "sims": params.n_sims,
        "pass_rate": result.pass_rate,
        "fail_died_mll": result.fail_died_mll,
        "fail_never_reached_target": result.fail_no_target,
        "fail_target_min_days": result.fail_target_min_days,
        "avg_days": result.avg_days,
        "avg_trades": result.avg_trades,
        "avg_final_balance": result.avg_final_balance,
        "observed_daily_count_zero_rate": float(np.mean(counts == 0)),
    }


def _walk_forward(trades: pd.DataFrame, holdout_sessions: list[object]) -> list[dict[str, object]]:
    buckets = np.array_split(np.asarray(holdout_sessions, dtype=object), 4)
    rows = []
    for number, bucket in enumerate(buckets, start=1):
        subset = trades.loc[trades["session"].isin(set(bucket))]
        row = {"bucket": number}
        if len(bucket):
            row.update({"start": str(bucket[0]), "end": str(bucket[-1])})
        row.update(_metrics(subset))
        rows.append(row)
    return rows


def _evaluate(name: str, model, raw: pd.DataFrame) -> dict[str, object]:
    frame = model._prepare_frame(raw)
    _, _, _, trade_records = model._simulate(frame)
    trades = _annotate_sessions(
        pd.DataFrame(
            [
                {
                    "entry_ts": trade.entry_ts,
                    "exit_ts": trade.exit_ts,
                    "side": trade.side,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "stop_price": trade.stop_price,
                    "target_price": trade.target_price,
                    "pnl": trade.pnl,
                    "reason": trade.reason,
                }
                for trade in trade_records
            ]
        )
    )
    train_sessions, holdout_sessions = _session_split(frame)
    train = trades.loc[trades["session"].isin(set(train_sessions))]
    holdout = trades.loc[trades["session"].isin(set(holdout_sessions))]
    result = {
        "name": name,
        "bar_rows": len(frame),
        "sessions": len(train_sessions) + len(holdout_sessions),
        "train_session_count": len(train_sessions),
        "holdout_session_count": len(holdout_sessions),
        "train": _metrics(train),
        "holdout": _metrics(holdout),
        "holdout_walk_forward": _walk_forward(trades, holdout_sessions),
        "holdout_gate": _gate(holdout),
        "holdout_lucid_monte_carlo": _monte_carlo(holdout, holdout_sessions),
    }
    trades.to_csv(OUT / f"{name}_trades.csv", index=False)
    return result


def _poc_proxy_fidelity() -> dict[str, float | int | str]:
    minute_path = ROOT / "data" / "sierra" / "NQ_continuous_1m_latest_90d.parquet"
    footprint_path = ROOT / "data" / "sierra" / "tick" / "NQ_continuous_1m_footprint.parquet"
    minute = pd.read_parquet(minute_path, columns=["close", "volume"]).reset_index()
    minute = minute.rename(columns={minute.columns[0]: "minute"})
    minute["minute"] = pd.to_datetime(minute["minute"], utc=True)
    local = minute["minute"].dt.tz_convert("America/New_York")
    minute = minute.loc[(local.dt.time >= pd.Timestamp("09:30").time()) & (local.dt.time < pd.Timestamp("16:00").time())].copy()
    minute["bucket"] = minute["minute"].dt.floor("5min")

    proxy_rows = []
    for bucket, group in minute.groupby("bucket", sort=True):
        volume_at_close = group.groupby("close", sort=False)["volume"].sum()
        proxy_rows.append((bucket, float(volume_at_close.idxmax())))
    proxy = pd.DataFrame(proxy_rows, columns=["bucket", "proxy_poc"])

    footprint = pd.read_parquet(footprint_path, columns=["minute", "price", "volume"])
    footprint["minute"] = pd.to_datetime(footprint["minute"], utc=True)
    local = footprint["minute"].dt.tz_convert("America/New_York")
    footprint = footprint.loc[(local.dt.time >= pd.Timestamp("09:30").time()) & (local.dt.time < pd.Timestamp("16:00").time())].copy()
    footprint["bucket"] = footprint["minute"].dt.floor("5min")
    exact = footprint.groupby(["bucket", "price"], sort=True)["volume"].sum().reset_index()
    exact = exact.loc[exact.groupby("bucket")["volume"].idxmax(), ["bucket", "price"]]
    exact = exact.rename(columns={"price": "exact_poc"})

    compared = proxy.merge(exact, on="bucket", how="inner")
    diff_ticks = (compared["proxy_poc"] - compared["exact_poc"]).abs() / 0.25
    return {
        "minute_source": str(minute_path.relative_to(ROOT)),
        "footprint_source": str(footprint_path.relative_to(ROOT)),
        "overlap_5m_bars": int(len(compared)),
        "exact_match_rate": float(np.mean(diff_ticks == 0)) if len(diff_ticks) else 0.0,
        "median_absolute_ticks": float(np.median(diff_ticks)) if len(diff_ticks) else 0.0,
        "p95_absolute_ticks": float(np.quantile(diff_ticks, 0.95)) if len(diff_ticks) else 0.0,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = pd.read_parquet(DATA)
    print("STEP 0 DATA SANITY")
    print(f"path={DATA.relative_to(ROOT)} rows={len(raw)} columns={list(raw.columns)}")
    print(f"index_min={raw.index.min()} index_max={raw.index.max()} duplicates={int(raw.index.duplicated().sum())}")
    print(f"nonfinite_ohlc={int((~np.isfinite(raw[['open','high','low','close']].to_numpy(float))).sum())}")
    print()

    fidelity = _poc_proxy_fidelity()
    print("SIERRA POC PROXY FIDELITY")
    print(json.dumps(fidelity, indent=2))
    print()

    results = {
        "pre_registered": True,
        "post_result_tuning": False,
        "poc_proxy_fidelity": fidelity,
        "candidates": [
            _evaluate("luxalgo_poc_sweep_reclaim", PocSweepReclaimModel("MNQ"), raw),
            _evaluate("youtube_opening_fvg_scalp", OpeningFvgScalpModel("MNQ"), raw),
        ],
    }
    for result in results["candidates"]:
        print(result["name"].upper())
        print(json.dumps(result, indent=2, default=str))
        print()

    output = OUT / "validation_2026-09-22.json"
    output.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"saved={output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
