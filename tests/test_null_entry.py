import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.null_entry_test import NullRandomModel


def flat_rows(price=100.0, volume=10.0):
    ts = pd.date_range("2026-07-02 09:30", "2026-07-02 14:00", freq="1min", tz="America/New_York")
    return pd.DataFrame(
        {
            "ts": ts,
            "open": price,
            "high": price + 0.25,
            "low": price - 0.25,
            "close": price,
            "volume": volume,
        }
    )


def test_null_random_same_seed_reproducible():
    model = NullRandomModel()
    prepared = model.prepare(flat_rows())

    first = model.simulate(prepared, seed=7)
    second = model.simulate(prepared, seed=7)

    assert first.to_dict("records") == second.to_dict("records")


def test_null_random_entry_side_ignores_price_and_volume():
    model = NullRandomModel()
    cheap = model.simulate(model.prepare(flat_rows(price=100.0, volume=10.0)), seed=11)
    expensive = model.simulate(model.prepare(flat_rows(price=1000.0, volume=9999.0)), seed=11)

    assert cheap["side"].tolist() == expensive["side"].tolist()


def test_null_random_stop_wins_when_stop_and_target_same_bar():
    rows = flat_rows(price=100.0)
    rows.loc[1, ["high", "low"]] = [106.0, 94.0]
    model = NullRandomModel(stop_ticks=20)
    trades = model.simulate(model.prepare(rows), seed=1)

    assert len(trades) >= 1
    assert trades.iloc[0]["reason"] == "stop"
    assert trades.iloc[0]["pnl"] == -27.25


def test_stop_slippage_ticks_change_stop_loss_size():
    rows = flat_rows(price=100.0)
    rows.loc[1, ["high", "low"]] = [106.0, 94.0]

    ideal = NullRandomModel(stop_ticks=20, stop_slippage_ticks=0).simulate(
        NullRandomModel(stop_ticks=20, stop_slippage_ticks=0).prepare(rows),
        seed=1,
    )
    conservative = NullRandomModel(stop_ticks=20, stop_slippage_ticks=2).simulate(
        NullRandomModel(stop_ticks=20, stop_slippage_ticks=2).prepare(rows),
        seed=1,
    )

    assert ideal.iloc[0]["pnl"] == -26.0
    assert conservative.iloc[0]["pnl"] == -28.5


def test_stop_limit_can_go_unfilled_and_flatten_worse():
    rows = flat_rows(price=100.0)
    rows.loc[1:, ["open", "high", "low", "close"]] = [106.0, 106.0, 105.5, 106.0]
    model = NullRandomModel(stop_ticks=20)

    trades = model.simulate_stop_limit(model.prepare(rows), seed=1, limit_offset_ticks=0)

    assert trades.iloc[0]["reason"] == "stop_limit_unfilled_flatten"
    assert trades.iloc[0]["stop_limit_compare"] == "worse"
    assert bool(trades.iloc[0]["stop_limit_pending"]) is True
