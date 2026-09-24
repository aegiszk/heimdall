"""Read + validate the append-only CSVs written by tools/sierra_acsil/HeimdallTapeRecorder.cpp (read-only).

Checks (fail loudly, never repair silently):
  * schema: 17 columns, known record types {0,1,2,6}
  * sequence: strictly increasing per file except logged resets; every jump > 1 is a GAP
  * duplicates: repeated seq (e.g. study re-added -> first-call backfill re-written) are reported, then dropped
  * SC_TS_MARKER (type 0) records are reported as feed gaps
Fidelity: per-minute traded volume and bid/ask volume vs Sierra's own .scid intraday file for the same symbol
(.scid Volume/BidVolume/AskVolume summed per UTC minute). The .scid is Sierra's stored data, not an independent
exchange source; agreement proves the recorder captured what Sierra received, nothing more.

Usage:
  python tools/sierra_tape_reader.py validate C:/SierraChart/Data/HeimdallTape/NQZ26-CME_20260923.csv
  python tools/sierra_tape_reader.py fidelity C:/SierraChart/Data/HeimdallTape/NQZ26-CME_20260923.csv C:/SierraChart/Data/NQZ26-CME.scid
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np
import pandas as pd

COLUMNS = ["seq", "type", "sc_utc_us", "local_proc_ns", "price", "volume", "bid", "ask", "bid_size", "ask_size",
           "total_bid_depth", "total_ask_depth", "unbundled", "trade_indicator", "num_trades", "batch", "backfill"]
TRADE_TYPES = {1, 2}          # 1 = at bid or lower (seller-initiated), 2 = at ask or higher (buyer-initiated)
KNOWN_TYPES = {0, 1, 2, 6}
SCID_HEADER, SCID_RECORD = 56, 40
SC_EPOCH_US = 25569 * 86_400_000_000


def load(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=COLUMNS)
    if df.shape[1] != len(COLUMNS):
        raise ValueError(f"expected {len(COLUMNS)} columns, got {df.shape[1]}")
    return df


def validate(df: pd.DataFrame) -> dict:
    bad_types = sorted(set(df["type"].unique()) - KNOWN_TYPES)
    dup = df.duplicated(subset=["seq", "type", "sc_utc_us", "price", "volume"], keep="first")
    d = df[~dup]
    seq = d["seq"].to_numpy(np.int64)
    step = np.diff(seq)
    gaps = [(int(seq[i]), int(seq[i + 1])) for i in np.nonzero(step > 1)[0]]
    backward = [(int(seq[i]), int(seq[i + 1])) for i in np.nonzero(step < 1)[0]]
    trades = d[d["type"].isin(TRADE_TYPES)]
    return {
        "rows": int(len(df)), "duplicates_dropped": int(dup.sum()), "unknown_types": bad_types,
        "trades": int(len(trades)), "quote_updates": int((d["type"] == 6).sum()), "markers": int((d["type"] == 0).sum()),
        "sequence_gaps": len(gaps), "missing_sequence_numbers": int(sum(b - a - 1 for a, b in gaps)),
        "first_gaps": gaps[:10], "backward_jumps": backward[:10],
        "backfill_rows": int(d["backfill"].sum()),
        "sc_time_nonmonotonic": int((np.diff(d["sc_utc_us"].to_numpy()) < 0).sum()),
        "first_utc": str(pd.to_datetime(d["sc_utc_us"].min(), unit="us")), "last_utc": str(pd.to_datetime(d["sc_utc_us"].max(), unit="us")),
        "PASS": not bad_types and not backward and len(gaps) == 0 and int((d["type"] == 0).sum()) == 0,
    }


def scid_minutes(path: str | Path, t0_us: int, t1_us: int) -> pd.DataFrame:
    raw = np.fromfile(path, dtype=np.uint8)
    hdr_size = struct.unpack("<I", raw[4:8].tobytes())[0]
    rec = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"),
                    ("n", "<u4"), ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])
    a = np.frombuffer(raw[hdr_size:hdr_size + (len(raw) - hdr_size) // SCID_RECORD * SCID_RECORD].tobytes(), dtype=rec)
    unix_us = a["dt"] - SC_EPOCH_US
    m = (unix_us >= t0_us) & (unix_us < t1_us)
    f = pd.DataFrame({"minute": unix_us[m] // 60_000_000, "v": a["v"][m], "bv": a["bv"][m], "av": a["av"][m]})
    return f.groupby("minute").sum()


def fidelity(df: pd.DataFrame, scid: str | Path) -> dict:
    t = df[df["type"].isin(TRADE_TYPES) & (df["backfill"] == 0)].drop_duplicates(subset=["seq"])
    if t.empty:
        return {"PASS": False, "reason": "no live trade rows"}
    t = t.assign(minute=t["sc_utc_us"] // 60_000_000)
    rec = pd.DataFrame({"v": t.groupby("minute")["volume"].sum(),
                        "bv": t[t["type"] == 1].groupby("minute")["volume"].sum(),
                        "av": t[t["type"] == 2].groupby("minute")["volume"].sum()}).fillna(0)
    lo, hi = int(rec.index.min() + 1), int(rec.index.max())       # drop partial first/last minute
    rec = rec.loc[lo:hi - 1]
    ref = scid_minutes(scid, lo * 60_000_000, hi * 60_000_000).reindex(rec.index).fillna(0)
    diff = (rec - ref).abs()
    out = {"minutes": int(len(rec)), "recorded_volume": float(rec.v.sum()), "scid_volume": float(ref.v.sum()),
           "minutes_mismatch_volume": int((diff.v > 0).sum()), "minutes_mismatch_bid_ask": int(((diff.bv > 0) | (diff.av > 0)).sum())}
    out["PASS"] = out["minutes"] > 0 and out["minutes_mismatch_volume"] == 0 and out["minutes_mismatch_bid_ask"] == 0
    return out


def main() -> None:
    cmd, path = sys.argv[1], sys.argv[2]
    df = load(path)
    res = validate(df) if cmd == "validate" else fidelity(df, sys.argv[3])
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
