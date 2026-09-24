"""BLIND builder for untouched Sierra history (Agent 2). Outcome-blind by construction.

Reads per-contract .scid files for one root, builds ONE canonical continuous 1-minute series and SEALS it.
Prints and records ONLY metadata: row counts, first/last timestamp, roll schedule (date + from->to contract),
duplicate counts, intra-session gap counts, SHA-256. It never prints, plots, or summarizes prices, returns, or
OHLC statistics. Volume is used internally ONLY to choose the roll contract (prior-session volume leader); volume
values are not emitted.

Roll rule (fixed, matches the development data's volume-lead construction and data/sierra/MANIFEST.md):
  for each CME trading day D (18:00 ET start), use the contract with the largest total volume in the PRIOR trading day
  among contracts with data; the chosen contract may never move backward in expiry order; no back-adjustment.
Hard window: trading days in [--start, --end] only (end inclusive). Data after --end is discarded before anything else.

Usage:
  python blind_build.py --root NQ --suffix CME --start 2008-06-01 --end 2024-06-30 --out-dir validation_data/SEALED
  python blind_build.py ... --test-label TEST_ON_2026_CONTRACTS   (for already-seen data; labelled, not sealed)
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import stat
import struct
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path("C:/SierraChart/Data")
HERE = Path(__file__).resolve().parent
SC_EPOCH_US = 25569 * 86_400_000_000
MONTHS = "FGHJKMNQUVXZ"
REC = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"),
                ("n", "<u4"), ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def expiry_key(name: str):
    m = re.match(r"^[A-Z0-9]+?([FGHJKMNQUVXZ])(\d{2})-", name)
    return (2000 + int(m.group(2)), MONTHS.index(m.group(1))) if m else None


def load_contract(p: Path) -> pd.DataFrame:
    raw = np.fromfile(p, dtype=np.uint8)
    hs = struct.unpack("<I", raw[4:8].tobytes())[0]
    a = np.frombuffer(raw[hs:hs + (len(raw) - hs) // 40 * 40].tobytes(), dtype=REC)
    ts = pd.to_datetime(a["dt"] - SC_EPOCH_US, unit="us", utc=True)
    days = np.unique(a["dt"] // 86_400_000_000)
    tick_stored = len(a) / max(len(days), 1) > 5000
    if tick_stored:
        # Tick-stored file: aggregate deterministically to 1-minute bars from the TRADE price (close field) only.
        # One-tick records' high/low fields hold quotes, not trades (MANIFEST caveat), so they are not used.
        t = pd.DataFrame({"px": a["c"].astype(np.float64), "v": a["v"].astype(np.int64)}, index=ts)
        g = t.groupby(t.index.floor("min"))
        bars = pd.DataFrame({"open": g.px.first(), "high": g.px.max(), "low": g.px.min(), "close": g.px.last(), "volume": g.v.sum()})
        ts = bars.index
    else:
        bars = pd.DataFrame({"open": a["o"].astype(np.float64), "high": a["h"].astype(np.float64), "low": a["l"].astype(np.float64),
                             "close": a["c"].astype(np.float64), "volume": a["v"].astype(np.int64)}, index=ts)
    et = ts.tz_convert("America/New_York")
    bars["tday"] = (et + pd.Timedelta(hours=6)).date
    bars.attrs["tick_stored"] = bool(tick_stored)
    return bars


def build(root: str, suffix: str, start: str, end: str):
    files = sorted((Path(f) for f in glob.glob(str(DATA / f"{root}[FGHJKMNQUVXZ][0-9][0-9]-{suffix}.scid"))
                    if os.path.getsize(f) > 56), key=lambda p: expiry_key(p.name))
    lo, hi = pd.Timestamp(start).date(), pd.Timestamp(end).date()
    meta = {"root": root, "suffix": suffix, "window": [start, end], "source_files": [], "duplicates_dropped": 0}
    frames = {}
    for p in files:
        d = load_contract(p)
        d = d[(d.tday >= lo) & (d.tday <= hi)]            # hard window FIRST
        dup = d.index.duplicated(keep="first")
        meta["duplicates_dropped"] += int(dup.sum())
        d = d[~dup]
        meta["source_files"].append({"file": p.name, "sha256": sha256(p), "rows_in_window": int(len(d)),
                                     "tick_stored_aggregated_to_1m": bool(load_contract.__dict__.get("_last_tick", False) or d.attrs.get("tick_stored", False))})
        if len(d):
            frames[p.name] = d
    if not frames:
        return None, meta
    # prior-session volume leader, never backward
    vol = pd.DataFrame({k: v.groupby("tday").volume.sum() for k, v in frames.items()}).fillna(0).sort_index()
    order = {k: expiry_key(k) for k in frames}
    days = list(vol.index)
    chosen, current = {}, None
    for i, d in enumerate(days):
        if i == 0:
            cand = vol.loc[d]
        else:
            cand = vol.loc[days[i - 1]]
        leader = cand[cand > 0].idxmax() if (cand > 0).any() else current
        if current is None or (leader is not None and order[leader] > order[current]):
            current = leader
        chosen[d] = current
    parts, rolls, prev = [], [], None
    for d in days:
        k = chosen[d]
        f = frames[k]
        seg = f[f.tday == d]
        if seg.empty:
            continue
        parts.append(seg.assign(symbol=k.split(".")[0]))
        if k != prev:
            rolls.append({"trading_day": str(d), "from": prev, "to": k})
            prev = k
    out = pd.concat(parts).sort_index()
    out = out[~out.index.duplicated(keep="first")]
    # intra-session gaps (count only): consecutive bars > 5 min apart within a trading day, excluding 17:00-18:00 ET halt
    gaps = 0
    for _, g in out.groupby("tday"):
        dts = np.diff(g.index.asi8) / 60e9
        gaps += int((dts > 5).sum())
    meta.update({"rows": int(len(out)), "first_utc": str(out.index.min()), "last_utc": str(out.index.max()),
                 "trading_days": int(out.tday.nunique()), "roll_schedule": rolls,
                 "intra_session_gaps_gt5min": gaps, "timestamp_monotonic": bool(out.index.is_monotonic_increasing)})
    return out.drop(columns=["tday"]), meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--suffix", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out-dir", default=str(HERE / "validation_data" / "SEALED"))
    ap.add_argument("--test-label", default=None, help="label for builds on ALREADY-SEEN data (not sealed)")
    a = ap.parse_args()
    out, meta = build(a.root, a.suffix, a.start, a.end)
    od = Path(a.out_dir)
    od.mkdir(parents=True, exist_ok=True)
    tag = f"{a.test_label}_" if a.test_label else ""
    name = f"{tag}{a.root}_continuous_1m_{a.start}_{a.end}.parquet"
    if out is None:
        meta["status"] = "NO_DATA_IN_WINDOW"
    else:
        p = od / name
        if p.exists():
            raise SystemExit(f"REFUSED: {p} exists (append-only; never overwrite a sealed dataset)")
        out.to_parquet(p)
        meta["dataset_file"] = str(p)
        meta["dataset_sha256"] = sha256(p)
        if not a.test_label:
            os.chmod(p, stat.S_IREAD)                      # sealed read-only
            meta["sealed_read_only"] = True
        meta["status"] = "BUILT"
    meta["generated_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    meta["policy"] = "metadata only; no prices/returns/OHLC statistics emitted"
    mp = od / (name.replace(".parquet", ".META.json"))
    mp.write_text(json.dumps(meta, indent=1, default=str))
    safe = {k: meta[k] for k in ("status", "rows", "first_utc", "last_utc", "trading_days", "duplicates_dropped",
                                 "intra_session_gaps_gt5min", "dataset_sha256") if k in meta}
    safe["rolls"] = len(meta.get("roll_schedule", []))
    print(json.dumps(safe, indent=1, default=str))


if __name__ == "__main__":
    main()
