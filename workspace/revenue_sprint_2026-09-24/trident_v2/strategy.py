"""TRIDENT_V2 — one canonical source-faithful LONG model (ADnslyKOwFE). See TRIDENT_V2_SOURCE_SPEC.md.

Changes vs V1 (E1-E4), each tied to a source quote in the spec:
- EMA200 is CONTEXT only (recorded, never gates)            [0:41:08 takes longs below EMA200, exits earlier]
- 5/9/13/21 EMA stack gate = `stack_gate` (frozen value set in the preregistration after the Agent-2 adjudication)
- FVG counts if its THIRD candle forms inside 03:00-06:30 ET [0:02:47 window; 0:06:24 & 0:33:54 "2:30 / 3:00 strongest",
                                                             "printed outside of our kill zone -> ignore"]
- exit = ride until a 30m close with EMA5 < EMA21              [0:19:39 "ride the trend until like the EMAs cross over"]
- one model only (no E1-E4 lattice); long only.
Unchanged from V1: doji geometry, next-candle-below-doji-high confirmation, entry at confirmation close, stop below the doji
low (1 pip), XAU close-based stop (+ catastrophic 3x doji-range stop), max hold 10 days, harness cost model.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "external_strategies" / "common"))
from harness import Order, ema, fvgs, resample  # noqa: E402


@dataclass(frozen=True)
class Cfg:
    name: str = "TRIDENT_V2"
    stack_gate: bool = True          # FROZEN in TRIDENT_V2_PREREGISTRATION.md
    doji_body: float = 0.25
    max_hold_days: int = 10
    kz_start: str = "03:00"
    kz_end: str = "06:30"


def _t(s: str) -> pd.Timedelta:
    h, m = s.split(":")
    return pd.Timedelta(hours=int(h), minutes=int(m))


def generate(m1: pd.DataFrame, cfg: Cfg, pair: str, pip: float) -> list[Order]:
    b = resample(m1, "30min")
    O, H, L, C = (b[c].to_numpy() for c in ("open", "high", "low", "close"))
    key = pd.DatetimeIndex(b["key"])
    end = pd.DatetimeIndex(b["end"])
    ends_ns = end.as_unit("ns").asi8
    e5, e9, e13, e21, e200 = (ema(C, n) for n in (5, 9, 13, 21, 200))
    stack = (e5 > e9) & (e9 > e13) & (e13 > e21)
    cross_exit = e5 < e21
    bull, _ = fvgs(H, L)
    tod = key - key.normalize()
    kz0, kz1 = _t(cfg.kz_start), _t(cfg.kz_end)
    in_kz = (tod >= kz0) & (tod < kz1)
    n = len(C)
    orders: list[Order] = []
    for i in np.flatnonzero(bull):
        if not in_kz[i]:                                         # third candle must form inside the kill zone
            continue
        if key[i] - key[i - 2] != pd.Timedelta(hours=1):          # three consecutive 30m bars
            continue
        bot, top = H[i - 2], L[i]
        ce = (bot + top) / 2.0
        for d in range(i + 1, min(n - 1, i + 8)):
            if not in_kz[d] or not in_kz[d + 1]:
                break
            if L[d] < bot:                                        # gap fully traded through -> FVG failed
                break
            rng = H[d] - L[d]
            if rng <= 0:
                continue
            doji = abs(C[d] - O[d]) <= cfg.doji_body * rng and L[d] < ce and min(O[d], C[d]) >= top
            if not doji:
                continue
            if not C[d + 1] < H[d]:                               # next candle closing above doji high invalidates
                break
            jc = d + 1
            if cfg.stack_gate and not stack[jc]:
                break
            entry_ref = C[jc]
            if pair == "XAUUSD":
                stop = L[d] - 3 * rng                             # catastrophic stop (declared assumption)
                risk_ref = abs(entry_ref - L[d])
                evs = [(ends_ns, (C < L[d]).copy(), "exit")]      # gold: close below the doji low
            else:
                stop = L[d] - pip
                risk_ref = abs(entry_ref - stop)
                evs = []
            if risk_ref <= 0:
                break
            evs.append((ends_ns, cross_exit.copy(), "exit"))
            for _, arr, _a in evs:
                arr[: jc + 1] = False
            orders.append(Order(1, end[jc], "close_at", stop=stop, targets=[], close_events=evs,
                                flatten=end[jc] + pd.Timedelta(days=cfg.max_hold_days), tag=cfg.name,
                                meta=dict(pair=pair, fvg_i=int(i), doji_i=int(d), fvg_top=float(top), fvg_bot=float(bot),
                                          ce=float(ce), doji_low=float(L[d]), doji_high=float(H[d]),
                                          ctx_ema_stack=bool(stack[jc]), ctx_above_ema200=bool(C[jc] > e200[jc]),
                                          risk_override=float(risk_ref))))
            break
    return orders


PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "NZDUSD", "XAUUSD"]
