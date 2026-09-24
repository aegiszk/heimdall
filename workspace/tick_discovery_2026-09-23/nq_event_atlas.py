"""NQ EVENT-TIME ATLAS (discovery on DEVELOPMENT data only; never to be reported as OOS).

Data: Sierra one-tick NQ records (1 trade/record, aggressor from bid/ask volume), continuous by prior-session volume
roll NQM26 -> NQU26 on 2026-06-16 -> NQZ26 on 2026-09-15 (data/sierra/MANIFEST.md).
Timestamps: 1 ms true resolution (Sierra adds 1 us increments for uniqueness) [I]; exchange-vs-Sierra semantics UNVERIFIED.
Price reference: AGGRESSOR-ADJUSTED MID = trade px - side * 0.5 tick (exact when the spread is 1 tick; NQ's normal state).
Markouts = direction * (mid(t+h) - mid(t)) in ticks (0.25 pt). "Tradable" markouts x_h start at mid(t+250 ms).
All families/thresholds are pre-declared below and ALL are reported. Events are causal (use data <= t).
Thresholds that are percentiles are calibrated on the FIRST 20 trading days only and then frozen.
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2] / "data" / "sierra" / "tick"
TICK = 0.25
H_MS = [50, 100, 250, 500, 1000, 2000, 5000, 10000, 30000, 60000]
LAT_MS = 250
FRICTION_TICKS = {"NQ": 2.7, "MNQ": 4.0}   # half-spread in + out (1 tick) + 1 adverse tick + commission
ROLLS = [("NQM26", None, "2026-06-16"), ("NQU26", "2026-06-16", "2026-09-15"), ("NQZ26", "2026-09-15", None)]


def load_contract(c, lo, hi):
    t = pq.read_table(ROOT / f"{c}_CME_1tick_full.parquet", columns=["ts", "close", "volume", "bid_volume", "ask_volume"]).to_pandas()
    ts = t.ts.astype("int64").to_numpy()
    et = pd.to_datetime(ts, unit="us", utc=True).tz_convert("America/New_York")
    tday = pd.Series((et + pd.Timedelta(hours=6)).date)          # CME trading day (18:00 ET start)
    m = np.ones(len(t), bool)
    if lo:
        m &= (tday >= pd.Timestamp(lo).date()).to_numpy()
    if hi:
        m &= (tday < pd.Timestamp(hi).date()).to_numpy()
    side = np.where(t.ask_volume.to_numpy() > 0, 1, -1).astype(np.int8)
    return pd.DataFrame({"us": ts[m], "px": t.close.to_numpy()[m].astype(np.float64), "v": t.volume.to_numpy()[m].astype(np.int64),
                         "s": side[m], "tday": tday.to_numpy()[m], "mins": (et.hour * 60 + et.minute).to_numpy()[m]})


def stratum(mins):
    return np.where((mins >= 570) & (mins < 630), "rth_open", np.where((mins >= 630) & (mins < 900), "rth_mid",
                    np.where((mins >= 900) & (mins < 960), "rth_close", "eth")))


class RMQ:
    """Sparse table for range max/min over inclusive index ranges."""

    def __init__(self, a, fn):
        self.fn = fn
        self.t = [a.copy()]
        k = 1
        while (1 << k) <= len(a):
            p = self.t[-1]
            self.t.append(fn(p[:-(1 << (k - 1))], p[(1 << (k - 1)):]))
            k += 1

    def q(self, lo, hi):
        k = np.floor(np.log2(np.maximum(hi - lo + 1, 1))).astype(int)
        out = np.empty(len(lo))
        for kk in np.unique(k):
            m = k == kk
            tab = self.t[kk]
            out[m] = self.fn(tab[lo[m]], tab[hi[m] - (1 << kk) + 1])
        return out


def day_arrays(d):
    us, px, v, s = d.us.to_numpy(), d.px.to_numpy(), d.v.to_numpy(), d.s.to_numpy()
    # AGGRESSOR-ADJUSTED MID: buyer-initiated prints at the ask, seller-initiated at the bid; NQ spread is ~always
    # 1 tick, so mid = px - side * 0.5 tick. No staleness (the earlier last-buy/last-sell proxy lagged by up to 5 s
    # and manufactured +1 to +2.4 tick markouts even for random trades -> INVALIDATED, see *_STALE_MIDPROXY_INVALID).
    mid = px - s * 0.5 * TICK
    sv = (s * v).astype(np.float64)
    csv = np.r_[0.0, np.cumsum(sv)]
    cnt = np.arange(len(us) + 1, dtype=np.float64)
    return us, px, v, s, mid, csv, cnt


def trailing(us, cs, win_us):
    """Sum over (t - win, t] for each record (inclusive of the record)."""
    j = np.searchsorted(us, us - win_us, side="right")
    i = np.arange(len(us))
    return cs[i + 1] - cs[j]


def refractory(idx, us, gap_us):
    keep, last = [], -10**18
    for i in idx:
        if us[i] - last >= gap_us:
            keep.append(i)
            last = us[i]
    return np.array(keep, dtype=np.int64)


def families(us, px, v, s, mid, csv, cnt, P):
    E = {}
    f1 = trailing(us, csv, 1_000_000)
    n1 = trailing(us, cnt, 1_000_000)
    f5 = trailing(us, csv, 5_000_000)
    j5 = np.searchsorted(us, us - 5_000_000, side="right")
    dm5 = (mid - mid[j5]) / TICK
    # E1 same-side run: event at the k-th consecutive same-side record
    brk = np.r_[True, s[1:] != s[:-1]]
    starts = np.nonzero(brk)[0]
    rid = np.cumsum(brk) - 1
    pos = np.arange(len(s)) - starts[rid] + 1
    for k in (8, 16, 32):
        i = np.nonzero(pos == k)[0]
        E[f"E1_same_side_run_k{k}"] = (i, s[i].astype(float))
    # E2 trade-arrival acceleration; direction = sign of trailing 1 s signed volume
    for q in ("p99", "p999"):
        i = refractory(np.nonzero((n1 >= P[f"n1_{q}"]) & (f1 != 0))[0], us, 5_000_000)
        E[f"E2_arrival_accel_{q}"] = (i, np.sign(f1[i]))
    # E3 signed-volume burst over 1 s
    for q in ("p99", "p999"):
        i = refractory(np.nonzero(np.abs(f1) >= P[f"f1_{q}"])[0], us, 5_000_000)
        E[f"E3_signed_vol_1s_{q}"] = (i, np.sign(f1[i]))
    # E4 large print
    for L in (20, 50, 100):
        i = np.nonzero(v >= L)[0]
        E[f"E4_large_print_ge{L}"] = (i, s[i].astype(float))
    # E5 large-print sequence: >= 2 prints >= 20 lots, same side, within 1 s (event at the 2nd)
    big = np.nonzero(v >= 20)[0]
    if len(big) > 1:
        a, b = big[:-1], big[1:]
        sel = b[(s[a] == s[b]) & (us[b] - us[a] <= 1_000_000)]
    else:
        sel = np.array([], dtype=np.int64)
    E["E5_large_seq_2x20_1s"] = (sel, s[sel].astype(float))
    # E6 small-print sequences: k consecutive same-side 1-lot records spanning <= 2 s
    one = v == 1
    brk1 = np.r_[True, (s[1:] != s[:-1]) | ~one[1:] | ~one[:-1]]
    st1 = np.nonzero(brk1)[0]
    rid1 = np.cumsum(brk1) - 1
    start = st1[rid1]
    pos1 = np.arange(len(s)) - start + 1
    for k in (20, 40):
        i = np.nonzero(one & (pos1 == k) & (us - us[start] <= 2_000_000))[0]
        E[f"E6_small_seq_1lot_k{k}"] = (i, s[i].astype(float))
    # E7 same-millisecond same-side cluster (sweep / unbundled PROXY; true unbundled flag unavailable in .scid)
    ms = us // 1000
    brk2 = np.r_[True, (ms[1:] != ms[:-1]) | (s[1:] != s[:-1])]
    st2 = np.nonzero(brk2)[0]
    rid2 = np.cumsum(brk2) - 1
    pos2 = np.arange(len(s)) - st2[rid2] + 1
    for k in (5, 10):
        i = np.nonzero(pos2 == k)[0]
        E[f"E7_same_ms_sweep_k{k}"] = (i, s[i].astype(float))
    # E8 / E9 high 5 s flow with high / low displacement
    hf = np.abs(f5) >= P["f5_p99"]
    i = refractory(np.nonzero(hf & (np.sign(f5) * dm5 >= P["dm5_p90"]))[0], us, 5_000_000)
    E["E8_hiflow_hidisp_5s"] = (i, np.sign(f5[i]))
    i = refractory(np.nonzero(hf & (np.abs(dm5) <= 1))[0], us, 5_000_000)
    E["E9_hiflow_lodisp_5s[overlaps_dead_absorption]"] = (i, np.sign(f5[i]))
    # E10-E12 conditional on E3 p99 bursts, evaluated 1-2 s later (causal)
    b_i, b_d = E["E3_signed_vol_1s_p99"]
    if len(b_i):
        t2 = np.searchsorted(us, us[b_i] + 2_000_000, side="right") - 1
        ok = t2 > b_i
        cont = b_d * (mid[t2] - mid[b_i]) / TICK
        fc = ok & (cont <= 0)
        E["E10_failed_continuation_2s(dir=reverse)"] = (t2[fc], -b_d[fc])
        n2 = cnt[t2 + 1] - cnt[b_i + 1]
        ex = ok & (n2 < P["n2_median"])
        E["E11_flow_exhaustion_2s(dir=orig)"] = (t2[ex], b_d[ex])
        t1 = np.searchsorted(us, us[b_i] + 1_000_000, side="right") - 1
        rev = (t1 > b_i) & (np.sign(f1[t1]) == -b_d) & (np.abs(f1[t1]) >= P["f1_p99"])
        E["E12_immediate_reversal_1s(dir=new)"] = (t1[rev], -b_d[rev])
    return E


def markouts(us, mid, px, idx, d, rmx, rmn):
    base = mid[idx]
    out = {}
    jl = np.searchsorted(us, us[idx] + LAT_MS * 1000, side="right") - 1
    for h in H_MS:
        j = np.searchsorted(us, us[idx] + h * 1000, side="right") - 1
        out[f"m{h}"] = d * (mid[j] - base) / TICK
        if h > LAT_MS:
            j2 = np.searchsorted(us, us[idx] + (LAT_MS + h) * 1000, side="right") - 1
            out[f"x{h}"] = d * (mid[j2] - mid[jl]) / TICK
    for hs in (10000, 60000):
        j = np.maximum(np.searchsorted(us, us[idx] + hs * 1000, side="right") - 1, idx)
        hi, lo = rmx.q(idx, j), rmn.q(idx, j)
        out[f"mfe{hs}"] = np.where(d > 0, hi - base, base - lo) / TICK
        out[f"mae{hs}"] = np.where(d > 0, base - lo, hi - base) / TICK
    return out


def main():
    t0 = time.time()
    days = []
    for c, lo, hi in ROLLS:
        d = load_contract(c, lo, hi)
        days += [g.reset_index(drop=True) for _, g in d.groupby("tday") if len(g) > 5000]
        print(c, len(d), "days so far", len(days), round(time.time() - t0), flush=True)
    cal = days[:20]
    f1s, n1s, f5s, dm5s, n2s = [], [], [], [], []
    for g in cal:
        us, px, v, s, mid, csv, cnt = day_arrays(g)
        f1s.append(trailing(us, csv, 1_000_000))
        n1s.append(trailing(us, cnt, 1_000_000))
        f5s.append(trailing(us, csv, 5_000_000))
        j5 = np.searchsorted(us, us - 5_000_000, side="right")
        dm5s.append(np.abs(mid - mid[j5]) / TICK)
        n2s.append(trailing(us, cnt, 2_000_000))
    F1, N1, F5, DM5, N2 = map(np.concatenate, (f1s, n1s, f5s, dm5s, n2s))
    P = {"f1_p99": float(np.nanpercentile(np.abs(F1), 99)), "f1_p999": float(np.nanpercentile(np.abs(F1), 99.9)),
         "n1_p99": float(np.percentile(N1, 99)), "n1_p999": float(np.percentile(N1, 99.9)),
         "f5_p99": float(np.nanpercentile(np.abs(F5), 99)), "dm5_p90": float(np.nanpercentile(DM5, 90)),
         "n2_median": float(np.median(N2)), "calibration_days": [str(g.tday.iloc[0]) for g in cal]}
    print("thresholds", {k: v for k, v in P.items() if k != "calibration_days"}, flush=True)
    rows = []
    for n, g in enumerate(days):
        us, px, v, s, mid, csv, cnt = day_arrays(g)
        rmx, rmn = RMQ(px, np.maximum), RMQ(px, np.minimum)
        st = stratum(g.mins.to_numpy())
        tday = str(g.tday.iloc[0])
        E = families(us, px, v, s, mid, csv, cnt, P)
        bi = np.arange(0, len(us), 1000)
        E["BASE_every1000th_trade_dir=aggr"] = (bi, s[bi].astype(float))
        f1 = trailing(us, csv, 1_000_000)
        for name, (idx, dd) in E.items():
            idx = np.asarray(idx, dtype=np.int64)
            dd = np.asarray(dd, dtype=float)
            if len(idx) == 0:
                continue
            keep = ~np.isnan(mid[idx]) & (dd != 0)
            idx, dd = idx[keep], dd[keep]
            if len(idx) == 0:
                continue
            df = pd.DataFrame(markouts(us, mid, px, idx, dd, rmx, rmn))
            df["fam"] = name
            df["day"] = tday
            df["stratum"] = st[idx]
            df["absvol1s"] = np.abs(f1[idx])
            rows.append(df)
        if n % 20 == 0:
            print("day", n, tday, round(time.time() - t0), flush=True)
    A = pd.concat(rows, ignore_index=True)
    A.to_parquet(Path(__file__).with_name("nq_event_atlas_events.parquet"))
    reg = {"thresholds": P, "days": len(days), "families": sorted(A.fam.unique().tolist()), "horizons_ms": H_MS,
           "latency_ms": LAT_MS, "friction_ticks": FRICTION_TICKS}
    Path(__file__).with_name("nq_event_atlas_registry.json").write_text(json.dumps(reg, indent=1))
    print("events", len(A), "days", len(days), "elapsed", round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
