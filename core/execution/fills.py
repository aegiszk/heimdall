"""Realistic paper fills: book-walk slippage, turnover costs, perp funding."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Iterable, Sequence

import numpy as np


DEFAULT_BASE_SLIPPAGE_BPS = 1.0
DEFAULT_IMPACT_K = 50.0
DEFAULT_ADV_USD = 10_000_000.0


@dataclass(frozen=True)
class FillConfig:
    """Fallback slippage parameters when no L2 book is available."""

    base_bps: float
    impact_k: float
    adv: float

    @classmethod
    def from_env(cls) -> "FillConfig":
        return cls(
            base_bps=float(os.getenv("HEIMDALL_FILL_BASE_BPS", DEFAULT_BASE_SLIPPAGE_BPS)),
            impact_k=float(os.getenv("HEIMDALL_FILL_IMPACT_K", DEFAULT_IMPACT_K)),
            adv=float(os.getenv("HEIMDALL_FILL_ADV_USD", DEFAULT_ADV_USD)),
        )


DEFAULT_FILL_CONFIG = FillConfig.from_env()
BookSide = list[tuple[float, float]]


def slippage_bps(
    qty: float,
    book_snapshot: Any | None = None,
    *,
    side: str = "buy",
    adv: float | None = None,
    base_bps: float | None = None,
    impact_k: float | None = None,
    config: FillConfig = DEFAULT_FILL_CONFIG,
    qty_is_notional: bool = True,
    mid: float | None = None,
) -> float:
    """Return adverse execution slippage in bps vs mid.

    With a book, ``qty`` defaults to quote notional (USD/USDT). Market buys walk
    asks; market sells walk bids. Without a book, fallback is configurable:
    ``base_bps + impact_k * (qty / adv)``. Passing a numeric second positional
    arg preserves the old ``slippage_bps(qty, adv)`` call shape.
    """

    if isinstance(book_snapshot, (int, float)) and adv is None:
        adv = float(book_snapshot)
        book_snapshot = None

    if book_snapshot is None:
        fallback_adv = config.adv if adv is None else adv
        fallback_base = config.base_bps if base_bps is None else base_bps
        fallback_k = config.impact_k if impact_k is None else impact_k
        if fallback_adv <= 0:
            raise ValueError("adv must be positive")
        return float(fallback_base + fallback_k * (qty / fallback_adv))

    avg_px, book_mid = execution_price(
        qty,
        book_snapshot,
        side=side,
        qty_is_notional=qty_is_notional,
        mid=mid,
    )
    if side.lower() == "buy":
        return float((avg_px - book_mid) / book_mid * 1e4)
    if side.lower() == "sell":
        return float((book_mid - avg_px) / book_mid * 1e4)
    raise ValueError("side must be 'buy' or 'sell'")


def execution_price(
    qty: float,
    book_snapshot: Any,
    *,
    side: str = "buy",
    qty_is_notional: bool = True,
    mid: float | None = None,
) -> tuple[float, float]:
    """Walk an L2 book and return ``(average_execution_price, mid)``."""

    if qty <= 0:
        raise ValueError("qty must be positive")

    bids, asks, inferred_mid = _normalize_book(book_snapshot)
    book_mid = inferred_mid if mid is None else float(mid)
    if book_mid <= 0:
        raise ValueError("mid must be positive")

    trade_side = side.lower()
    if trade_side == "buy":
        return _walk_levels(qty, asks, qty_is_notional=qty_is_notional), book_mid
    if trade_side == "sell":
        return _walk_levels(qty, bids, qty_is_notional=qty_is_notional), book_mid
    raise ValueError("side must be 'buy' or 'sell'")


def fill_price(
    mid: float,
    side: str,
    qty: float,
    adv: float | None = None,
    *,
    book_snapshot: Any | None = None,
    qty_is_notional: bool = True,
    config: FillConfig = DEFAULT_FILL_CONFIG,
) -> float:
    """Return book-walk average fill if a book is supplied, else parametric fill."""

    if book_snapshot is not None:
        avg_px, _ = execution_price(
            qty,
            book_snapshot,
            side=side,
            qty_is_notional=qty_is_notional,
            mid=mid,
        )
        return avg_px

    slip = slippage_bps(qty, adv, config=config) / 1e4
    if side.lower() == "buy":
        return float(mid * (1 + slip))
    if side.lower() == "sell":
        return float(mid * (1 - slip))
    raise ValueError("side must be 'buy' or 'sell'")


def apply_costs(
    strategy_returns: Sequence[float],
    positions: Sequence[float],
    turnover: Sequence[float] | float | None = None,
    cost_bps_per_turn: float = 0.0,
):
    """Subtract turnover-driven round-trip trading costs from returns.

    ``positions`` are portfolio weights or normalized exposure. If ``turnover``
    is omitted, it is ``abs(position_t - position_{t-1})`` with prior position
    zero. ``cost_bps_per_turn`` is the full round-trip cost for entering and
    later exiting 1.0 exposure, so each one-way turnover unit pays half of it.
    """

    if cost_bps_per_turn < 0:
        raise ValueError("cost_bps_per_turn must be non-negative")

    returns = np.asarray(strategy_returns, dtype=float)
    pos = np.asarray(positions, dtype=float)
    if returns.shape != pos.shape:
        raise ValueError("strategy_returns and positions must have same shape")

    if turnover is None:
        prior = np.roll(pos, 1)
        prior[0] = 0.0
        turns = np.abs(pos - prior)
    else:
        turns = np.asarray(turnover, dtype=float)
        if turns.shape == ():
            turns = np.full_like(returns, float(turns))
        if turns.shape != returns.shape:
            raise ValueError("turnover must be scalar or same shape as returns")
        if np.any(turns < 0):
            raise ValueError("turnover must be non-negative")

    one_way_cost = (cost_bps_per_turn / 2.0) / 1e4
    net = returns - turns * one_way_cost
    return _like_input(strategy_returns, net)


def funding_accrual(notional: float, funding_rate: float, periods: int) -> float:
    """Perp funding PnL.

    Sign convention: ``notional`` is signed perp exposure, positive for long and
    negative for short. Positive funding means longs pay shorts, so a short perp
    with positive funding receives positive PnL.
    """

    return float(-notional * funding_rate * periods)


def _normalize_book(book_snapshot: Any) -> tuple[BookSide, BookSide, float]:
    raw = _unwrap_book(book_snapshot)

    if isinstance(raw, dict) and "bids" in raw and "asks" in raw:
        bids = _parse_levels(raw["bids"])
        asks = _parse_levels(raw["asks"])
    elif isinstance(raw, dict) and "levels" in raw:
        levels = raw["levels"]
        if len(levels) < 2:
            raise ValueError("book levels must include bids and asks")
        bids = _parse_levels(levels[0])
        asks = _parse_levels(levels[1])
    else:
        raise ValueError("book_snapshot must include bids/asks or Hyperliquid levels")

    if not bids or not asks:
        raise ValueError("book_snapshot must include non-empty bids and asks")

    bids = sorted(bids, key=lambda level: level[0], reverse=True)
    asks = sorted(asks, key=lambda level: level[0])
    mid = (bids[0][0] + asks[0][0]) / 2.0
    return bids, asks, mid


def _unwrap_book(book_snapshot: Any) -> Any:
    if isinstance(book_snapshot, dict) and "data" in book_snapshot:
        data = book_snapshot["data"]
        if isinstance(data, list) and data:
            return data[0]
    return book_snapshot


def _parse_levels(levels: Iterable[Any]) -> BookSide:
    parsed = []
    for level in levels:
        if isinstance(level, dict):
            price = level.get("price") or level.get("px")
            size = level.get("size") or level.get("sz") or level.get("amount")
        else:
            price = level[0]
            size = level[1]
        price_f = float(price)
        size_f = float(size)
        if price_f <= 0 or size_f < 0:
            raise ValueError("book levels must have positive price and non-negative size")
        if size_f > 0:
            parsed.append((price_f, size_f))
    return parsed


def _walk_levels(qty: float, levels: BookSide, *, qty_is_notional: bool) -> float:
    remaining = float(qty)
    notional = 0.0
    base = 0.0

    for price, size in levels:
        if remaining <= 1e-9:
            break

        if qty_is_notional:
            level_notional = price * size
            take_notional = min(remaining, level_notional)
            notional += take_notional
            base += take_notional / price
            remaining -= take_notional
        else:
            take_base = min(remaining, size)
            notional += take_base * price
            base += take_base
            remaining -= take_base

    if remaining > max(float(qty), 1.0) * 1e-9:
        raise ValueError("book depth insufficient for requested qty")
    if base <= 0:
        raise ValueError("book depth insufficient for requested qty")
    return float(notional / base)


def _like_input(original: Sequence[float], values: np.ndarray):
    try:
        import pandas as pd

        if isinstance(original, pd.Series):
            return pd.Series(values, index=original.index, name=original.name)
    except ImportError:
        pass
    return values
