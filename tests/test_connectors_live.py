import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.data.connectors import CcxtReadOnly


VENUES = ("okx", "hyperliquid", "binance")
ASSETS = ("BTC", "ETH")


def test_live_public_connectors():
    table = []
    failures = []

    for venue in VENUES:
        try:
            client = CcxtReadOnly(venue)
            rows = client.ohlcv("BTC", timeframe="1h", limit=10)
            assert len(rows) == 10, f"{venue} returned {len(rows)} BTC candles"
            for row in rows:
                assert len(row) >= 6, f"{venue} returned malformed candle: {row!r}"
                _, open_, high, low, close, volume = row[:6]
                assert open_ > 0 and high > 0 and low > 0 and close > 0
                assert volume >= 0

            funding = {}
            for asset in ASSETS:
                funding[asset] = client.funding_bps(asset, "now")
                assert isinstance(funding[asset], float)
                assert math.isfinite(funding[asset])

            oi_btc = client.open_interest("BTC")
            assert isinstance(oi_btc, float)
            assert math.isfinite(oi_btc)
            assert oi_btc > 0

            table.append((venue, funding["BTC"], funding["ETH"], oi_btc))
        except Exception as exc:
            failures.append((venue, exc))

    print("venue | funding_bps(BTC) | funding_bps(ETH) | oi(BTC)")
    for venue, btc_bps, eth_bps, oi_btc in table:
        print(f"{venue} | {btc_bps:.8f} | {eth_bps:.8f} | {oi_btc:.2f}")
    for venue, exc in failures:
        print(f"{venue} | FAILED | FAILED | FAILED")
        print(f"{venue} failure: {exc}")

    assert not failures, "; ".join(f"{venue}: {exc}" for venue, exc in failures)
