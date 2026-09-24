"""Phase 3B — cross-index flow information (ES/NQ/RTY/YM), 1-minute, RTH only, descriptive strata.
Data: Sierra continuous 1m (volume roll, non-back-adjusted) with exchange-aggressor bid/ask volume (~90 days).
Target return r(t+1 .. t+h) from close of minute t+1 (one full minute of delay) to close of t+1+h, in ticks.
M0 (target own info): target returns lags 1-5, target 15m return, target flow lags 1-5.
M1 = M0 + SOURCE flow lags 1-5.  OOS: leave-one-week-out.  Controls: source flow shifted +60 min (placebo),
source flow from the previous trading day same clock minute (placebo), CONTEMPORANEOUS source flow over the
target window (positive control, deliberate leak).  Economic: target move after top/bottom-decile source flow
residual (fixed decile, not optimized) vs friction (1 tick each side + commission)."""
import json, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path("../../data/sierra")
TICK = {"ES": 0.25, "NQ": 0.25, "RTY": 0.10, "YM": 1.0}
TICK_USD = {"ES": 12.5, "NQ": 5.0, "RTY": 5.0, "YM": 5.0}
COMM_RT = {"ES": 3.5, "NQ": 3.5, "RTY": 3.5, "YM": 3.5}   # mini RT commission [confirmed for ES/NQ only; RTY/YM assumed same]
D = {}
for s in TICK:
    d = pd.read_parquet(ROOT / f"{s}_continuous_1m_latest_90d.parquet")
    d.index = pd.to_datetime(d.index, utc=True).tz_convert("America/New_York")
    D[s] = d
idx = D["ES"].index
for s in TICK: idx = idx.intersection(D[s].index)
t = idx[(idx.time >= pd.Timestamp("09:30").time()) & (idx.time < pd.Timestamp("16:00").time())]
def stratum(ts):
    m = ts.hour * 60 + ts.minute
    return np.where(m < 630, "open_0930_1030", np.where((m >= 690) & (m < 840), "midday_1130_1400", np.where(m >= 900, "final_1500_1600", "other")))
out = {}
for tgt in TICK:
    for src in TICK:
        if src == tgt: continue
        T, S = D[tgt].loc[t], D[src].loc[t]
        f = pd.DataFrame(index=t)
        rt = T.close.diff() / TICK[tgt]; ft = T.ask_volume - T.bid_volume; fs = S.ask_volume - S.bid_volume
        day = f.index.date
        g = lambda x, k: x.groupby(day).shift(k)                       # never lag across sessions
        for k in range(5):
            f[f"rt{k}"] = g(rt, k); f[f"ft{k}"] = g(ft, k) / 1e3; f[f"fs{k}"] = g(fs, k) / 1e3
            f[f"pl{k}"] = g(fs, k + 60) / 1e3                           # placebo: source flow 60 min earlier
        prev = fs.copy(); prev.index = [ts - pd.Timedelta(days=1) for ts in prev.index]   # same clock, previous day
        pday = fs.groupby(fs.index.time).shift(1) / 1e3
        for k in range(5): f[f"pd{k}"] = pday.groupby(day).shift(k)
        f["rt15"] = rt.groupby(day).transform(lambda x: x.rolling(15).sum())
        out_pair = {}
        for h in (1, 5):
            c = T.close
            y = (c.groupby(day).shift(-(1 + h)) - c.groupby(day).shift(-1)) / TICK[tgt]
            leak = fs.groupby(day).transform(lambda x: x.shift(-2).rolling(h).sum().shift(-(h - 1))) / 1e3  # minutes t+2..t+1+h
            F = f.assign(y=y, leak=leak, wk=[x.isocalendar()[1] for x in f.index], st=stratum(f.index)).dropna()
            M0 = [f"rt{k}" for k in range(5)] + [f"ft{k}" for k in range(5)] + ["rt15"]
            def oos(cols):
                num = den = 0.0; pred = pd.Series(index=F.index, dtype=float)
                for w in F.wk.unique():
                    tr, te = F[F.wk != w], F[F.wk == w]
                    A = np.column_stack([tr[cols], np.ones(len(tr))]); b, *_ = np.linalg.lstsq(A, tr.y, rcond=None)
                    p = np.column_stack([te[cols], np.ones(len(te))]) @ b; pred.loc[te.index] = p
                    num += ((te.y - p) ** 2).sum(); den += ((te.y - tr.y.mean()) ** 2).sum()
                return 1 - num / den, pred
            r0, p0 = oos(M0); r1, p1 = oos(M0 + [f"fs{k}" for k in range(5)])
            rpl, _ = oos(M0 + [f"pl{k}" for k in range(5)]); rpd, _ = oos(M0 + [f"pd{k}" for k in range(5)]); rlk, _ = oos(M0 + ["leak"])
            sig = p1 - p0                                                 # incremental OOS prediction from source flow
            lo, hi = sig.quantile(0.10), sig.quantile(0.90)
            sel = F[(sig <= lo) | (sig >= hi)]; direction = np.sign(sig.loc[sel.index])
            move = direction * sel.y
            fr_ticks = 2 + COMM_RT[tgt] / TICK_USD[tgt]
            strata = {s: {"dR2_pp": None} for s in ("open_0930_1030", "midday_1130_1400", "final_1500_1600")}
            for s in strata:
                m = F.st == s
                if m.sum() > 200:
                    yy = F.y[m]; strata[s] = {"n": int(m.sum()),
                        "dR2_pp": round(100 * (((yy - p0[m]) ** 2).sum() - ((yy - p1[m]) ** 2).sum()) / ((yy - yy.mean()) ** 2).sum(), 3)}
            out_pair[f"h{h}"] = {"n": int(len(F)), "R2_M0_pp": round(100 * r0, 3), "dR2_source_flow_pp": round(100 * (r1 - r0), 3),
                "dR2_placebo_60m_pp": round(100 * (rpl - r0), 3), "dR2_placebo_prevday_pp": round(100 * (rpd - r0), 3),
                "dR2_POSITIVE_CONTROL_leak_pp": round(100 * (rlk - r0), 3),
                "decile_move_ticks_mean": round(float(move.mean()), 3), "decile_move_t": round(float(move.mean() / (move.std(ddof=1) / np.sqrt(len(move)))), 2),
                "decile_n": int(len(move)), "friction_ticks": round(fr_ticks, 2), "move_over_friction": round(float(move.mean() / fr_ticks), 3),
                "strata": strata}
        out[f"{src}->{tgt}"] = out_pair
        print(src, "->", tgt, {h: {k: v for k, v in x.items() if k != "strata"} for h, x in out_pair.items()}, flush=True)
json.dump(out, open("cross_index_flow.json", "w"), indent=1, default=float)
