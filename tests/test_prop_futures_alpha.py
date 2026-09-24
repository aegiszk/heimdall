import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.alpha.prop_futures import (
    FabioORBDeltaModel,
    SwingTrendModel,
    TimeStructuredScalpModel,
    TrendPullbackContinuationModel,
    VWAPReversionHardStopModel,
)


def bars(start, rows):
    ts = pd.date_range(start, periods=len(rows), freq="5min")
    frame = pd.DataFrame(rows, columns=["open", "high", "low", "close", "vwap"])
    frame["ts"] = ts
    frame["prior_close"] = 5000.0
    return frame


def test_reversion_hard_stop_caps_runaway_fade():
    df = bars(
        "2026-07-02 09:45",
        [
            [5006.0, 5006.5, 5005.5, 5006.0, 5000.0],
            [5008.0, 5011.0, 5007.0, 5010.0, 5000.2],
            [5010.0, 5012.0, 5009.0, 5011.0, 5000.3],
        ],
    )
    model = VWAPReversionHardStopModel(stretch_ticks=24, stop_ticks=18, max_trades_day=3)

    trade_pnls = model.trade_pnls(df)
    pnl, pos, _ = model.strategy_returns(df)

    assert len(trade_pnls) == 1
    assert trade_pnls[0] == -26.0
    assert pnl.sum() == trade_pnls[0]
    assert np.count_nonzero(pos) == 2


def test_trend_pullback_uses_pullback_stop_and_two_r_target():
    df = bars(
        "2026-07-02 09:45",
        [
            [5000.0, 5000.5, 4999.5, 5000.0, 4999.5],
            [5001.0, 5002.5, 5000.5, 5002.0, 5000.5],
            [5003.0, 5004.5, 5002.5, 5004.0, 5001.0],
            [5002.75, 5004.0, 5002.5, 5003.5, 5001.5],
            [5003.5, 5006.25, 5003.25, 5006.0, 5002.0],
        ],
    )
    model = TrendPullbackContinuationModel(
        trend_lookback_bars=3,
        pullback_ticks=4,
        max_stop_ticks=20,
    )

    mc_frame = model.prop_montecarlo_frame(df)

    assert len(mc_frame) == 1
    assert mc_frame["reason"].iloc[0] == "target"
    assert mc_frame["side"].iloc[0] == 1
    assert mc_frame["pnl"].iloc[0] == 10.25


def test_time_structured_scalp_limits_daily_trades_and_exports_pnl_column():
    ts = pd.date_range("2026-07-02 10:00", periods=20, freq="30min")
    rows = []
    price = 5000.0
    for i, stamp in enumerate(ts):
        if stamp.time() > pd.Timestamp("2026-07-02 15:30").time():
            break
        close = price + 1.0
        rows.append([price, close + 2.25, price - 0.25, close, close - 0.5])
        price = close
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "vwap"])
    df["ts"] = ts[: len(df)]
    df["prior_close"] = 5000.0

    model = TimeStructuredScalpModel(scalp_ticks=8, max_trades_day=2, cooldown_bars=0)
    mc_frame = model.prop_montecarlo_frame(df)

    assert list(mc_frame.columns) == ["entry_ts", "exit_ts", "side", "pnl", "reason"]
    assert len(mc_frame) == 2
    assert (mc_frame["reason"] == "target").all()
    assert (mc_frame["pnl"] == 7.75).all()


def test_swing_trend_enters_next_session_and_targets_two_and_half_r():
    sessions = pd.bdate_range("2026-01-01", periods=24)
    rows = []
    for i, session in enumerate(sessions):
        ts = session + pd.Timedelta(hours=15)
        if i < 20:
            rows.append([ts, 100.0, 101.0, 99.0, 100.0])
        elif i == 20:
            rows.append([ts, 100.0, 103.0, 100.0, 103.0])
        elif i == 21:
            rows.append([ts, 103.0, 109.0, 102.5, 102.5])
        else:
            rows.append([ts, 108.0, 108.5, 107.5, 108.0])
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close"])

    model = SwingTrendModel(breakout_days=20, atr_days=14, reward_r=2.5, contract="ES")
    mc_frame = model.prop_montecarlo_frame(df)

    assert len(mc_frame) == 1
    assert mc_frame["reason"].iloc[0] == "target"
    assert mc_frame["side"].iloc[0] == 1
    assert mc_frame["pnl"].iloc[0] > 0


def fabio_rows(
    breakout_open: float = 99.5,
    breakout_close: float = 101.0,
    follow_open: float = 101.0,
    follow_high: float = 104.5,
    follow_low: float = 100.5,
    follow_close: float = 104.0,
):
    ts = pd.date_range(
        "2026-07-02 08:30",
        periods=50,
        freq="1min",
        tz="America/New_York",
    )
    rows = []
    for stamp in ts:
        if stamp.time() < pd.Timestamp("2026-07-02 09:00").time():
            rows.append([stamp, 99.0, 100.0, 98.0, 99.0, 10.0])
        elif stamp.time() < pd.Timestamp("2026-07-02 09:06").time():
            rows.append([stamp, breakout_open, 101.25, 99.25, breakout_close, 100.0])
        else:
            rows.append([stamp, follow_open, follow_high, follow_low, follow_close, 25.0])
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])


def test_fabio_orb_delta_enters_after_orb_and_exits_target():
    model = FabioORBDeltaModel(contract="MNQ")
    mc_frame = model.prop_montecarlo_frame(fabio_rows())

    assert len(mc_frame) == 1
    assert mc_frame["side"].iloc[0] == 1
    assert mc_frame["reason"].iloc[0] == "target"
    assert mc_frame["pnl"].iloc[0] > 0


def test_fabio_orb_delta_filters_negative_candle_delta_breakout():
    model = FabioORBDeltaModel(contract="MNQ")
    mc_frame = model.prop_montecarlo_frame(
        fabio_rows(
            breakout_open=102.0,
            breakout_close=101.0,
            follow_open=99.5,
            follow_high=100.0,
            follow_low=98.5,
            follow_close=99.0,
        )
    )

    assert mc_frame.empty


def test_candidate_specs_keep_three_strategy_params_and_skew_docstrings():
    models = [
        VWAPReversionHardStopModel(),
        TrendPullbackContinuationModel(),
        TimeStructuredScalpModel(),
        SwingTrendModel(),
        FabioORBDeltaModel(),
    ]

    for model in models:
        assert len(model.strategy_params) <= 3
        doc = type(model).__doc__ or ""
        assert "Expected skew sign" in doc
        assert "Lucid fit" in doc
        assert "Max trades/day" in doc
