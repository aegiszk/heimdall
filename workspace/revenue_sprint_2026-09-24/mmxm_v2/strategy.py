"""MMXM_V2 — one canonical source-faithful model (IB-fyWI5j8w, MBB Trader). See MMXM_V2_SOURCE_SPEC.md.

Changes vs V1 (F1-F3), each adjudicated in the spec:
- NO outside-kill-zone day veto (unsourced; Agent 2 + Agent 1 agree)
- broken swing = most recent confirmed k=1 swing before the SMR extreme, NO lookback cap (V1: 60 bars, unsourced)
- fib 0 = low (sell) / high (buy) of the displacement leg, taken when the leg completes = the first confirmed k=1 swing
  at/after the break bar ("you'll have some sort of swing made", 0:37:21; "from this high to this low", 0:40:07)
- kill zones are CONTEXT only (recorded per trade); no kill-zone gate of any kind (no verbatim basis for a gate)
- entry limit 0.62, stop 0.9, TP 0 (stated plan 0:55:52); BE on a 15m close beyond 0.2 (0:45:20)
- unfilled order expires at the end of the FX day (17:00 NY) (declared assumption; V1 used 12:00 NY)
- key levels: previous day AND previous week high/low (both stated, 0:03:41)
- day filter: "I'm only considering days where we open closer to one of these key levels. I'm not going in every day"
  (0:06:27) -> a level is eligible only if the FX-day open is closer to it than to its opposite level (PDH vs PDL,
  PWH vs PWL); parameter-free mapping, declared
Unchanged: weekly bias (previous week close vs open), displacement = body >= 50% of range with the break colour, no
second-leg / Silver-Bullet entry, 17:00 NY FX day, harness cost model.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "external_strategies" / "common"))
from harness import ET, Order, pivots, resample  # noqa: E402

KZ = [(2.0, 5.0), (7.0, 10.0), (10.0, 12.0)]


@dataclass(frozen=True)
class Cfg:
    name: str = "MMXM_V2"
    ote: float = 0.62
    stop_lvl: float = 0.90
    be_lvl: float = 0.20
    min_body_frac: float = 0.5
    max_hold_days: int = 3
    expiry_hour: float = 17.0      # end of the FX day on which the displacement closed


def generate(m1: pd.DataFrame, cfg: Cfg) -> list[Order]:
    b = resample(m1, "15min")
    O, H, L, C = (b[c].to_numpy() for c in ("open", "high", "low", "close"))
    key = pd.DatetimeIndex(b["key"])
    end = pd.DatetimeIndex(b["end"])
    ends_ns = end.as_unit("ns").asi8
    ph, pl = pivots(H, L, 1)
    n = len(C)
    sday = (key + pd.Timedelta(hours=7)).normalize()                   # FX day opens 17:00 NY
    d1 = pd.DataFrame({"h": H, "l": L, "o": O, "c": C, "d": sday}).groupby("d").agg(
        h=("h", "max"), l=("l", "min"), o=("o", "first"), c=("c", "last"))
    wk = d1.index.to_period("W-FRI")
    w1 = d1.groupby(wk).agg(h=("h", "max"), l=("l", "min"), o=("o", "first"), c=("c", "last"))
    days = list(d1.index)
    tod = (key - key.normalize()) / pd.Timedelta(hours=1)
    in_kz = np.zeros(n, bool)
    for a, z in KZ:
        in_kz |= (tod >= a) & (tod < z)
    orders: list[Order] = []
    for di in range(1, len(days)):
        day = days[di]
        pw = wk[di] - 1
        if pw not in w1.index:
            continue
        pwr, prev = w1.loc[pw], d1.iloc[di - 1]
        side = 1 if pwr.c > pwr.o else -1                              # trade only with the weekly bias
        idx = np.flatnonzero(sday == day)
        if len(idx) < 10:
            continue
        day_open = O[idx[0]]
        pairs_ = [(prev.h, prev.l), (pwr.h, pwr.l)] if side < 0 else [(prev.l, prev.h), (pwr.l, pwr.h)]
        lvls = [lv for lv, opp in pairs_ if abs(day_open - lv) < abs(day_open - opp)]
        if not lvls:
            continue                                                    # did not open close to a key level
        run_i = next((j for j in idx if any((H[j] > lv) if side < 0 else (L[j] < lv) for lv in lvls)), None)
        if run_i is None:
            continue
        ext = run_i
        last = int(idx[-1])
        for j in range(run_i + 1, last + 1):
            if (side < 0 and H[j] > H[ext]) or (side > 0 and L[j] < L[ext]):
                ext = j
                continue
            piv = pl if side < 0 else ph
            q = next((q for q in range(ext - 1, 0, -1) if piv[q] and q + 1 <= j - 1), None)
            if q is None:
                continue
            lvl = L[q] if side < 0 else H[q]
            if not ((C[j] < lvl) if side < 0 else (C[j] > lvl)):
                continue
            rng = H[j] - L[j]
            displaced = rng > 0 and abs(C[j] - O[j]) >= cfg.min_body_frac * rng and ((C[j] < O[j]) if side < 0 else (C[j] > O[j]))
            if not displaced:
                break                                                   # wicky break: no first-leg trade (no 2nd leg)
            one = H[ext] if side < 0 else L[ext]
            leg = pl if side < 0 else ph                                # displacement leg ends at the next confirmed swing
            z = next((z for z in range(j, last) if leg[z] and z + 1 <= last), None)
            if z is None:
                break
            zero = L[ext:z + 1].min() if side < 0 else H[ext:z + 1].max()
            t_dec = end[z + 1]                                          # leg low known at the close of bar z+1
            span = abs(one - zero)
            exp_utc = (pd.Timestamp(day) + pd.Timedelta(hours=cfg.expiry_hour)).tz_localize(ET).tz_convert("UTC")
            if span <= 0 or t_dec >= exp_utc:
                break
            sgn = -side                                                 # fib measured from 0 toward 1
            ent, stop, be = (zero + sgn * cfg.ote * span, zero + sgn * cfg.stop_lvl * span, zero + sgn * cfg.be_lvl * span)
            be_cond = ((C < be) if side < 0 else (C > be)).copy()
            be_cond[: z + 2] = False
            orders.append(Order(side, t_dec, "limit", stop=stop, entry_px=ent, targets=[(zero, 1.0)], expiry=exp_utc,
                                close_events=[(ends_ns, be_cond, "be")],
                                flatten=t_dec + pd.Timedelta(days=cfg.max_hold_days), tag=cfg.name,
                                meta=dict(one=float(one), zero=float(zero), broken_swing=float(lvl), smr_i=int(ext),
                                          disp_i=int(j), leg_end_i=int(z), day=str(day.date()),
                                          ctx_disp_in_kz=bool(in_kz[j]))))
            break
    return orders


PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
