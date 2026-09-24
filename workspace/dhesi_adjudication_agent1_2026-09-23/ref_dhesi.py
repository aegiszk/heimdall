"""Agent 1 independent reference implementation of the Dhesi inversion model.

Written from the written specification only:
  - v2 frozen docstring + discretion_gaps() list (core/alpha/inversion_model.py:144-249, read as TEXT)
  - DHESI_V3_PREREGISTRATION.md (SHA C9D143E5...D843)
It imports NOTHING from core.alpha (no signal, pool, FVG, swing or simulator code).
Only pandas/numpy. Used solely to reproduce historical DEVELOPMENT trades.

Config:
  mode="v2": RTH-clock HTF bins, sweeps >= 10:00, no session pools, 1 entry/session, no stop guard
  mode="v3": 18:00-anchored 24h HTF bins, sweeps >= 09:30, asia/london pools, <=3 attempts, 2-loss stop
  guard: "none" | "side" | "side_floor"   (floor = 10.0 pts from slipped entry)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, asdict
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

ET = "America/New_York"
TICK = 0.25
PV = 2.0            # MNQ $/pt
TICKV = 0.50        # MNQ $/tick
COMM = 1.0          # $ round turn / contract
BUFFER = 325.0
MAXC = 40
LOOKBACK = 20
EQ_TOL = 0.0005
DISP_MIN = 30.0
TP1_R = 1.5
FLOOR = 10.0
T0930, T1000, T1600 = time(9, 30), time(10, 0), time(16, 0)


@dataclass
class Fvg:
    uid: int
    formed: pd.Timestamp
    session: object
    d: int          # +1 bullish gap, -1 bearish gap
    lo: float
    hi: float
    c3lo: float
    c3hi: float


@dataclass
class Inv:
    ts: pd.Timestamp
    session: object
    bias: int
    lo: float
    hi: float
    formed: pd.Timestamp
    close: float
    disp: float
    c3lo: float
    c3hi: float


# ------------------------------------------------------------------ bars
def rth_frame(raw: pd.DataFrame) -> pd.DataFrame:
    et = raw.index.tz_convert(ET)
    f = raw.copy()
    f["et"] = et
    f["date"] = et.date
    f["t"] = et.time
    m = (et.weekday < 5) & (f["t"] >= T0930) & (f["t"] <= T1600)
    return f.loc[m].reset_index(drop=True)


def resample_right(f: pd.DataFrame, rule: str) -> pd.DataFrame:
    g = f.set_index("et").resample(rule, label="right", closed="right")
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "session": g["date"].last()}).dropna()
    b["ts"] = b.index
    return b.reset_index(drop=True)


def bins_24h(raw: pd.DataFrame, hours: int) -> pd.DataFrame:
    wall = raw.index.tz_convert(ET).tz_localize(None)
    sh = wall - pd.Timedelta(hours=18)
    start = sh.normalize() + pd.to_timedelta((sh.hour // hours) * hours, unit="h") + pd.Timedelta(hours=18)
    df = raw[["open", "high", "low", "close"]].copy()
    df["bin"] = start
    g = df.groupby("bin", sort=True)
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last()})
    end = b.index + pd.Timedelta(hours=hours)
    b = b.reset_index(drop=True)
    b["ts"] = pd.DatetimeIndex(end).tz_localize(ET, ambiguous=True, nonexistent="shift_forward")
    b["session"] = [(e - pd.Timedelta(minutes=1) + pd.Timedelta(hours=6)).date() for e in end]
    return b


# ------------------------------------------------------------------ FVG / inversion
def inversions(b: pd.DataFrame, sord: dict) -> tuple[list[Fvg], list[Inv]]:
    H, L, O, C = (b[k].to_numpy(float) for k in ("high", "low", "open", "close"))
    TS, SS = list(b["ts"]), list(b["session"])
    active: list[Fvg] = []
    allf: list[Fvg] = []
    dead: set[int] = set()
    out: list[Inv] = []
    uid = 0
    for i in range(len(b)):
        cur = sord.get(SS[i])
        if cur is not None:
            active = [g for g in active if g.uid not in dead and g.session in sord and 0 <= cur - sord[g.session] <= LOOKBACK]
            hit = [g for g in active if (g.d == 1 and C[i] < g.lo) or (g.d == -1 and C[i] > g.hi)]
            for g in hit:
                dead.add(g.uid)
            for bias in (-1, 1):
                same = [g for g in hit if -g.d == bias]
                if same:
                    best = same[0]
                    for g in same[1:]:
                        if g.formed > best.formed:
                            best = g
                    out.append(Inv(TS[i], SS[i], bias, best.lo, best.hi, best.formed, C[i], abs(C[i] - O[i]), best.c3lo, best.c3hi))
        if i >= 2:
            if H[i - 2] < L[i]:
                g = Fvg(uid, TS[i], SS[i], 1, H[i - 2], L[i], L[i], H[i]); uid += 1
                active.append(g); allf.append(g)
            if L[i - 2] > H[i]:
                g = Fvg(uid, TS[i], SS[i], -1, H[i], L[i - 2], L[i], H[i]); uid += 1
                active.append(g); allf.append(g)
    return allf, out


def fractals(ts, sess, H, L):
    """3-bar fractal: middle high > prev high and >= next high (mirror for lows). Confirmed at next bar."""
    out = []
    for i in range(1, len(H) - 1):
        if H[i] > H[i - 1] and H[i] >= H[i + 1]:
            out.append(("high", ts[i], ts[i + 1], sess[i], H[i]))
        if L[i] < L[i - 1] and L[i] <= L[i + 1]:
            out.append(("low", ts[i], ts[i + 1], sess[i], L[i]))
    return out


def clusters(vals):
    vals = sorted(v for v in vals if np.isfinite(v) and v > 0)
    res, cur = [], []
    for v in vals:
        if not cur:
            cur = [v]; continue
        a = sum(cur) / len(cur)
        if abs(v - a) / a <= EQ_TOL:
            cur.append(v)
        else:
            if len(cur) >= 2:
                res.append(cur)
            cur = [v]
    if len(cur) >= 2:
        res.append(cur)
    return res


def dedupe(pools):
    seen, out = set(), []
    for lvl, kind in pools:
        if not np.isfinite(lvl):
            continue
        k = (kind, int(round(lvl / TICK)))
        if k in seen:
            continue
        seen.add(k); out.append((lvl, kind))
    return out


# ------------------------------------------------------------------ model
def run(raw: pd.DataFrame, mode: str = "v3", guard: str = "side_floor") -> pd.DataFrame:
    v3 = mode == "v3"
    raw = raw[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
    f = rth_frame(raw)
    sessions = list(dict.fromkeys(f["date"]))
    sord = {s: i for i, s in enumerate(sessions)}

    # pools -------------------------------------------------------------
    alld = raw.copy(); alld["d"] = raw.index.tz_convert(ET).date
    dayhl = alld.groupby("d").agg(h=("high", "max"), l=("low", "min"))
    pdh, pdl = dayhl["h"].shift(1), dayhl["l"].shift(1)
    rth = f.groupby("date").agg(h=("high", "max"), l=("low", "min"))
    prh, prl = rth["h"].shift(1), rth["l"].shift(1)
    r20h = rth["h"].shift(1).rolling(LOOKBACK, min_periods=LOOKBACK).max()
    r20l = rth["l"].shift(1).rolling(LOOKBACK, min_periods=LOOKBACK).min()
    sw1 = fractals(list(f["et"]), list(f["date"]), f["high"].to_numpy(float), f["low"].to_numpy(float))
    sw_by_sess_kind: dict = {}
    for kind, _, _, s, p in sw1:
        sw_by_sess_kind.setdefault((s, kind), []).append(p)
    asia = london = None
    if v3:
        tt = alld.index.tz_convert(ET)
        tm = tt.time
        ai = (tm >= time(20, 0)) & (tm <= time(23, 59))
        li = (tm >= time(2, 0)) & (tm <= time(4, 59))
        ak = (tt[ai].tz_localize(None).normalize() + pd.Timedelta(days=1)).date
        lk = tt[li].tz_localize(None).normalize().date
        asia = alld.loc[ai].assign(k=ak).groupby("k").agg(h=("high", "max"), l=("low", "min"))
        london = alld.loc[li].assign(k=lk).groupby("k").agg(h=("high", "max"), l=("low", "min"))
    pools = {}
    for s in sessions:
        cur = sord[s]
        hi = [(prh.get(s, np.nan), "prior_rth_high"), (pdh.get(s, np.nan), "prior_day_high"), (r20h.get(s, np.nan), "rolling20_high")]
        lo = [(prl.get(s, np.nan), "prior_rth_low"), (pdl.get(s, np.nan), "prior_day_low"), (r20l.get(s, np.nan), "rolling20_low")]
        hi = [(float(a), b) for a, b in hi if np.isfinite(a)]
        lo = [(float(a), b) for a, b in lo if np.isfinite(a)]
        prev = [sessions[j] for j in range(max(0, cur - LOOKBACK), cur)]
        mh, ml = [], []
        for kind, lst, mj in (("high", hi, mh), ("low", lo, ml)):
            vals = [p for ps in prev for p in sw_by_sess_kind.get((ps, kind), [])]
            for c in clusters(vals):
                lvl = max(c) if kind == "high" else min(c)
                lst.append((lvl, f"equal_{kind}"))
                if len(c) >= 3:
                    mj.append((lvl, f"stacked_equal_{kind}"))
        if np.isfinite(r20h.get(s, np.nan)):
            mh.append((float(r20h[s]), "rolling20_high"))
        if np.isfinite(r20l.get(s, np.nan)):
            ml.append((float(r20l[s]), "rolling20_low"))
        hi, lo = dedupe(hi), dedupe(lo)
        if v3:
            for tab, nm in ((asia, "asia"), (london, "london")):
                if s in tab.index:
                    hi = dedupe(hi + [(float(tab.loc[s, "h"]), f"{nm}_high")])
                    lo = dedupe(lo + [(float(tab.loc[s, "l"]), f"{nm}_low")])
        pools[s] = {"high": hi, "low": lo, "mhigh": dedupe(mh), "mlow": dedupe(ml)}

    # bars / events -------------------------------------------------------
    if v3:
        b4, b1 = bins_24h(raw, 4), bins_24h(raw, 1)
    else:
        b4, b1 = resample_right(f, "4h"), resample_right(f, "1h")
    b15, b5 = resample_right(f, "15min"), resample_right(f, "5min")
    f4, inv4 = inversions(b4, sord)
    _, inv1 = inversions(b1, sord)
    s5 = {s: i for i, s in enumerate(dict.fromkeys(b5["session"]))}
    _, ltf = inversions(b5, s5)
    ltf.sort(key=lambda e: e.ts)
    sw15 = fractals(list(b15["ts"]), list(b15["session"]), b15["high"].to_numpy(float), b15["low"].to_numpy(float))

    def group(evs):
        d = {}
        for e in evs:
            d.setdefault((e.session, e.bias), []).append(e)
        for v in d.values():
            v.sort(key=lambda e: e.ts)
        return d

    g4, g1, gl = group(inv4), group(inv1), group(ltf)
    f4_meta = [(g.formed, g.session) for g in f4]
    b15_by = {s: d.reset_index(drop=True) for s, d in b15.groupby("session", sort=True)}
    sw15_by: dict = {}
    for kind, ts, conf, s, p in sw15:
        sw15_by.setdefault(s, []).append((kind, ts, conf, p))
    pos = {t: i for i, t in enumerate(f["et"])}
    O, Hh, Ll, Cc = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    TT, DD, TM = list(f["et"]), list(f["date"]), list(f["t"])

    def simulate(i0, side, entry, stop, tp1, runner, n):
        s = DD[i0]
        j = i0 + 1
        rstop, hit, frac, g1 = stop, False, 1.0, 0.0
        last = None
        while j < len(TT) and DD[j] == s:
            last = j
            if side > 0:
                ex = (min(O[j], rstop - TICK), "gap_stop") if O[j] <= rstop else ((rstop - TICK, "stop") if Ll[j] <= rstop else None)
            else:
                ex = (max(O[j], rstop + TICK), "gap_stop") if O[j] >= rstop else ((rstop + TICK, "stop") if Hh[j] >= rstop else None)
            if ex:
                g = frac * n * side * (ex[0] - entry) * PV
                return j, ex[0], (g1 + g) if hit else g, ("runner_" + ex[1]) if hit else ex[1], hit
            if not hit and ((Hh[j] >= tp1) if side > 0 else (Ll[j] <= tp1)):
                hit, frac, rstop = True, 0.5, entry
                g1 = 0.5 * n * side * (tp1 - entry) * PV
                j += 1
                continue
            if hit and runner is not None and ((Hh[j] >= runner) if side > 0 else (Ll[j] <= runner)):
                return j, runner, g1 + frac * n * side * (runner - entry) * PV, "runner_target", hit
            if TM[j] >= T1600:
                break
            j += 1
        if last is None:
            px = Cc[i0] - side * TICK
            return i0, px, n * side * (px - entry) * PV, "session_flatten", False
        # flatten at last bar of the session
        k = i0 + 1
        while k + 1 < len(TT) and DD[k + 1] == s:
            k += 1
        px = Cc[k] - side * TICK
        g = frac * n * side * (px - entry) * PV
        return k, px, (g1 + g) if hit else g, "runner_session_flatten" if hit else "session_flatten", hit

    def try_entry(s, bias, inv, rts, not_before):
        for e in gl.get((s, bias), []):
            if e.formed < rts or e.ts <= rts:
                continue
            if not_before is not None and e.ts <= not_before:
                continue
            if e.ts.time() < T1000 or e.ts.time() > T1600:
                continue
            if max(e.c3lo, inv.lo) > min(e.c3hi, inv.hi):
                continue
            if e.ts not in pos:
                continue
            want = "low" if bias > 0 else "high"
            cands = [(ts, p) for kind, ts, conf, p in sw15_by.get(s, []) if kind == want and conf <= e.ts and ts >= inv.ts]
            if not cands:
                continue
            ts_best = max(c[0] for c in cands)
            p = [c[1] for c in cands if c[0] == ts_best][0]
            stop = p - TICK if bias > 0 else p + TICK
            entry = e.close + bias * TICK
            dist = bias * (entry - stop)
            if guard == "side" and dist <= 0:
                continue
            if guard == "side_floor" and dist < FLOOR:
                continue
            rp = abs(entry - stop)
            n = min(int(np.floor(BUFFER / (TICKV * rp / TICK))), MAXC)
            if n <= 0:
                continue
            risk = n * rp * PV
            if risk <= 0 or risk > BUFFER + 1e-9:
                continue
            P = pools[s]
            if bias > 0:
                opp = sorted([x for x in P["high"] if x[0] > entry], key=lambda x: x[0])
                maj = sorted([x for x in P["mhigh"] if x[0] > entry], key=lambda x: x[0])
            else:
                opp = sorted([x for x in P["low"] if x[0] < entry], key=lambda x: -x[0])
                maj = sorted([x for x in P["mlow"] if x[0] < entry], key=lambda x: -x[0])
            if not opp:
                continue
            near = opp[0][0]
            tp1 = near if bias * (near - entry) >= TP1_R * rp else entry + bias * TP1_R * rp
            rc = [x for x in maj if bias * (x[0] - tp1) > 0]
            runner = rc[0][0] if rc else None
            i0 = pos[e.ts]
            j, px, gross, why, hit = simulate(i0, bias, entry, stop, tp1, runner, n)
            return dict(entry_ts=e.ts, exit_ts=TT[j], session=s, side=bias, entry_price=entry, exit_price=px,
                        stop_price=stop, tp1_price=tp1, runner_target_price=runner, contracts=n, risk_dollars=risk,
                        pnl=gross - n * COMM, gross_pnl=gross, tp1_hit=hit, reason=why)
        return None

    return _session_loop(v3, sessions, sord, pools, f, g4, g1, f4_meta, b15_by, try_entry)


def _detect_sweeps(day: pd.DataFrame, P: dict):
    ev, pend = [], []
    H, L, C, TS = day["high"].to_numpy(float), day["low"].to_numpy(float), day["close"].to_numpy(float), list(day["et"])
    for i in range(len(day)):
        for lvl, kind in P["high"]:
            if H[i] > lvl:
                pend.append((i + 3, lvl, kind, -1))
        for lvl, kind in P["low"]:
            if L[i] < lvl:
                pend.append((i + 3, lvl, kind, 1))
        keep = []
        for exp, lvl, kind, b in pend:
            if i > exp:
                continue
            if (C[i] < lvl) if b < 0 else (C[i] > lvl):
                ev.append((TS[i], b, lvl, kind))
            else:
                keep.append((exp, lvl, kind, b))
        pend = keep
    ev.sort(key=lambda x: x[0])
    return ev


def _session_loop(v3, sessions, sord, pools, f, g4, g1, f4_meta, b15_by, try_entry):
    trades = []
    for s, day in f.groupby("date", sort=True):
        sweeps = _detect_sweeps(day, pools[s])
        taken = losses = 0
        last_exit = None
        for ts, bias, lvl, kind in sweeps:
            if v3:
                if taken >= 3 or losses >= 2:
                    break
            else:
                if taken >= 1 or losses >= 2:
                    break
                if ts.time() < T1000:
                    continue
            if last_exit is not None and ts < last_exit:
                continue
            cur = sord[s]
            has4 = any(fm < ts and fs in sord and 0 <= cur - sord[fs] <= LOOKBACK for fm, fs in f4_meta)
            evs = (g4 if has4 else g1).get((s, bias), [])
            cand = [e for e in evs if e.ts > ts and e.ts.time() <= T1600]
            if not cand:
                continue
            inv = min(cand, key=lambda e: e.ts)
            if inv.disp < DISP_MIN:
                continue
            b15 = b15_by.get(s)
            if b15 is None:
                continue
            rts = None
            for _, r in b15[(b15["ts"] > inv.ts) & (b15["ts"].dt.time <= T1600)].iterrows():
                if max(float(r["low"]), inv.lo) <= min(float(r["high"]), inv.hi):
                    rts = r["ts"]; break
            if rts is None:
                continue
            t = try_entry(s, bias, inv, rts, last_exit if v3 else None)
            if t is None:
                continue
            t["sweep_pool"], t["htf_timeframe"] = kind, "4H" if has4 else "1H"
            trades.append(t)
            taken += 1
            if t["pnl"] < 0:
                losses += 1
            last_exit = t["exit_ts"]
    return pd.DataFrame(trades)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    mode, guard = sys.argv[1], sys.argv[2]
    raw = pd.read_parquet(root / "data" / "MNQ_1m.parquet")
    out = run(raw, mode, guard)
    out.to_csv(Path(__file__).resolve().parent / f"ref_{mode}_{guard}.csv", index=False)
    print(mode, guard, len(out), round(float(out["pnl"].sum()), 2) if len(out) else 0.0)
