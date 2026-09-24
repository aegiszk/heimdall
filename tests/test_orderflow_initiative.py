import pandas as pd

from core.alpha.orderflow_initiative import initiative_side


def _bar(**updates):
    values = {
        "open": 100.0,
        "high": 102.0,
        "low": 99.75,
        "close": 101.75,
        "delta": 50,
        "short_ask": 30,
        "short_bid": 5,
        "long_bid": 1,
        "long_ask": 1,
    }
    values.update(updates)
    return pd.Series(values)


def test_long_initiative_requires_displacement_and_extreme_imbalance():
    assert initiative_side(_bar(), val=98.0, vah=101.0) == 1


def test_rejects_high_effort_without_directional_result():
    assert initiative_side(_bar(close=100.25), val=98.0, vah=101.0) == 0


def test_short_is_mirrored():
    bar = _bar(
        open=100.0,
        high=100.25,
        low=98.0,
        close=98.25,
        delta=-50,
        short_ask=1,
        short_bid=1,
        long_bid=30,
        long_ask=5,
    )
    assert initiative_side(bar, val=99.0, vah=102.0) == -1
