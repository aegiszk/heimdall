"""Build RTH one-minute, price-level footprints from one-trade Sierra Parquet."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


TICK_SIZE = 0.25
SOURCE_COLUMNS = [
    "ts",
    "close",
    "num_trades",
    "volume",
    "bid_volume",
    "ask_volume",
]
OUTPUT_SCHEMA = pa.schema(
    [
        pa.field("minute", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("price", pa.float32(), nullable=False),
        pa.field("volume", pa.uint64(), nullable=False),
        pa.field("bid_volume", pa.uint64(), nullable=False),
        pa.field("ask_volume", pa.uint64(), nullable=False),
        pa.field("bar_open", pa.float32(), nullable=False),
        pa.field("bar_high", pa.float32(), nullable=False),
        pa.field("bar_low", pa.float32(), nullable=False),
        pa.field("bar_close", pa.float32(), nullable=False),
    ]
)


def _aggregate(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=[field.name for field in OUTPUT_SCHEMA])
    ts = pd.DatetimeIndex(frame["ts"])
    ts = ts.tz_localize("UTC") if ts.tz is None else ts.tz_convert("UTC")
    local = ts.tz_convert("America/New_York")
    minutes = local.hour * 60 + local.minute
    keep = (minutes >= 9 * 60 + 30) & (minutes <= 16 * 60)
    frame = frame.loc[keep].copy()
    if frame.empty:
        return pd.DataFrame(columns=[field.name for field in OUTPUT_SCHEMA])
    if (frame["num_trades"] != 1).any():
        raise ValueError("non-tick SCID record encountered")
    if (frame[["volume", "bid_volume", "ask_volume"]] < 0).any().any():
        raise ValueError("negative volume encountered")
    if (frame["bid_volume"] + frame["ask_volume"] != frame["volume"]).any():
        raise ValueError("bid_volume + ask_volume must equal volume")
    frame["minute"] = pd.DatetimeIndex(frame["ts"]).floor("min")
    frame["price"] = (frame["close"] / TICK_SIZE).round() * TICK_SIZE
    frame = frame.sort_values("ts", kind="stable")
    levels = (
        frame.groupby(["minute", "price"], as_index=False, sort=True)[
            ["volume", "bid_volume", "ask_volume"]
        ]
        .sum()
    )
    bars = frame.groupby("minute", as_index=False, sort=True).agg(
        first_ts=("ts", "first"),
        last_ts=("ts", "last"),
        bar_open=("price", "first"),
        bar_high=("price", "max"),
        bar_low=("price", "min"),
        bar_close=("price", "last"),
    )
    return levels.merge(bars, on="minute", validate="many_to_one").sort_values(
        ["minute", "price"], kind="stable"
    ).reset_index(drop=True)


def _combine_partial(frame: pd.DataFrame) -> pd.DataFrame:
    levels = frame.groupby(["minute", "price"], as_index=False, sort=True)[
        ["volume", "bid_volume", "ask_volume"]
    ].sum()
    ordered_open = frame.sort_values("first_ts", kind="stable").groupby("minute", as_index=False).first()
    ordered_close = frame.sort_values("last_ts", kind="stable").groupby("minute", as_index=False).last()
    bars = frame.groupby("minute", as_index=False).agg(
        first_ts=("first_ts", "min"),
        last_ts=("last_ts", "max"),
        bar_high=("bar_high", "max"),
        bar_low=("bar_low", "min"),
    )
    bars["bar_open"] = bars["minute"].map(ordered_open.set_index("minute")["bar_open"])
    bars["bar_close"] = bars["minute"].map(ordered_close.set_index("minute")["bar_close"])
    return levels.merge(bars, on="minute", validate="many_to_one").sort_values(
        ["minute", "price"], kind="stable"
    )


def build_footprint(source: str | Path, destination: str | Path, *, batch_size: int = 1_000_000) -> tuple[int, int]:
    """Stream a tick Parquet into price-level cells; returns source/output rows."""
    source_path, output_path = Path(source), Path(destination)
    parquet = pq.ParquetFile(source_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer: pq.ParquetWriter | None = None
    carry = pd.DataFrame()
    source_rows = output_rows = 0
    try:
        for batch in parquet.iter_batches(batch_size=batch_size, columns=SOURCE_COLUMNS):
            frame = batch.to_pandas()
            source_rows += len(frame)
            grouped = _aggregate(frame)
            if not carry.empty:
                grouped = pd.concat([carry, grouped], ignore_index=True)
                grouped = _combine_partial(grouped)
            if grouped.empty:
                continue
            last_minute = grouped["minute"].max()
            complete = grouped[grouped["minute"] < last_minute]
            carry = grouped[grouped["minute"] == last_minute].copy()
            if complete.empty:
                continue
            table = pa.Table.from_pandas(
                complete[[field.name for field in OUTPUT_SCHEMA]], schema=OUTPUT_SCHEMA, preserve_index=False
            )
            if writer is None:
                writer = pq.ParquetWriter(output_path, OUTPUT_SCHEMA, compression="zstd")
            writer.write_table(table)
            output_rows += len(complete)
        if not carry.empty:
            table = pa.Table.from_pandas(
                carry[[field.name for field in OUTPUT_SCHEMA]], schema=OUTPUT_SCHEMA, preserve_index=False
            )
            if writer is None:
                writer = pq.ParquetWriter(output_path, OUTPUT_SCHEMA, compression="zstd")
            writer.write_table(table)
            output_rows += len(carry)
    finally:
        if writer is not None:
            writer.close()
    if writer is None:
        raise ValueError("no RTH records found")
    return source_rows, output_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()
    source_rows, output_rows = build_footprint(args.source, args.destination)
    print(f"source_rows={source_rows:,} footprint_rows={output_rows:,} path={args.destination}")


if __name__ == "__main__":
    main()
