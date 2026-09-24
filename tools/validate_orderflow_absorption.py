"""Offline validation of the frozen MNQ order-flow absorption v1 candidate."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.orderflow_absorption import OrderflowAbsorptionModel
from core.config import DEFAULT_GATE_CFG
from core.validation.battery import run_gate
from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many


DATA = ROOT / "data" / "sierra" / "MNQ_continuous_1m_latest_90d.parquet"
OUT_DIR = ROOT / "data" / "prop_futures"
STARTING_BALANCE = 50_000.0
TRAIN_FRAC = 0.50
MIN_HOLDOUT_TRADES = 30


def main() -> int:
    if not DATA.exists():
        raise FileNotFoundError(f"required local parquet missing; refusing network fallback: {DATA}")
    raw = pd.read_parquet(DATA)
    print("ORDERFLOW ABSORPTION V1 OFFLINE VALIDATION")
    print(f"preregistration_sha256={OrderflowAbsorptionModel.preregistration_sha256}")
    print("network_calls=0 threshold_sweeps=0 split=50/50_by_RTH_session")
    print_step0(raw)

    model = OrderflowAbsorptionModel()
    result = model._run_backtest(raw)
    trades = model.trades_frame(raw)
    sessions = np.asarray(sorted(result.frame["_session"].dropna().unique()), dtype=object)
    cut = int(len(sessions) * TRAIN_FRAC)
    train_sessions = set(sessions[:cut])
    holdout_session_array = sessions[cut:]
    holdout_sessions = set(holdout_session_array)
    train = trades[trades["session"].isin(train_sessions)].copy() if not trades.empty else trades.copy()
    holdout = trades[trades["session"].isin(holdout_sessions)].copy() if not trades.empty else trades.copy()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trade_path = OUT_DIR / "orderflow_absorption_v1_MNQ_1m_trades.csv"
    trades.to_csv(trade_path, index=False)

    print_metrics("TRAIN", train)
    print_metrics("HOLDOUT", holdout)
    bucket_means = print_walk_forward(holdout_session_array, holdout)
    gate = gate_result(model, result, holdout_sessions, holdout)
    mc = monte_carlo(holdout_session_array, holdout)

    print("FUNNEL_GATE_HOLDOUT")
    print(
        f"passed={gate.passed} reasons={','.join(gate.reasons)} n={gate.n_trades} "
        f"dsr={gate.dsr:.6f} nw_t={gate.nw_t:.6f} boot_lo={gate.boot_lo:.6f} "
        f"max_dd={gate.max_dd:.6f} wf_min={gate.wf_min:.6f} mc_p={gate.mc_p}"
    )
    print()

    print("PROP_MONTECARLO_BUFFER_325")
    if mc is None:
        print("pass=0.0000% EV=-$99.00 died=0.0000% never=100.0000% 5day=0.0000%")
        pass_rate = 0.0
    else:
        pass_rate = mc.pass_rate
        print(
            f"pass={100*mc.pass_rate:.4f}% EV=${ev_per_eval(mc.pass_rate,2400.0,99.0):.2f} "
            f"died={100*mc.fail_died_mll:.4f}% never={100*mc.fail_no_target:.4f}% "
            f"5day={100*mc.fail_target_min_days:.4f}% avg_final=${mc.avg_final_balance:.2f} "
            f"avg_trades={mc.avg_trades:.2f}"
        )
    print()

    print("DISCRETION_GAP_LIST")
    for index, gap in enumerate(model.discretion_gaps(), start=1):
        print(f"{index}. {gap}")
    print()

    stable = sum(mean > 0 for mean in bucket_means) >= 3
    enough = len(holdout) >= MIN_HOLDOUT_TRADES
    net_positive = not holdout.empty and float(holdout["pnl"].mean()) > 0.0
    passed = bool(gate.passed and stable and enough and net_positive and pass_rate > 0.0)
    print("PRE_REGISTERED_VERDICT")
    print(
        f"{'PASS_CANDIDATE' if passed else 'FAIL_V1'} "
        f"holdout_n={len(holdout)} min_required={MIN_HOLDOUT_TRADES} "
        f"positive_wf_buckets={sum(mean > 0 for mean in bucket_means)}/4 "
        f"net_positive={net_positive} gate_pass={gate.passed} prop_pass_rate={pass_rate:.6f}"
    )
    print(f"trade_log={trade_path.relative_to(ROOT)}")
    return 0


def print_step0(raw: pd.DataFrame) -> None:
    idx = pd.DatetimeIndex(raw.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    gaps = idx.to_series().diff().dropna()
    required = ["open", "high", "low", "close", "volume", "bid_volume", "ask_volume", "delta"]
    mismatch = (raw["bid_volume"] + raw["ask_volume"] - raw["volume"]).abs()
    bad = mismatch > raw["volume"] * 0.05
    print("STEP_0_DATA_SANITY_MNQ")
    print(
        f"rows={len(raw)} start_utc={idx.min().isoformat()} end_utc={idx.max().isoformat()} "
        f"gaps_gt_1m={int((gaps > pd.Timedelta(minutes=1)).sum())} max_gap={gaps.max()} "
        f"duplicates={int(idx.duplicated().sum())} nan_required={int(raw[required].isna().sum().sum())} "
        f"bidask_mismatch_gt_5pct={100*float(bad.mean()):.4f}%"
    )
    print(f"price_min={raw['low'].min():.2f} price_max={raw['high'].max():.2f}")
    print()


def metric_values(trades: pd.DataFrame) -> dict[str, float | int | str]:
    if trades.empty:
        return {"n": 0, "win": 0.0, "avg_win": 0.0, "avg_loss": 0.0, "rr": 0.0, "mean": 0.0, "total": 0.0, "skew": 0.0, "worst": 0.0, "max_cl": 0, "reasons": ""}
    pnl = trades["pnl"].to_numpy(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0
    reason_counts = trades["reason"].value_counts().sort_index()
    return {
        "n": len(pnl),
        "win": float((pnl > 0).mean()),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "rr": avg_win / abs(avg_loss) if avg_loss < 0 else 0.0,
        "mean": float(pnl.mean()),
        "total": float(pnl.sum()),
        "skew": finite(stats.skew(pnl, bias=False)) if len(pnl) >= 3 else 0.0,
        "worst": float(pnl.min()),
        "max_cl": max_consecutive_losses(pnl),
        "reasons": ",".join(f"{key}:{value}" for key, value in reason_counts.items()),
    }


def print_metrics(label: str, trades: pd.DataFrame) -> None:
    m = metric_values(trades)
    print(label)
    print(
        f"trades={m['n']} win={100*float(m['win']):.2f}% avg_win=${float(m['avg_win']):.2f} "
        f"avg_loss=${float(m['avg_loss']):.2f} RR={float(m['rr']):.3f} mean=${float(m['mean']):.2f} "
        f"total=${float(m['total']):.2f} skew={float(m['skew']):.3f} worst=${float(m['worst']):.2f} "
        f"max_consecutive_losses={m['max_cl']} exits={m['reasons']}"
    )
    print()


def print_walk_forward(sessions: np.ndarray, trades: pd.DataFrame) -> list[float]:
    means: list[float] = []
    print("WALK_FORWARD_4_BUCKETS_HOLDOUT")
    for number, bucket in enumerate(np.array_split(sessions, 4), start=1):
        bucket_trades = trades[trades["session"].isin(set(bucket))] if len(bucket) and not trades.empty else trades.iloc[0:0]
        m = metric_values(bucket_trades)
        mean = float(m["mean"])
        means.append(mean)
        start = bucket[0] if len(bucket) else "n/a"
        end = bucket[-1] if len(bucket) else "n/a"
        print(f"bucket={number} start={start} end={end} trades={m['n']} win={100*float(m['win']):.2f}% mean=${mean:.2f} RR={float(m['rr']):.3f}")
    print()
    return means


def gate_result(model, result, holdout_sessions: set[object], holdout: pd.DataFrame):
    mask = result.frame["_session"].isin(holdout_sessions).to_numpy()
    active = holdout["pnl"].to_numpy(float) / STARTING_BALANCE if not holdout.empty else np.array([], dtype=float)
    cfg = DEFAULT_GATE_CFG.copy()
    cfg["wf_splits"] = 4
    return run_gate(
        result.pnl[mask] / STARTING_BALANCE,
        cfg,
        nb_trials=1,
        sr_trials_var=0.0,
        positions=result.pos[mask],
        active_returns=active,
        market_returns=result.market[mask] / STARTING_BALANCE,
        n_params=len(model.strategy_params),
    )


def monte_carlo(sessions: np.ndarray, holdout: pd.DataFrame):
    if holdout.empty:
        return None
    counts = holdout["session"].value_counts()
    daily_counts = np.asarray([int(counts.get(session, 0)) for session in sessions], dtype=int)
    params = SimParams(n_sims=10_000, daily_buffer=325.0, min_trades_per_day=0, max_trades_per_day=1, commission_per_rt=1.0)
    return run_empirical_many(params, holdout["pnl"].to_numpy(float), daily_counts)


def max_consecutive_losses(pnl: np.ndarray) -> int:
    best = run = 0
    for value in pnl:
        run = run + 1 if value < 0 else 0
        best = max(best, run)
    return best


def finite(value: float) -> float:
    value = float(value)
    return value if np.isfinite(value) else 0.0


if __name__ == "__main__":
    raise SystemExit(main())
