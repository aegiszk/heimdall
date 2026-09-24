"""Free Dukascopy 1-minute BID+ASK candle pull (FX majors + XAUUSD) for the external-strategy program.

Source: https://datafeed.dukascopy.com/datafeed/{SYM}/{YYYY}/{MM0}/{DD}/{BID|ASK}_candles_min_1.bi5
(month is 0-based; LZMA; 24-byte big-endian records: uint32 sec-from-day-start UTC, open, close, low, high
as uint32 price*divisor, float32 volume). Verified live 2026-09-24 (USDJPY/XAUUSD decoded).

Resumable: one parquet per (symbol, side, day) cached under data/fx_dukascopy/raw/; failures logged and retried.
No paid service. Read-only public endpoint.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import lzma
import struct
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "fx_dukascopy" / "raw"
DIV = {"USDJPY": 1e3, "XAUUSD": 1e3}


def fetch(sym: str, side: str, day: dt.date, tries: int = 6) -> str:
    out = OUT / sym / side / f"{day.isoformat()}.npy"
    if out.exists():
        return "cached"
    url = (f"https://datafeed.dukascopy.com/datafeed/{sym}/{day.year}/{day.month - 1:02d}/"
           f"{day.day:02d}/{side}_candles_min_1.bi5")
    for k in range(tries):
        try:
            raw = urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
            b = lzma.decompress(raw) if raw else b""
            n = len(b) // 24
            arr = np.array([struct.unpack(">IIIIIf", b[i * 24:(i + 1) * 24]) for i in range(n)],
                           dtype="float64").reshape(-1, 6)
            out.parent.mkdir(parents=True, exist_ok=True)
            np.save(out, arr)
            return f"ok {n}"
        except Exception as e:  # noqa: BLE001 - network flakiness is expected; logged
            last = f"{type(e).__name__}"
            time.sleep(2 + 3 * k)
    return f"FAIL {last}"


def build(sym: str) -> None:
    div = DIV.get(sym, 1e5)
    frames = []
    for side in ("BID", "ASK"):
        rows = []
        for f in sorted((OUT / sym / side).glob("*.npy")):
            a = np.load(f)
            if not len(a):
                continue
            base = pd.Timestamp(f.stem, tz="UTC")
            d = pd.DataFrame(a, columns=["sec", "open", "close", "low", "high", "volume"])
            d.index = base + pd.to_timedelta(d.pop("sec"), unit="s")
            d[["open", "close", "low", "high"]] /= div
            rows.append(d)
        s = pd.concat(rows).sort_index()
        s = s[s["volume"] > 0]  # Dukascopy pads flat zero-volume minutes; drop them
        frames.append(s.add_prefix(side.lower() + "_"))
    df = frames[0].join(frames[1], how="inner")
    df.to_parquet(ROOT / "data" / "fx_dukascopy" / f"{sym}_1m_bidask.parquet")
    print(sym, len(df), df.index.min(), df.index.max())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", nargs="+", default=["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "NZDUSD", "XAUUSD"])
    p.add_argument("--start", default="2022-01-01")
    p.add_argument("--end", default="2026-09-18")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--build-only", action="store_true")
    a = p.parse_args()
    if not a.build_only:
        days = [d.date() for d in pd.date_range(a.start, a.end) if d.weekday() != 5]
        jobs = [(s, side, d) for s in a.symbols for side in ("BID", "ASK") for d in days]
        log = ROOT / "data" / "fx_dukascopy" / "pull_log.txt"
        log.parent.mkdir(parents=True, exist_ok=True)
        with cf.ThreadPoolExecutor(a.workers) as ex, open(log, "a") as lg:
            for (s, side, d), r in zip(jobs, ex.map(lambda j: fetch(*j), jobs)):
                if r.startswith("FAIL"):
                    lg.write(f"{s} {side} {d} {r}\n")
        print("pull done")
    for s in a.symbols:
        build(s)


if __name__ == "__main__":
    main()
