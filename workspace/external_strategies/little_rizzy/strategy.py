"""Family D - "Little Rizzy" trendline measured move (AVVM-FyewLg).

Recovered source rules (auto-generated transcript; timestamps in SOURCE_MATRIX.md):
- establish the trend; wait for the initial drop and the bounce; draw the descending trend line     [15:04-15:52, ~22:00]
- find the candle with the lowest low in the pattern, measure straight up to the trend line;
  the next move down is that same distance below the low                                          [08:54-09:34, 13:13]
- exit for a loss on an actual candle CLOSE through the trend line; always apply a max loss        [14:02, 29:08-30:07]
- first one or two patterns work best; 4th/5th = market getting tired                             [14:25-14:39]
- Bollinger (2 std) middle line = "reality"; a close below the middle band is an entry example     [10:53, 1:11:34]
- uptrend version: same inverse pattern, measure from the highest-high candle, project above      [05:40, 23:57-24:22]
- prefers longer time frames; works on any                                                         [~11:30]

Mechanization: pivots with k=2 on the signal timeframe (24h data). Short pattern = two consecutive confirmed
pivot highs P1 > P2; L = lowest low strictly between them; TL through (P1,P2); D = TL(L) - low(L) > 0;
target = low(L) - D. Entry at market when P2 is confirmed (bar P2+k close) if that close is below TL and above
low(L) ('pivot' entry) or at the first close below the BB(20,2) middle within 5 bars after confirmation ('bb'
entry). Hard max-loss stop = P2 high + 1 tick; loss exit = first signal-TF close above TL. Pattern count: a
pattern whose P1 is the previous pattern's P2 increments the count; only counts 1-2 are traded.
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
    tf: str = "1h"
    entry: str = "pivot"   # 'pivot' | 'bb'
    side: int = -1         # -1 = downtrend continuation short (F); +1 = uptrend continuation long (G)
    k: int = 2
    max_count: int = 2


def generate(m1: pd.DataFrame, cfg: Cfg, tick: float) -> list[Order]:
    b = resample(m1, cfg.tf)
    H, L, C = (b[c].to_numpy() for c in ("high", "low", "close"))
    end = pd.DatetimeIndex(b["end"])
    ends_ns = end.as_unit("ns").asi8
    ph, pl = pivots(H, L, cfg.k)
    mid = pd.Series(C).rolling(20).mean().to_numpy()
    s = cfg.side
    # mirror: for longs operate on negated prices
    hi = H if s < 0 else -L
    lo = L if s < 0 else -H
    cl = C if s < 0 else -C
    md = mid if s < 0 else -mid
    piv = np.flatnonzero(ph if s < 0 else pl)
    orders: list[Order] = []
    prev_p2 = None
    count = 0
    for a, b_ in zip(piv[:-1], piv[1:]):
        p1, p2 = int(a), int(b_)
        if not hi[p2] < hi[p1] or p2 - p1 < 2:
            prev_p2 = None
            count = 0
            continue
        count = count + 1 if prev_p2 == p1 else 1
        prev_p2 = p2
        seg = np.arange(p1 + 1, p2)
        li = int(seg[np.argmin(lo[seg])])
        slope = (hi[p2] - hi[p1]) / (p2 - p1)
        tl = lambda t: hi[p1] + slope * (t - p1)  # noqa: E731
        D = tl(li) - lo[li]
        if D <= 0 or count > cfg.max_count:
            continue
        target = lo[li] - D
        jc = p2 + cfg.k                       # confirmation bar
        if jc >= len(C):
            break
        je = None
        if cfg.entry == "pivot":
            if lo[li] < cl[jc] < tl(jc):
                je = jc
        else:
            for j in range(jc, min(len(C), jc + 6)):
                if cl[j] >= tl(j) or cl[j] <= lo[li]:
                    break
                if np.isfinite(md[j]) and cl[j] < md[j] and (j == jc or cl[j - 1] >= md[j - 1]):
                    je = j
                    break
        if je is None:
            continue
        stop_m = hi[p2] + tick
        # loss exit: first close above TL after entry (known at bar end)
        tl_arr = hi[p1] + slope * (np.arange(len(C)) - p1)
        cond = cl > tl_arr
        cond[: je + 1] = False
        to_px = (lambda x: x) if s < 0 else (lambda x: -x)
        orders.append(Order(s, end[je], "close_at", stop=to_px(stop_m), targets=[(to_px(target), 1.0)],
                            close_events=[(ends_ns, cond, "exit")], tag=cfg.name,
                            meta=dict(p1=to_px(hi[p1]), p2=to_px(hi[p2]), low=to_px(lo[li]), D=D,
                                      count=count, target=to_px(target))))
    return orders


CONFIGS = [
    Cfg("D1_F_short_1h_pivot", tf="1h"),
    Cfg("D2_F_short_4h_pivot", tf="4h"),
    Cfg("D3_F_short_1h_bb", tf="1h", entry="bb"),
    Cfg("D4_G_long_1h_pivot", tf="1h", side=1),
]
