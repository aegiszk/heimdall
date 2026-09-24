"""V1 validation audit: hand-computed PnL oracle vs Heimdall trade simulators.

Every expected number below was computed by hand from contract specs
(MNQ $2/pt, MES $5/pt, ES $50/pt, NQ $20/pt, tick 0.25) and Lucid round-turn
commission ($1.00 micro, $3.50 mini). The simulators are never used to derive
the expected values.

Documented Heimdall fill semantics under test (shared RTH simulator):
  entry  = signal-bar close + 1 tick adverse
  target = limit fill at exact target price on touch
  stop   = stop price - 1 tick adverse on touch
  gap    = worse of bar open and stop-1-tick when bar opens through stop
  same bar stop+target -> stop (worst case)
  flatten = flatten-bar close - 1 tick adverse
  commission charged exactly once per round turn
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd
import pytest

from core.alpha.prop_futures import EntryPlan, FuturesRTHModel
from core.alpha import orderflow_footprint as fp


def oracle_pnl(side: int, entry: float, exit_: float, point_value: float, commission_rt: float, qty: int = 1) -> float:
    """Independent reference: signed price move x point value x qty - commission x qty."""
    return side * (exit_ - entry) * point_value * qty - commission_rt * qty


class _FixtureModel(FuturesRTHModel):
    """Enters once, on the bar whose index is ``signal_i``, with a fixed plan."""

    entry_start = time(9, 30)
    entry_end = time(15, 30)
    flatten_time = time(15, 55)

    def __init__(self, contract: str, signal_i: int, side: int, stop: float, target: float):
        super().__init__(contract)
        self.signal_i, self.side, self.stop, self.target = signal_i, side, stop, target

    @property
    def name(self) -> str:
        return "audit_fixture"

    def _max_trades_day(self) -> int:
        return 1

    def _entry_plan(self, frame, i):
        if i != self.signal_i:
            return None
        return EntryPlan(self.side, self.stop, self.target)


def _bars(rows, start="2026-03-02 10:00"):
    """rows = [(open, high, low, close), ...] one-minute ET bars (UTC-indexed like real data)."""
    idx = pd.date_range(start, periods=len(rows), freq="1min", tz="America/New_York").tz_convert("UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)
    df["vwap"] = df["close"]
    return df


def _run(contract, rows, side, stop, target, signal_i=0, start="2026-03-02 10:00"):
    model = _FixtureModel(contract, signal_i, side, stop, target)
    trades = model.prop_montecarlo_frame(_bars(rows, start))
    assert len(trades) == 1
    return trades.iloc[0]


# ---- MNQ long / short target ------------------------------------------------
def test_mnq_long_target_plus_10_points():
    # signal close 20000.00 -> entry 20000.25; target 20010.25 touched; +10.00 pts * $2 - $1 = $19.00
    t = _run("MNQ", [(20000, 20000, 20000, 20000), (20001, 20011, 19995, 20008)], 1, 19990.25, 20010.25)
    assert t.reason == "target"
    assert t.pnl == pytest.approx(19.00)
    assert t.pnl == pytest.approx(oracle_pnl(1, 20000.25, 20010.25, 2.0, 1.0))


def test_mnq_short_target_plus_10_points():
    # entry 19999.75; target 19989.75; +10 pts * $2 - $1 = $19.00
    t = _run("MNQ", [(20000, 20000, 20000, 20000), (19999, 20005, 19989, 19992)], -1, 20009.75, 19989.75)
    assert t.reason == "target"
    assert t.pnl == pytest.approx(19.00)


# ---- MNQ stop / same-bar / gap ------------------------------------------------
def test_mnq_long_stop_adverse_tick():
    # stop 19990.25 touched -> fill 19990.00; (19990.00-20000.25)*2 - 1 = -21.50
    t = _run("MNQ", [(20000, 20000, 20000, 20000), (19998, 19999, 19990, 19992)], 1, 19990.25, 20010.25)
    assert t.reason == "stop"
    assert t.pnl == pytest.approx(-21.50)


def test_mnq_short_stop_adverse_tick():
    # entry 19999.75, stop 20009.75 -> fill 20010.00; -(20010.00-19999.75)*2 - 1 = -21.50
    t = _run("MNQ", [(20000, 20000, 20000, 20000), (20001, 20010, 19995, 20008)], -1, 20009.75, 19989.75)
    assert t.reason == "stop"
    assert t.pnl == pytest.approx(-21.50)


def test_same_bar_stop_and_target_resolves_to_stop():
    t = _run("MNQ", [(20000, 20000, 20000, 20000), (20001, 20011, 19990, 20005)], 1, 19990.25, 20010.25)
    assert t.reason == "stop"
    assert t.pnl == pytest.approx(-21.50)


def test_gap_through_stop_fills_at_open():
    # opens 19985 below stop 19990.25 -> fill min(19985, 19990.00) = 19985; (19985-20000.25)*2-1 = -31.50
    t = _run("MNQ", [(20000, 20000, 20000, 20000), (19985, 19987, 19980, 19986)], 1, 19990.25, 20010.25)
    assert t.reason == "gap_stop"
    assert t.pnl == pytest.approx(-31.50)


def test_gap_through_target_fills_at_target_not_open():
    # opens 20020 above target -> Heimdall fills at target (conservative: forgoes positive gap)
    t = _run("MNQ", [(20000, 20000, 20000, 20000), (20020, 20025, 20015, 20022)], 1, 19990.25, 20010.25)
    assert t.reason == "target"
    assert t.pnl == pytest.approx(19.00)


# ---- MES / ES point values and commission -----------------------------------
def test_mes_long_and_short_plus_10_points():
    long_ = _run("MES", [(6000, 6000, 6000, 6000), (6001, 6011, 5995, 6008)], 1, 5990.25, 6010.25)
    short = _run("MES", [(6000, 6000, 6000, 6000), (5999, 6005, 5989, 5992)], -1, 6009.75, 5989.75)
    assert long_.pnl == pytest.approx(10 * 5.0 - 1.0)  # 49.00
    assert short.pnl == pytest.approx(10 * 5.0 - 1.0)


def test_es_commission_is_mini_rate():
    t = _run("ES", [(6000, 6000, 6000, 6000), (6001, 6011, 5995, 6008)], 1, 5990.25, 6010.25)
    assert t.pnl == pytest.approx(10 * 50.0 - 3.50)  # 496.50


# ---- Session flatten ----------------------------------------------------------
def test_session_flatten_at_close_minus_tick():
    rows = [(20000, 20000, 20000, 20000)] + [(20002, 20004, 20001, 20003)] * 25
    t = _run("MNQ", rows, 1, 19990.25, 20010.25, start="2026-03-02 15:30")
    # signal 15:30, bars to 15:55 -> flatten on 15:55 at 20003-0.25
    assert t.reason == "session_flatten"
    assert t.pnl == pytest.approx((20002.75 - 20000.25) * 2 - 1)  # 4.00


# ---- Commission charged exactly once; no double charging in MC ----------------
def test_commission_once_per_round_turn():
    model = _FixtureModel("MNQ", 0, 1, 19990.25, 20010.25)
    _, _, _, trades = model._simulate(model._prepare_frame(_bars([(20000, 20000, 20000, 20000), (20001, 20011, 19995, 20008)])))
    t = trades[0]
    gross = (t.exit_price - t.entry_price) * t.side * 2.0
    assert gross - t.pnl == pytest.approx(1.0)


def test_empirical_montecarlo_does_not_recharge_commission():
    from tools.prop_montecarlo import SimParams, run_empirical_many
    # One +$160 trade per day: day 19 reaches +$3,040 with 19 qualifying (>= $150) days -> pass.
    # An absurd commission param must NOT change the result if MC treats pnl as already net.
    pnl = np.array([160.0])
    counts = np.array([1])
    a = run_empirical_many(SimParams(n_sims=5, max_days=200, commission_per_rt=0.0, daily_buffer=325.0), pnl, counts)
    b = run_empirical_many(SimParams(n_sims=5, max_days=200, commission_per_rt=999.0, daily_buffer=325.0), pnl, counts)
    assert a.pass_rate == b.pass_rate == 1.0
    assert a.avg_final_balance == b.avg_final_balance


# ---- Quantity scaling (oracle-level; shared RTH sim is 1-lot by construction) --
def test_oracle_quantity_scaling_linear_before_impact():
    one = oracle_pnl(1, 20000.25, 20010.25, 2.0, 1.0, qty=1)
    four = oracle_pnl(1, 20000.25, 20010.25, 2.0, 1.0, qty=4)
    assert four == pytest.approx(4 * one)


# ---- Footprint v2 simulator: same semantics except entry=open+tick, no gap rule --
def test_footprint_sim_matches_oracle_and_documents_gap_optimism():
    idx = pd.date_range("2026-07-01 10:00", periods=2, freq="1min", tz="America/New_York").tz_convert("UTC")
    bars = pd.DataFrame({"open": [19985.0, 19985.0], "high": [19987.0, 19987.0],
                         "low": [19980.0, 19980.0], "close": [19986.0, 19986.0]}, index=idx)
    t = fp._simulate("s", 1, idx[0], idx[0], 20000.25, 19990.25, 20010.25, bars)
    # Footprint sim fills a gapped stop at stop-1tick (19990.00) instead of the open (19985):
    # optimistic by 5 points ($10) vs the shared simulator's gap rule. Documented, not a false negative.
    assert t.reason == "stop"
    assert t.pnl == pytest.approx(oracle_pnl(1, 20000.25, 19990.00, 2.0, 1.0))


# ---- Randomized differential: shared RTH sim vs oracle replay -------------------
def _oracle_replay(rows, side, stop, target, pv, comm, flatten_idx):
    entry = rows[0][3] + side * 0.25
    for k, (o, h, l, c) in enumerate(rows[1:], start=1):
        if (side > 0 and o <= stop) or (side < 0 and o >= stop):
            return oracle_pnl(side, entry, min(o, stop - 0.25) if side > 0 else max(o, stop + 0.25), pv, comm)
        stop_hit = l <= stop if side > 0 else h >= stop
        tgt_hit = h >= target if side > 0 else l <= target
        if stop_hit:
            return oracle_pnl(side, entry, stop - side * 0.25, pv, comm)
        if tgt_hit:
            return oracle_pnl(side, entry, target, pv, comm)
        if k == flatten_idx:
            return oracle_pnl(side, entry, c - side * 0.25, pv, comm)
    raise AssertionError("fixture must terminate")


@pytest.mark.parametrize("seed", range(40))
def test_random_paths_shared_sim_equals_oracle(seed):
    rng = np.random.default_rng(seed)
    side = int(rng.choice([-1, 1]))
    price = 20000.0
    rows = [(price, price, price, price)]
    for _ in range(30):
        o = price + rng.integers(-8, 9) * 0.25
        c = o + rng.integers(-12, 13) * 0.25
        h = max(o, c) + rng.integers(0, 8) * 0.25
        l = min(o, c) - rng.integers(0, 8) * 0.25
        rows.append((o, h, l, c))
        price = c
    entry = 20000.0 + side * 0.25
    stop = entry - side * rng.integers(8, 40) * 0.25
    target = entry + side * rng.integers(8, 40) * 0.25
    # start 15:25 so bar index 30 is 15:55 = flatten
    t = _run("MNQ", rows, side, stop, target, start="2026-03-02 15:25")
    assert t.pnl == pytest.approx(_oracle_replay(rows, side, stop, target, 2.0, 1.0, flatten_idx=30))
