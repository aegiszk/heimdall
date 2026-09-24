"""Family F - MBB Trader (Omar) market-maker model framework + OTE entry (IB-fyWI5j8w). Forex, 15-minute.

Recovered source rules (creator transcript; timestamps in SOURCE_MATRIX.md):
- framework forms at key levels: previous day / week high & low, 4H-or-higher FVG/breaker/OB        [03:41-04:39]
- need a predetermined expectation (bias) for the day; "only favor [the sell model] when bearish";
  "if we're bearish on the week ... favoring this run and reversal"                                 [05:32, 29:02-29:52]
- smart money reversal = run of a high, then a 15-minute BODY close through the swing low
  (displacement); a wicky close or an opposing 15m PDA -> let a retracement go (second leg)          [11:59-13:51, 16:35-18:19]
- entry = optimal trade entry on the fib from the swing (1) to the displacement low (0):
  0.62 / 0.705 / 0.79; "50% or nothing" when selling; limit entry                                   [36:21-40:07, 57:33]
- stop at 1.0; refinement: 0.9 (price rarely reaches 0.9 and not 1.0); TP initial = the low (0)     [40:58-42:42, 51:33]
- break-even on a CLOSE beyond the 0.2 level                                                         [45:20-46:15]
- kill zones (NY time): London 02:00-05:00, New York 07:00-10:00, London close 10:00-12:00          [29:52-30:49]
- first-leg breaker often does not reach OTE (50% or less)                                          [54:10]

Mechanization (RESEARCH_ASSUMPTION in PREREGISTRATION.md): bias = direction of the previous completed week
(close vs open) - sells only in a bearish-week context, buys only bullish; key levels = PDH/PDL (and
PWH/PWL in F3); the run must happen inside a kill zone; SMR swing = the highest 15m high since the run;
displacement = the first 15m bar after the run whose BODY closes below the most recent confirmed 15m swing
low (k=1) formed before the SMR high, with body >= 50% of its range; else no trade (second-leg entries not
implemented); fib 1 = SMR high, 0 = lowest low from SMR high through the displacement bar (fixed at the displacement
close) - fixed once set; limit at the OTE level; cancel if unfilled by 12:00 NY or if price trades beyond 1.0 first.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from harness import ET, Order, pivots, resample  # noqa: E402

KZ = [(2.0, 5.0), (7.0, 10.0), (10.0, 12.0)]


@dataclass(frozen=True)
class Cfg:
    name: str
    ote: float = 0.62
    stop_lvl: float = 1.0
    weekly_levels: bool = False
    max_hold_days: int = 3


def generate(m1: pd.DataFrame, cfg: Cfg) -> list[Order]:
    b = resample(m1, "15min")
    O, H, L, C = (b[c].to_numpy() for c in ("open", "high", "low", "close"))
    key = pd.DatetimeIndex(b["key"])
    end = pd.DatetimeIndex(b["end"])
    ends_ns = end.as_unit("ns").asi8
    ph, pl = pivots(H, L, 1)
    sday = (key + pd.Timedelta(hours=7)).normalize()   # FX day rolls at 17:00 NY
    d1 = pd.DataFrame({"h": H, "l": L, "o": O, "c": C, "d": sday}).groupby("d").agg(
        h=("h", "max"), l=("l", "min"), o=("o", "first"), c=("c", "last"))
    wk = d1.index.to_period("W-FRI")
    w1 = d1.groupby(wk).agg(h=("h", "max"), l=("l", "min"), o=("o", "first"), c=("c", "last"))
    days = list(d1.index)
    orders: list[Order] = []
    tod = (key - key.normalize()) / pd.Timedelta(hours=1)
    in_kz = np.zeros(len(b), bool)
    for a, z in KZ:
        in_kz |= (tod >= a) & (tod < z)
    for di in range(1, len(days)):
        day = days[di]
        prev = d1.iloc[di - 1]
        pw = wk[di] - 1
        if pw not in w1.index:
            continue
        pwr = w1.loc[pw]
        bias = 1 if pwr.c > pwr.o else -1
        idx = np.flatnonzero(sday == day)
        if len(idx) < 10:
            continue
        for side in (-1, 1):
            if side != bias:
                continue
            lvls = [prev.h if side < 0 else prev.l]
            if cfg.weekly_levels:
                lvls.append(pwr.h if side < 0 else pwr.l)
            run_i = None
            for j in idx:
                ran = any((H[j] > lv) if side < 0 else (L[j] < lv) for lv in lvls)
                if ran and in_kz[j]:
                    run_i = j
                    break
                if ran:
                    break   # level ran outside a kill zone -> not the framework
            if run_i is None:
                continue
            smr = run_i
            for j in range(run_i + 1, min(idx[-1] + 1, len(C))):
                if (side < 0 and H[j] > H[smr]) or (side > 0 and L[j] < L[smr]):
                    smr = j
                    continue
                # most recent confirmed swing (k=1) before the SMR extreme, confirmed by bar j-1
                sw = [q for q in range(smr - 1, max(0, smr - 60), -1) if (pl[q] if side < 0 else ph[q]) and q + 1 <= j - 1]
                if not sw:
                    continue
                q = sw[0]
                lvl = L[q] if side < 0 else H[q]
                broke = (C[j] < lvl) if side < 0 else (C[j] > lvl)
                if not broke:
                    continue
                rng = H[j] - L[j]
                if rng <= 0 or abs(C[j] - O[j]) < 0.5 * rng or ((C[j] > O[j]) if side < 0 else (C[j] < O[j])):
                    break   # wicky / non-displacement break -> no first-leg trade (second leg not implemented)
                one = H[smr] if side < 0 else L[smr]
                zero = L[smr:j + 1].min() if side < 0 else H[smr:j + 1].max()
                span = abs(one - zero)
                if span <= 0:
                    break
                if side < 0:
                    ent, stop, tgt, be_lvl = (zero + cfg.ote * span, zero + cfg.stop_lvl * span, zero,
                                              zero + 0.2 * span)
                else:
                    ent, stop, tgt, be_lvl = (zero - cfg.ote * span, zero - cfg.stop_lvl * span, zero,
                                              zero - 0.2 * span)
                be_cond = ((C < be_lvl) if side < 0 else (C > be_lvl)).copy()
                be_cond[: j + 1] = False
                exp_utc = (key[j].normalize() + pd.Timedelta(hours=12)).tz_localize(ET).tz_convert("UTC")
                if exp_utc <= end[j]:
                    break
                orders.append(Order(side, end[j], "limit", stop=stop, entry_px=ent, targets=[(tgt, 1.0)],
                                    expiry=exp_utc, close_events=[(ends_ns, be_cond, "be")],
                                    flatten=end[j] + pd.Timedelta(days=cfg.max_hold_days), tag=cfg.name,
                                    meta=dict(one=one, zero=zero, level=lvls[0], bias=bias, disp_i=int(j))))
                break
    return orders


CONFIGS = [
    Cfg("F1_ote62_sl100_PD"),
    Cfg("F2_ote705_sl90_PD", ote=0.705, stop_lvl=0.9),
    Cfg("F3_ote62_sl90_PDPW", stop_lvl=0.9, weekly_levels=True),
]
PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
