"""Shared research harness for the external 8-strategy program (workspace-only; NOT part of /core money path).

Contents
- Instrument specs and cost models (futures: trade prices, tick slippage, commission; FX/XAU: bid bars + modelled
  spread + commission + slippage).
- Data loaders: Databento continuous 1m (Panama back-adjusted at instrument_id changes), Sierra 90d, HistData FX.
- ET-anchored resampling (4H bins start 18:00 ET; 1H on the hour; D = 18:00 ET session day). Every resampled bar
  carries `end` (UTC, exclusive) = the first moment its information is known. Strategies may only act at >= end.
- Fill/cost engine `simulate()` on 1-minute bars: market / stop / limit entries, hard stop, 1..n targets,
  intrabar break-even trigger, close-event exits/BE on higher-timeframe closes, time flatten. Conservative
  same-bar semantics: stop beats target in the same minute; no target credit in the entry minute; an entry
  minute that also touches the stop is stopped.
- Position sequencing (one position at a time per instrument/interpretation).

DATA FIREWALL: nothing here reads NQ/MNQ/ES/MES history before 2024-07-01 (Dhesi V3 reserved window). The
Databento files on disk start 2024-07-01; `load_futures` asserts this.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
ET = "America/New_York"
FIREWALL_START = pd.Timestamp("2024-07-01", tz="UTC")


# ----------------------------------------------------------------------------------------------- specs
@dataclass(frozen=True)
class Spec:
    name: str
    tick: float          # minimum price increment (futures) / pip (FX)
    point_value: float   # $ per 1.0 price unit for ONE contract / ONE standard lot
    comm_rt: float       # $ round-turn per contract/lot
    slip: float          # adverse slippage in PRICE units applied to market/stop fills
    spread: float        # modelled ask-bid in price units (0 for futures trade prices)
    limit_through: float  # price must trade THROUGH a limit by this much to fill (futures: 1 tick)
    kind: str            # 'future' | 'fx'

    @property
    def comm_px(self) -> float:
        return self.comm_rt / self.point_value


# Futures commissions: MNQ/MES $1.00 RT, ES/NQ $3.50 RT (CLAUDE.md, Lucid fee table 2026-02-09).
# YM $3.50 RT is an ASSUMPTION (not in the confirmed Lucid table) - labelled wherever used.
# FX: $7 RT per 100k lot commission and spreads below are RESEARCH ASSUMPTIONS (typical raw-ECN London-session
# values), NOT measured; cost-sensitivity (x1.25/x1.5/x2) is reported for every FX result.
SPECS = {
    "MNQ": Spec("MNQ", 0.25, 2.0, 1.00, 0.25, 0.0, 0.25, "future"),
    "ES": Spec("ES", 0.25, 50.0, 3.50, 0.25, 0.0, 0.25, "future"),
    "YM": Spec("YM", 1.0, 5.0, 3.50, 1.0, 0.0, 1.0, "future"),
    "EURUSD": Spec("EURUSD", 0.0001, 100000.0, 7.0, 0.00002, 0.00003, 0.0, "fx"),
    "GBPUSD": Spec("GBPUSD", 0.0001, 100000.0, 7.0, 0.00002, 0.00006, 0.0, "fx"),
    "USDJPY": Spec("USDJPY", 0.01, 100000.0 / 150.0, 7.0, 0.002, 0.004, 0.0, "fx"),
    "USDCAD": Spec("USDCAD", 0.0001, 100000.0 / 1.37, 7.0, 0.00002, 0.00006, 0.0, "fx"),
    "NZDUSD": Spec("NZDUSD", 0.0001, 100000.0, 7.0, 0.00002, 0.00007, 0.0, "fx"),
    "XAUUSD": Spec("XAUUSD", 0.01, 100.0, 7.0, 0.05, 0.20, 0.0, "fx"),
}


def scaled_spec(spec: Spec, k: float) -> Spec:
    """Cost-stressed copy: slippage, spread and commission multiplied by k (fills re-simulated)."""
    return Spec(spec.name, spec.tick, spec.point_value, spec.comm_rt * k, spec.slip * k, spec.spread * k,
                spec.limit_through, spec.kind)


# ----------------------------------------------------------------------------------------------- loaders
def _panama(df: pd.DataFrame, roll_idx: list[int]) -> pd.DataFrame:
    """Back-adjust: at each roll row r, gap = open[r] - close[r-1]; add gap to all rows before r."""
    df = df.copy()
    adj = np.zeros(len(df))
    for r in roll_idx:
        gap = df["open"].iat[r] - df["close"].iat[r - 1]
        adj[:r] += gap
    for c in ("open", "high", "low", "close"):
        df[c] = df[c].to_numpy() + adj
    df.attrs["roll_rows"] = roll_idx
    df.attrs["roll_times"] = [df.index[r] for r in roll_idx]
    return df


def load_futures(name: str) -> pd.DataFrame:
    """1m OHLCV, UTC index, back-adjusted continuous. name in MNQ, ES (Databento dev) or YM_S (Sierra 90d)."""
    if name in ("MNQ", "ES"):
        d = pd.read_parquet(ROOT / "data" / f"{name}_1m.parquet")
        assert d.index.min() >= FIREWALL_START, "firewall: pre-2024-07-01 index futures must not be read"
        ch = np.flatnonzero(d["instrument_id"].to_numpy()[1:] != d["instrument_id"].to_numpy()[:-1]) + 1
        d = _panama(d[["open", "high", "low", "close", "volume"]], list(ch))
    elif name == "YM_S":
        d = pd.read_parquet(ROOT / "data" / "sierra" / "YM_continuous_1m_latest_90d.parquet")
        r = int(d.index.get_loc(pd.Timestamp("2026-09-14 00:00", tz="UTC")))
        d = _panama(d[["open", "high", "low", "close", "volume"]], [r])
    else:
        raise KeyError(name)
    d = d[~d.index.duplicated(keep="first")].sort_index()
    return d


def load_fx(pair: str) -> pd.DataFrame:
    d = pd.read_parquet(ROOT / "data" / "fx_histdata" / f"{pair}_1m_bid.parquet")
    return d[["open", "high", "low", "close"]].sort_index()


# ----------------------------------------------------------------------------------------------- time
def et_index(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return idx.tz_convert(ET)


def session_day(idx: pd.DatetimeIndex) -> pd.Series:
    """Futures/FX trading day = ET calendar date of (t + 6h) so 18:00 ET opens the next day."""
    e = idx.tz_convert(ET).tz_localize(None) + pd.Timedelta(hours=6)
    return pd.Series(e.normalize(), index=idx)


def resample(m1: pd.DataFrame, rule: str) -> pd.DataFrame:
    """ET wall-clock anchored bars. rule: '3min','5min','15min','30min','1h','4h','1D'.
    Returns columns open high low close volume start(UTC) end(UTC, exclusive) with RangeIndex."""
    et = m1.index.tz_convert(ET).tz_localize(None)
    if rule == "4h":
        key = (et - pd.Timedelta(hours=18)).floor("4h") + pd.Timedelta(hours=18)
    elif rule == "1D":
        key = (et + pd.Timedelta(hours=6)).normalize()
    else:
        key = et.floor(rule)
    g = m1.assign(_k=key).groupby("_k", sort=True)
    out = pd.DataFrame({
        "open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
    })
    if "volume" in m1:
        out["volume"] = g["volume"].sum()
    last_ts = m1.index.to_series().groupby(key).max()
    first_ts = m1.index.to_series().groupby(key).min()
    out["start"] = first_ts.to_numpy()
    out["end"] = last_ts.to_numpy() + pd.Timedelta(minutes=1)
    out["key"] = out.index  # ET wall-clock bin label (naive)
    return out.reset_index(drop=True)


# ----------------------------------------------------------------------------------------------- structure
def pivots(high: np.ndarray, low: np.ndarray, k: int):
    """Swing highs/lows with k bars each side (k=1 = 3-candle swing). Strict: pivot high must exceed the
    k neighbours on each side (ties do not qualify). Returns boolean arrays; a pivot at i is CONFIRMED only at
    bar i+k (callers must not use it before bar i+k closes)."""
    n = len(high)
    ph = np.zeros(n, bool)
    pl = np.zeros(n, bool)
    for i in range(k, n - k):
        h = high[i]
        if all(h > high[i - j] for j in range(1, k + 1)) and all(h > high[i + j] for j in range(1, k + 1)):
            ph[i] = True
        lo = low[i]
        if all(lo < low[i - j] for j in range(1, k + 1)) and all(lo < low[i + j] for j in range(1, k + 1)):
            pl[i] = True
    return ph, pl


def fvgs(high: np.ndarray, low: np.ndarray):
    """3-candle FVGs indexed by the THIRD candle i (known at close of i).
    bullish: low[i] > high[i-2] -> zone (bottom=high[i-2], top=low[i]); bearish: high[i] < low[i-2]."""
    n = len(high)
    bull = np.zeros(n, bool)
    bear = np.zeros(n, bool)
    bull[2:] = low[2:] > high[:-2]
    bear[2:] = high[2:] < low[:-2]
    return bull, bear


def ema(x: np.ndarray, span: int) -> np.ndarray:
    return pd.Series(x).ewm(span=span, adjust=False).mean().to_numpy()


# ----------------------------------------------------------------------------------------------- orders
@dataclass
class Order:
    side: int                         # +1 long / -1 short
    t_signal: pd.Timestamp            # decision time (UTC); must be >= end of every bar used to decide
    entry_type: str                   # 'market' | 'stop' | 'limit' | 'close_at' (fill at 1m close ending t)
    stop: float
    entry_px: float | None = None     # for stop/limit orders
    targets: list = field(default_factory=list)   # [(price, fraction)] fractions sum to 1 (or empty)
    expiry: pd.Timestamp | None = None            # pending-entry cancel time
    flatten: pd.Timestamp | None = None           # hard time exit (market)
    be_level: float | None = None                 # intrabar touch -> stop to entry (from next minute)
    be_after_first_target: bool = False
    close_events: list = field(default_factory=list)  # [(end_ts_array(UTC ns int64), bool_array, 'exit'|'be')]
    tag: str = ""
    meta: dict = field(default_factory=dict)


@dataclass
class Trade:
    tag: str
    side: int
    t_signal: pd.Timestamp
    t_entry: pd.Timestamp
    entry_fill: float
    stop0: float
    t_exit: pd.Timestamp
    exit_reason: str
    gross_px: float     # side*(exit_ref - entry_ref) weighted, before costs (reference = order/trigger levels)
    net_px: float       # after spread, slippage, commission
    risk_px: float      # |entry_fill - stop0|
    mfe_px: float
    mae_px: float
    meta: dict

    @property
    def R(self) -> float:
        return self.net_px / self.risk_px if self.risk_px > 0 else np.nan


class Book:
    """1m arrays for fast simulation."""

    def __init__(self, m1: pd.DataFrame, spec: Spec):
        self.spec = spec
        self.ts = m1.index.as_unit("ns").asi8
        self.idx = m1.index
        self.o = m1["open"].to_numpy(float)
        self.h = m1["high"].to_numpy(float)
        self.l = m1["low"].to_numpy(float)
        self.c = m1["close"].to_numpy(float)

    def pos(self, t: pd.Timestamp) -> int:
        """First minute whose start >= t."""
        return int(np.searchsorted(self.ts, t.value, side="left"))


def simulate(book: Book, od: Order, max_minutes: int = 60 * 24 * 12) -> Trade | None:
    """Resolve one order on 1m bars. Prices in bars are trade prices (futures) or BID (fx); ask = bid + spread.
    Longs buy at ask / sell at bid; shorts sell at bid / buy at ask. `ref` = spread/slippage-free level used for
    the gross figure; `fill` = executed price."""
    s = book.spec
    sp = s.spread
    side = od.side
    i = book.pos(od.t_signal)
    n = len(book.ts)
    if i >= n or i == 0 and od.entry_type == "close_at":
        return None
    last = min(n - 1, i + max_minutes)
    ie = None
    if od.entry_type == "market":
        ie, start = i, i
        ref_in = book.o[i]
        fill_in = book.o[i] + (sp if side > 0 else 0.0) + side * s.slip
    elif od.entry_type == "close_at":
        ie, start = i - 1, i
        if book.ts[ie] + 60_000_000_000 != od.t_signal.value:
            return None  # the decision minute is missing from the data
        ref_in = book.c[ie]
        fill_in = book.c[ie] + (sp if side > 0 else 0.0) + side * s.slip
    else:
        exp_i = book.pos(od.expiry) if od.expiry is not None else last + 1
        P = od.entry_px
        for j in range(i, min(exp_i - 1, last) + 1):
            o, h, lo = book.o[j], book.h[j], book.l[j]
            if od.entry_type == "stop":
                if side > 0 and h + sp >= P:
                    ie, fill_in = j, max(P, o + sp) + s.slip
                elif side < 0 and lo <= P:
                    ie, fill_in = j, min(P, o) - s.slip
            else:
                if side > 0 and lo + sp <= P - s.limit_through:
                    ie, fill_in = j, min(P, o + sp)
                elif side < 0 and h >= P + s.limit_through:
                    ie, fill_in = j, max(P, o)
            if ie is not None:
                break
            if (side > 0 and lo <= od.stop) or (side < 0 and h + sp >= od.stop):
                return None  # invalidated before fill
        if ie is None:
            return None
        ref_in = P
        start = ie
    if side * (fill_in - od.stop) <= 0:
        return None
    risk = abs(fill_in - od.stop)
    stop = od.stop
    tg = sorted(od.targets, key=lambda x: side * x[0])
    rem, r_ref, r_fill = 1.0, 0.0, 0.0
    mfe = mae = 0.0
    fl_i = book.pos(od.flatten) if od.flatten is not None else None
    ev = []
    for ets, cond, act in od.close_events:
        k0 = int(np.searchsorted(ets, book.ts[ie] + 60_000_000_000, side="left"))
        if od.entry_type == "close_at":
            k0 = int(np.searchsorted(ets, od.t_signal.value, side="right"))
        ev.extend((int(ets[k]), act) for k in np.flatnonzero(cond[k0:]) + k0)
    ev.sort()
    evp = 0
    be_armed = False
    reason, t_exit_i = "open_end", None
    j = start
    while j <= last:
        o, h, lo, c = book.o[j], book.h[j], book.l[j], book.c[j]
        if side > 0:
            mfe, mae = max(mfe, h - fill_in), min(mae, lo - fill_in)
        else:
            mfe, mae = max(mfe, fill_in - (lo + sp)), min(mae, fill_in - (h + sp))
        if fl_i is not None and j >= fl_i and j > ie:
            r_ref += rem * o
            r_fill += rem * ((o - s.slip) if side > 0 else (o + sp + s.slip))
            rem, reason, t_exit_i = 0.0, "time", j
            break
        if (side > 0 and lo <= stop) or (side < 0 and h + sp >= stop):
            if j == ie:
                f = stop
            else:
                f = min(stop, o) if side > 0 else max(stop, o + sp)
            r_ref += rem * stop
            r_fill += rem * (f - side * s.slip)
            reason = "be" if be_armed and stop == fill_in else "stop"
            rem, t_exit_i = 0.0, j
            break
        if j > ie:
            while tg and rem > 1e-12:
                P, frac = tg[0]
                if not ((side > 0 and h >= P + s.limit_through) or (side < 0 and lo + sp <= P - s.limit_through)):
                    break
                q = min(frac, rem)
                r_ref += q * P
                r_fill += q * (max(P, o) if side > 0 else min(P, o + sp))
                rem -= q
                tg.pop(0)
                if od.be_after_first_target and not be_armed:
                    stop, be_armed = fill_in, True
            if rem <= 1e-12:
                reason, t_exit_i = "target", j
                break
            if od.be_level is not None and not be_armed:
                if (side > 0 and h >= od.be_level) or (side < 0 and lo + sp <= od.be_level):
                    stop, be_armed = fill_in, True
        t_end = book.ts[j] + 60_000_000_000
        done = False
        while evp < len(ev) and ev[evp][0] <= t_end:
            if ev[evp][0] == t_end:
                if ev[evp][1] == "exit":
                    r_ref += rem * c
                    r_fill += rem * ((c - s.slip) if side > 0 else (c + sp + s.slip))
                    rem, reason, t_exit_i, done = 0.0, "close_exit", j, True
                    break
                if ev[evp][1] == "be" and not be_armed:
                    stop, be_armed = fill_in, True
            evp += 1
        if done:
            break
        j += 1
    if rem > 1e-12:
        j = min(j, last)
        c = book.c[j]
        r_ref += rem * c
        r_fill += rem * ((c - s.slip) if side > 0 else (c + sp + s.slip))
        reason, t_exit_i = "max_hold", j
    gross = side * (r_ref - ref_in)
    net = side * (r_fill - fill_in) - s.comm_px
    return Trade(od.tag, side, od.t_signal, book.idx[ie], fill_in, od.stop, book.idx[t_exit_i], reason,
                 gross, net, risk, mfe, mae, dict(od.meta))


def run_sequenced(book: Book, orders: list[Order], one_at_a_time: bool = True) -> list[Trade]:
    """Resolve every order independently, then keep trades greedily by FILL time so that only one position is
    open at a time (a pending order that fills while a position is open is ignored)."""
    sims = [t for t in (simulate(book, od) for od in orders) if t is not None]
    sims.sort(key=lambda t: (t.t_entry, t.t_signal))
    if not one_at_a_time:
        return sims
    out: list[Trade] = []
    busy_until = None
    for tr in sims:
        if busy_until is not None and tr.t_entry < busy_until:
            continue
        out.append(tr)
        busy_until = tr.t_exit + pd.Timedelta(minutes=1)
    return out


def trades_frame(trades: list[Trade], spec: Spec) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    rows = []
    for t in trades:
        rk = float(t.meta.get("risk_override", t.risk_px))   # close-stop designs: R vs the declared invalidation
        rows.append(dict(tag=t.tag, side=t.side, t_signal=t.t_signal, t_entry=t.t_entry, entry=t.entry_fill,
                         stop0=t.stop0, t_exit=t.t_exit, reason=t.exit_reason, gross_px=t.gross_px,
                         net_px=t.net_px, risk_px=rk, R=t.net_px / rk if rk else np.nan,
                         gross_R=t.gross_px / rk if rk else np.nan,
                         mfe_R=t.mfe_px / rk if rk else np.nan,
                         mae_R=t.mae_px / rk if rk else np.nan,
                         net_usd_1=t.net_px * spec.point_value, **{f"m_{k}": v for k, v in t.meta.items()}))
    return pd.DataFrame(rows)
