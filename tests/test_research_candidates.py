from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.alpha.research_candidates import (
    OpeningFvgScalpModel,
    PocSweepReclaimModel,
    _pine_proxy_poc,
)


def _minute_frame(rows: list[tuple[str, float, float, float, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=["ts", "open", "high", "low", "close", "volume"],
    ).assign(ts=lambda frame: pd.to_datetime(frame["ts"], utc=True))


def test_pine_proxy_poc_uses_running_volume_and_keeps_first_tie() -> None:
    bars = pd.DataFrame(
        {
            "close": [100.0, 101.0, 100.0, 101.0],
            "volume": [5.0, 8.0, 3.0, 1.0],
        }
    )

    assert _pine_proxy_poc(bars) == 101.0


def test_poc_reclaim_signal_and_execution_wrapper_are_frozen() -> None:
    model = PocSweepReclaimModel("MNQ")
    frame = pd.DataFrame(
        {
            "_long_signal": [True],
            "_short_signal": [False],
            "_poc_2": [100.0],
            "close": [101.0],
        }
    )

    plan = model._entry_plan(frame, 0)

    assert plan is not None
    assert plan.side == 1
    assert plan.stop_price == 99.75
    assert plan.target_price == 102.75


def test_poc_reclaim_rejects_entry_on_wrong_side_of_stop() -> None:
    model = PocSweepReclaimModel("MNQ")
    frame = pd.DataFrame(
        {
            "_long_signal": [True],
            "_short_signal": [False],
            "_poc_2": [101.0],
            "close": [100.0],
        }
    )

    assert model._entry_plan(frame, 0) is None


def test_opening_fvg_scalp_finds_break_retest_and_engulf() -> None:
    # Input timestamps are UTC; 13:30 UTC is 09:30 New York in September.
    start = pd.Timestamp("2026-09-01 13:30:00+00:00")
    values = [
        (95.0, 99.0, 94.0, 98.0),
        (98.0, 100.0, 96.0, 99.0),
        (99.0, 100.0, 97.0, 98.0),
        (98.0, 99.0, 95.0, 96.0),
        (96.0, 98.0, 90.0, 97.0),
        (98.0, 99.0, 97.0, 98.0),
        (98.0, 101.0, 98.0, 100.5),
        (100.5, 102.0, 100.5, 101.5),  # FVG and close above OR high.
        (100.8, 101.0, 99.5, 100.2),  # Retest overlaps [99.0, 100.5].
        (100.1, 101.25, 99.75, 101.0),  # Bullish body engulfs retest body.
        (101.0, 107.5, 100.75, 107.0),
    ]
    rows = []
    for offset, (open_, high, low, close) in enumerate(values):
        rows.append((start + pd.Timedelta(minutes=offset), open_, high, low, close, 10.0))
    raw = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])

    model = OpeningFvgScalpModel("MNQ")
    prepared = model._prepare_frame(raw)
    signal_rows = prepared.loc[prepared["_signal_side"] != 0]

    assert len(signal_rows) == 1
    signal_i = int(signal_rows.index[0])
    assert signal_rows.iloc[0]["_time"].isoformat() == "09:39:00"
    assert signal_rows.iloc[0]["_signal_stop"] == 99.25

    plan = model._entry_plan(prepared, signal_i)
    assert plan is not None
    assert plan.side == 1
    assert plan.stop_price == 99.25
    assert plan.target_price == 107.25

    trades = model.prop_montecarlo_frame(raw)
    assert len(trades) == 1
    assert trades.iloc[0]["reason"] == "target"
    assert trades.iloc[0]["pnl"] == pytest.approx(11.0)


def test_opening_fvg_does_not_carry_state_across_sessions() -> None:
    start = pd.Timestamp("2026-09-01 13:30:00+00:00")
    rows = []
    for day in range(2):
        day_start = start + pd.Timedelta(days=day)
        for minute in range(10):
            rows.append((day_start + pd.Timedelta(minutes=minute), 100, 101, 99, 100, 10))
    raw = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])

    prepared = OpeningFvgScalpModel("MNQ")._prepare_frame(raw)

    assert np.count_nonzero(prepared["_signal_side"].to_numpy()) == 0
