"""Differential test, step 4: per-trade comparison Heimdall production sim vs backtesting.py 0.6.6.

Raw diff  = Heimdall - bt (both in $; bt points * $2 point value, bt commission 0.25pt/side = $1 RT).
Neutralised expectation: apply Heimdall's documented fixed-tick rules to bt's raw fills:
  entry  E_h = E_bt + side*tick
  stop   X_h = X_bt - side*tick  unless gapped (open beyond stop by >= 1 tick): X_h = X_bt (= open)
  target X_h = target price      (bt fills a gapped-through target at the open)
  flatten X_h = X_bt - side*tick
Residual = Heimdall - neutralised expectation. Every residual must be exactly 0 or is a finding.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
TICK, PV, COMM = 0.25, 2.0, 1.0


def classify_bt(row) -> str:
    side = 1 if row["Size"] > 0 else -1
    x = row["ExitPrice"]
    if np.isfinite(row["SL"]) and (side * (x - row["SL"]) <= 0):
        return "stop"
    if np.isfinite(row["TP"]) and (side * (x - row["TP"]) >= 0):
        return "target"
    return "flatten"


def compare(name: str) -> dict:
    h = pd.read_csv(HERE / f"heimdall_trades_{name}.csv", parse_dates=["entry_ts", "exit_ts"])
    b = pd.read_csv(HERE / f"bt_trades_{name}.csv", parse_dates=["EntryTime", "ExitTime"])
    # bt EntryTime is the signal bar (trade_on_close => time_index = signal bar); same as Heimdall entry_ts
    m = h.merge(b, left_on="entry_ts", right_on="EntryTime", how="outer", indicator=True)
    unmatched = int((m["_merge"] != "both").sum())
    m = m[m["_merge"] == "both"].copy()
    side = m["side"].to_numpy(int)
    bt_reason = m.apply(classify_bt, axis=1)
    e_exp = m["EntryPrice"] + side * TICK
    gapped = bt_reason.eq("stop") & (side * (m["SL"] - m["ExitPrice"]) >= TICK)
    x_exp = np.where(
        bt_reason.eq("stop"),
        np.where(gapped, m["ExitPrice"], m["ExitPrice"] - side * TICK),
        np.where(bt_reason.eq("target"), m["TP"], m["ExitPrice"] - side * TICK),
    )
    pnl_exp = side * (x_exp - e_exp) * PV - COMM
    bt_pnl_usd = m["PnL"] * PV
    m["bt_reason"] = bt_reason
    m["raw_entry_diff"] = m["entry_price"] - m["EntryPrice"]
    m["raw_exit_diff"] = m["exit_price"] - m["ExitPrice"]
    m["raw_pnl_diff"] = m["pnl"] - bt_pnl_usd
    m["exit_time_match"] = m["exit_ts"] == m["ExitTime"]
    m["resid_entry"] = m["entry_price"] - e_exp
    m["resid_exit"] = m["exit_price"] - x_exp
    m["resid_pnl"] = m["pnl"] - pnl_exp
    reason_map = {"stop": "stop", "gap_stop": "stop", "target": "target", "session_flatten": "flatten"}
    m["reason_match"] = m["reason"].map(reason_map) == m["bt_reason"]
    gap_target = bt_reason.eq("target") & (side * (m["ExitPrice"] - m["TP"]) > 0)
    m["gap_target"] = gap_target
    bars = pd.read_parquet(HERE / "diff_data_rth.parquet").set_index("ts")[["high", "low"]]
    xb = bars.loc[m["exit_ts"]].to_numpy()
    both = pd.Series(np.where(side > 0, (xb[:, 0] >= m["TP"]) & (xb[:, 1] <= m["SL"]), (xb[:, 1] <= m["TP"]) & (xb[:, 0] >= m["SL"])), index=m.index)
    m["both_touched"] = both
    m.to_csv(HERE / f"diff_pertrade_{name}.csv", index=False)

    raw_breakdown = (
        m.groupby(["reason", "bt_reason"])["raw_pnl_diff"].agg(["count", "min", "max", "sum"]).reset_index().to_dict("records")
    )
    return {
        "heimdall_trades": int(len(h)),
        "bt_trades": int(len(b)),
        "unmatched": unmatched,
        "heimdall_total_pnl": round(float(h["pnl"].sum()), 4),
        "bt_total_pnl_usd": round(float(b["PnL"].sum() * PV), 4),
        "raw_total_pnl_diff": round(float(m["raw_pnl_diff"].sum()), 4),
        "raw_nonzero_pnl_diffs": int((m["raw_pnl_diff"].abs() > 1e-9).sum()),
        "raw_diff_by_reason": raw_breakdown,
        "exit_time_mismatch": int((~m["exit_time_match"]).sum()),
        "reason_mismatch": int((~m["reason_match"]).sum()),
        "gap_stop_trades": int(gapped.sum()),
        "gap_target_trades": int(gap_target.sum()),
        "exit_bar_both_levels_touched": int(both.sum()),
        "exit_bar_both_levels_touched_resolved_as_stop": int((both & bt_reason.eq("stop")).sum()),
        "residual_nonzero_entry": int((m["resid_entry"].abs() > 1e-9).sum()),
        "residual_nonzero_exit": int((m["resid_exit"].abs() > 1e-9).sum()),
        "residual_nonzero_pnl": int((m["resid_pnl"].abs() > 1e-9).sum()),
        "residual_total_pnl": round(float(m["resid_pnl"].sum()), 6),
        "residual_max_abs_pnl": round(float(m["resid_pnl"].abs().max()), 6),
    }


def main() -> None:
    specs = json.loads((HERE / "diff_specs.json").read_text(encoding="utf-8"))
    out = {"engine": "backtesting.py 0.6.6 (Python 3.12.10, pandas 3.0.6, numpy 2.5.3)", "fixtures": {}}
    for name in specs:
        out["fixtures"][name] = compare(name)
    (HERE / "diff_results.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
