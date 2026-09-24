"""Power diagnostics for the H2 aggregate test: (1) raw contemporaneous corr(HL flow, NQ return) per window;
(2) LEAN baseline (rn1, rn15, basis15, vol30) with/without lagged flow and with FUTURE flow (positive control)."""
import json, numpy as np, pandas as pd
from pathlib import Path
src = Path(__file__).with_name("h2_aggregate_flow_control.py").read_text()
ns = {"__file__": str(Path(__file__).with_name("h2_aggregate_flow_control.py"))}
exec(src.split("out = {}")[0], ns)
LEAN = ["rn1", "rn15", "basis15", "vol30"]; LAGF = ["fl1", "fl15"]
out = {}
for sym in ("xyz:XYZ100", "xyz:SP500"):
    for h in (1, 5, 15):
        frames = []
        corr_rows = []
        for d in ns["DAYS"]:
            X, ys = ns["build"](d, sym)
            X[f"y{h}"] = ys[h]
            X["fut_flow"] = X["fl1"].shift(-2).rolling(h).sum().shift(-(h - 1))  # minutes t+2..t+1+h = target window
            Z = X.dropna(); frames.append((d, Z))
            corr_rows.append(np.corrcoef(Z.fut_flow, Z[f"y{h}"])[0, 1])
        r = {"contemp_corr_flow_vs_NQret_by_day": [round(c, 3) for c in corr_rows],
             "R2_lean": round(ns["loo_r2"](frames, LEAN, h), 4),
             "R2_lean_plus_lagged_flow": round(ns["loo_r2"](frames, LEAN + LAGF, h), 4),
             "R2_lean_plus_FUTURE_flow(pos.control)": round(ns["loo_r2"](frames, LEAN + ["fut_flow"], h), 4)}
        out[f"{sym}|h{h}"] = r; print(sym, h, r)
Path(__file__).with_name("h2_power_check.json").write_text(json.dumps(out, indent=1))
