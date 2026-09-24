import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.alpha.inversion_model import InversionModel


def test_inversion_model_detects_long_and_short_htf_inversions():
    model = InversionModel(contract="MES")
    bars = pd.DataFrame(
        [
            ["2026-07-01 09:00", 100.0, 101.0, 99.0, 100.0, "2026-07-01"],
            ["2026-07-01 10:00", 100.0, 100.5, 98.0, 99.0, "2026-07-01"],
            ["2026-07-01 11:00", 97.0, 97.5, 96.0, 96.5, "2026-07-01"],
            ["2026-07-01 12:00", 96.5, 102.0, 96.0, 102.0, "2026-07-01"],
            ["2026-07-02 09:00", 110.0, 111.0, 109.0, 110.0, "2026-07-02"],
            ["2026-07-02 10:00", 110.0, 112.0, 109.5, 111.0, "2026-07-02"],
            ["2026-07-02 11:00", 113.0, 114.0, 113.0, 113.5, "2026-07-02"],
            ["2026-07-02 12:00", 113.5, 114.0, 108.0, 108.0, "2026-07-02"],
        ],
        columns=["ts", "open", "high", "low", "close", "session"],
    )
    bars["ts"] = pd.to_datetime(bars["ts"]).dt.tz_localize("America/New_York")
    bars["_time"] = bars["ts"].dt.time
    session_ord = {session: idx for idx, session in enumerate(bars["session"].drop_duplicates())}

    _, events = model._build_inversion_events(bars, "1H", session_ord)

    assert [event.bias for event in events] == [1, -1]
    assert events[0].zone_low == 97.5
    assert events[0].zone_high == 99.0
    assert events[1].zone_low == 111.0
    assert events[1].zone_high == 113.0


def test_inversion_model_sizes_full_stop_under_daily_buffer_and_caps_contracts():
    mes = InversionModel(contract="MES")
    mnq = InversionModel(contract="MNQ")
    es = InversionModel(contract="ES")

    assert mes._allowed_contracts(80) == 3
    assert mnq._allowed_contracts(50) == 13
    assert es._allowed_contracts(1) == 4
    assert es._allowed_contracts(40) == 0


def test_inversion_model_empty_trade_frame_has_stable_columns():
    model = InversionModel(contract="MNQ")
    trades = model.trades_frame([])

    assert list(trades.columns) == [
        "entry_ts",
        "exit_ts",
        "session",
        "side",
        "entry_price",
        "exit_price",
        "stop_price",
        "tp1_price",
        "runner_target_price",
        "contracts",
        "risk_dollars",
        "pnl",
        "gross_pnl",
        "tp1_hit",
        "tp1_gross_pnl",
        "runner_gross_pnl",
        "reason",
        "htf_timeframe",
        "sweep_pool",
        "tp1_pool",
        "runner_pool",
        "r_mult",
    ]
