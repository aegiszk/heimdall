import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.alpha.okala8020 import (
    Okala8020Model,
    PendingZone,
    SETUP_C,
    missed_level_by_allowed_ticks,
    next_okala_level,
    okala_levels,
)


def test_okala_level_grid_and_allowed_miss_proxy():
    levels = okala_levels(25600.0, 25700.0)

    assert levels == [25620.0, 25680.0]
    assert next_okala_level(25679.75, side=1) == 25680.0
    assert next_okala_level(25620.25, side=-1) == 25620.0
    assert missed_level_by_allowed_ticks(25679.75, levels, side=1)
    assert missed_level_by_allowed_ticks(25677.5, levels, side=1)
    assert missed_level_by_allowed_ticks(25620.25, levels, side=-1)
    assert missed_level_by_allowed_ticks(25622.5, levels, side=-1)
    assert not missed_level_by_allowed_ticks(25680.0, levels, side=1)
    assert not missed_level_by_allowed_ticks(25677.25, levels, side=1)


def test_okala_cross_section_zone_touch_allows_two_ticks_short():
    model = Okala8020Model()
    zone = PendingZone(
        setup="B_CROSS_SECTION",
        created_i=1,
        side=1,
        zone_low=100.0,
        zone_high=101.0,
        level=100.8,
        session="s",
    )
    row = pd.Series({"high": 110.0, "low": 101.5, "ts": pd.Timestamp("2026-07-01", tz="UTC")})

    assert model._touched_zones([zone], row, local_pos=2) == [zone]
    signal = model._cross_section_signal(zone, row)
    assert signal.signal_price == 101.5


def test_okala_model_sizes_ten_point_mnq_stop_under_buffer():
    model = Okala8020Model()

    assert model._allowed_contracts(40.0) == 16


def test_okala_empty_trade_frame_has_setup_management_columns():
    model = Okala8020Model()
    trades = model.trades_frame([])

    assert list(trades.columns) == [
        "entry_ts",
        "exit_ts",
        "session",
        "setup",
        "side",
        "entry_price",
        "exit_price",
        "stop_price",
        "tp1_price",
        "runner_target_price",
        "contracts",
        "tp1_contracts",
        "runner_contracts",
        "risk_dollars",
        "pnl",
        "gross_pnl",
        "tp1_hit",
        "tp1_gross_pnl",
        "runner_gross_pnl",
        "reason",
        "r_mult",
    ]


def test_okala_resample_rule_is_right_closed_and_right_labeled():
    model = Okala8020Model()
    raw = pd.DataFrame(
        {
            "open": [1.0, 2.0, 3.0, 4.0],
            "high": [1.5, 2.5, 3.5, 4.5],
            "low": [0.5, 1.5, 2.5, 3.5],
            "close": [1.1, 2.1, 3.1, 4.1],
            "volume": [1.0, 1.0, 1.0, 1.0],
        },
        index=pd.to_datetime(
            [
                "2026-07-01 13:30:00",
                "2026-07-01 13:31:00",
                "2026-07-01 13:32:00",
                "2026-07-01 13:33:00",
            ],
            utc=True,
        ),
    )

    prepared = model._prepare_raw(raw)
    bars = model._resample(prepared, "200s")

    assert bars.iloc[0]["ts"].isoformat() == "2026-07-01T09:30:00-04:00"
    assert bars.iloc[0]["open"] == 1.0
    assert bars.iloc[0]["close"] == 1.1
    assert bars.iloc[1]["ts"].isoformat() == "2026-07-01T09:33:20-04:00"
    assert bars.iloc[1]["open"] == 2.0
    assert bars.iloc[1]["close"] == 4.1


def test_okala_c_pattern_is_explicitly_dropped():
    assert SETUP_C == "C_DROPPED"
    assert any("h-pattern dropped" in item for item in Okala8020Model.discretion_gaps())
