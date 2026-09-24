from pathlib import Path

import pandas as pd
import pytest

from tools.sierra_csv_loader import load_sierra_csv


SIERRA_HEADER = (
    "Date, Time, Open, High, Low, Last, Volume, NumberOfTrades, BidVolume, AskVolume\n"
)


def _write_export(path: Path, rows: str) -> Path:
    path.write_text(SIERRA_HEADER + rows, encoding="utf-8")
    return path


def test_loads_observed_sierra_header_into_normalized_utc_schema(tmp_path):
    source = _write_export(
        tmp_path / "nq.txt",
        "2026/9/21, 11:13:00, 30230.75, 30233.25, 30230.50, 30232.25, 69, 69, 32, 37\n",
    )

    frame = load_sierra_csv(source)

    assert list(frame.columns) == [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "bid_volume",
        "ask_volume",
        "delta",
    ]
    assert frame.index.equals(pd.DatetimeIndex(["2026-09-21 11:13:00+00:00"], name="ts"))
    assert frame.iloc[0].to_dict() == {
        "open": 30230.75,
        "high": 30233.25,
        "low": 30230.50,
        "close": 30232.25,
        "volume": 69.0,
        "bid_volume": 32.0,
        "ask_volume": 37.0,
        "delta": 5.0,
    }


def test_source_timezone_is_converted_to_utc(tmp_path):
    source = _write_export(
        tmp_path / "nq_ny.txt",
        "2026/9/21, 09:30:00, 1, 1, 1, 1, 2, 2, 1, 1\n",
    )

    frame = load_sierra_csv(source, tz_source="America/New_York")

    assert frame.index[0] == pd.Timestamp("2026-09-21 13:30:00+00:00")


def test_missing_bid_ask_volume_fails_closed(tmp_path):
    source = tmp_path / "bad.txt"
    source.write_text(
        "Date, Time, Open, High, Low, Last, Volume\n"
        "2026/9/21, 11:13:00, 1, 1, 1, 1, 2\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing expected columns"):
        load_sierra_csv(source)
