"""Offline validation of frozen NQ price-level footprint absorption v2."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.orderflow_footprint import run_backtest
from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many


DATA = ROOT / "data" / "sierra" / "tick" / "NQ_continuous_1m_footprint.parquet"
PREREG = ROOT / "ORDERFLOW_FOOTPRINT_PREREGISTRATION.md"
MIN_HOLDOUT = 30


def metrics(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {"n": 0, "win": 0, "mean": 0, "total": 0, "rr": 0, "worst": 0}
    pnl = frame.pnl.to_numpy(float)
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    return {
        "n": len(pnl),
        "win": float((pnl > 0).mean()),
        "mean": float(pnl.mean()),
        "total": float(pnl.sum()),
        "rr": float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses) else 0,
        "worst": float(pnl.min()),
    }


def show(label: str, frame: pd.DataFrame) -> None:
    m = metrics(frame)
    reasons = ",".join(f"{k}:{v}" for k, v in frame.reason.value_counts().sort_index().items()) if not frame.empty else ""
    print(f"{label} trades={m['n']} win={100*m['win']:.2f}% mean=${m['mean']:.2f} total=${m['total']:.2f} RR={m['rr']:.3f} worst=${m['worst']:.2f} exits={reasons}")


def main() -> int:
    expected = (ROOT / "ORDERFLOW_FOOTPRINT_PREREGISTRATION.sha256").read_text().split()[0]
    actual = hashlib.sha256(PREREG.read_bytes()).hexdigest().upper()
    if actual != expected:
        raise RuntimeError("pre-registration hash mismatch")
    footprint = pd.read_parquet(DATA)
    sessions = np.asarray(sorted(footprint.session.unique()), dtype=object)
    print("ORDERFLOW FOOTPRINT V2 OFFLINE VALIDATION")
    print(f"preregistration_sha256={actual}")
    print("network_calls=0 threshold_sweeps=0 split=50/50_by_selected_RTH_session")
    print(f"STEP_0 rows={len(footprint):,} sessions={len(sessions)} start={footprint.minute.min()} end={footprint.minute.max()} duplicate_cells={int(footprint.duplicated(['minute','price']).sum())} nulls={int(footprint.isna().sum().sum())}")
    trades, funnel = run_backtest(footprint)
    eligible = sessions[20:]
    cut = len(eligible) // 2
    train_sessions, holdout_sessions = set(eligible[:cut]), eligible[cut:]
    train = trades[trades.session.isin(train_sessions)] if not trades.empty else trades
    holdout = trades[trades.session.isin(set(holdout_sessions))] if not trades.empty else trades
    print("FUNNEL " + " ".join(f"{key}={value}" for key, value in funnel.items()))
    show("TRAIN", train)
    show("HOLDOUT", holdout)
    positive = 0
    print("WALK_FORWARD_4_BUCKETS_HOLDOUT")
    for number, bucket in enumerate(np.array_split(holdout_sessions, 4), 1):
        part = holdout[holdout.session.isin(set(bucket))] if len(bucket) and not holdout.empty else holdout.iloc[0:0]
        m = metrics(part)
        positive += m["mean"] > 0
        print(f"bucket={number} sessions={len(bucket)} trades={m['n']} win={100*m['win']:.2f}% mean=${m['mean']:.2f}")
    if holdout.empty:
        pass_rate = 0.0
        print("PROP pass=0.0000% never=100.0000%")
    else:
        counts = holdout.session.value_counts()
        daily = np.asarray([int(counts.get(session, 0)) for session in holdout_sessions])
        result = run_empirical_many(
            SimParams(n_sims=10_000, daily_buffer=325.0, min_trades_per_day=0, max_trades_per_day=1, commission_per_rt=1.0),
            holdout.pnl.to_numpy(float),
            daily,
        )
        pass_rate = result.pass_rate
        print(f"PROP pass={100*pass_rate:.4f}% EV=${ev_per_eval(pass_rate,2400.0,99.0):.2f} died={100*result.fail_died_mll:.4f}% never={100*result.fail_no_target:.4f}%")
    m = metrics(holdout)
    passed = m["n"] >= MIN_HOLDOUT and m["win"] >= 0.50 and m["mean"] > 0 and positive >= 3 and pass_rate > 0.0396
    verdict = "PASS_CANDIDATE" if passed else "FAIL_V2"
    print(f"PRE_REGISTERED_VERDICT {verdict} holdout_n={m['n']} min_required={MIN_HOLDOUT} win={100*m['win']:.2f}% positive_wf={positive}/4 net_positive={m['mean']>0} prop_above_breakeven={pass_rate>0.0396}")
    out = ROOT / "data" / "prop_futures" / "orderflow_footprint_v2_NQ_trades.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out, index=False)
    print(f"trade_log={out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
