import numpy as np
import pandas as pd
import pytest

from harness import (SPECS, Book, Order, _panama, fvgs, pivots, resample, run_sequenced, scaled_spec, simulate)


def bars(rows, start="2025-03-05 15:00"):
    idx = pd.date_range(start, periods=len(rows), freq="1min", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)


MNQ = SPECS["MNQ"]


def test_market_long_target_and_costs():
    m = bars([[100, 100.5, 99.75, 100.25], [100.25, 101, 100, 100.75], [100.75, 102.5, 100.5, 102]])
    tr = simulate(Book(m, MNQ), Order(1, m.index[0], "market", stop=99.0, targets=[(102.0, 1.0)]))
    assert tr.entry_fill == 100.25            # open + 1 tick slippage
    assert tr.exit_reason == "target"
    assert tr.gross_px == pytest.approx(2.0)  # 102 - 100 reference
    assert tr.net_px == pytest.approx(102.0 - 100.25 - 0.5)  # $1 RT / $2 per point = 0.5 pt


def test_stop_beats_target_same_minute():
    m = bars([[100, 100.25, 99.9, 100], [100, 103, 98, 100]])
    tr = simulate(Book(m, MNQ), Order(1, m.index[0], "market", stop=99.0, targets=[(102.0, 1.0)]))
    assert tr.exit_reason == "stop"
    assert tr.net_px == pytest.approx(99.0 - 0.25 - 100.25 - 0.5)


def test_entry_minute_touching_stop_is_stopped():
    m = bars([[100, 100.25, 98.5, 100], [100, 103, 99.5, 102]])
    tr = simulate(Book(m, MNQ), Order(1, m.index[0], "market", stop=99.0, targets=[(102.0, 1.0)]))
    assert tr.exit_reason == "stop"


def test_limit_needs_trade_through():
    m = bars([[101, 101, 100.0, 100.5], [100.5, 101, 99.75, 100.5], [100.5, 103, 100.4, 102.5]])
    tr = simulate(Book(m, MNQ), Order(1, m.index[0], "limit", stop=98.0, entry_px=100.0, targets=[(102.0, 1)]))
    assert tr.t_entry == m.index[1]           # minute 0 only touched 100.0; minute 1 traded through
    assert tr.entry_fill == 100.0


def test_short_stop_entry_gap_fill():
    m = bars([[100, 100, 99.5, 99.75], [98.0, 98.5, 97.5, 98]])
    tr = simulate(Book(m, MNQ), Order(-1, m.index[0], "stop", stop=101.0, entry_px=99.0, targets=[]))
    assert tr.t_entry == m.index[1] and tr.entry_fill == 98.0 - 0.25   # gap below trigger -> open - slip
    m2 = bars([[100, 100, 98.5, 99.75], [99.5, 99.8, 99.0, 99.5]])
    tr2 = simulate(Book(m2, MNQ), Order(-1, m2.index[0], "stop", stop=101.0, entry_px=99.0))
    assert tr2.t_entry == m2.index[0] and tr2.entry_fill == 99.0 - 0.25


def test_fx_spread_long_short():
    eu = SPECS["EURUSD"]
    m = bars([[1.1000, 1.1002, 1.0999, 1.1001]] * 3)
    tr = simulate(Book(m, eu), Order(1, m.index[0], "market", stop=1.0990, targets=[(1.1100, 1)]))
    assert tr.entry_fill == pytest.approx(1.1000 + eu.spread + eu.slip)
    trs = simulate(Book(m, eu), Order(-1, m.index[0], "market", stop=1.1010, targets=[]))
    assert trs.entry_fill == pytest.approx(1.1000 - eu.slip)


def test_be_trigger_then_scratch():
    m = bars([[100, 100.25, 99.9, 100], [100, 101.5, 100, 101], [101, 101, 99.0, 99.5]])
    tr = simulate(Book(m, MNQ), Order(1, m.index[0], "market", stop=98.0, be_level=101.0, targets=[(105, 1)]))
    assert tr.exit_reason == "be"


def test_close_event_exit():
    m = bars([[100, 100.25, 99.9, 100], [100, 100.5, 99.8, 100.2], [100.2, 100.5, 99.8, 100.4]])
    ets = np.array([(m.index[1] + pd.Timedelta(minutes=1)).as_unit("ns").value])
    tr = simulate(Book(m, MNQ), Order(1, m.index[0], "market", stop=98.0, close_events=[(ets, np.array([True]), "exit")]))
    assert tr.exit_reason == "close_exit" and tr.t_exit == m.index[1]


def test_scaled_costs_worse():
    m = bars([[100, 100.5, 99.75, 100.25], [100.25, 101, 100, 100.75], [100.75, 102.5, 100.5, 102]])
    od = Order(1, m.index[0], "market", stop=99.0, targets=[(102.0, 1.0)])
    a = simulate(Book(m, MNQ), od).net_px
    b = simulate(Book(m, scaled_spec(MNQ, 2.0)), od).net_px
    assert b < a


def test_resample_4h_bins_respect_dst():
    # 2025-03-09 is the US DST switch. 4H bins must start 18:00 ET on both sides.
    idx = pd.date_range("2025-03-06 22:00", "2025-03-11 02:00", freq="1min", tz="UTC")
    m = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0}, index=idx)
    b4 = resample(m, "4h")
    hours = sorted(set(k.hour for k in b4["key"]))
    assert hours == [2, 6, 10, 14, 18, 22]
    b1 = resample(m, "1h")
    k10 = b1[b1["key"] == pd.Timestamp("2025-03-10 10:00")]
    assert k10["start"].iat[0] == pd.Timestamp("2025-03-10 14:00", tz="UTC")   # EDT = UTC-4
    k10b = b1[b1["key"] == pd.Timestamp("2025-03-07 10:00")]
    assert k10b["start"].iat[0] == pd.Timestamp("2025-03-07 15:00", tz="UTC")  # EST = UTC-5
    assert (b4["end"] > b4["start"]).all()


def test_pivots_and_fvg():
    h = np.array([1, 3, 2, 5, 4, 4, 6.0])
    lo = h - 1
    ph, pl = pivots(h, lo, 1)
    assert list(np.flatnonzero(ph)) == [1, 3]
    hh = np.array([10, 12, 15.0]); ll = np.array([9, 11, 13.0])
    bu, be = fvgs(hh, ll)
    assert bu[2] and not be[2]


def test_panama_removes_roll_gap():
    m = bars([[100, 100, 100, 100], [100, 100, 100, 100], [300, 300, 300, 300]])
    adj = _panama(m, [2])
    assert adj["close"].iat[1] == 300 and adj["close"].iat[2] == 300


def test_sequencing_one_at_a_time():
    m = bars([[100, 100.25, 99.9, 100]] * 30)
    ods = [Order(1, m.index[0], "market", stop=90.0, flatten=m.index[10]),
           Order(1, m.index[5], "market", stop=90.0, flatten=m.index[20])]
    out = run_sequenced(Book(m, MNQ), ods)
    assert len(out) == 1


def test_sequencing_first_fill_wins():
    m = bars([[100, 100.25, 99.9, 100]] * 5 + [[100, 106, 99.9, 105]] + [[105, 105.2, 104.9, 105]] * 20)
    late_fill = Order(1, m.index[0], "stop", stop=90.0, entry_px=104.0, flatten=m.index[20])
    early_fill = Order(1, m.index[1], "market", stop=90.0, flatten=m.index[3])
    out = run_sequenced(Book(m, MNQ), [late_fill, early_fill])
    assert [t.t_entry for t in out] == [m.index[1], m.index[5]]
