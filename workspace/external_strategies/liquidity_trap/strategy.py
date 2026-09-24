"""Family A - Liquidity-trap reversal (DAnXM7C16h0, Marco). Mechanized interpretation; see SOURCE_MATRIX.md and
PREREGISTRATION.md. Signals are built on 5-minute bars from 24h data; fills are resolved on 1-minute bars.

Short setup (long is the exact mirror):
  1. Anchor high A: a confirmed swing high whose own bars [p-k, p] traded above an OLDER, already-confirmed,
     untaken swing high (source: "we have spiked out a high ... there shouldn't be any liquidity above this high").
  2. Internal high H: a confirmed swing high formed after A with H < A, still untaken ("liquidity").
  3. Trigger: price trades above H while A is intact -> sell ("as soon as the high is spiked out").
  4. Stop: A + 2 ticks ("a tick or two above the high", "my stop covers this high on the left").
  5. Target: nearest untaken confirmed swing low below H at order time ("targeting opposing liquidity").
  6. Entries only 09:30-11:30 ET, flat by 12:00 ET ("entries after the open", "out before lunch").
Swings/lookback: pivots on 5m bars (k each side) formed during the current or the previous session day.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from harness import ET, Order, pivots, resample  # noqa: E402


@dataclass(frozen=True)
class Cfg:
    name: str
    k: int = 1                 # pivot half-width
    entry: str = "spike"       # 'spike' = resting SELL limit 1 tick above H (BUY limit below L): fills when price
    #                            trades through the level ("as soon as the high is spiked out"). BUGFIX 2026-09-24:
    #                            first run used a harness 'stop' order, which for shorts triggers on price FALLING to
    #                            the level -> 98.8% of fills were on the wrong side (see _program/BUGFIX_A_ENTRY.md)
    # 'close' = 5m bar spikes beyond H and closes back
    targets: str = "nearest"   # 'nearest' | 'split' (50% nearest, 50% second-nearest, BE after first)
    tick: float = 0.25
    stop_ticks: int = 2
    win_open: str = "09:30"
    win_close: str = "11:30"
    flat: str = "12:00"


@dataclass
class Swing:
    price: float
    i: int
    day: np.datetime64
    anchor: bool = False
    taken_at: int | None = None


def _hm(s: str) -> pd.Timedelta:
    h, m = s.split(":")
    return pd.Timedelta(hours=int(h), minutes=int(m))


def _utc(naive_et: pd.Timestamp) -> pd.Timestamp:
    return naive_et.tz_localize(ET).tz_convert("UTC")


def generate(m1: pd.DataFrame, cfg: Cfg) -> list[Order]:
    b = resample(m1, "5min")
    H, L, C = b["high"].to_numpy(), b["low"].to_numpy(), b["close"].to_numpy()
    ph, pl = pivots(H, L, cfg.k)
    end = pd.DatetimeIndex(b["end"])
    key = pd.DatetimeIndex(b["key"])
    sday = (key + pd.Timedelta(hours=6)).normalize().to_numpy()
    udays = np.unique(sday)
    prev_of = {udays[i]: udays[i - 1] for i in range(1, len(udays))}
    highs: list[Swing] = []
    lows: list[Swing] = []
    orders: list[Order] = []
    placed: set = set()
    n = len(b)
    for j in range(n):
        # (a) swings taken by bar j (only swings already confirmed before bar j)
        for s in highs:
            if s.taken_at is None and H[j] > s.price:
                s.taken_at = j
        for s in lows:
            if s.taken_at is None and L[j] < s.price:
                s.taken_at = j
        # (b) pivot at p = j-k becomes known at the close of bar j
        p = j - cfg.k
        if p >= cfg.k:
            if ph[p]:
                a = any(s.taken_at is not None and p - cfg.k <= s.taken_at <= p and s.i < p for s in highs)
                highs.append(Swing(H[p], p, sday[p], anchor=a))
            if pl[p]:
                a = any(s.taken_at is not None and p - cfg.k <= s.taken_at <= p and s.i < p for s in lows)
                lows.append(Swing(L[p], p, sday[p], anchor=a))
        cur = sday[j]
        ok_days = {cur, prev_of.get(cur, cur)}
        highs = [s for s in highs if s.day in ok_days or s.day > cur]
        lows = [s for s in lows if s.day in ok_days or s.day > cur]
        # (c) decisions at the close of bar j
        et_dec = end[j].tz_convert(ET).tz_localize(None)
        d0 = et_dec.normalize()
        w_open, w_close, flat = d0 + _hm(cfg.win_open), d0 + _hm(cfg.win_close), d0 + _hm(cfg.flat)
        if not (w_open - pd.Timedelta(minutes=5) <= et_dec < w_close):
            continue
        for side, same, opp_book in ((-1, highs, lows), (1, lows, highs)):
            live = [s for s in same if s.taken_at is None]
            for a in (s for s in live if s.anchor):
                for h in live:
                    if h.i <= a.i or not ((h.price < a.price) if side < 0 else (h.price > a.price)):
                        continue
                    k_ = (side, a.i, h.i)
                    if k_ in placed:
                        continue
                    opp = [s for s in opp_book if s.taken_at is None
                           and ((s.price < h.price) if side < 0 else (s.price > h.price))]
                    if not opp:
                        continue
                    placed.add(k_)
                    opp.sort(key=lambda s: abs(s.price - h.price))
                    tick = cfg.tick
                    trig = h.price + tick if side < 0 else h.price - tick
                    stop = a.price + cfg.stop_ticks * tick if side < 0 else a.price - cfg.stop_ticks * tick
                    tg = ([(opp[0].price, 0.5), (opp[1].price, 0.5)] if cfg.targets == "split" and len(opp) >= 2
                          else [(opp[0].price, 1.0)])
                    t_place = max(end[j], _utc(w_open))
                    meta = dict(anchor=a.price, internal=h.price, anchor_i=a.i, internal_i=h.i,
                                tgt1=opp[0].price, day=str(pd.Timestamp(cur).date()))
                    od = Order(side, t_place, "limit", stop=stop, entry_px=trig, targets=tg,
                               expiry=_utc(w_close), flatten=_utc(flat),
                               be_after_first_target=(cfg.targets == "split"), tag=cfg.name, meta=meta)
                    if cfg.entry == "close":
                        od = _close_confirm(od, h.price, H, L, C, end, j)
                        if od is None:
                            continue
                    orders.append(od)
    return orders


def _close_confirm(od: Order, lvl: float, H, L, C, end: pd.DatetimeIndex, j0: int) -> Order | None:
    """First 5m bar after placement that trades beyond the internal level and CLOSES back on the entry side ->
    enter at that bar's close. Cancelled if the stop level is breached first or the entry window ends."""
    for j in range(j0 + 1, len(H)):
        if end[j] > od.expiry:
            return None
        if od.side < 0:
            if H[j] >= od.stop:
                return None
            if H[j] > lvl:            # first bar that spikes the level must close back below it
                if C[j] < lvl:
                    break
                return None
        else:
            if L[j] <= od.stop:
                return None
            if L[j] < lvl:
                if C[j] > lvl:
                    break
                return None
    else:
        return None
    return Order(od.side, end[j], "close_at", stop=od.stop, targets=od.targets, flatten=od.flatten,
                 be_after_first_target=od.be_after_first_target, tag=od.tag, meta=dict(od.meta, confirm_bar=j))


CONFIGS = [
    Cfg("A1_k1_spike_nearest", k=1),
    Cfg("A2_k2_spike_nearest", k=2),
    Cfg("A3_k1_spike_split", k=1, targets="split"),
    Cfg("A4_k1_close_nearest", k=1, entry="close"),
]
