"""Read-only market-data via ccxt public endpoints."""
from __future__ import annotations

from math import isfinite
from time import sleep
from typing import Any, Protocol

class DataClient(Protocol):
    def funding_bps(self, asset: str, ts: str) -> float: ...
    def ohlcv(self, asset: str, timeframe: str, limit: int) -> list: ...
    def open_interest(self, asset: str) -> float: ...

class CcxtReadOnly:
    ASSETS = frozenset({"BTC", "ETH"})
    VENUES = frozenset({"okx", "hyperliquid", "binance"})
    REQUEST_TIMEOUT_MS = 15_000
    REQUEST_ATTEMPTS = 2

    def __init__(self, venue: str):
        import ccxt

        venue = venue.lower()
        if venue not in self.VENUES:
            raise ValueError(f"Unsupported venue {venue!r}; expected one of {sorted(self.VENUES)}")

        self.venue = venue
        config: dict[str, Any] = {
            "enableRateLimit": True,
            "timeout": self.REQUEST_TIMEOUT_MS,
        }
        if venue == "okx":
            config["options"] = {
                "defaultType": "swap",
                "fetchMarkets": {"types": ["swap"]},
            }
        elif venue == "binance":
            config["options"] = {"defaultType": "future"}

        self.ex = getattr(ccxt, venue)(config)
        self._symbols: dict[str, str] = {}

    def ohlcv(self, asset, timeframe="1h", limit=720):
        self._require_public_method("fetchOHLCV")
        symbol = self._symbol(asset)
        rows = self._call("fetch_ohlcv", symbol, timeframe=timeframe, limit=limit)
        if not isinstance(rows, list):
            raise RuntimeError(f"{self.venue} fetch_ohlcv({symbol}) returned non-list data")
        return rows

    def funding_bps(self, asset, ts):
        symbol = self._symbol(asset)
        fr = self._call("fetch_funding_rate", symbol)
        return self._funding_bps_from_row(fr, f"{self.venue} fetch_funding_rate({symbol})")

    def open_interest(self, asset):
        self._require_public_method("fetchOpenInterest")
        symbol = self._symbol(asset)
        market = self.ex.market(symbol)
        oi = self._call("fetch_open_interest", symbol)

        value = self._first_number(
            oi,
            "openInterestValue",
            "quoteVolume",
            context=f"{self.venue} fetch_open_interest({symbol})",
        )
        if value is not None:
            return value
        info_value = self._first_info_number(oi, "oiUsd", "openInterestValue", "sumOpenInterestValue")
        if info_value is not None:
            return self._finite(info_value, f"{self.venue} open interest info value for {symbol}")

        amount = self._first_number(
            oi,
            "openInterestAmount",
            "baseVolume",
            "openInterest",
            context=f"{self.venue} fetch_open_interest({symbol})",
        )
        if amount is None:
            info_amount = self._first_info_number(oi, "openInterest", "oi", "oiCcy")
            if info_amount is not None:
                amount = info_amount

        if amount is None:
            raise RuntimeError(
                f"{self.venue} fetch_open_interest({symbol}) returned no usable OI amount/value"
            )

        price = self._current_price(symbol)
        contract_size = self._number(market.get("contractSize")) or 1.0
        if self.venue == "okx" and market.get("contract"):
            amount *= contract_size
        return self._finite(amount * price, f"{self.venue} notional open interest for {symbol}")

    def funding_history(self, asset, since_ms, limit):
        if not self.ex.has.get("fetchFundingRateHistory"):
            return []
        symbol = self._symbol(asset)
        rows = self._call("fetch_funding_rate_history", symbol, since=since_ms, limit=limit)
        if not isinstance(rows, list):
            raise RuntimeError(f"{self.venue} fetch_funding_rate_history({symbol}) returned non-list data")

        history = []
        for row in rows:
            ts = row.get("timestamp")
            if ts is None:
                raise RuntimeError(f"{self.venue} funding history row for {symbol} is missing timestamp")
            history.append([
                int(ts),
                self._funding_bps_from_row(row, f"{self.venue} funding history row for {symbol}"),
            ])
        return history

    def _symbol(self, asset: str) -> str:
        asset = asset.upper()
        if asset not in self.ASSETS:
            raise ValueError(f"Unsupported asset {asset!r}; expected BTC or ETH")
        if asset in self._symbols:
            return self._symbols[asset]

        markets = self._call("load_markets")
        candidates = []
        for symbol, market in markets.items():
            if market.get("base") != asset:
                continue
            if not (market.get("swap") or market.get("type") == "swap"):
                continue
            if market.get("active") is False:
                continue
            candidates.append((symbol, market))

        if not candidates:
            raise RuntimeError(f"{self.venue} has no active {asset} perpetual market in ccxt metadata")

        preferred = {"USDT": 0, "USDC": 1, "USD": 2}
        symbol, _market = sorted(
            candidates,
            key=lambda item: (
                preferred.get(str(item[1].get("settle") or item[1].get("quote") or ""), 99),
                str(item[0]),
            ),
        )[0]
        self._symbols[asset] = symbol
        return symbol

    def _require_public_method(self, ccxt_has_key: str) -> None:
        if not self.ex.has.get(ccxt_has_key):
            raise RuntimeError(f"{self.venue} does not support ccxt public method {ccxt_has_key}")

    def _call(self, method: str, *args, **kwargs):
        fn = getattr(self.ex, method, None)
        if fn is None:
            raise RuntimeError(f"{self.venue} does not support ccxt public method {method}")
        last_error: Exception | None = None
        for attempt in range(self.REQUEST_ATTEMPTS):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # ccxt exception classes are runtime imports.
                last_error = exc
                transient = exc.__class__.__name__ in {
                    "NetworkError",
                    "RequestTimeout",
                    "DDoSProtection",
                    "RateLimitExceeded",
                    "ExchangeNotAvailable",
                }
                if not transient or attempt == self.REQUEST_ATTEMPTS - 1:
                    break
                sleep(0.75 * (attempt + 1))
        raise RuntimeError(
            f"{self.venue}.{method} public request failed: {last_error.__class__.__name__}: {last_error}"
        ) from last_error

    def _funding_bps_from_row(self, row: dict, context: str) -> float:
        value = self._number(row.get("fundingRate"))
        if value is None:
            value = self._first_info_number(row, "funding", "fundingRate", "lastFundingRate")
        if value is None:
            raise RuntimeError(f"{context} returned no fundingRate")
        return self._finite(value * 1e4, f"{context} funding bps")

    def _current_price(self, symbol: str) -> float:
        ticker = self._call("fetch_ticker", symbol)
        value = self._first_number(
            ticker,
            "mark",
            "last",
            "close",
            "index",
            context=f"{self.venue} fetch_ticker({symbol})",
        )
        if value is not None:
            return value

        info_value = self._first_info_number(ticker, "markPx", "markPrice", "lastPrice", "indexPrice")
        if info_value is not None:
            return self._finite(info_value, f"{self.venue} ticker info price for {symbol}")

        raise RuntimeError(f"{self.venue} fetch_ticker({symbol}) returned no usable price")

    def _first_number(self, row: dict, *keys: str, context: str) -> float | None:
        for key in keys:
            value = self._number(row.get(key))
            if value is not None:
                return self._finite(value, f"{context} {key}")
        return None

    def _first_info_number(self, row: dict, *keys: str) -> float | None:
        info = row.get("info")
        if not isinstance(info, dict):
            return None
        for key in keys:
            value = self._number(info.get(key))
            if value is not None:
                return value
        return None

    def _number(self, value: object) -> float | None:
        if value is None:
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if not isfinite(number):
            return None
        return number

    def _finite(self, value: float, context: str) -> float:
        if not isfinite(value):
            raise RuntimeError(f"{context} is not finite: {value!r}")
        return float(value)
