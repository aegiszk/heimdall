"""Synthetic rule tests: hand-built paths where the source-faithful signal is known in advance."""
import numpy as np
import pandas as pd

import registry as rg


def m1_from_bars(bars, start_utc, minutes):
    """Expand OHLC bars of `minutes` length into 1m bars (open->low->high->close path, or open->high->low->close)."""
    rows, idx = [], []
    t = pd.Timestamp(start_utc)
    for o, h, l, c in bars:
        path = np.linspace(o, l, minutes // 2).tolist() + np.linspace(l, h, minutes - minutes // 2).tolist() if c >= o \
            else np.linspace(o, h, minutes // 2).tolist() + np.linspace(h, l, minutes - minutes // 2).tolist()
        path[-1] = c
        prev = o
        for k in range(minutes):
            p = path[k]
            lo, hi = min(prev, p), max(prev, p)
            if k == 0:
                lo, hi = min(o, p), max(o, p)
            rows.append([prev if k else o, hi, lo, p])
            idx.append(t + pd.Timedelta(minutes=k))
            prev = p
        # force exact bar extremes
        blk = rows[-minutes:]
        blk_h = max(r[1] for r in blk); blk_l = min(r[2] for r in blk)
        if blk_h < h:
            blk[minutes // 2][1] = h
        if blk_l > l:
            blk[minutes // 2][2] = l
        t += pd.Timedelta(minutes=minutes)
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=pd.DatetimeIndex(idx))


def test_little_rizzy_projection_and_entry():
    D = rg.load_mod("little_rizzy")
    # 1h bars: P1 high 110 at bar 3, drop to low 90 at bar 7, bounce to P2 high 104 at bar 11, then drift lower
    highs = [100, 104, 108, 110, 107, 103, 99, 95, 97, 100, 102, 104, 101, 99, 98, 97, 96, 95]
    lows = [h - 3 for h in highs]
    lows[7] = 90
    bars = []
    for h, l in zip(highs, lows):
        bars.append((l + 1, h, l, h - 1))
    m1 = m1_from_bars(bars, pd.Timestamp("2025-02-03 14:00", tz="UTC"), 60)
    ods = D.generate(m1, D.Cfg("t", tf="1h"), 0.25)
    assert len(ods) == 1
    od = ods[0]
    # TL through (3,110)->(11,104): slope -0.75; TL at bar 7 = 107; D = 107 - 90 = 17; target = 73
    assert abs(od.meta["target"] - 73.0) < 1e-9
    assert od.side == -1 and abs(od.stop - 104.25) < 1e-9


def test_trident_requires_confirmation_below_doji_high():
    E = rg.load_mod("trident")
    # 30m bars (ET wall clock 2025-02-04, EST=UTC-5). Long, stacked uptrend warmup then FVG + doji + confirm.
    base = [(1.0 + 0.0005 * i, 1.0 + 0.0005 * i + 0.0004, 1.0 + 0.0005 * i - 0.0001, 1.0 + 0.0005 * i + 0.0003)
            for i in range(260)]
    last = base[-1][3]
    fvg = [(last, last + 0.0010, last - 0.0001, last + 0.0009),        # c1 (02:30) high = last+0.0010
           (last + 0.0009, last + 0.0030, last + 0.0008, last + 0.0029),  # c2 (03:00)
           (last + 0.0029, last + 0.0040, last + 0.0020, last + 0.0038)]  # c3 low = last+0.0020 -> gap
    ce = (last + 0.0010 + last + 0.0020) / 2
    doji = (last + 0.0036, last + 0.0045, ce - 0.0001, last + 0.0037)     # wick through CE, body above gap
    conf_ok = (last + 0.0037, last + 0.0044, last + 0.0030, last + 0.0040)  # close < doji high
    start = pd.Timestamp("2025-02-04 07:30", tz="UTC") - pd.Timedelta(minutes=30 * 260)   # c1 at 02:30 ET
    m1 = m1_from_bars(base + fvg + [doji, conf_ok] + [conf_ok] * 5, start, 30)
    ods = E.generate(m1, E.Cfg("t"), "EURUSD", 0.0001)
    assert len(ods) == 1 and ods[0].side == 1
    assert abs(ods[0].stop - (doji[2] - 0.0001)) < 1e-9
    conf_bad = (last + 0.0037, last + 0.0050, last + 0.0030, last + 0.0047)  # closes ABOVE doji high -> invalid
    m1b = m1_from_bars(base + fvg + [doji, conf_bad] + [conf_bad] * 5, start, 30)
    assert E.generate(m1b, E.Cfg("t"), "EURUSD", 0.0001) == []


def test_liquidity_trap_anchor_internal_short():
    A = rg.load_mod("liquidity_trap")
    # 5m bars on 2025-02-04 (EST). Pre-open: swing high 100 (old liquidity), sweep to 105 -> anchor; pullback;
    # internal swing high 102; swing low 96 (target). 09:40 price trades above 102 -> short, stop 105.5, tgt 96.
    seq = [(97, 98, 96.5, 97.5), (97.5, 100, 97, 99), (99, 99.5, 97.5, 98), (98, 99, 97, 98.5),
           (98.5, 105, 98, 104), (104, 104.5, 100, 101), (101, 101.5, 96, 97), (97, 102, 96.5, 101.5),
           (101.5, 101.8, 99, 99.5), (99.5, 100, 97, 98), (98, 99, 97.5, 98.5)]
    start = pd.Timestamp("2025-02-04 14:05", tz="UTC")     # 09:05 ET
    tail = [(98.5, 103, 98.4, 99)] + [(99, 99.5, 95, 95.5)] * 6
    m1 = m1_from_bars(seq + tail, start, 5)
    ods = [o for o in A.generate(m1, A.Cfg("t", k=1)) if o.side == -1]
    assert ods, "expected a short order"
    o = [x for x in ods if abs(x.meta["internal"] - 102) < 1e-9]
    assert o and abs(o[0].stop - 105.5) < 1e-9 and abs(o[0].entry_px - 102.25) < 1e-9
    assert o[0].targets[0][0] == 96.0


def test_liquidity_trap_short_fills_only_on_spike_above_internal():
    import harness as hz
    A = rg.load_mod("liquidity_trap")
    seq = [(97, 98, 96.5, 97.5), (97.5, 100, 97, 99), (99, 99.5, 97.5, 98), (98, 99, 97, 98.5),
           (98.5, 105, 98, 104), (104, 104.5, 100, 101), (101, 101.5, 96, 97), (97, 102, 96.5, 101.5),
           (101.5, 101.8, 99, 99.5), (99.5, 100, 97, 98), (98, 99, 97.5, 98.5)]
    start = pd.Timestamp("2025-02-04 14:05", tz="UTC")
    tail = [(98.5, 98.9, 98.4, 98.6)] * 3 + [(98.6, 103, 98.5, 99)] + [(99, 99.5, 95, 95.5)] * 6
    m1 = m1_from_bars(seq + tail, start, 5)
    ods = [o for o in A.generate(m1, A.Cfg("t", k=1)) if o.side == -1 and abs(o.meta["internal"] - 102) < 1e-9]
    tr = hz.simulate(hz.Book(m1, hz.SPECS["MNQ"]), ods[0])
    assert tr is not None
    assert tr.entry_fill >= 102.25 - 1e-9              # sold ABOVE the internal high, never below it
    assert tr.t_entry >= start + pd.Timedelta(minutes=5 * 14)   # not before the spike bar
