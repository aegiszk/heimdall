"""FROZEN converter: Sierra Chart "Export Bar Data to Text File" (1-minute, NQ continuous, chart time zone UTC)
-> sealed Dhesi validation parquet. Agent 2, 2026-09-24. Hash-bound in VALIDATION_BINDING_V2.json (D5).

Input format (verified on the 2026 NQ export already on disk):
    Date, Time, Open, High, Low, Last, Volume, NumberOfTrades, BidVolume, AskVolume
    2026/6/23, 20:15:00, ...
Timestamp convention VERIFIED 2026-09-24 on consumed data (Sierra NQ export vs Databento MNQ_1m, 7,065 shared
minutes 2026-06-23..06-30): with the chart in UTC, `Time` labels the bar START (share |diff|<=2pt: lag 0 = 96.8%,
lag -1 = 19.7%, lag +1 = 19.5%). Spec M4 requires bar-start UTC stamps: no shift is applied.

Output: parquet, index `ts` (UTC, bar start), columns open, high, low, close(=Last), volume (float64).
Nothing is filled, dropped, rounded, imputed or REORDERED: out-of-order or duplicate rows are written as exported so
integrity gate 1 (non_monotonic_steps / duplicate_timestamps) sees them and BLOCKS the run (Agent 1 review, PR #2).

Prints METADATA ONLY (protocol V1 section 2.4 "Allowed"): hashes, row count, first/last stamp, duplicate count,
non-parsable rows, out-of-order rows. It never prints or summarises a price, return, range or volume.

usage: python dhesi_v3_sierra_convert.py <sierra_export.txt> <out.parquet>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

HEADER = ["Date", "Time", "Open", "High", "Low", "Last", "Volume"]
OUT_COLS = {"Open": "open", "High": "high", "Low": "low", "Last": "close", "Volume": "volume"}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def convert(src: Path, dst: Path) -> dict:
    df = pd.read_csv(src, skipinitialspace=True, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in HEADER if c not in df.columns]
    if missing:
        raise SystemExit(f"BLOCKED: export header missing {missing}; got {list(df.columns)}")
    ts = pd.to_datetime(df["Date"].str.strip() + " " + df["Time"].str.strip(), format="%Y/%m/%d %H:%M:%S",
                        errors="coerce")
    bad_ts = int(ts.isna().sum())
    out = pd.DataFrame({v: pd.to_numeric(df[k], errors="coerce").astype("float64") for k, v in OUT_COLS.items()})
    out.index = pd.DatetimeIndex(ts).tz_localize("UTC")
    out.index.name = "ts"
    out_of_order = int((out.index[1:] <= out.index[:-1]).sum()) if len(out) > 1 else 0   # reported, never repaired
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dst)
    meta = {
        "converter_sha256": sha(Path(__file__)), "input": str(src), "input_sha256": sha(src),
        "output": str(dst), "output_sha256": sha(dst), "rows": int(len(out)),
        "first_utc": str(out.index.min()), "last_utc": str(out.index.max()),
        "unparsable_timestamps": bad_ts, "duplicate_timestamps": int(out.index.duplicated().sum()),
        "non_increasing_steps_left_for_gate1": out_of_order,
        "nonnumeric_cells": {c: int(out[c].isna().sum()) for c in out.columns},
        "convention": "UTC chart, bar-start stamps, Last->close, no fill/shift",
    }
    Path(str(dst) + ".convert.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    return meta


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print(json.dumps(convert(Path(sys.argv[1]), Path(sys.argv[2])), indent=1))
