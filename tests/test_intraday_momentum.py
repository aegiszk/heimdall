import pandas as pd
import pytest

from core.alpha.intraday_momentum import daily_trades


def _bars(rows):
    idx = pd.DatetimeIndex([r[0] for r in rows]).tz_localize("America/New_York").tz_convert("UTC")
    return pd.DataFrame({"close": [r[1] for r in rows]}, index=idx)


def test_signal_uses_prior_close_and_1530_and_exits_at_1600():
    df = _bars([
        ("2026-03-02 15:59", 100.0),   # previous RTH close C0
        ("2026-03-03 09:30", 100.0),
        ("2026-03-03 09:59", 101.0),
        ("2026-03-03 15:29", 102.0),   # price at 15:30 -> r_rod > 0 -> long
        ("2026-03-03 15:59", 103.0),   # price at 16:00
    ])
    t = daily_trades(df, "MNQ").iloc[0]
    assert t["side"] == 1
    assert t["gross"] == pytest.approx(2.0)                     # 1 point * $2
    assert t["pnl"] == pytest.approx(2.0 - 2 * 0.25 * 2.0 - 1.0)  # one tick each side + $1


def test_short_signal_and_missing_exit_bar_skips_session():
    df = _bars([
        ("2026-03-02 15:59", 100.0),
        ("2026-03-03 15:29", 99.0),
        ("2026-03-03 15:59", 98.0),
        ("2026-03-04 15:29", 97.0),    # no 15:59 bar -> no trade, but sets next C0
    ])
    t = daily_trades(df, "MES")
    assert len(t) == 1 and t.iloc[0]["side"] == -1
    assert t.iloc[0]["gross"] == pytest.approx(5.0)


def test_premarket_bars_are_not_rth_close():
    df = _bars([
        ("2026-03-02 15:59", 100.0),
        ("2026-03-02 17:30", 50.0),    # evening bar must not become C0
        ("2026-03-03 15:29", 101.0),
        ("2026-03-03 15:59", 101.0),
    ])
    t = daily_trades(df, "ES").iloc[0]
    assert t["c0"] == 100.0 and t["side"] == 1
