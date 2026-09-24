"""One-shot validation for DHESI_V3_PREREGISTRATION.md. No network, no tuning."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.inversion_model import InversionModel
from core.alpha.inversion_model_v3 import InversionModelV3
from tools.prop_montecarlo import SimParams, ev_per_eval, run_empirical_many
from tools.validate_inversion_model import gate_result, metrics, observed_daily_counts, walk_forward_rows


OUT = ROOT / "data" / "strategy_research"
FRESH_START = pd.Timestamp("2026-07-01", tz="UTC")
FRESH_FIRST_SESSION = pd.Timestamp("2026-07-01").date()
FRESH_LAST_SESSION = pd.Timestamp("2026-09-18").date()
TRAIN_FRAC = 0.60
OHLCV = ["open", "high", "low", "close", "volume"]


def step0(name: str, raw: pd.DataFrame) -> None:
    idx = pd.DatetimeIndex(raw.index)
    print(f"STEP0 {name}: rows={len(raw)} start={idx.min()} end={idx.max()} "
          f"dup={int(idx.duplicated().sum())} nan={int(raw[OHLCV].isna().sum().sum())}")


def monte_carlo(trades: pd.DataFrame, sessions) -> dict:
    if trades.empty:
        return {"pass_rate": 0.0, "note": "zero trades"}
    counts = observed_daily_counts(np.asarray(sessions, dtype=object), trades)
    params = SimParams(n_sims=10_000, seed=20260922, daily_buffer=325.0, min_trades_per_day=0,
                       max_trades_per_day=3, commission_per_rt=0.0)
    mc = run_empirical_many(params, trades["pnl"].to_numpy(float), counts)
    return {"pass_rate": mc.pass_rate, "ev_per_eval": ev_per_eval(mc.pass_rate, 2400.0, 99.0),
            "fail_died_mll": mc.fail_died_mll, "fail_never_target": mc.fail_no_target,
            "fail_5day": mc.fail_target_min_days, "avg_trades": mc.avg_trades}


def evaluate(model, raw: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    result = model._run_backtest(raw)
    trades = model.trades_frame(result.trades)
    sessions = np.asarray(sorted(result.frame["_session"].dropna().unique()), dtype=object)
    cut = int(len(sessions) * TRAIN_FRAC)
    train, hold = set(sessions[:cut]), set(sessions[cut:])
    tr = trades[trades["session"].isin(train)] if len(trades) else trades
    ho = trades[trades["session"].isin(hold)] if len(trades) else trades
    buckets = walk_forward_rows(model.contract, sessions[cut:], ho)
    gate = gate_result(model, result, hold, ho)
    out = {
        "whole": metrics(trades),
        "train": metrics(tr),
        "holdout": metrics(ho),
        "holdout_buckets": [{k: b[k] for k in ("bucket", "start", "end", "n_trades", "win_rate", "mean_pnl", "total_pnl")}
                            for b in buckets],
        "holdout_gate": {"passed": gate.passed, "reasons": list(gate.reasons), "dsr": gate.dsr, "nw_t": gate.nw_t,
                         "boot_lo": gate.boot_lo, "wf_min": gate.wf_min},
        "holdout_mc": monte_carlo(ho, sessions[cut:]),
        "entry_hour_counts": trades["entry_ts"].map(lambda t: pd.Timestamp(t).hour).value_counts().sort_index().to_dict()
        if len(trades) else {},
        "reason_counts": trades["reason"].value_counts().to_dict() if len(trades) else {},
    }
    return out, trades


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    dev = pd.read_parquet(ROOT / "data" / "MNQ_1m.parquet")[OHLCV]
    sierra = pd.read_parquet(ROOT / "data" / "sierra" / "MNQ_continuous_1m_latest_90d.parquet")[OHLCV]
    step0("MNQ_1m", dev)
    step0("sierra_MNQ", sierra)

    overlap = dev[["close"]].join(sierra[["close"]], how="inner", lsuffix="_dev", rsuffix="_sierra")
    overlap_rate = float((overlap["close_dev"] == overlap["close_sierra"]).mean()) if len(overlap) else 0.0
    print(f"OVERLAP minutes={len(overlap)} close_equal_rate={overlap_rate:.4f}")

    report: dict = {"preregistration": "DHESI_V3_PREREGISTRATION.md", "overlap_minutes": len(overlap),
                    "overlap_close_equal_rate": overlap_rate}

    v2_trades = InversionModel(contract="MNQ").trades_frame(InversionModel(contract="MNQ")._run_backtest(dev).trades)
    off = InversionModelV3(contract="MNQ", htf_24h=False, early_sweeps=False, session_pools=False,
                           stop_guard=False, attempts=False)
    off_trades = off.trades_frame(off._run_backtest(dev).trades)
    report["reproduction"] = {"v2_trades": len(v2_trades), "v3_all_off_trades": len(off_trades),
                              "v2_total": float(v2_trades["pnl"].sum()), "v3_all_off_total": float(off_trades["pnl"].sum())}
    print("REPRODUCTION", report["reproduction"])

    v3 = InversionModelV3(contract="MNQ")
    report["development_v3"], dev_trades = evaluate(v3, dev)
    dev_trades.to_csv(OUT / "dhesi_v3_development_trades.csv", index=False)
    print("DEVELOPMENT_V3", json.dumps(report["development_v3"], default=str, indent=1))

    ablations = {}
    for switch in ("htf_24h", "early_sweeps", "session_pools", "stop_guard", "attempts"):
        flags = {k: False for k in ("htf_24h", "early_sweeps", "session_pools", "stop_guard", "attempts")}
        flags[switch] = True
        res, _ = evaluate(InversionModelV3(contract="MNQ", **flags), dev)
        ablations[switch] = {"whole": res["whole"], "holdout": res["holdout"]}
        print("ABLATION", switch, {k: res["whole"][k] for k in ("n_trades", "win_rate", "mean_pnl", "total_pnl")})
    report["ablations_single_fix_on_v2"] = ablations

    if overlap_rate < 0.95:
        report["fresh"] = {"not_run": True, "reason": f"overlap close-equal {overlap_rate:.4f} < 0.95"}
    else:
        stitched = pd.concat([dev.loc[dev.index < FRESH_START], sierra.loc[sierra.index >= FRESH_START]])
        result = v3._run_backtest(stitched)
        trades = v3.trades_frame(result.trades)
        fresh_sessions = [s for s in sorted(result.frame["_session"].unique())
                          if FRESH_FIRST_SESSION <= s <= FRESH_LAST_SESSION]
        fresh = trades[trades["session"].isin(set(fresh_sessions))] if len(trades) else trades
        fresh.to_csv(OUT / "dhesi_v3_fresh_trades.csv", index=False)
        report["fresh"] = {"sessions": len(fresh_sessions), **metrics(fresh),
                           "mc": monte_carlo(fresh, fresh_sessions)}
    print("FRESH", json.dumps(report["fresh"], default=str, indent=1))

    d = report["development_v3"]
    fresh_mean = report["fresh"].get("mean_pnl") if not report["fresh"].get("not_run") else None
    dead = []
    if d["whole"]["mean_pnl"] <= 0:
        dead.append("development whole-period mean <= 0")
    if d["holdout"]["mean_pnl"] <= 0:
        dead.append("development holdout mean <= 0")
    if sum(1 for b in d["holdout_buckets"] if b["total_pnl"] >= 0) < 3:
        dead.append("fewer than 3/4 development holdout buckets >= 0")
    if fresh_mean is None or fresh_mean <= 0 or report["fresh"].get("n_trades", 0) == 0:
        dead.append("fresh-window mean <= 0 or not evaluable")
    report["verdict"] = "DEAD" if dead else "SURVIVING RESEARCH CANDIDATE (not validated)"
    report["dead_reasons"] = dead
    print("VERDICT", report["verdict"], dead)
    (OUT / "dhesi_v3_validation_2026-09-22.json").write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
