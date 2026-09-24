"""H2 zero-cost aggregate test (NO wallet identity, NO final-period data):
Does HL xyz:XYZ100 / xyz:SP500 price lead or follow CME NQ?  Free Tardis first-of-month HL trades
(event time = block time) vs Sierra NQ one-tick trades (Sierra timestamp; exchange-time semantics [U]).
Days: CME weekdays inside the Sierra tick archive: 2026-04-01, 05-01, 06-01, 07-01, 09-01.
Excludes 21:00-22:00 UTC (CME daily halt). Positive lag => NQ leads HL.
"""
import json, urllib.request, urllib.error, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "tardis_free" / "hyperliquid" / "trades"
DAYS = ["2026-04-01", "2026-05-01", "2026-06-01", "2026-07-01", "2026-09-01"]
THETAS = np.arange(-5000, 10001, 100)

def hl_trades(day, sym):
    p = CACHE / day / f"{sym.replace(':', '_')}.csv.gz"
    if not p.exists():
        y, m, d = day.split("-"); p.parent.mkdir(parents=True, exist_ok=True)
        try: urllib.request.urlretrieve(f"https://datasets.tardis.dev/v1/hyperliquid/trades/{y}/{m}/{d}/{sym}.csv.gz", p)
        except urllib.error.HTTPError: return None
    return pd.read_csv(p, usecols=["timestamp", "local_timestamp", "price"])

_nq = {}
def nq_trades(day):
    contract = "NQM26" if day < "2026-06-16" else ("NQU26" if day < "2026-09-15" else "NQZ26")
    if contract not in _nq:
        _nq[contract] = pd.read_parquet(ROOT / "data" / "sierra" / "tick" / f"{contract}_CME_1tick_full.parquet", columns=["ts", "close"])
    d = _nq[contract]; t = pd.to_datetime(d.ts, utc=True)
    lo = pd.Timestamp(day, tz="UTC"); m = (t >= lo) & (t < lo + pd.Timedelta(days=1))
    return pd.DataFrame({"timestamp": t[m].astype("int64").to_numpy(), "price": d.close[m].to_numpy()}), contract

def keep_hours(df, col="timestamp"):
    h = (df[col] // 3_600_000_000) % 24
    return df[h != 21]

def tick_ret(df, col="timestamp"):
    d = df.sort_values(col, kind="stable"); t, p = d[col].to_numpy(np.int64), d.price.to_numpy(float)
    k = np.r_[True, p[1:] != p[:-1]]; t, p = t[k], p[k]
    return t[:-1], t[1:], np.diff(np.log(p))

def hy(a, b):  # a = leader candidate (NQ), b = HL; theta>0 => a leads
    sa, ea, ra = a; sb, eb, rb = b; cs = np.r_[0.0, np.cumsum(rb)]; den = np.sqrt((ra**2).sum() * (rb**2).sum()); out = {}
    for th in THETAS:
        lo = np.searchsorted(eb, sa + th * 1000, "right"); hi = np.maximum(np.searchsorted(sb, ea + th * 1000, "left"), lo)
        out[int(th)] = float((ra * (cs[hi] - cs[lo])).sum() / den)
    return out

def grid(df, col, step=1_000_000):
    return df.groupby(df[col] // step).price.last()

def granger(x_lead, y, lags=30):
    """OOS R^2 of y_t on x_{t-1..t-lags} (fit first half, test second half)."""
    X = np.column_stack([np.roll(x_lead, k) for k in range(1, lags + 1)])[lags:]; Y = y[lags:]
    n = len(Y) // 2; beta, *_ = np.linalg.lstsq(X[:n], Y[:n], rcond=None)
    e = Y[n:] - X[n:] @ beta; return float(1 - (e**2).sum() / ((Y[n:] - Y[:n].mean())**2).sum())

res = {}
for day in DAYS:
    nq, contract = nq_trades(day); nq = keep_hours(nq)
    for sym in ("xyz:XYZ100", "xyz:SP500"):
        hl = hl_trades(day, sym)
        if hl is None or len(hl) < 1000: res[f"{day}|{sym}"] = {"status": "unavailable"}; continue
        hl = keep_hours(hl)
        c = hy(tick_ret(nq), tick_ret(hl)); best = max(c, key=c.get)
        cr = hy(tick_ret(nq), tick_ret(hl.assign(timestamp=hl.local_timestamp)))  # HL on receive time
        bestr = max(cr, key=cr.get)
        G1 = grid(nq, "timestamp"); G2 = grid(hl, "timestamp")
        idx = np.arange(max(G1.index.min(), G2.index.min()), min(G1.index.max(), G2.index.max()) + 1)
        M = pd.DataFrame({"nq": G1.reindex(idx).ffill(), "hl": G2.reindex(idx).ffill()}).dropna()
        rn, rh = np.diff(np.log(M.nq.values)), np.diff(np.log(M.hl.values))
        res[f"{day}|{sym}"] = {"status": "ok", "nq_contract": contract, "hl_price_changes": int(len(tick_ret(hl)[2])),
            "nq_price_changes": int(len(tick_ret(nq)[2])), "hy_best_lag_ms": best, "hy_rho_best": round(c[best], 4),
            "hy_rho_0": round(c[0], 4), "hy_mass_nq_leads": round(sum(v for k, v in c.items() if k > 0), 3),
            "hy_mass_hl_leads": round(sum(v for k, v in c.items() if k < 0), 3),
            "hy_best_lag_ms_hl_receive_time": bestr,
            "oos_R2_hl_on_lagged_nq_1s": round(granger(rn, rh), 4), "oos_R2_nq_on_lagged_hl_1s": round(granger(rh, rn), 4),
            "curve_hy": {k: round(v, 4) for k, v in c.items() if k % 500 == 0}}
        r = res[f"{day}|{sym}"]
        print(day, sym, contract, "HY best", r["hy_best_lag_ms"], r["hy_rho_best"], "| mass NQ->HL", r["hy_mass_nq_leads"],
              "HL->NQ", r["hy_mass_hl_leads"], "| R2 HL|NQ", r["oos_R2_hl_on_lagged_nq_1s"], "R2 NQ|HL", r["oos_R2_nq_on_lagged_hl_1s"],
              "| HL recv-time best", bestr)
Path(__file__).with_name("h2_zero_cost_leadlag.json").write_text(json.dumps(res, indent=1))
