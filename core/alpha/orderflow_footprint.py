"""Frozen v2 price-level footprint absorption backtest."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


TICK = 0.25
POINT_VALUE = 2.0
COMMISSION = 1.0
MIN_PRIOR_SESSIONS = 20


@dataclass(frozen=True)
class FootprintTrade:
    session: object
    side: int
    signal_time: pd.Timestamp
    entry_time: pd.Timestamp
    entry: float
    stop: float
    target: float
    exit_time: pd.Timestamp
    exit_price: float
    reason: str
    pnl: float


def volume_area(levels: pd.DataFrame) -> tuple[float, float]:
    profile = levels.groupby("price", sort=True)["volume"].sum().sort_index()
    if profile.empty or float(profile.sum()) <= 0:
        raise ValueError("prior session has no positive volume")
    maximum = profile.max()
    poc = float(profile[profile == maximum].index.min())
    volumes = {float(price): float(volume) for price, volume in profile.items()}
    minimum_price, maximum_price = min(volumes), max(volumes)
    low = high = poc
    cumulative = volumes[poc]
    target = float(profile.sum()) * 0.68
    while cumulative < target:
        lower = low - TICK
        upper = high + TICK
        lower_volume = volumes.get(lower, 0.0)
        upper_volume = volumes.get(upper, 0.0)
        if lower_volume == 0 and upper_volume == 0 and lower < minimum_price and upper > maximum_price:
            break
        if lower < minimum_price:
            chosen = upper
        elif upper > maximum_price:
            chosen = lower
        else:
            chosen = lower if lower_volume >= upper_volume else upper
        if chosen == lower:
            low = lower
        else:
            high = upper
        cumulative += volumes.get(chosen, 0.0)
    return low, high


def _bars(day: pd.DataFrame) -> pd.DataFrame:
    work = day.copy()
    highest = work.groupby("minute")["price"].transform("max")
    lowest = work.groupby("minute")["price"].transform("min")
    work["short_ask"] = work["ask_volume"].where(work["price"] >= highest - TICK, 0)
    work["short_bid"] = work["bid_volume"].where(work["price"] >= highest - TICK, 0)
    work["long_bid"] = work["bid_volume"].where(work["price"] <= lowest + TICK, 0)
    work["long_ask"] = work["ask_volume"].where(work["price"] <= lowest + TICK, 0)
    bars = work.groupby("minute", sort=True).agg(
        open=("bar_open", "first"),
        high=("bar_high", "first"),
        low=("bar_low", "first"),
        close=("bar_close", "first"),
        bid_volume=("bid_volume", "sum"),
        ask_volume=("ask_volume", "sum"),
        short_ask=("short_ask", "sum"),
        short_bid=("short_bid", "sum"),
        long_bid=("long_bid", "sum"),
        long_ask=("long_ask", "sum"),
    )
    bars["delta"] = bars["ask_volume"] - bars["bid_volume"]
    return bars


def _candidate(bar: pd.Series, val: float, vah: float) -> int:
    short = (
        bar.high >= vah
        and bar.close <= vah - TICK
        and bar.short_ask >= 20
        and bar.short_ask >= 3 * max(1.0, bar.short_bid)
        and bar.short_ask >= 0.20 * max(1.0, float(bar.ask_volume))
    )
    long = (
        bar.low <= val
        and bar.close >= val + TICK
        and bar.long_bid >= 20
        and bar.long_bid >= 3 * max(1.0, bar.long_ask)
        and bar.long_bid >= 0.20 * max(1.0, float(bar.bid_volume))
    )
    return 0 if short == long else (-1 if short else 1)


def run_backtest(footprint: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    required = {"minute", "price", "volume", "bid_volume", "ask_volume", "bar_open", "bar_high", "bar_low", "bar_close", "session"}
    missing = required - set(footprint)
    if missing:
        raise ValueError(f"missing footprint columns: {sorted(missing)}")
    sessions = sorted(footprint["session"].unique())
    by_session = {session: frame.sort_values(["minute", "price"]) for session, frame in footprint.groupby("session", sort=True)}
    trades: list[FootprintTrade] = []
    funnel = {"eligible_sessions": 0, "candidate_bars": 0, "confirmed": 0, "entered": 0}
    for index in range(MIN_PRIOR_SESSIONS, len(sessions)):
        session = sessions[index]
        prior = by_session[sessions[index - 1]]
        day = by_session[session]
        val, vah = volume_area(prior)
        bars = _bars(day)
        if bars.empty:
            continue
        funnel["eligible_sessions"] += 1
        times = list(bars.index)
        for pos, timestamp in enumerate(times):
            local = timestamp.tz_convert("America/New_York")
            if local.hour * 60 + local.minute > 15 * 60 + 30:
                break
            side = _candidate(bars.loc[timestamp], val, vah)
            if side == 0:
                continue
            funnel["candidate_bars"] += 1
            midpoint = (float(bars.loc[timestamp, "high"]) + float(bars.loc[timestamp, "low"])) / 2
            confirmation_pos = None
            for probe in range(pos + 1, min(pos + 3, len(times))):
                confirm = bars.iloc[probe]
                valid = (
                    confirm.delta < 0 and confirm.close < confirm.open and confirm.close < midpoint
                    if side < 0
                    else confirm.delta > 0 and confirm.close > confirm.open and confirm.close > midpoint
                )
                if valid:
                    confirmation_pos = probe
                    break
            if confirmation_pos is None or confirmation_pos + 1 >= len(times):
                continue
            funnel["confirmed"] += 1
            entry_pos = confirmation_pos + 1
            entry_time = times[entry_pos]
            entry_local = entry_time.tz_convert("America/New_York")
            if entry_local.hour * 60 + entry_local.minute > 15 * 60 + 30:
                continue
            signal = bars.loc[timestamp]
            entry = float(bars.iloc[entry_pos].open) + side * TICK
            stop = float(signal.low - TICK if side > 0 else signal.high + TICK)
            risk = (entry - stop) * side
            if risk < 4 * TICK or (risk + TICK) * POINT_VALUE + COMMISSION > 325:
                continue
            target = entry + side * risk
            trade = _simulate(session, side, timestamp, entry_time, entry, stop, target, bars.iloc[entry_pos:])
            trades.append(trade)
            funnel["entered"] += 1
            break
    return pd.DataFrame([asdict(trade) for trade in trades]), funnel


def _simulate(session, side, signal_time, entry_time, entry, stop, target, future) -> FootprintTrade:
    exit_time = future.index[-1]
    exit_price = float(future.iloc[-1].close) - side * TICK
    reason = "session_flat"
    for timestamp, bar in future.iterrows():
        local = timestamp.tz_convert("America/New_York")
        stop_hit = bar.low <= stop if side > 0 else bar.high >= stop
        target_hit = bar.high >= target if side > 0 else bar.low <= target
        if stop_hit:
            exit_time, exit_price, reason = timestamp, stop - side * TICK, "stop"
            break
        if target_hit:
            exit_time, exit_price, reason = timestamp, target, "target"
            break
        if local.hour * 60 + local.minute >= 15 * 60 + 55:
            exit_time, exit_price, reason = timestamp, float(bar.close) - side * TICK, "session_flat"
            break
    pnl = (exit_price - entry) * side * POINT_VALUE - COMMISSION
    return FootprintTrade(session, side, signal_time, entry_time, entry, stop, target, exit_time, exit_price, reason, pnl)
