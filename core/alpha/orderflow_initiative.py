"""Frozen v3 price-level initiative continuation backtest."""
from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from .orderflow_footprint import (
    COMMISSION,
    MIN_PRIOR_SESSIONS,
    POINT_VALUE,
    TICK,
    _bars,
    _simulate,
    volume_area,
)


def initiative_side(bar: pd.Series, val: float, vah: float) -> int:
    spread = float(bar.high - bar.low)
    body = float(abs(bar.close - bar.open))
    long = (
        spread > 0
        and bar.high > vah
        and bar.close >= vah + TICK
        and bar.close > bar.open
        and body >= 0.50 * spread
        and bar.delta > 0
        and bar.short_ask >= 20
        and bar.short_ask >= 3 * max(1.0, bar.short_bid)
    )
    short = (
        spread > 0
        and bar.low < val
        and bar.close <= val - TICK
        and bar.close < bar.open
        and body >= 0.50 * spread
        and bar.delta < 0
        and bar.long_bid >= 20
        and bar.long_bid >= 3 * max(1.0, bar.long_ask)
    )
    return 0 if long == short else (1 if long else -1)


def run_backtest(footprint: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    required = {"minute", "price", "volume", "bid_volume", "ask_volume", "bar_open", "bar_high", "bar_low", "bar_close", "session"}
    missing = required - set(footprint)
    if missing:
        raise ValueError(f"missing footprint columns: {sorted(missing)}")
    sessions = sorted(footprint.session.unique())
    by_session = {session: frame.sort_values(["minute", "price"]) for session, frame in footprint.groupby("session", sort=True)}
    trades = []
    funnel = {"eligible_sessions": 0, "initiative_bars": 0, "confirmed": 0, "entered": 0}
    for index in range(MIN_PRIOR_SESSIONS, len(sessions)):
        session = sessions[index]
        val, vah = volume_area(by_session[sessions[index - 1]])
        bars = _bars(by_session[session])
        if bars.empty:
            continue
        funnel["eligible_sessions"] += 1
        times = list(bars.index)
        for position, timestamp in enumerate(times):
            local = timestamp.tz_convert("America/New_York")
            if local.hour * 60 + local.minute > 15 * 60 + 30:
                break
            side = initiative_side(bars.loc[timestamp], val, vah)
            if side == 0:
                continue
            funnel["initiative_bars"] += 1
            if position + 2 >= len(times):
                continue
            signal = bars.loc[timestamp]
            confirmation = bars.iloc[position + 1]
            midpoint = (float(signal.high) + float(signal.low)) / 2
            valid_confirmation = (
                confirmation.close >= vah and confirmation.close >= midpoint and confirmation.delta >= 0
                if side > 0
                else confirmation.close <= val and confirmation.close <= midpoint and confirmation.delta <= 0
            )
            if not valid_confirmation:
                continue
            funnel["confirmed"] += 1
            entry_position = position + 2
            entry_time = times[entry_position]
            entry_local = entry_time.tz_convert("America/New_York")
            if entry_local.hour * 60 + entry_local.minute > 15 * 60 + 30:
                continue
            entry = float(bars.iloc[entry_position].open) + side * TICK
            stop = float(signal.low - TICK if side > 0 else signal.high + TICK)
            risk = (entry - stop) * side
            stopped_loss = (risk + TICK) * POINT_VALUE + COMMISSION
            if risk < 4 * TICK or stopped_loss > 325:
                continue
            target = entry + side * risk
            trades.append(_simulate(session, side, timestamp, entry_time, entry, stop, target, bars.iloc[entry_position:]))
            funnel["entered"] += 1
            break
    return pd.DataFrame([asdict(trade) for trade in trades]), funnel
