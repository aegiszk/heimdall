import numpy as np
import pandas as pd
import pytest

from core.alpha.orderflow_absorption import OrderflowAbsorptionModel


def _fixture() -> pd.DataFrame:
    rows = []
    days = pd.bdate_range("2026-01-05", periods=21)
    for day_idx, day in enumerate(days):
        base = pd.Timestamp(day.date(), tz="America/New_York") + pd.Timedelta(hours=9, minutes=30)
        for minute in range(6):
            ts = (base + pd.Timedelta(minutes=minute)).tz_convert("UTC")
            rows.append(
                {
                    "ts": ts,
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 100.0,
                    "bid_volume": 55.0,
                    "ask_volume": 45.0,
                    "delta": -10.0,
                }
            )
        if day_idx == 20:
            rows[-6].update(high=100.25, low=100.0, close=100.0, bid_volume=0.0, ask_volume=100.0, delta=100.0)
            rows[-5].update(open=100.0, high=100.0, low=99.25, close=99.5, bid_volume=90.0, ask_volume=10.0, delta=-80.0)
            rows[-4].update(open=99.5, high=99.5, low=96.5, close=97.0, bid_volume=80.0, ask_volume=20.0, delta=-60.0)
    return pd.DataFrame(rows).set_index("ts")


def test_volume_area_tie_expands_lower_first():
    day = pd.DataFrame(
        {
            "close": [99.0, 100.0, 101.0],
            "volume": [30.0, 40.0, 30.0],
        }
    )
    assert OrderflowAbsorptionModel._volume_area(day) == (99.0, 100.0)


def test_requires_real_bid_ask_and_delta_columns():
    frame = _fixture().drop(columns=["ask_volume"])
    with pytest.raises(ValueError, match="ask_volume"):
        OrderflowAbsorptionModel().strategy_returns(frame)


def test_delta_must_reconcile_to_bid_ask():
    frame = _fixture()
    frame.iloc[0, frame.columns.get_loc("delta")] = 99.0
    with pytest.raises(ValueError, match="delta must equal"):
        OrderflowAbsorptionModel().strategy_returns(frame)


def test_pre_registered_short_reaches_fixed_two_r_target():
    model = OrderflowAbsorptionModel()
    trades = model.trades_frame(_fixture())
    assert len(trades) == 1
    trade = trades.iloc[0]
    assert trade.side == -1
    assert trade.level_kind == "prior_vah"
    assert trade.reason == "target"
    assert trade.entry_price == pytest.approx(99.25)
    assert trade.stop_price == pytest.approx(100.5)
    assert trade.target_price == pytest.approx(96.75)
    assert trade.pnl == pytest.approx(4.0)


def test_model_has_no_free_strategy_parameters():
    assert OrderflowAbsorptionModel.strategy_params == ()
    assert len(OrderflowAbsorptionModel.preregistration_sha256) == 64


def test_strategy_arrays_align_with_input_rth_rows():
    model = OrderflowAbsorptionModel()
    pnl, pos, market = model.strategy_returns(_fixture())
    assert len(pnl) == len(pos) == len(market) == 21 * 6
    assert np.count_nonzero(pnl) == 1
