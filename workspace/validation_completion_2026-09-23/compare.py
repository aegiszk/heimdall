"""Per-trade differential: Heimdall shared RTH simulator vs backtesting.py.

1) zero_slip Heimdall vs backtesting.py (matched semantics). Every nonzero diff must be explained
   by a documented semantic difference (TP gapped through -> backtesting.py fills at open).
2) base (production, 1-tick slippage) Heimdall vs backtesting.py: every diff must equal the
   analytic slippage tax: entry 1 tick adverse; stop/session_flatten exit 1 tick adverse;
   gap_stop exit = min/max(open, stop -/+ tick) vs open; target 0; + any TP-gap explanation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PV, TICK, EPS = 2.0, 0.25, 1e-9
bars = pd.read_parquet(HERE / "bars.parquet").set_index("ts_et")
H = json.loads((HERE / "heimdall_trades.json").read_text())
X = json.loads((HERE / "ext_trades.json").read_text())


def explain_zero(h, x):
    """Return (explained: bool, label)."""
    if h["reason"] == "target":
        o = float(bars.loc[pd.Timestamp(h["exit_ts"]), "open"])
        gapped = (o >= h["target"]) if h["side"] > 0 else (o <= h["target"])
        if gapped and abs(x["exit"] - o) < EPS:
            return True, "tp_gap_open_fill"
    return False, "UNEXPLAINED"


rows, summary = [], {}
for name in X["results"]:
    xs = {t["entry_ts"]: t for t in X["results"][name]}
    for mode in ("zero_slip", "base"):
        hs = {t["entry_ts"]: t for t in H[mode][name]}
        only_h = sorted(set(hs) - set(xs)); only_x = sorted(set(xs) - set(hs))
        n_diff = unexplained = 0
        labels: dict[str, int] = {}
        tot_h = sum(t["pnl"] for t in hs.values()); tot_x = sum(t["pnl"] for t in xs.values())
        for k in sorted(set(hs) & set(xs)):
            h, x = hs[k], xs[k]
            d_exit_ts = h["exit_ts"] != x["exit_ts"]
            d_entry = h["entry"] - x["entry"]; d_exit = h["exit"] - x["exit"]; d_pnl = h["pnl"] - x["pnl"]
            if mode == "zero_slip":
                nz = d_exit_ts or abs(d_entry) > EPS or abs(d_exit) > EPS or abs(d_pnl) > EPS
                ok, lab = (True, "exact") if not nz else explain_zero(h, x)
                if d_exit_ts:
                    ok, lab = False, "EXIT_BAR_MISMATCH"
            else:
                # predicted production tax relative to the zero-slip Heimdall trade
                z = {t["entry_ts"]: t for t in H["zero_slip"][name]}[k]
                s = h["side"]
                pred_entry = z["entry"] + s * TICK
                if h["reason"] in ("stop", "session_flatten"):
                    pred_exit = z["exit"] - s * TICK
                elif h["reason"] == "gap_stop":
                    o = float(bars.loc[pd.Timestamp(h["exit_ts"]), "open"])
                    pred_exit = min(o, h["stop"] - TICK) if s > 0 else max(o, h["stop"] + TICK)
                else:
                    pred_exit = z["exit"]
                pred_pnl = s * (pred_exit - pred_entry) * PV - 1.0
                ok = (not d_exit_ts and z["reason"] == h["reason"] and abs(h["entry"] - pred_entry) < EPS
                      and abs(h["exit"] - pred_exit) < EPS and abs(h["pnl"] - pred_pnl) < EPS)
                nz = abs(d_pnl) > EPS or d_exit_ts
                lab = f"slippage_tax_{h['reason']}" if ok else "UNEXPLAINED"
            if nz:
                n_diff += 1
            if not ok:
                unexplained += 1
            labels[lab] = labels.get(lab, 0) + 1
            rows.append({"fixture": name, "mode": mode, "entry_ts": k, "side": h["side"], "reason": h["reason"],
                         "h_entry": h["entry"], "x_entry": x["entry"], "h_exit": h["exit"], "x_exit": x["exit"],
                         "h_exit_ts": h["exit_ts"], "x_exit_ts": x["exit_ts"], "h_pnl": h["pnl"], "x_pnl": x["pnl"],
                         "d_pnl": d_pnl, "label": lab})
        summary[f"{name}|{mode}"] = {"n_heimdall": len(hs), "n_ext": len(xs), "only_heimdall": only_h,
                                     "only_ext": only_x, "n_nonzero_diff": n_diff, "unexplained": unexplained,
                                     "labels": labels, "total_pnl_heimdall": round(tot_h, 4),
                                     "total_pnl_ext": round(tot_x, 4), "total_diff": round(tot_h - tot_x, 4)}

pd.DataFrame(rows).to_csv(HERE / "diff_per_trade.csv", index=False)
(HERE / "diff_summary.json").write_text(json.dumps({"engine": X["engine"], "summary": summary}, indent=1))
for k, v in summary.items():
    print(k, {kk: v[kk] for kk in ("n_heimdall", "n_ext", "n_nonzero_diff", "unexplained", "labels",
                                    "total_pnl_heimdall", "total_pnl_ext", "total_diff")},
          "only_h" if v["only_heimdall"] else "", v["only_heimdall"][:3], v["only_ext"][:3])
