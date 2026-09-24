"""Phase 3A — CL response around EIA Weekly Petroleum Status Report releases (1-minute resolution ONLY).
Owned data: Sierra per-contract CL 1m records (bid/ask volume from CME aggressor), front = max-volume contract per day.
Events: official EIA schedule (Wed 10:30 ET; 2026-05-28 and 2026-09-10 Thu 12:00 ET). No thresholds, no entries optimized.
Placebo: same clock time (10:30 ET) on non-release weekdays in the same period.
Sub-minute windows (0-5s, 5-15s, 15-30s, 30-60s) are NOT computable from 1m bars -> INSUFFICIENT DATA."""
import json, numpy as np, pandas as pd
from scid_io import read_scid, front_by_day
TICK = 0.01
front, _ = front_by_day("C:/SierraChart/Data/CL[A-Z][0-9][0-9]-NYMEX.scid")
cache = {}
def bars(f):
    if f not in cache: cache[f] = read_scid("C:/SierraChart/Data/" + f)
    return cache[f]
SHIFTED = {"2026-05-27": ("2026-05-28", "12:00"), "2026-09-09": ("2026-09-10", "12:00")}
days = pd.date_range("2026-04-06", "2026-09-18", freq="B")
events, placebo = [], []
for d in days:
    ds = str(d.date())
    if d.weekday() == 2:
        ev_day, hhmm = SHIFTED.get(ds, (ds, "10:30")); events.append((ev_day, hhmm))
    elif ds not in {v[0] for v in SHIFTED.values()}:
        placebo.append((ds, "10:30"))
def measure(day, hhmm):
    t0 = pd.Timestamp(f"{day} {hhmm}", tz="America/New_York").tz_convert("UTC")
    f = front.get(pd.Timestamp(day).date())
    if f is None: return None
    b = bars(f); w = b[(b.index >= t0 - pd.Timedelta(minutes=60)) & (b.index < t0 + pd.Timedelta(minutes=15))]
    pre = w[w.index < t0]; post = w[w.index >= t0]
    if len(pre) < 50 or len(post) < 15 or pre.v.sum() == 0: return None
    p0 = pre.c.iloc[-1]; base_vpm = pre.v.tail(30).median() or 1
    def win(a, bnd):
        x = post.iloc[a:bnd]
        return dict(disp_t=round((x.c.iloc[-1] - (p0 if a == 0 else post.c.iloc[a - 1])) / TICK, 1),
                    flow=int((x.av - x.bv).sum()), intensity=round(x.v.mean() / base_vpm, 2))
    r = {"day": day, "t": hhmm, "contract": f, "pre10_flow": int((pre.av - pre.bv).tail(10).sum()),
         "pre10_disp_t": round((pre.c.iloc[-1] - pre.c.iloc[-11]) / TICK, 1)}
    for name, (a, bnd) in {"m0_1": (0, 1), "m1_2": (1, 2), "m2_5": (2, 5), "m5_15": (5, 15)}.items():
        for k, v in win(a, bnd).items(): r[f"{name}_{k}"] = v
    s = np.sign(r["m0_1_disp_t"]) or 1.0
    r["cont_1_5_t"] = round(s * (post.c.iloc[4] - post.c.iloc[0]) / TICK, 1)      # after first minute, in its direction
    r["cont_1_15_t"] = round(s * (post.c.iloc[14] - post.c.iloc[0]) / TICK, 1)
    nxt = post.iloc[1:5]                                                           # entry at close of minute 1
    r["mae_1_5_t"] = round(((post.c.iloc[0] - nxt.l.min()) if s > 0 else (nxt.h.max() - post.c.iloc[0])) / TICK, 1)
    r["eff_t_per_100"] = round(100 * r["m0_1_disp_t"] / r["m0_1_flow"], 2) if r["m0_1_flow"] else None
    return r
E = pd.DataFrame([x for x in (measure(*e) for e in events) if x]); P = pd.DataFrame([x for x in (measure(*p) for p in placebo) if x])
def summ(D):
    out = {"n": int(len(D))}
    for c in ["m0_1_disp_t", "m1_2_disp_t", "m2_5_disp_t", "m5_15_disp_t", "cont_1_5_t", "cont_1_15_t", "mae_1_5_t"]:
        x = D[c]; out[c] = {"mean": round(x.mean(), 2), "median": round(x.median(), 2), "mean_abs": round(x.abs().mean(), 2),
                            "t": round(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))), 2) if len(x) > 2 else None}
    out["m0_1_intensity_median"] = round(D.m0_1_intensity.median(), 2)
    out["corr_flow_disp_m0_1"] = round(float(np.corrcoef(D.m0_1_flow, D.m0_1_disp_t)[0, 1]), 3)
    out["share_continuation_1_5"] = round(float((D.cont_1_5_t > 0).mean()), 3)
    out["corr_first_min_vs_next_4"] = round(float(np.corrcoef(D.m0_1_disp_t, D.m0_1_disp_t.apply(np.sign) * D.cont_1_5_t)[0, 1]), 3)
    return out
res = {"events": summ(E), "placebo_same_clock_non_release_days": summ(P)}
E.to_csv("eia_cl_events.csv", index=False); P.to_csv("eia_cl_placebo.csv", index=False)
json.dump(res, open("eia_cl_response.json", "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))
