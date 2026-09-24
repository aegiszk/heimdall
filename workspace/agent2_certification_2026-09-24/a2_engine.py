"""Agent 2 independent research engine (certification of the EXT8 program @ 8f70789).

Written from the preregistration text (common protocol + family tables), NOT from Agent 1's code.
Imports nothing from workspace/external_strategies. Only pandas/numpy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ET = "America/New_York"
MIN = 60_000_000_000


# ------------------------------------------------------------------ data (prereg: Panama at instrument_id change)
def load_cme(name: str) -> pd.DataFrame:
    d = pd.read_parquet(ROOT / "data" / f"{name}_1m.parquet")
    assert d.index.min() >= pd.Timestamp("2024-07-01", tz="UTC")  # Dhesi firewall
    d = d[~d.index.duplicated(keep="first")].sort_index()
    iid = d["instrument_id"].to_numpy()
    rolls = np.flatnonzero(iid[1:] != iid[:-1]) + 1
    adj = np.zeros(len(d))
    for r in rolls:
        adj[:r] += d["open"].iat[r] - d["close"].iat[r - 1]
    out = d[["open", "high", "low", "close"]].astype(float).copy()
    for c in out.columns:
        out[c] = out[c].to_numpy() + adj
    return out


def bars(m1: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """ET wall-clock bins; `end` = last present minute + 1 min (first instant the bar is known)."""
    et = m1.index.tz_convert(ET).tz_localize(None)
    key = et.floor(f"{minutes}min")
    g = m1.assign(k=key, t=m1.index).groupby("k", sort=True)
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "end": g["t"].max() + pd.Timedelta(minutes=1)})
    b["key"] = b.index
    return b.reset_index(drop=True)


# ------------------------------------------------------------------ fills (prereg common protocol, own code)
@dataclass
class Spec:
    tick: float
    pv: float
    comm: float
    slip: float
    spread: float = 0.0      # FX/XAU: bars are BID, ask = bid + spread


MNQ = Spec(0.25, 2.0, 1.0, 0.25)
ES = Spec(0.25, 50.0, 3.5, 0.25)
XAU = Spec(0.01, 100.0, 7.0, 0.05, 0.20)


@dataclass
class Ord:
    side: int
    t0: pd.Timestamp          # first minute (start >= t0) the order may act
    kind: str                 # 'limit' | 'trigger' (price reaches P -> market, 1 tick adverse) | 'close_at'
    P: float | None
    stop: float
    targets: list
    expiry: pd.Timestamp | None
    flat: pd.Timestamp | None
    be_after_first: bool = False
    meta: dict = field(default_factory=dict)
    exit_ends: object = None   # sorted int64 ns bar-end times at which a close-exit condition is true
    be_level: float | None = None   # intrabar touch -> stop moves to entry from the next minute


class Tape:
    def __init__(self, m1: pd.DataFrame, spec: Spec):
        self.t = m1.index.as_unit("ns").asi8
        self.ix = m1.index
        self.o, self.h, self.l, self.c = (m1[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        self.s = spec

    def at(self, ts: pd.Timestamp) -> int:
        return int(np.searchsorted(self.t, ts.value))


def fill(tp: Tape, od: Ord, max_min: int = 60 * 24 * 12):
    s, side = tp.s, od.side
    i = tp.at(od.t0)
    n = len(tp.t)
    if i >= n:
        return None
    last = min(n - 1, i + max_min)
    if od.kind == "close_at":
        ie = i - 1
        if ie < 0 or tp.t[ie] + MIN != od.t0.value:
            return None
        px = tp.c[ie] + (s.spread if side > 0 else 0.0) + side * s.slip
        j0 = i
    else:
        ex = tp.at(od.expiry) if od.expiry is not None else last + 1
        ie = None
        for j in range(i, min(ex, last + 1)):
            o, h, lo = tp.o[j], tp.h[j], tp.l[j]
            if od.kind == "limit":        # need 1-tick trade-through
                if side < 0 and h >= od.P + s.tick:
                    ie, px = j, max(od.P, o)
                elif side > 0 and lo <= od.P - s.tick:
                    ie, px = j, min(od.P, o)
            else:                         # 'trigger': price reaches P, market fill 1 tick adverse
                if side < 0 and h >= od.P:
                    ie, px = j, max(od.P, o) - s.slip
                elif side > 0 and lo <= od.P:
                    ie, px = j, min(od.P, o) + s.slip
            if ie is not None:
                break
            if (side < 0 and h >= od.stop) or (side > 0 and lo <= od.stop):
                return None               # stop level traded first -> cancel
        if ie is None:
            return None
        j0 = ie
    if side * (px - od.stop) <= 0:
        return None
    risk = abs(px - od.stop)
    stop, rem, acc = od.stop, 1.0, 0.0
    tg = sorted(od.targets, key=lambda x: side * x[0])
    fl = tp.at(od.flat) if od.flat is not None else None
    be = False
    why, jx = "max_hold", None
    j = j0
    while j <= last:
        o, h, lo, c = tp.o[j], tp.h[j], tp.l[j], tp.c[j]
        if fl is not None and j >= fl and j > ie:
            acc += rem * (o - s.slip if side > 0 else o + s.spread + s.slip); rem, why, jx = 0.0, "time", j
            break
        if (side < 0 and h + s.spread >= stop) or (side > 0 and lo <= stop):
            f = stop if j == ie else (max(stop, o + s.spread) if side < 0 else min(stop, o))
            acc += rem * (f - side * s.slip); rem, jx = 0.0, j
            why = "be" if be and stop == px else "stop"
            break
        if j > ie:
            while tg and rem > 1e-12:
                P, q = tg[0]
                thr = 0.0 if s.spread else s.tick   # futures limits need 1-tick trade-through; FX none
                if not ((side > 0 and h >= P + thr) or (side < 0 and lo + s.spread <= P - thr)):
                    break
                q = min(q, rem)
                acc += q * (max(P, o) if side > 0 else min(P, o + s.spread)); rem -= q; tg.pop(0)
                if od.be_after_first and not be:
                    stop, be = px, True
            if rem <= 1e-12:
                why, jx = "target", j
                break
            if od.be_level is not None and not be and ((side > 0 and h >= od.be_level) or (side < 0 and lo + s.spread <= od.be_level)):
                stop, be = px, True
            if od.exit_ends is not None:
                te = tp.t[j] + MIN
                k_ = np.searchsorted(od.exit_ends, te)
                if k_ < len(od.exit_ends) and od.exit_ends[k_] == te:
                    acc += rem * (c - s.slip if side > 0 else c + s.spread + s.slip); rem, why, jx = 0.0, "close_exit", j
                    break
        j += 1
    if rem > 1e-12:
        jx = min(j, last)
        acc += rem * (tp.c[jx] - s.slip if side > 0 else tp.c[jx] + s.spread + s.slip)
    net = side * (acc - px) - s.comm / s.pv
    return dict(side=side, t_entry=tp.ix[ie], entry=px, stop0=od.stop, t_exit=tp.ix[jx], reason=why,
                net_px=net, R=net / risk, **od.meta)


def sequence(tp: Tape, orders: list[Ord]) -> pd.DataFrame:
    sims = [x for x in (fill(tp, od) for od in orders) if x is not None]
    sims.sort(key=lambda x: (x["t_entry"], x["t_signal"]))
    out, busy = [], None
    for x in sims:
        if busy is not None and x["t_entry"] < busy:
            continue
        out.append(x)
        busy = x["t_exit"] + pd.Timedelta(minutes=1)
    return pd.DataFrame(out)


def strict_pivots(H, L, k):
    n = len(H)
    ph = np.zeros(n, bool); pl = np.zeros(n, bool)
    for i in range(k, n - k):
        nb = list(range(i - k, i)) + list(range(i + 1, i + k + 1))
        ph[i] = all(H[i] > H[x] for x in nb)
        pl[i] = all(L[i] < L[x] for x in nb)
    return ph, pl


def cluster_ci(df: pd.DataFrame, B: int = 5000, seed: int = 7):
    """Date-clustered bootstrap 95% CI of mean R (own implementation)."""
    d = pd.to_datetime(df["t_entry"]).dt.tz_convert(ET).dt.date
    g = df.groupby(d.values)["R"].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), size=(B, len(s)))
    m = s[idx].sum(1) / c[idx].sum(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))
