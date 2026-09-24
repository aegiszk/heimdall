"""Read Sierra Chart ``.scid`` intraday files without loading them into memory.

The binary layout is Sierra Chart's documented version-1 intraday format:
a 56-byte header followed by 40-byte little-endian records.  Sierra stores
timestamps as microseconds since 1899-12-30 UTC.

For one-tick data, ``close`` is the trade price, ``high`` is the contemporaneous
ask, ``low`` is the contemporaneous bid, and ``open`` is a record-type marker.
The original fields are preserved so unbundled CME summary trades remain
reconstructable.
"""
from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


HEADER = struct.Struct("<4sIIHHI36s")
HEADER_SIZE = 56
RECORD_SIZE = 40
SC_EPOCH = np.datetime64("1899-12-30T00:00:00", "us")

RECORD_DTYPE = np.dtype(
    [
        ("datetime_us", "<i8"),
        ("open", "<f4"),
        ("high", "<f4"),
        ("low", "<f4"),
        ("close", "<f4"),
        ("num_trades", "<u4"),
        ("volume", "<u4"),
        ("bid_volume", "<u4"),
        ("ask_volume", "<u4"),
    ]
)

OUTPUT_SCHEMA = pa.schema(
    [
        pa.field("ts", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("open", pa.float32(), nullable=False),
        pa.field("high", pa.float32(), nullable=False),
        pa.field("low", pa.float32(), nullable=False),
        pa.field("close", pa.float32(), nullable=False),
        pa.field("num_trades", pa.uint32(), nullable=False),
        pa.field("volume", pa.uint32(), nullable=False),
        pa.field("bid_volume", pa.uint32(), nullable=False),
        pa.field("ask_volume", pa.uint32(), nullable=False),
    ]
)


@dataclass(frozen=True)
class ScidInfo:
    path: Path
    record_count: int
    first_ts: pd.Timestamp | None
    last_ts: pd.Timestamp | None


def _timestamp_us(value: str | None) -> int | None:
    if value is None:
        return None
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return int((ts.to_datetime64().astype("datetime64[us]") - SC_EPOCH).astype("timedelta64[us]").astype(np.int64))


def _to_timestamp(value: int) -> pd.Timestamp:
    return pd.Timestamp(SC_EPOCH + np.timedelta64(int(value), "us"), tz="UTC")


def inspect_scid(path: str | Path) -> ScidInfo:
    source = Path(path)
    size = source.stat().st_size
    if size < HEADER_SIZE or (size - HEADER_SIZE) % RECORD_SIZE:
        raise ValueError(f"Invalid SCID size: {size} bytes")

    with source.open("rb") as handle:
        header = HEADER.unpack(handle.read(HEADER_SIZE))
    magic, header_size, record_size, version, unused, utc_start, _ = header
    if (magic, header_size, record_size, version, unused, utc_start) != (
        b"SCID",
        HEADER_SIZE,
        RECORD_SIZE,
        1,
        0,
        0,
    ):
        raise ValueError(f"Unsupported SCID header: {header[:6]}")

    count = (size - HEADER_SIZE) // RECORD_SIZE
    if count == 0:
        return ScidInfo(source, 0, None, None)
    records = np.memmap(source, dtype=RECORD_DTYPE, mode="r", offset=HEADER_SIZE, shape=(count,))
    return ScidInfo(
        source,
        count,
        _to_timestamp(records[0]["datetime_us"]),
        _to_timestamp(records[-1]["datetime_us"]),
    )


def _table(records: np.ndarray) -> pa.Table:
    timestamps = SC_EPOCH + records["datetime_us"].astype("timedelta64[us]")
    arrays = [pa.array(timestamps, type=OUTPUT_SCHEMA.field("ts").type)]
    arrays.extend(
        pa.array(records[OUTPUT_SCHEMA.field(index).name], type=OUTPUT_SCHEMA.field(index).type)
        for index in range(1, len(OUTPUT_SCHEMA))
    )
    return pa.Table.from_arrays(arrays, schema=OUTPUT_SCHEMA)


def export_scid_parquet(
    source: str | Path,
    destination: str | Path,
    *,
    start: str | None = None,
    end: str | None = None,
    chunk_records: int = 1_000_000,
) -> tuple[int, pd.Timestamp | None, pd.Timestamp | None]:
    """Stream an inclusive UTC interval from SCID to compressed Parquet."""
    if chunk_records <= 0:
        raise ValueError("chunk_records must be positive")
    info = inspect_scid(source)
    start_us, end_us = _timestamp_us(start), _timestamp_us(end)
    if start_us is not None and end_us is not None and start_us > end_us:
        raise ValueError("start must be <= end")

    records = np.memmap(
        info.path,
        dtype=RECORD_DTYPE,
        mode="r",
        offset=HEADER_SIZE,
        shape=(info.record_count,),
    )
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    writer: pq.ParquetWriter | None = None
    written = 0
    first: pd.Timestamp | None = None
    last: pd.Timestamp | None = None
    try:
        for offset in range(0, info.record_count, chunk_records):
            chunk = records[offset : offset + chunk_records]
            mask = np.ones(len(chunk), dtype=bool)
            if start_us is not None:
                mask &= chunk["datetime_us"] >= start_us
            if end_us is not None:
                mask &= chunk["datetime_us"] <= end_us
            selected = chunk[mask]
            if not len(selected):
                continue
            table = _table(selected)
            if writer is None:
                writer = pq.ParquetWriter(output, OUTPUT_SCHEMA, compression="zstd")
                first = _to_timestamp(selected[0]["datetime_us"])
            writer.write_table(table)
            last = _to_timestamp(selected[-1]["datetime_us"])
            written += len(selected)
    finally:
        if writer is not None:
            writer.close()
    if writer is None:
        raise ValueError("No records matched the requested interval")
    return written, first, last


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("destination")
    parser.add_argument("--start", help="inclusive UTC timestamp")
    parser.add_argument("--end", help="inclusive UTC timestamp")
    args = parser.parse_args()
    info = inspect_scid(args.source)
    print(
        f"[source] records={info.record_count:,} "
        f"range={info.first_ts}->{info.last_ts}"
    )
    count, first, last = export_scid_parquet(
        args.source,
        args.destination,
        start=args.start,
        end=args.end,
    )
    print(f"[output] rows={count:,} range={first}->{last} path={args.destination}")


if __name__ == "__main__":
    main()
