import struct

import pandas as pd
import pyarrow.parquet as pq
import pytest

from tools.sierra_scid_loader import (
    HEADER,
    inspect_scid,
    export_scid_parquet,
)


def _write_scid(path):
    epoch = pd.Timestamp("1899-12-30", tz="UTC")
    rows = []
    for second, side in [(0, "ask"), (1, "bid"), (2, "ask")]:
        ts = pd.Timestamp("2026-09-01 12:00:00", tz="UTC") + pd.Timedelta(seconds=second)
        micros = int((ts - epoch).total_seconds() * 1_000_000)
        bid_volume = 1 if side == "bid" else 0
        ask_volume = 1 if side == "ask" else 0
        rows.append(struct.pack("<q4f4I", micros, 0.0, 100.25, 100.0, 100.25, 1, 1, bid_volume, ask_volume))
    path.write_bytes(HEADER.pack(b"SCID", 56, 40, 1, 0, 0, b"\0" * 36) + b"".join(rows))
    return path


def test_inspects_documented_header_and_time_range(tmp_path):
    source = _write_scid(tmp_path / "test.scid")

    info = inspect_scid(source)

    assert info.record_count == 3
    assert info.first_ts == pd.Timestamp("2026-09-01 12:00:00+00:00")
    assert info.last_ts == pd.Timestamp("2026-09-01 12:00:02+00:00")


def test_streams_inclusive_utc_slice_to_parquet(tmp_path):
    source = _write_scid(tmp_path / "test.scid")
    output = tmp_path / "test.parquet"

    count, first, last = export_scid_parquet(
        source,
        output,
        start="2026-09-01 12:00:01Z",
        end="2026-09-01 12:00:02Z",
        chunk_records=1,
    )
    frame = pq.read_table(output).to_pandas()

    assert count == 2
    assert first == pd.Timestamp("2026-09-01 12:00:01+00:00")
    assert last == pd.Timestamp("2026-09-01 12:00:02+00:00")
    assert frame["ts"].tolist() == [first, last]
    assert frame["bid_volume"].tolist() == [1, 0]
    assert frame["ask_volume"].tolist() == [0, 1]
    assert frame["close"].tolist() == [100.25, 100.25]


def test_rejects_invalid_header(tmp_path):
    bad = tmp_path / "bad.scid"
    bad.write_bytes(b"NOPE" + b"\0" * 52)

    with pytest.raises(ValueError, match="Unsupported SCID header"):
        inspect_scid(bad)
