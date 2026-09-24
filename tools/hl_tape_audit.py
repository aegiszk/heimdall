"""Completeness audit for the prospective HL tape (tools/hl_trade_recorder.py).

Compares recorded non-snapshot trades per exchange-time minute with the independent per-minute trade
count `n` from Hyperliquid's public 1m candles. Read-only; one info request per coin.
Candles only cover the most recent 5000 minutes (~3.5 days), so audit at least every 3 days.

Usage: python tools/hl_tape_audit.py [--root data/hl_tape] [--days 2026-09-23 ...]
"""

from __future__ import annotations

import argparse
import collections
import json
import urllib.request
from pathlib import Path

INFO_URL = "https://api.hyperliquid.xyz/info"


def recorded_counts(root: Path, days: list[str] | None) -> dict[str, collections.Counter]:
    counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    dirs = [root / "trades" / d for d in days] if days else sorted((root / "trades").iterdir())
    for day_dir in dirs:
        for f in sorted(day_dir.glob("*.jsonl")):
            with f.open(encoding="ascii") as fh:
                for line in fh:
                    r = json.loads(line)
                    if not r["snap"]:
                        counts[r["coin"]][r["ex_ms"] // 60000] += 1
    return counts


def candle_counts(coin: str, first_min: int, last_min: int) -> dict[int, int]:
    body = {"type": "candleSnapshot", "req": {"coin": coin, "interval": "1m",
                                              "startTime": first_min * 60000, "endTime": last_min * 60000}}
    req = urllib.request.Request(INFO_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    return {x["t"] // 60000: x["n"] for x in data if first_min <= x["t"] // 60000 <= last_min}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="data/hl_tape")
    ap.add_argument("--days", nargs="*")
    args = ap.parse_args()
    report = {}
    for coin, per_min in sorted(recorded_counts(Path(args.root), args.days).items()):
        minutes = sorted(per_min)
        if len(minutes) < 3:
            continue
        ref = candle_counts(coin, minutes[1], minutes[-2])  # drop partial first/last minute
        rec = sum(per_min[m] for m in ref)
        total = sum(ref.values())
        gaps = [m for m in ref if per_min[m] < ref[m]]
        report[coin] = {"minutes": len(ref), "recorded": rec, "candle_n": total,
                        "ratio": round(rec / total, 5) if total else None, "minutes_short": len(gaps)}
        print(coin, report[coin])
    (Path(args.root) / "audit_latest.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
