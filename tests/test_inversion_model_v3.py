import datetime as dt

import pandas as pd

from core.alpha.inversion_model_v3 import ASIA_WINDOW, InversionModelV3


def _full(stamps_et: list[str]) -> pd.DataFrame:
    ts = pd.DatetimeIndex(stamps_et).tz_localize("America/New_York").tz_convert("UTC")
    frame = pd.DataFrame(
        {"open": 1.0, "high": [float(i + 2) for i in range(len(ts))], "low": [float(i) for i in range(len(ts))],
         "close": 1.0, "volume": 1.0},
        index=ts,
    )
    return InversionModelV3._full_frame(frame)


def test_4h_bins_open_at_10_and_label_by_bin_end():
    full = _full(["2026-07-01 09:59", "2026-07-01 10:00", "2026-07-01 13:59", "2026-07-01 14:00"])
    bars = InversionModelV3._htf_bars_24h(full, 4)
    ends = [ts.strftime("%H:%M") for ts in bars["ts"]]
    assert ends == ["10:00", "14:00", "18:00"]
    assert bars["session"].tolist() == [dt.date(2026, 7, 1)] * 3


def test_evening_bins_belong_to_next_session():
    full = _full(["2026-07-01 18:00", "2026-07-01 21:59", "2026-07-01 22:00"])
    bars = InversionModelV3._htf_bars_24h(full, 4)
    assert [ts.strftime("%m-%d %H:%M") for ts in bars["ts"]] == ["07-01 22:00", "07-02 02:00"]
    assert bars["session"].tolist() == [dt.date(2026, 7, 2), dt.date(2026, 7, 2)]


def test_asia_window_is_keyed_to_the_following_session():
    full = _full(["2026-07-05 20:00", "2026-07-05 23:59", "2026-07-06 09:30"])
    table = InversionModelV3._window_extremes(full, ASIA_WINDOW, day_offset=1)
    assert list(table.index) == [dt.date(2026, 7, 6)]
    assert table.iloc[0]["hi"] == 3.0 and table.iloc[0]["lo"] == 0.0
