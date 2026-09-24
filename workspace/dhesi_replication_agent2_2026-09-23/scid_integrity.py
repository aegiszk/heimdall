"""Post-harvest INTEGRITY ONLY for untouched Sierra .scid files (Agent 2).

Allowed by the freshness firewall: file size, SHA-256, modification time, record count, first/last timestamp, storage
granularity (records per active day), contract coverage per root, missing-day counts. This script reads ONLY the
timestamp field (first 8 bytes of each 40-byte record). It never reads prices, volumes, or computes returns.

Usage: python scid_integrity.py <ROOT_PREFIX>... e.g.  MNQ NQ ES MES RTY M2K YM MYM CL GC
Writes UNTOUCHED_SCID_MANIFEST.json next to this script. Copies are NOT made here (no reading of contents).
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import os
import re
import struct
import sys
from pathlib import Path

import numpy as np

DATA = Path("C:/SierraChart/Data")
HERE = Path(__file__).resolve().parent
EPOCH = dt.datetime(1899, 12, 30)
MONTHS = "FGHJKMNQUVXZ"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def timestamps_only(p: Path) -> np.ndarray:
    raw = np.memmap(p, dtype=np.uint8, mode="r")
    hs = struct.unpack("<I", bytes(raw[4:8]))[0]
    n = (len(raw) - hs) // 40
    rec = np.ndarray((n,), dtype=np.dtype([("dt", "<i8"), ("rest", "V32")]), buffer=raw, offset=hs)
    return np.asarray(rec["dt"])


def contract_key(name: str):
    m = re.match(r"^([A-Z0-9]+?)([FGHJKMNQUVXZ])(\d{2})-", name)
    return (m.group(1), 2000 + int(m.group(3)), MONTHS.index(m.group(2))) if m else None


def main(roots):
    out = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "policy": "timestamps/metadata only; no prices read",
           "files": []}
    for root in roots:
        for f in sorted(glob.glob(str(DATA / f"{root}[FGHJKMNQUVXZ][0-9][0-9]-*.scid"))):
            p = Path(f)
            if p.stat().st_size <= 56:
                continue
            ts = timestamps_only(p)
            days = np.unique(ts // 86_400_000_000)
            per_day = len(ts) / max(len(days), 1)
            k = contract_key(p.name)
            out["files"].append({
                "file": p.name, "root": root, "contract_year": k[1] if k else None, "contract_month_index": k[2] if k else None,
                "bytes": p.stat().st_size, "mtime_utc": dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc).isoformat(),
                "sha256": sha256(p), "records": int(len(ts)),
                "first_utc": str(EPOCH + dt.timedelta(microseconds=int(ts[0]))),
                "last_utc": str(EPOCH + dt.timedelta(microseconds=int(ts[-1]))),
                "active_days": int(len(days)), "records_per_active_day": round(per_day, 1),
                "storage_inferred": "1-tick" if per_day > 5000 else "1-minute",
                "timestamp_nonmonotonic": int((np.diff(ts) < 0).sum())})
            print(out["files"][-1]["file"], out["files"][-1]["records"], out["files"][-1]["storage_inferred"],
                  out["files"][-1]["first_utc"][:10], "->", out["files"][-1]["last_utc"][:10], flush=True)
    cov = {}
    for r in roots:
        ks = sorted((x["contract_year"], x["contract_month_index"]) for x in out["files"] if x["root"] == r and x["contract_year"])
        cov[r] = {"contracts": len(ks), "first": ks[0] if ks else None, "last": ks[-1] if ks else None}
    out["coverage"] = cov
    (HERE / "UNTOUCHED_SCID_MANIFEST.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:] or ["MNQ", "NQ", "ES", "MES", "RTY", "M2K", "YM", "MYM", "CL", "GC"])
