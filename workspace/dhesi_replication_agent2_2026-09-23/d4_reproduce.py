"""Agent 2 independent D4 reproduction from the v2 trade LOG (not the strategy module).
Classifies each v2 trade: wrong-side stop (side*(entry-stop) <= 0), tiny correct-side stop (0 < side*(entry-stop) < 10 pts),
or valid. Then computes v2 totals with each category removed (no knock-on re-entries: a log cannot generate those)."""
import json, numpy as np, pandas as pd
from pathlib import Path
t = pd.read_csv("data/prop_futures/inversion_model_MNQ_1m_trades.csv")
s = np.where(t.side.astype(str).str.lower().isin(["1", "long", "buy", "1.0"]), 1, -1) if t.side.dtype == object else np.sign(t.side)
dist = s * (t.entry_price - t.stop_price)                         # protective distance in points (>0 = correct side)
t["protective_pts"] = dist
t["class"] = np.where(dist <= 0, "WRONG_SIDE", np.where(dist < 10.0, "TINY_<10pt", "VALID"))
out = {"n": int(len(t)), "total_pnl_v2": round(float(t.pnl.sum()), 2),
       "counts": t["class"].value_counts().to_dict(),
       "pnl_by_class": t.groupby("class").pnl.agg(["sum", "count", "mean"]).round(2).to_dict("index"),
       "total_if_wrong_side_removed": round(float(t[t["class"] != "WRONG_SIDE"].pnl.sum()), 2),
       "total_if_wrong_and_tiny_removed": round(float(t[t["class"] == "VALID"].pnl.sum()), 2)}
cols = ["entry_ts", "side", "entry_price", "stop_price", "protective_pts", "contracts", "reason", "pnl", "class"]
out["flagged_trades"] = t[t["class"] != "VALID"][cols].to_dict("records")
Path("workspace/dhesi_replication_agent2_2026-09-23/d4_reproduce.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps({k: v for k, v in out.items() if k != "flagged_trades"}, indent=1, default=str))
print(t[t["class"] != "VALID"][cols].to_string(index=False))
