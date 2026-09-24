"""Generate the stop_guard-only ablation trade list on DEVELOPMENT data (data/MNQ_1m.parquet, already seen; not
validation) and diff it against the v2 log by entry timestamp. Only reads outputs; changes no shared file."""
import json, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, ".")
from core.alpha.inversion_model_v3 import InversionModelV3
dev = pd.read_parquet("data/MNQ_1m.parquet")
m = InversionModelV3(contract="MNQ", htf_24h=False, early_sweeps=False, session_pools=False, stop_guard=True, attempts=False)
res = m._run_backtest(dev) if hasattr(m, "_run_backtest") else None
tr = pd.DataFrame(res.trades) if hasattr(res, "trades") else None
if tr is None or tr.empty:
    print("could not extract trades:", type(res), [a for a in dir(res) if not a.startswith("_")][:20]); sys.exit(1)
v2 = pd.read_csv("data/prop_futures/inversion_model_MNQ_1m_trades.csv")
a = set(v2.entry_ts.astype(str)); b = set(pd.to_datetime(tr.entry_ts).astype(str) if "entry_ts" in tr else [])
tr["entry_ts"] = tr["entry_ts"].astype(str)
common = sorted(a & b); only_v2 = sorted(a - b); only_guard = sorted(b - a)
out = {"guard_trades": int(len(tr)), "guard_total": round(float(tr.pnl.sum()), 2), "v2_trades": int(len(v2)),
       "common": len(common), "removed_from_v2": only_v2, "new_in_guard": only_guard,
       "pnl_common_in_guard": round(float(tr[tr.entry_ts.isin(common)].pnl.sum()), 2),
       "pnl_common_in_v2": round(float(v2[v2.entry_ts.astype(str).isin(common)].pnl.sum()), 2),
       "pnl_new_in_guard": round(float(tr[tr.entry_ts.isin(only_guard)].pnl.sum()), 2),
       "pnl_removed_v2": round(float(v2[v2.entry_ts.astype(str).isin(only_v2)].pnl.sum()), 2),
       "new_trades_detail": tr[tr.entry_ts.isin(only_guard)][["entry_ts", "side", "entry_price", "stop_price", "reason", "pnl"]].to_dict("records")}
Path("workspace/dhesi_replication_agent2_2026-09-23/d4_knockon.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps({k: v for k, v in out.items() if k != "new_trades_detail"}, indent=1, default=str))
print(pd.DataFrame(out["new_trades_detail"]).to_string(index=False))
