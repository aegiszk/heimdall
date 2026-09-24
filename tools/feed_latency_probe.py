"""Measure event-timestamp -> local-receipt latency for Binance USD-M and Hyperliquid trades
FROM THIS HOST, with an independent SNTP clock-offset log. Read-only; no keys, no orders.

Outputs (one run directory):
    msgs.csv   venue,coin,event_ms,trade_ms,recv_ns,snap
               Binance aggTrade: event_ms = E (event time), trade_ms = T (trade/match time)
               Hyperliquid trades: event_ms = trade_ms = `time` (block time)
               snap=1 marks the HL snapshot batch sent on subscribe (excluded from latency)
    ntp.csv    server,t0_ns,offset_ms,rtt_ms   (offset = server_clock - local_clock)
    summary.json  written by `--summarize DIR`

Latency_corrected = (recv_ns/1e6 + offset_ms) - event_ms, using the median offset of the
lowest-RTT third of all SNTP samples in the run.

Usage:
    python tools/feed_latency_probe.py --minutes 65 --out data/latency_probe/<run>
    python tools/feed_latency_probe.py --summarize data/latency_probe/<run>
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import socket
import struct
import time
from pathlib import Path

BINANCE_URL = "wss://fstream.binance.com/market/stream?streams=btcusdt@aggTrade/ethusdt@aggTrade/solusdt@aggTrade"
HL_URL = "wss://api.hyperliquid.xyz/ws"
HL_COINS = ("BTC", "ETH", "SOL")
NTP_SERVERS = ("time.google.com", "time.cloudflare.com", "pool.ntp.org")
NTP_EPOCH_DELTA = 2208988800  # seconds between 1900-01-01 and 1970-01-01


def _ntp_to_ns(seconds: int, fraction: int) -> int:
    return (seconds - NTP_EPOCH_DELTA) * 1_000_000_000 + (fraction * 1_000_000_000 >> 32)


def sntp_offset(t0: int, t1: int, t2: int, t3: int) -> tuple[float, float]:
    """Standard NTP: offset = ((t1-t0)+(t2-t3))/2, rtt = (t3-t0)-(t2-t1); inputs ns, outputs ms."""
    return ((t1 - t0) + (t2 - t3)) / 2e6, ((t3 - t0) - (t2 - t1)) / 1e6


def sntp_query(server: str, timeout: float = 2.0) -> tuple[float, float]:
    packet = b"\x23" + 47 * b"\0"  # LI=0, VN=4, Mode=3 (client)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        t0 = time.time_ns()
        sock.sendto(packet, (server, 123))
        data, _ = sock.recvfrom(48)
        t3 = time.time_ns()
    if len(data) < 48:
        raise ValueError("short SNTP reply")
    fields = struct.unpack("!12I", data[:48])
    t1 = _ntp_to_ns(fields[8], fields[9])    # receive timestamp
    t2 = _ntp_to_ns(fields[10], fields[11])  # transmit timestamp
    return sntp_offset(t0, t1, t2, t3)


async def ntp_loop(out: Path, stop_at: float) -> None:
    with (out / "ntp.csv").open("a", newline="") as fh:
        w = csv.writer(fh)
        while time.monotonic() < stop_at:
            for server in NTP_SERVERS:
                for _ in range(3):
                    try:
                        off, rtt = await asyncio.to_thread(sntp_query, server)
                        w.writerow([server, time.time_ns(), f"{off:.3f}", f"{rtt:.3f}"])
                    except (OSError, ValueError) as exc:
                        w.writerow([server, time.time_ns(), "", f"ERR {exc}"])
            fh.flush()
            await asyncio.sleep(max(0.0, min(300.0, stop_at - time.monotonic())))


async def binance_loop(writer, stop_at: float) -> None:
    import websockets

    while time.monotonic() < stop_at:
        try:
            async with websockets.connect(BINANCE_URL, max_size=None, ping_interval=20) as ws:
                while time.monotonic() < stop_at:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                    recv_ns = time.time_ns()
                    d = json.loads(raw)["data"]
                    writer.writerow(["binance", d["s"], d["E"], d["T"], recv_ns, 0])
        except Exception as exc:  # noqa: BLE001
            writer.writerow(["binance", "DISCONNECT", "", "", time.time_ns(), str(exc)[:80]])
            await asyncio.sleep(2)


async def hl_loop(writer, stop_at: float) -> None:
    import websockets

    while time.monotonic() < stop_at:
        try:
            async with websockets.connect(HL_URL, max_size=None, ping_interval=20) as ws:
                for coin in HL_COINS:
                    await ws.send(json.dumps({"method": "subscribe", "subscription": {"type": "trades", "coin": coin}}))
                first = set(HL_COINS)
                while time.monotonic() < stop_at:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                    recv_ns = time.time_ns()
                    msg = json.loads(raw)
                    if msg.get("channel") != "trades" or not msg.get("data"):
                        continue
                    coin = msg["data"][0]["coin"]
                    snap = 1 if coin in first else 0
                    first.discard(coin)
                    for t in msg["data"]:
                        writer.writerow(["hyperliquid", t["coin"], t["time"], t["time"], recv_ns, snap])
        except Exception as exc:  # noqa: BLE001
            writer.writerow(["hyperliquid", "DISCONNECT", "", "", time.time_ns(), str(exc)[:80]])
            await asyncio.sleep(2)


async def probe(minutes: float, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    stop_at = time.monotonic() + minutes * 60
    with (out / "msgs.csv").open("a", newline="") as fh:
        w = csv.writer(fh)

        async def flusher():
            while time.monotonic() < stop_at:
                await asyncio.sleep(5)
                fh.flush()

        await asyncio.gather(ntp_loop(out, stop_at), binance_loop(w, stop_at), hl_loop(w, stop_at), flusher())


def summarize(run: Path) -> dict:
    import numpy as np
    import pandas as pd

    ntp = pd.read_csv(run / "ntp.csv", names=["server", "t0_ns", "offset_ms", "rtt_ms"])
    ntp = ntp[pd.to_numeric(ntp.offset_ms, errors="coerce").notna()].astype({"offset_ms": float, "rtt_ms": float})
    best = ntp[ntp.rtt_ms <= ntp.rtt_ms.quantile(1 / 3)]
    offset = float(best.offset_ms.median())
    msgs = pd.read_csv(run / "msgs.csv", names=["venue", "coin", "event_ms", "trade_ms", "recv_ns", "snap"])
    disconnects = msgs[msgs.coin == "DISCONNECT"]
    msgs = msgs[(msgs.coin != "DISCONNECT")].copy()
    msgs["snap"] = pd.to_numeric(msgs.snap, errors="coerce").fillna(0).astype(int)
    msgs = msgs[msgs.snap == 0]
    for c in ("event_ms", "trade_ms", "recv_ns"):
        msgs[c] = pd.to_numeric(msgs[c])
    recv_ms = msgs.recv_ns / 1e6
    msgs["lat_event_raw"] = recv_ms - msgs.event_ms
    msgs["lat_event"] = recv_ms + offset - msgs.event_ms
    msgs["lat_trade"] = recv_ms + offset - msgs.trade_ms
    q = lambda s: {f"p{p}": round(float(np.percentile(s, p)), 1) for p in (1, 10, 50, 90, 99)}
    out = {
        "run": str(run),
        "duration_min": round((msgs.recv_ns.max() - msgs.recv_ns.min()) / 6e10, 1),
        "ntp": {"samples_ok": int(len(ntp)), "offset_ms_used": round(offset, 3),
                "offset_ms_range_all": [round(float(ntp.offset_ms.min()), 3), round(float(ntp.offset_ms.max()), 3)],
                "rtt_ms_median": round(float(ntp.rtt_ms.median()), 2),
                "per_server_median_offset": ntp.groupby("server").offset_ms.median().round(3).to_dict()},
        "disconnects": disconnects.venue.value_counts().to_dict(),
        "latency_ms": {},
    }
    for (venue, coin), g in msgs.groupby(["venue", "coin"]):
        entry = {"n": int(len(g)), "event_to_recv_corrected": q(g.lat_event), "event_to_recv_raw_clock": q(g.lat_event_raw)}
        if venue == "binance":
            entry["trade_T_to_recv_corrected"] = q(g.lat_trade)
        out["latency_ms"][f"{venue}:{coin}"] = entry
    (run / "summary.json").write_text(json.dumps(out, indent=1))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--minutes", type=float, default=65)
    ap.add_argument("--out", default=None)
    ap.add_argument("--summarize", default=None)
    args = ap.parse_args()
    if args.summarize:
        print(json.dumps(summarize(Path(args.summarize)), indent=1))
        return
    out = Path(args.out or f"data/latency_probe/{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}")
    asyncio.run(probe(args.minutes, out))
    print(json.dumps(summarize(out), indent=1))


if __name__ == "__main__":
    main()
