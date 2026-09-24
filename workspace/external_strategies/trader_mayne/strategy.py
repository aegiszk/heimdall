"""Family B - Trader Mayne HTF-range / order-block / LTF-breaker framework (coBMd1vk2Lo).

Source rules recovered from the creator-uploaded transcript (timestamps in SOURCE_MATRIX.md):
- two timeframes: HTF analysis, LTF execution (weekly->daily, daily->H1, H4->M15, H1->M5)          [07:20]
- 3-candle swing points; market-structure break (MSB) = a candle CLOSE through the swing            [07:20-08:17]
- trading range = the most immediate swing low -> the swing high formed after the MSB               [18:58, 53:36]
- order block = the down candle(s) before the up move that broke structure (last down candle ok)    [19:49-20:42]
- look for longs in the OB inside the discount (lower half) of the range; target the range high     [23:19-24:15]
- LTF breaker: an LTF swing low forms, gets taken out, then the high that generated it is broken   [28:41-31:22]
- stop below the stop-run low; minimum 2:1 R:R or no trade; at 2R de-risk (half off or BE)          [32:14-35:47]
- alternative: enter directly at the HTF OB top, stop at its bottom, target external               [26:57]
Bearish ranges are the mirror (short examples at 47:18-52:45).

Mechanization choices marked RESEARCH_ASSUMPTION in the preregistration: OB = consecutive bearish candles
ending at the leg low (max 3); range low = lowest low between the broken swing high and the MSB bar; setup
expires after 30 HTF bars or on an HTF close beyond the range low; entry on LTF close through the generating
high (close_at); de-risk = move stop to break-even at +2R.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from harness import Order, pivots, resample  # noqa: E402


@dataclass(frozen=True)
class Cfg:
    name: str
    htf: str = "4h"
    ltf: str = "15min"
    entry: str = "breaker"      # 'breaker' (LTF sweep + close through generating high) | 'ob_limit'
    tick: float = 0.25
    min_rr: float = 2.0
    expiry_bars: int = 30


@dataclass
class Setup:
    side: int
    lo: float          # range low (long) / range high (short) = invalidation extreme
    hi: float          # external target
    ob_lo: float
    ob_hi: float
    t_active: pd.Timestamp
    t_expire: pd.Timestamp
    msb_i: int


def _ob(O, C, H, L, leg_i: int, side: int):
    """Consecutive opposite-colour candles ending at/before the leg extreme (max 3)."""
    bad = (C < O) if side > 0 else (C > O)
    j = leg_i
    while j >= 0 and not bad[j] and leg_i - j < 3:
        j -= 1
    if j < 0 or not bad[j]:
        return None
    k = j
    while k - 1 >= 0 and bad[k - 1] and j - (k - 1) < 3:
        k -= 1
    return float(L[k:j + 1].min()), float(H[k:j + 1].max())


def htf_setups(m1: pd.DataFrame, cfg: Cfg) -> list[Setup]:
    b = resample(m1, cfg.htf)
    O, H, L, C = (b[c].to_numpy() for c in ("open", "high", "low", "close"))
    end = pd.DatetimeIndex(b["end"])
    ph, pl = pivots(H, L, 1)
    n = len(b)
    out: list[Setup] = []
    sh = sl = None                  # last confirmed swing (price, idx) not yet broken
    pend = {1: None, -1: None}      # MSB waiting for its post-break swing
    for j in range(n):
        p = j - 1
        if p >= 1:
            if ph[p]:
                sh = (H[p], p)
                for side in (1,):
                    pe = pend[1]
                    if pe is not None and p >= pe["msb_i"]:
                        ob = pe["ob"]
                        out.append(Setup(1, pe["lo"], H[p], ob[0], ob[1], end[j],
                                         end[min(n - 1, j + cfg.expiry_bars)], pe["msb_i"]))
                        pend[1] = None
            if pl[p]:
                sl = (L[p], p)
                pe = pend[-1]
                if pe is not None and p >= pe["msb_i"]:
                    ob = pe["ob"]
                    out.append(Setup(-1, pe["lo"], L[p], ob[0], ob[1], end[j],
                                     end[min(n - 1, j + cfg.expiry_bars)], pe["msb_i"]))
                    pend[-1] = None
        if sh is not None and C[j] > sh[0]:          # bullish MSB by close
            seg = slice(sh[1], j + 1)
            leg_i = sh[1] + int(np.argmin(L[seg]))
            ob = _ob(O, C, H, L, leg_i, 1)
            if ob is not None:
                pend[1] = dict(msb_i=j, lo=float(L[leg_i]), ob=ob)
            sh = None
        if sl is not None and C[j] < sl[0]:          # bearish MSB by close
            seg = slice(sl[1], j + 1)
            leg_i = sl[1] + int(np.argmax(H[seg]))
            ob = _ob(O, C, H, L, leg_i, -1)
            if ob is not None:
                pend[-1] = dict(msb_i=j, lo=float(H[leg_i]), ob=ob)
            sl = None
    return out


def generate(m1: pd.DataFrame, cfg: Cfg) -> list[Order]:
    setups = htf_setups(m1, cfg)
    b = resample(m1, cfg.ltf)
    H, L, C = (b[c].to_numpy() for c in ("high", "low", "close"))
    end = pd.DatetimeIndex(b["end"])
    ends_ns = end.as_unit("ns").asi8
    ph, pl = pivots(H, L, 1)
    orders: list[Order] = []
    for s in setups:
        mid = (s.lo + s.hi) / 2.0
        j0 = int(np.searchsorted(ends_ns, s.t_active.value, side="right"))
        j1 = int(np.searchsorted(ends_ns, s.t_expire.value, side="right"))
        meta = dict(range_lo=s.lo, range_hi=s.hi, ob_lo=s.ob_lo, ob_hi=s.ob_hi, msb_i=s.msb_i)
        if cfg.entry == "ob_limit":
            px = s.ob_hi if s.side > 0 else s.ob_lo
            stop = s.ob_lo - cfg.tick if s.side > 0 else s.ob_hi + cfg.tick
            if abs(s.hi - px) < cfg.min_rr * abs(px - stop):
                continue
            if (s.side > 0 and px > mid) or (s.side < 0 and px < mid):
                continue
            orders.append(Order(s.side, s.t_active, "limit", stop=stop, entry_px=px, targets=[(s.hi, 1.0)],
                                expiry=s.t_expire, be_level=px + s.side * 2 * abs(px - stop),
                                tag=cfg.name, meta=meta))
            continue
        touched = False
        lows: list = []      # confirmed LTF swings of the counter direction (long: swing lows) with generating highs
        last_gen = None
        for j in range(j0, min(j1, len(b))):
            # invalidation: close beyond the HTF range extreme or external target taken before entry
            if (s.side > 0 and (C[j] < s.lo or H[j] >= s.hi)) or (s.side < 0 and (C[j] > s.lo or L[j] <= s.hi)):
                break
            if not touched and ((s.side > 0 and L[j] <= s.ob_hi) or (s.side < 0 and H[j] >= s.ob_lo)):
                touched = True
            p = j - 1
            if p >= 1 and p >= j0:
                if s.side > 0 and ph[p]:
                    last_gen = H[p]
                if s.side < 0 and pl[p]:
                    last_gen = L[p]
                if touched and s.side > 0 and pl[p] and last_gen is not None:
                    lows.append(dict(px=L[p], gen=last_gen, swept=False, ext=L[p]))
                if touched and s.side < 0 and ph[p] and last_gen is not None:
                    lows.append(dict(px=H[p], gen=last_gen, swept=False, ext=H[p]))
            fired = False
            for w in lows:
                if s.side > 0:
                    if not w["swept"] and L[j] < w["px"]:
                        w["swept"] = True
                    if w["swept"]:
                        w["ext"] = min(w["ext"], L[j])
                        if C[j] > w["gen"]:
                            fired = True
                else:
                    if not w["swept"] and H[j] > w["px"]:
                        w["swept"] = True
                    if w["swept"]:
                        w["ext"] = max(w["ext"], H[j])
                        if C[j] < w["gen"]:
                            fired = True
                if fired:
                    entry = C[j]
                    stop = w["ext"] - cfg.tick if s.side > 0 else w["ext"] + cfg.tick
                    risk = abs(entry - stop)
                    in_disc = (entry <= mid) if s.side > 0 else (entry >= mid)
                    if risk > 0 and abs(s.hi - entry) >= cfg.min_rr * risk and in_disc:
                        orders.append(Order(s.side, end[j], "close_at", stop=stop, targets=[(s.hi, 1.0)],
                                            be_level=entry + s.side * 2 * risk, tag=cfg.name,
                                            meta=dict(meta, sweep_low=w["ext"], gen_high=w["gen"])))
                    break
            if fired:
                break
    return orders


CONFIGS = [
    Cfg("B1_H4_M15_breaker", htf="4h", ltf="15min"),
    Cfg("B2_H1_M5_breaker", htf="1h", ltf="5min"),
    Cfg("B3_D_H1_breaker", htf="1D", ltf="1h"),
    Cfg("B4_H4_OB_limit", htf="4h", entry="ob_limit"),
]
