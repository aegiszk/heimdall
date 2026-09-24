"""READ-ONLY prospective recorder for Hyperliquid public trades (wallet-attributed tape).

Subscribes to the public `trades` WebSocket channel, which carries `users: [buyer, seller]`,
and appends one JSON object per trade to hourly UTC files:

    data/hl_tape/trades/YYYY-MM-DD/HH.jsonl
    data/hl_tape/events/YYYY-MM-DD.jsonl   (connect / subscribe / disconnect / reject /
                                            clock_offset every 10 min; correct recv_ns with it)

Record fields:
    ex_ms   exchange (block) timestamp, ms            recv_ns  local wall-clock receive time, ns
    coin, side ('B' buyer-aggressor / 'A' seller-aggressor), px, sz (exact decimal strings)
    tid, hash, buyer, seller, snap (True = part of the snapshot sent on subscribe; recv_ns is
    then NOT a latency observation)

No keys, no signing, no order path. Files are opened in append mode only; prior bytes are
never rewritten. Duplicates (coin, tid) seen on reconnect snapshots are dropped.

Usage:
    python tools/hl_trade_recorder.py                     # default coins
    python tools/hl_trade_recorder.py --coins BTC ETH --out data/hl_tape --hours 1
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import datetime as dt
import json
import os
import re
import time
from pathlib import Path

WS_URL = "wss://api.hyperliquid.xyz/ws"
DEFAULT_COINS = (
    "BTC", "ETH", "SOL",                                   # H1 bounded subset
    "xyz:SP500", "xyz:XYZ100",                             # H2 (ES / NQ analogs)
    "xyz:CL", "xyz:GOLD",                                  # Lucid CL / GC analogs
)
_ADDR = re.compile(r"^0x[0-9a-f]{40}$")
_DEC = re.compile(r"^\d+(\.\d+)?$")


def parse_trade(item: dict, recv_ns: int, snapshot: bool) -> dict:
    """Validate one WsTrade and return the canonical record. Raises ValueError on bad input."""
    users = item.get("users")
    if not isinstance(users, list) or len(users) != 2:
        raise ValueError("trade must carry users=[buyer, seller]")
    buyer, seller = (str(u).lower() for u in users)
    if not (_ADDR.match(buyer) and _ADDR.match(seller)):
        raise ValueError("buyer/seller must be 0x-prefixed 20-byte hex addresses")
    px, sz = str(item.get("px")), str(item.get("sz"))
    if not (_DEC.match(px) and _DEC.match(sz)) or float(px) <= 0 or float(sz) <= 0:
        raise ValueError("px/sz must be positive decimal strings")
    side = item.get("side")
    if side not in ("A", "B"):
        raise ValueError("side must be 'A' or 'B'")
    ex_ms, tid = item.get("time"), item.get("tid")
    if not isinstance(ex_ms, int) or ex_ms <= 0 or not isinstance(tid, int):
        raise ValueError("time/tid must be integers")
    return {
        "ex_ms": ex_ms, "recv_ns": int(recv_ns), "coin": str(item.get("coin")), "side": side,
        "px": px, "sz": sz, "tid": tid, "hash": str(item.get("hash", "")),
        "buyer": buyer, "seller": seller, "snap": bool(snapshot),
    }


class AppendOnlyHourlyWriter:
    """Append records to hourly files keyed by the UTC hour of recv_ns; fsync on flush()."""

    def __init__(self, root: str | Path, dedup_window: int = 500_000) -> None:
        self.root = Path(root)
        self._handles: dict[Path, object] = {}
        self._seen: set[tuple[str, int]] = set()
        self._order: collections.deque = collections.deque()
        self._window = dedup_window
        self.written = 0
        self.dropped_duplicates = 0

    def _path(self, recv_ns: int) -> Path:
        t = dt.datetime.fromtimestamp(recv_ns / 1e9, dt.timezone.utc)
        return self.root / "trades" / t.strftime("%Y-%m-%d") / f"{t:%H}.jsonl"

    def write(self, record: dict) -> bool:
        key = (record["coin"], record["tid"])
        if key in self._seen:
            self.dropped_duplicates += 1
            return False
        self._seen.add(key)
        self._order.append(key)
        if len(self._order) > self._window:
            self._seen.discard(self._order.popleft())
        path = self._path(record["recv_ns"])
        handle = self._handles.get(path)
        if handle is None:
            for old in list(self._handles):  # an hour rolled over: close older files
                self._close(old)
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = self._handles[path] = path.open("ab")
        handle.write((json.dumps(record, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii"))
        self.written += 1
        return True

    def flush(self) -> None:
        for handle in self._handles.values():
            handle.flush()
            os.fsync(handle.fileno())

    def _close(self, path: Path) -> None:
        handle = self._handles.pop(path)
        handle.flush()
        os.fsync(handle.fileno())
        handle.close()

    def close(self) -> None:
        for path in list(self._handles):
            self._close(path)


def log_event(root: Path, **fields) -> None:
    now = time.time_ns()
    t = dt.datetime.fromtimestamp(now / 1e9, dt.timezone.utc)
    path = root / "events" / f"{t:%Y-%m-%d}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write((json.dumps({"recv_ns": now, **fields}, separators=(",", ":")) + "\n").encode("ascii"))


async def clock_offset_loop(out: Path, every_s: float = 600.0) -> None:
    """Log SNTP clock offsets (server - local, ms) so recv_ns can be corrected offline.
    This host's clock was measured 14.97 s fast on 2026-09-23; never trust raw recv_ns alone."""
    from feed_latency_probe import NTP_SERVERS, sntp_query  # sibling script in tools/

    while True:
        for server in NTP_SERVERS:
            try:
                offset_ms, rtt_ms = await asyncio.to_thread(sntp_query, server)
                log_event(out, event="clock_offset", server=server, offset_ms=round(offset_ms, 3), rtt_ms=round(rtt_ms, 3))
            except (OSError, ValueError) as exc:
                log_event(out, event="clock_offset_error", server=server, error=str(exc))
        await asyncio.sleep(every_s)


async def run(coins: list[str], out: Path, hours: float | None) -> None:
    import websockets  # imported here so parsing/tests need no network dependency

    asyncio.get_running_loop().create_task(clock_offset_loop(out))
    writer = AppendOnlyHourlyWriter(out)
    deadline = time.monotonic() + hours * 3600 if hours else None
    backoff = 1.0
    try:
        while deadline is None or time.monotonic() < deadline:
            try:
                async with websockets.connect(WS_URL, max_size=None, ping_interval=20) as ws:
                    log_event(out, event="connect", coins=coins)
                    for coin in coins:
                        await ws.send(json.dumps({"method": "subscribe", "subscription": {"type": "trades", "coin": coin}}))
                    first_batch = set(coins)  # first trades message per coin after subscribe = snapshot
                    backoff = 1.0
                    last_flush = time.monotonic()
                    while deadline is None or time.monotonic() < deadline:
                        raw = await asyncio.wait_for(ws.recv(), timeout=60)
                        recv_ns = time.time_ns()
                        msg = json.loads(raw)
                        channel = msg.get("channel")
                        if channel == "subscriptionResponse":
                            log_event(out, event="subscribed", sub=msg.get("data"))
                        elif channel == "trades":
                            items = msg.get("data") or []
                            coin = items[0].get("coin") if items else None
                            snapshot = coin in first_batch
                            first_batch.discard(coin)
                            for item in items:
                                try:
                                    writer.write(parse_trade(item, recv_ns, snapshot))
                                except ValueError as exc:
                                    log_event(out, event="reject", reason=str(exc), item=item)
                        elif channel == "error":
                            log_event(out, event="server_error", data=msg.get("data"))
                        if time.monotonic() - last_flush >= 1.0:
                            writer.flush()
                            last_flush = time.monotonic()
            except Exception as exc:  # noqa: BLE001 - log every failure, then reconnect
                writer.flush()
                log_event(out, event="disconnect", error=f"{type(exc).__name__}: {exc}", backoff_s=backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)
    finally:
        writer.close()
        log_event(out, event="stop", written=writer.written, dropped_duplicates=writer.dropped_duplicates)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--coins", nargs="+", default=list(DEFAULT_COINS))
    ap.add_argument("--out", default="data/hl_tape")
    ap.add_argument("--hours", type=float, default=None, help="stop after N hours (default: run until killed)")
    args = ap.parse_args()
    asyncio.run(run(args.coins, Path(args.out), args.hours))


if __name__ == "__main__":
    main()
