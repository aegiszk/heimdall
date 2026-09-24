"""Family E - TG Capital "Trident" (ADnslyKOwFE). USD majors + XAUUSD, 30-minute chart only, London kill zone.

Recovered source rules (creator transcript; timestamps in SOURCE_MATRIX.md):
- trade only 03:00-06:30 New York time; one timeframe: 30-minute; daily for context/TP            [02:47-03:42]
- 5 / 9 / 13 (or 15 - "I don't really remember") / 21 EMAs stacking; intertwining = skip            [05:31-06:24, 32:57]
- above the 200 EMA = long bias; below = look for shorts                                             [33:54]
- a fair value gap printed around 03:00 (2:30 / 3:00 / 3:30 strongest; one example at 4:00);
  "FVG printed outside of our kill zone - ignore"                                                    [06:24-07:19, 33:54-34:54, 41:08]
- a doji whose wick goes through the FVG 50% (consequent encroachment); body NOT inside the FVG      [07:19, 09:06-10:01]
- next candle must close BELOW the doji high (closing above = invalidation)                         [07:19, 42:06-43:00]
- enter (limit or at close), stop below the candle low (~10 pips; 8.4-9 pip examples)               [07:19-08:11, 43:00]
- minimum 1:20 R:R; ride the trend until the EMAs cross / a large bearish candle                    [12:41, 19:39-20:30]
- gold: no hard stop - exit on a candle close below                                                 [12:41-13:34]
- pairs: USDCAD, NZDUSD, EURUSD, GBPUSD, USDJPY (not AUDUSD) + gold; ~6-8 entries/yr/pair, gold 10-15 [08:11, 27:38]
- long-biased; shorts taken but not described                                                        [03:42, 05:31]

Mechanization (RESEARCH_ASSUMPTION in PREREGISTRATION.md): 30m bars on the ET wall clock; FVG = 3-candle
bullish gap with the MIDDLE candle opening inside the allowed window; doji = |close-open| <= 0.25*(high-low),
low below the FVG midpoint, open and close both >= FVG top; confirmation = next bar closes < doji high; all
of doji+confirmation inside 03:00-06:30; EMA stack 5>9>13>21 and close > EMA200 at the confirmation close;
entry at the confirmation close; stop = doji low - 1 pip (FX); XAU exits on a 30m close below the doji low
(plus a catastrophic hard stop 3x the doji range below, labelled); exits: fixed 20R target or EMA5<EMA21 close.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from harness import Order, ema, fvgs, resample  # noqa: E402


@dataclass(frozen=True)
class Cfg:
    name: str
    fvg_from: str = "03:00"      # earliest ET start of the FVG middle candle
    exit: str = "20R"            # '20R' | 'ema_cross'
    side: int = 1
    doji_body: float = 0.25
    max_hold_days: int = 10


def _t(s):
    h, m = s.split(":")
    return pd.Timedelta(hours=int(h), minutes=int(m))


def generate(m1: pd.DataFrame, cfg: Cfg, pair: str, pip: float) -> list[Order]:
    b = resample(m1, "30min")
    O, H, L, C = (b[c].to_numpy() for c in ("open", "high", "low", "close"))
    key = pd.DatetimeIndex(b["key"])
    end = pd.DatetimeIndex(b["end"])
    ends_ns = end.as_unit("ns").asi8
    e5, e9, e13, e21, e200 = (ema(C, n) for n in (5, 9, 13, 21, 200))
    s = cfg.side
    if s > 0:
        bull, _ = fvgs(H, L)
        stack = (e5 > e9) & (e9 > e13) & (e13 > e21) & (C > e200)
        cross = e5 < e21
    else:
        _, bull = fvgs(H, L)
        stack = (e5 < e9) & (e9 < e13) & (e13 < e21) & (C < e200)
        cross = e5 > e21
    tod = key - key.normalize()
    lo_t, kz0, kz1 = _t(cfg.fvg_from), _t("03:00"), _t("06:30")
    in_kz = (tod >= kz0) & (tod < kz1)
    orders: list[Order] = []
    n = len(C)
    for i in np.flatnonzero(bull):
        mid_c = i - 1
        if not (lo_t <= tod[mid_c] < kz1):
            continue
        if key[i] - key[i - 2] != pd.Timedelta(hours=1):   # three consecutive 30m bars (no data gap)
            continue
        top, bot = (L[i], H[i - 2]) if s > 0 else (L[i - 2], H[i])
        if s > 0:
            ce = (H[i - 2] + L[i]) / 2
        else:
            ce = (L[i - 2] + H[i]) / 2
        for d in range(i + 1, min(n - 1, i + 8)):
            if not in_kz[d] or not in_kz[d + 1]:
                break
            rng = H[d] - L[d]
            if rng <= 0:
                continue
            body_ok = abs(C[d] - O[d]) <= cfg.doji_body * rng
            if s > 0:
                wick = L[d] < ce and min(O[d], C[d]) >= L[i]
                conf = C[d + 1] < H[d]
                broke = L[d] < H[i - 2]          # traded through the whole gap -> FVG failed
            else:
                wick = H[d] > ce and max(O[d], C[d]) <= H[i]
                conf = C[d + 1] > L[d]
                broke = H[d] > L[i - 2]
            if broke:
                break
            if not (body_ok and wick):
                continue
            if not conf:
                break                              # the doji's next candle invalidated the setup
            jc = d + 1
            if not stack[jc]:
                break
            entry_ref = C[jc]
            if pair == "XAUUSD":
                stop_h = (L[d] - 3 * rng) if s > 0 else (H[d] + 3 * rng)   # catastrophic stop (assumption)
                risk_ref = abs(entry_ref - (L[d] if s > 0 else H[d]))
                close_stop = (C < L[d]) if s > 0 else (C > H[d])
                evs = [(ends_ns, close_stop.copy(), "exit")]
            else:
                stop_h = (L[d] - pip) if s > 0 else (H[d] + pip)
                risk_ref = abs(entry_ref - stop_h)
                evs = []
            if risk_ref <= 0:
                break
            tg = []
            if cfg.exit == "20R":
                tg = [(entry_ref + s * 20 * risk_ref, 1.0)]
            else:
                evs = evs + [(ends_ns, cross.copy(), "exit")]
            for _, arr, _a in evs:
                arr[: jc + 1] = False
            orders.append(Order(s, end[jc], "close_at", stop=stop_h, targets=tg, close_events=evs,
                                flatten=end[jc] + pd.Timedelta(days=cfg.max_hold_days), tag=cfg.name,
                                meta=dict(pair=pair, fvg_i=int(i), doji_i=int(d), fvg_top=float(top),
                                          fvg_bot=float(bot), ce=float(ce), doji_low=float(L[d]),
                                          doji_high=float(H[d]), risk_override=float(risk_ref))))
            break
    return orders


CONFIGS = [
    Cfg("E1_long_kz0300_20R"),
    Cfg("E2_long_kz0300_emacross", exit="ema_cross"),
    Cfg("E3_long_fvg0230_20R", fvg_from="02:30"),
    Cfg("E4_short_mirror_20R", side=-1),
]
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "NZDUSD", "XAUUSD"]
