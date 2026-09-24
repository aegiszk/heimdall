"""H2 falsification control (zero cost, dev-period diagnostics only): does AGGREGATE HL signed taker flow in
xyz:XYZ100 / xyz:SP500 add out-of-sample information about FUTURE NQ minute returns beyond M0?
M0: NQ returns (lags 1-5, cum 15m), HL returns (lags 1-5), basis change (HL cum15 - NQ cum15),
    30m realized vol, UTC-hour dummies.   M1 = M0 + signed flow (lags 1-5, cum 15m).  Flow-only = flow + const.
Target: NQ log return from end of minute t+1 to end of t+1+h (one full minute of delay), h in {1,5,15}.
Leave-one-day-out OOS R^2, pooled over 5 free days. Also time-shift placebo (flow lagged +/- 60 min) and sign-flip.
"""
import json, numpy as np, pandas as pd
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location("z", Path(__file__).with_name("h2_zero_cost_leadlag.py"))
ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "tardis_free" / "hyperliquid" / "trades"
DAYS = ["2026-04-01", "2026-05-01", "2026-06-01", "2026-07-01", "2026-09-01"]
M = 60_000_000

def nq_min(day):
    c = "NQM26" if day < "2026-06-16" else "NQU26"
    d = pd.read_parquet(ROOT / "data" / "sierra" / "tick" / f"{c}_CME_1tick_full.parquet", columns=["ts", "close"])
    t = d.ts.astype("int64"); lo = pd.Timestamp(day, tz="UTC").value // 1000
    m = (t >= lo) & (t < lo + 86_400_000_000)
    return pd.Series(d.close[m].to_numpy(), index=(t[m] // M).to_numpy()).groupby(level=0).last()

def hl_min(day, sym):
    d = pd.read_csv(CACHE / day / f"{sym.replace(':', '_')}.csv.gz", usecols=["timestamp", "side", "price", "amount"])
    k = d.timestamp // M; sgn = np.where(d.side == "buy", 1.0, -1.0)
    px = d.groupby(k).price.last(); flow = pd.Series(sgn * d.price * d.amount).groupby(k).sum()
    return px, flow

def build(day, sym, flow_shift=0):
    nq = nq_min(day); px, flow = hl_min(day, sym)
    idx = np.arange(max(nq.index.min(), px.index.min()), min(nq.index.max(), px.index.max()) + 1)
    f = pd.DataFrame({"nq": nq.reindex(idx).ffill(), "hl": px.reindex(idx).ffill(),
                      "flow": flow.reindex(idx).fillna(0.0)}, index=idx).dropna()
    f = f[((f.index // 60) % 24) != 21]  # CME halt hour
    if flow_shift: f["flow"] = f.flow.shift(flow_shift)
    f["flow"] = f.flow / (f.flow.abs().rolling(120, min_periods=30).mean() + 1e-9)
    rn, rh = np.log(f.nq).diff(), np.log(f.hl).diff()
    X = pd.DataFrame(index=f.index)
    for k in range(1, 6):
        X[f"rn{k}"] = rn.shift(k - 1); X[f"rh{k}"] = rh.shift(k - 1); X[f"fl{k}"] = f.flow.shift(k - 1)
    X["rn15"] = rn.rolling(15).sum(); X["basis15"] = rh.rolling(15).sum() - X.rn15
    X["fl15"] = f.flow.rolling(15).sum(); X["vol30"] = rn.abs().rolling(30).mean()
    for h in range(24): X[f"h{h}"] = (((f.index // 60) % 24) == h).astype(float)
    ys = {hh: np.log(f.nq).shift(-(1 + hh)) - np.log(f.nq).shift(-1) for hh in (1, 5, 15)}
    X["day"] = day
    return X, ys

M0 = [f"{p}{k}" for p in ("rn", "rh") for k in range(1, 6)] + ["rn15", "basis15", "vol30"] + [f"h{h}" for h in range(24)]
FL = [f"fl{k}" for k in range(1, 6)] + ["fl15"]

def loo_r2(frames, cols, h):
    num = den = 0.0
    for d in DAYS:
        tr = pd.concat([fr for dd, fr in frames if dd != d]); te = [fr for dd, fr in frames if dd == d][0]
        A = np.column_stack([tr[cols].to_numpy(), np.ones(len(tr))]); beta, *_ = np.linalg.lstsq(A, tr[f"y{h}"].to_numpy(), rcond=None)
        B = np.column_stack([te[cols].to_numpy(), np.ones(len(te))]); e = te[f"y{h}"].to_numpy() - B @ beta
        num += (e ** 2).sum(); den += ((te[f"y{h}"] - tr[f"y{h}"].mean()) ** 2).sum()
    return 1 - num / den

out = {}
for sym in ("xyz:XYZ100", "xyz:SP500"):
    for tag, shift, sign in (("actual", 0, 1), ("placebo_flow_lagged_60m", 60, 1), ("placebo_flow_lead_60m_LEAKAGE_CHECK", -60, 1), ("sign_flipped", 0, -1)):
        frames = []
        for d in DAYS:
            X, ys = build(d, sym, shift)
            X[FL] = X[FL] * sign
            for hh, y in ys.items(): X[f"y{hh}"] = y
            frames.append((d, X.dropna()))
        r = {}
        for h in (1, 5, 15):
            r0, r1, rf = loo_r2(frames, M0, h), loo_r2(frames, M0 + FL, h), loo_r2(frames, FL, h)
            r[f"h{h}"] = {"R2_M0": round(r0, 5), "R2_M1": round(r1, 5), "dR2_flow_over_M0": round(r1 - r0, 5), "R2_flow_only": round(rf, 5)}
        out[f"{sym}|{tag}"] = {"n_minutes": int(sum(len(f) for _, f in frames)), **r}
        print(sym, tag, out[f"{sym}|{tag}"])
Path(__file__).with_name("h2_aggregate_flow_control.json").write_text(json.dumps(out, indent=1))
