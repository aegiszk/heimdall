"""Plumbing check for harness v2 on ALREADY-SEEN development data only (data/MNQ_1m.parquet, reused holdout window).
Bypasses the gates deliberately (dev data is not a validation dataset). Must reproduce the frozen v3 holdout:
20 trades, mean +$34.79, total +$695.75. Output is labelled DEV and is not evidence."""
import importlib.util, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("h", HERE / "dhesi_validation_harness.py"); H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
b = {"strategy": {"module": "core.alpha.inversion_model_v3", "class": "InversionModelV3", "kwargs": {"contract": "MNQ"}},
     "eval_window": {"start": "2025-09-11", "end": "2026-06-30"}, "tick_value": 0.5, "commission_rt_per_contract": 1.0,
     "criteria": {"min_positive_year_fraction": 0.6, "max_single_trade_share": 0.25, "fail_if_upper_below": 20.0, "min_trades_per_year_counted": 10}}
r = H.run_market(b, {"path": "data/MNQ_1m.parquet"})
t = r["trades"]
out = {"label": "DEV_PLUMBING_NOT_EVIDENCE", "n": len(t), "mean": round(float(t.pnl.mean()), 2), "total": round(float(t.pnl.sum()), 2),
       "expected": {"n": 20, "mean": 34.79, "total": 695.75}, "verdict_field_present": "ALPHA_VERDICT" in r["ALPHA"],
       "prop_present": "PROP_LUCID_SEPARATE" in r}
out["MATCH"] = (out["n"] == 20 and abs(out["total"] - 695.75) < 0.01)
Path(HERE / "dev_plumbing_check_v2.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
