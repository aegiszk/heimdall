#!/usr/bin/env python3
"""Calibrate L2 slippage from a book snapshot or live ccxt fetch."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.execution.fills import slippage_bps


DEFAULT_SIZES_USD = (1_000, 10_000, 50_000, 100_000, 250_000)


def sample_btc_book() -> dict[str, list[list[float]]]:
    """Synthetic 10-level BTC book deep enough for offline calibration tests."""

    mid = 100_000.0
    bids = [[mid - 10 - i * 25, 0.55 + i * 0.08] for i in range(10)]
    asks = [[mid + 10 + i * 25, 0.55 + i * 0.08] for i in range(10)]
    return {"bids": bids, "asks": asks}


def load_book(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def fetch_book(exchange_id: str, symbol: str, limit: int | None = None) -> Any:
    try:
        import ccxt
    except ImportError as exc:
        raise SystemExit("ccxt is not installed; pass --book or install ccxt") from exc

    exchange_cls = getattr(ccxt, exchange_id)
    exchange = exchange_cls({"enableRateLimit": True})
    return exchange.fetch_order_book(symbol, limit=limit)


def calibrate_table(
    book: Any,
    sizes_usd: Iterable[float] = DEFAULT_SIZES_USD,
    *,
    side: str = "buy",
) -> list[tuple[float, float]]:
    return [
        (float(size), slippage_bps(float(size), book, side=side, qty_is_notional=True))
        for size in sizes_usd
    ]


def print_table(rows: Iterable[tuple[float, float]]) -> None:
    print("size|slippage_bps")
    for size, slip in rows:
        print(f"{size:,.0f}|{slip:.4f}")


def parse_sizes(raw: str) -> list[float]:
    return [float(part.strip().replace("_", "")) for part in raw.split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", type=Path, help="Path to OKX/ccxt/Hyperliquid order book JSON")
    parser.add_argument("--exchange", default="okx", help="ccxt exchange id for live fetch")
    parser.add_argument("--symbol", default="BTC/USDT", help="ccxt symbol for live fetch")
    parser.add_argument("--limit", type=int, default=None, help="ccxt order book depth limit")
    parser.add_argument("--fetch", action="store_true", help="Fetch order book with ccxt")
    parser.add_argument("--side", choices=("buy", "sell"), default="buy", help="Market order side")
    parser.add_argument(
        "--sizes",
        default="1000,10000,50000,100000,250000",
        help="Comma-separated USD order sizes",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sizes = parse_sizes(args.sizes)

    if args.book:
        book = load_book(args.book)
    elif args.fetch:
        book = fetch_book(args.exchange, args.symbol, args.limit)
    else:
        book = sample_btc_book()

    print_table(calibrate_table(book, sizes, side=args.side))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
