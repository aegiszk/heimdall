"""V7 metamorphic invariants + V10 prop-engine / prop-Monte-Carlo hand-constructed paths.

Tests marked "documents current behaviour" pin semantics whose Lucid source is UNVERIFIED
(see VALIDATION_AUDIT_2026-09-22.md); they are not claims that the behaviour is correct.
"""
from __future__ import annotations

from datetime import datetime, time, timezone

import numpy as np
import pandas as pd
import pytest

from core.alpha import prop_futures
from core.config import DEFAULT_GATE_CFG
from core.risk.prop_engine import Action, PropRiskConfig, PropRiskEngine
from core.validation.battery import run_gate
from tests.test_audit_pnl_oracle import _FixtureModel, _bars
from tools.prop_montecarlo import FAIL_NO_TARGET, FAIL_TARGET_MIN_DAYS, SimParams, run_empirical_many
from tools.validate_research_candidates import _session_split


# ------------------------------- V7 invariants -------------------------------
def _one_trade(rows, side, stop, target, contract="MNQ"):
    m = _FixtureModel(contract, 0, side, stop, target)
    return m.prop_montecarlo_frame(_bars(rows)).iloc[0]


def test_higher_commission_never_increases_pnl(monkeypatch):
    rows = [(20000, 20000, 20000, 20000), (20001, 20011, 19995, 20008)]
    base = _one_trade(rows, 1, 19990.25, 20010.25).pnl
    monkeypatch.setitem(prop_futures.CONTRACTS, "MNQ", {"point_value": 2.0, "commission_rt": 5.0})
    higher = _one_trade(rows, 1, 19990.25, 20010.25).pnl
    monkeypatch.setitem(prop_futures.CONTRACTS, "MNQ", {"point_value": 2.0, "commission_rt": 0.0})
    zero = _one_trade(rows, 1, 19990.25, 20010.25).pnl
    assert zero >= base >= higher
    assert zero - base == pytest.approx(1.0) and base - higher == pytest.approx(4.0)


@pytest.mark.parametrize("seed", range(25))
def test_mirrored_path_mirrors_pnl(seed):
    rng = np.random.default_rng(100 + seed)
    p0, price, rows = 20000.0, 20000.0, [(20000.0,) * 4]
    for _ in range(30):
        o = price + rng.integers(-6, 7) * 0.25
        c = o + rng.integers(-10, 11) * 0.25
        rows.append((o, max(o, c) + rng.integers(0, 6) * 0.25, min(o, c) - rng.integers(0, 6) * 0.25, c))
        price = c
    mirror = [(2 * p0 - o, 2 * p0 - l, 2 * p0 - h, 2 * p0 - c) for o, h, l, c in rows]
    entry = p0 + 0.25
    stop, target = entry - rng.integers(8, 30) * 0.25, entry + rng.integers(8, 30) * 0.25
    a = _FixtureModel("MNQ", 0, 1, stop, target).prop_montecarlo_frame(_bars(rows, "2026-03-02 15:25")).iloc[0]
    b = _FixtureModel("MNQ", 0, -1, 2 * p0 - stop, 2 * p0 - target).prop_montecarlo_frame(_bars(mirror, "2026-03-02 15:25")).iloc[0]
    assert a.pnl == pytest.approx(b.pnl) and a.reason == b.reason


def test_irrelevant_columns_do_not_change_trades():
    rows = [(20000, 20000, 20000, 20000), (20001, 20011, 19995, 20008)]
    plain = _bars(rows)
    noisy = plain.assign(volume=[5, 9], symbol="MNQ.v.0", junk=[1.0, -1.0])
    m = _FixtureModel("MNQ", 0, 1, 19990.25, 20010.25)
    pd.testing.assert_frame_equal(m.prop_montecarlo_frame(plain), m.prop_montecarlo_frame(noisy))


def test_gate_is_deterministic_for_identical_inputs():
    r = np.random.default_rng(4).normal(3, 20, 120) / 50_000
    a = run_gate(r, DEFAULT_GATE_CFG, 1, 0.0, active_returns=r, n_params=3)
    b = run_gate(r.copy(), DEFAULT_GATE_CFG, 1, 0.0, active_returns=r.copy(), n_params=3)
    assert a == b


def test_gate_pass_flag_is_invariant_to_capital_divisor_when_drawdown_not_binding():
    r = np.random.default_rng(5).normal(8, 20, 300)
    a = run_gate(r / 50_000, DEFAULT_GATE_CFG, 1, 0.0, active_returns=r / 50_000, n_params=3)
    b = run_gate(r / 500_000, DEFAULT_GATE_CFG, 1, 0.0, active_returns=r / 500_000, n_params=3)
    assert (a.passed, a.reasons) == (b.passed, b.reasons)


def test_chronological_split_never_leaks_future_sessions():
    days = pd.bdate_range("2025-01-01", periods=101).date
    frame = pd.DataFrame({"_session": np.random.default_rng(0).permutation(np.repeat(days, 3))})
    train, holdout = _session_split(frame)
    assert max(train) < min(holdout) and not set(train) & set(holdout)


# ------------------------------- V10 prop engine -----------------------------
def _engine(**cfg):
    return PropRiskEngine(50_000.0, PropRiskConfig(daily_buffer=325.0, **cfg))


def test_mll_trails_on_eod_then_locks_at_start_balance():  # documents current behaviour
    e = _engine()
    assert e.mll_floor == 48_000
    e.on_fill(800); e.on_eod_close()
    assert e.mll_floor == 48_800
    e.on_fill(1_700); e.on_eod_close()          # peak EOD 52,500 -> raw 50,500 -> locked 50,000
    assert e.mll_floor == 50_000
    e.on_fill(-100); e.on_eod_close()
    assert e.mll_floor == 50_000                 # never trails down


def test_mll_uses_eod_peak_not_intraday_peak():
    e = _engine()
    e.on_fill(1_500)                             # intraday +1,500 ...
    e.on_fill(-1_400)                            # ... closes +100
    e.on_eod_close()
    assert e.mll_floor == 48_100


def test_transition_order_dead_flatten_stop_green_session():
    e = _engine()
    e.on_fill(-1_600)                            # 48,400 = floor + cushion
    assert e.check() == Action.FLATTEN_NOW       # cushion outranks STOP_DAY
    e.on_fill(-400)
    assert e.check() == Action.DEAD
    e = _engine(); e.on_fill(-325)
    assert e.check() == Action.STOP_DAY
    e = _engine(); e.on_fill(-324.99)
    assert e.check() == Action.OK
    e = _engine(); e.on_fill(500); e.on_fill(-250)
    assert e.check() == Action.STOP_DAY          # green protect: gave back 50% of a >=$500 peak
    e = _engine(); e.on_fill(500); e.on_fill(-249)
    assert e.check() == Action.OK


def test_session_flatten_respects_dst():
    e = _engine()
    assert e.check(datetime(2026, 7, 1, 20, 45, tzinfo=timezone.utc)) == Action.FLATTEN_NOW   # 16:45 EDT
    assert e.check(datetime(2026, 7, 1, 20, 44, tzinfo=timezone.utc)) == Action.OK
    assert e.check(datetime(2026, 1, 15, 21, 45, tzinfo=timezone.utc)) == Action.FLATTEN_NOW  # 16:45 EST
    assert e.check(datetime(2026, 1, 15, 20, 45, tzinfo=timezone.utc)) == Action.OK


def test_session_flatten_also_fires_in_evening_session():  # documents current behaviour
    assert _engine().check(time(18, 30)) == Action.FLATTEN_NOW


def test_default_daily_buffer_differs_from_documented_default():  # documents current behaviour
    assert PropRiskConfig().daily_buffer == 400.0   # CLAUDE.md / AGENT_HANDOFF say default 325


# ------------------------------- V10 prop Monte Carlo ------------------------
def test_mc_hand_path_pass_on_day_15():
    a = run_empirical_many(SimParams(n_sims=3, daily_buffer=325.0), np.array([200.0]), np.array([1]))
    assert a.pass_rate == 1.0 and a.avg_days == 15


def test_mc_treats_target_before_five_qualifying_days_as_terminal_fail():  # documents current behaviour
    # +$1,000 per day reaches target on day 3 with 3 qualifying days -> run ends as a FAIL.
    a = run_empirical_many(SimParams(n_sims=3, daily_buffer=325.0), np.array([1_000.0]), np.array([1]))
    assert a.fail_target_min_days == 1.0


def test_mc_one_lot_sizing_confounds_alpha_with_prop_verdict():
    # Same true edge (+$10/trade, sd ~$20, one trade per day): 1 lot cannot reach +$3,000 in 80 days
    # (80 x $10 = $800) -> 0% pass regardless of statistical quality; 5 lots is a different verdict.
    rng = np.random.default_rng(0)
    one = rng.choice([30.0, -10.0], size=4000)        # 50% x +30 / 50% x -10 -> mean +10
    r1 = run_empirical_many(SimParams(n_sims=2000, daily_buffer=325.0), one, np.array([1]))
    r5 = run_empirical_many(SimParams(n_sims=2000, daily_buffer=325.0), one * 5, np.array([1]))
    assert r1.pass_rate == 0.0 and r1.fail_no_target == 1.0
    assert r5.pass_rate > 0.5
