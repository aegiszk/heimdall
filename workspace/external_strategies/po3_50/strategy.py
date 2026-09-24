"""Family C - Trader Kane 50% rebalance / PO3 (HNuRp9Z1bMs). NQ traded (MNQ 1m), ES compared (SMT).

Recovered source rules (creator transcript; timestamps in SOURCE_MATRIX.md):
- only NASDAQ; ES for divergence ("NQ makes the high, ES fails")                          [03:43, 28:59-29:56]
- 10:00 ET hourly candle manipulates above the previous (09:00) hourly high, inside the H4 wick above
  the previous H4 high; active 09:15-11:30                                                 [10:09-11:59, 47:16]
- entry: SMT + weakness = an inversion (a prior FVG that impulsed higher is traded below); sell-stop /
  close below it (or limit re-tap)                                                          [30:57-32:55, 49:09-50:06]
- stop above the SMT (divergence) high; target 50% of the range ("base hit")                [33:55]
- break-even once the new hourly candle flips bearish / the 15-minute low is taken         [50:06-51:01, 1:01:56]
Bullish mirror: "if you were looking at the upside it would just be the exact same just flipped" [12:54].

Mechanization (RESEARCH_ASSUMPTION where marked in PREREGISTRATION.md): the manipulation hour is 10:00-11:00
ET; SMT = at entry time NQ's high since 10:00 exceeds its 09:00-hour high while ES's high since 10:00 does NOT
exceed ES's 09:00-hour high; inversion FVG = most recent bullish 3-candle FVG on the execution timeframe
completed between 09:30 and the NQ manipulation high; entry at the close of the first execution bar closing
below that FVG's bottom (10:00-11:30); stop = NQ high since 10:00 + 1 tick; target = 50% of [range low,
stop-high]; BE when the low of the last completed 15m candle before entry is taken; flat 16:00 ET.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from harness import ET, Order, fvgs, resample  # noqa: E402


@dataclass(frozen=True)
class Cfg:
    name: str
    exec_tf: str = "3min"
    range_low: str = "overnight"   # 'overnight' = extreme since 18:00 ET ; 'h4prev' = previous 06:00-10:00 H4 bin
    need_h4: bool = False          # also require the 10:00 H4 bin to exceed the previous H4 bin extreme
    tick: float = 0.25


def _day_slices(m1: pd.DataFrame):
    et = m1.index.tz_convert(ET).tz_localize(None)
    sd = (et + pd.Timedelta(hours=6)).normalize()
    return et, sd


def generate(nq: pd.DataFrame, es: pd.DataFrame, cfg: Cfg) -> list[Order]:
    orders: list[Order] = []
    et_nq, sd_nq = _day_slices(nq)
    et_es, _ = _day_slices(es)
    ex = resample(nq, cfg.exec_tf)
    exk = pd.DatetimeIndex(ex["key"])
    exH, exL, exC = (ex[c].to_numpy() for c in ("high", "low", "close"))
    bull, bear = fvgs(exH, exL)
    exend = pd.DatetimeIndex(ex["end"])
    m15 = resample(nq, "15min")
    m15end = pd.DatetimeIndex(m15["end"]).as_unit("ns").asi8
    for day in np.unique(sd_nq):
        d = pd.Timestamp(day)
        t9, t10, t11, t1130, t16 = (d + pd.Timedelta(hours=h) for h in (9, 10, 11, 11.5, 16))
        t6, t930, t18 = d + pd.Timedelta(hours=6), d + pd.Timedelta(hours=9.5), d - pd.Timedelta(hours=6)
        nqd = nq[(et_nq >= t18) & (et_nq < t16)]
        esd = es[(et_es >= t18) & (et_es < t16)]
        if nqd.empty or esd.empty:
            continue
        ne = nqd.index.tz_convert(ET).tz_localize(None)
        ee = esd.index.tz_convert(ET).tz_localize(None)
        n9 = nqd[(ne >= t9) & (ne < t10)]
        e9 = esd[(ee >= t9) & (ee < t10)]
        if len(n9) < 50 or len(e9) < 50:
            continue
        h4p_n = nqd[(ne >= t6) & (ne < t10)]
        if h4p_n.empty:
            continue
        # execution bars in the entry window
        sel = np.flatnonzero((exk >= t10) & (exk < t1130))
        for side in (-1, 1):
            ref_n = n9["high"].max() if side < 0 else n9["low"].min()
            ref_e = e9["high"].max() if side < 0 else e9["low"].min()
            h4_ref = h4p_n["high"].max() if side < 0 else h4p_n["low"].min()
            for j in sel:
                t_end_et = exend[j].tz_convert(ET).tz_localize(None)
                nwin = nqd[(ne >= t10) & (ne < t_end_et)]
                ewin = esd[(ee >= t10) & (ee < t_end_et)]
                if nwin.empty or ewin.empty:
                    continue
                n_ext = nwin["high"].max() if side < 0 else nwin["low"].min()
                e_ext = ewin["high"].max() if side < 0 else ewin["low"].min()
                n10 = nwin[nwin.index.tz_convert(ET).tz_localize(None) < t11]
                n10_ext = n10["high"].max() if side < 0 else n10["low"].min()
                n_swept = n10_ext > ref_n if side < 0 else n10_ext < ref_n
                e_held = e_ext <= ref_e if side < 0 else e_ext >= ref_e
                if not (n_swept and e_held):
                    continue
                if cfg.need_h4 and not (n10_ext > h4_ref if side < 0 else n10_ext < h4_ref):
                    continue
                t_ext = (nwin["high"].idxmax() if side < 0 else nwin["low"].idxmin())
                # inversion FVG: most recent same-direction-as-push FVG completed after 09:30 and before extreme
                fv = bull if side < 0 else bear
                i = None
                for q in range(j - 1, 1, -1):
                    if exk[q - 2] < t930:
                        break
                    if fv[q] and exend[q] <= t_ext + pd.Timedelta(minutes=1):
                        i = q
                        break
                if i is None:
                    continue
                edge = exH[i - 2] if side < 0 else exL[i - 2]      # FVG bottom (bull) / top (bear)
                crossed = exC[j] < edge if side < 0 else exC[j] > edge
                prev_ok = exC[j - 1] >= edge if side < 0 else exC[j - 1] <= edge
                if not (crossed and prev_ok):
                    continue
                stop = n_ext + cfg.tick if side < 0 else n_ext - cfg.tick
                if cfg.range_low == "overnight":
                    pre = nqd[ne < t_end_et]
                    rl = pre["low"].min() if side < 0 else pre["high"].max()
                else:
                    rl = h4p_n["low"].min() if side < 0 else h4p_n["high"].max()
                tgt = (rl + n_ext) / 2.0
                entry_ref = exC[j]
                if (side < 0 and tgt >= entry_ref) or (side > 0 and tgt <= entry_ref):
                    continue
                k15 = int(np.searchsorted(m15end, exend[j].as_unit("ns").value, side="right")) - 1
                be = None
                if k15 >= 0:
                    be = (m15["low"].iat[k15] - cfg.tick) if side < 0 else (m15["high"].iat[k15] + cfg.tick)
                    if (side < 0 and be >= entry_ref) or (side > 0 and be <= entry_ref):
                        be = None
                orders.append(Order(side, exend[j], "close_at", stop=stop, targets=[(tgt, 1.0)], be_level=be,
                                    flatten=(d + pd.Timedelta(hours=16)).tz_localize(ET).tz_convert("UTC"),
                                    tag=cfg.name,
                                    meta=dict(day=str(d.date()), ref_nq=ref_n, ref_es=ref_e, n_ext=n_ext,
                                              e_ext=e_ext, fvg_edge=edge, range_low=rl, target=tgt)))
                break   # one setup per side per day
    return orders


CONFIGS = [
    Cfg("C1_3m_overnight"),
    Cfg("C2_3m_overnight_H4", need_h4=True),
    Cfg("C3_5m_overnight", exec_tf="5min"),
    Cfg("C4_3m_h4range", range_low="h4prev"),
]
