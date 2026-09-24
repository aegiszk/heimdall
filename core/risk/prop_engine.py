"""Prop-account survival engine.

Deterministic state machine for EOD-trailing max-loss protection. This module
does not import /meta and intentionally contains no strategy logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from math import floor, isfinite
from zoneinfo import ZoneInfo


EASTERN = ZoneInfo("America/New_York")


class Action(str, Enum):
    OK = "OK"
    STOP_DAY = "STOP_DAY"
    FLATTEN_NOW = "FLATTEN_NOW"
    DEAD = "DEAD"


@dataclass(frozen=True)
class PropRiskConfig:
    max_loss_limit: float = 2_000.0
    daily_buffer: float = 400.0
    kill_cushion: float = 400.0
    protect_green_at: float = 500.0
    session_flatten: str = "16:45 EST"
    min_profit_day: float = 150.0
    lock_trailing: bool = True
    trail_lock_floor: float | None = None


@dataclass
class PropRiskEngine:
    starting_balance: float = 50_000.0
    config: PropRiskConfig = field(default_factory=PropRiskConfig)
    balance: float | None = None
    peak_eod_balance: float | None = None

    mll_floor: float = field(init=False)
    daily_realized_pnl: float = field(default=0.0, init=False)
    peak_day_profit: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.starting_balance = self._valid_money(self.starting_balance, "starting_balance")
        self.balance = self.starting_balance if self.balance is None else self._valid_money(self.balance, "balance")
        self.peak_eod_balance = (
            self.starting_balance
            if self.peak_eod_balance is None
            else self._valid_money(self.peak_eod_balance, "peak_eod_balance")
        )
        if self.peak_eod_balance < self.starting_balance:
            raise ValueError("peak_eod_balance cannot start below starting_balance")
        self.mll_floor = self._compute_mll_floor()

    @property
    def live_equity(self) -> float:
        return float(self.balance)

    @property
    def daily_realized_profit(self) -> float:
        return max(self.daily_realized_pnl, 0.0)

    @property
    def daily_realized_loss(self) -> float:
        return max(-self.daily_realized_pnl, 0.0)

    def on_fill(self, pnl_delta: float) -> None:
        pnl = self._valid_money(pnl_delta, "pnl_delta")
        self.daily_realized_pnl += pnl
        self.balance = float(self.balance) + pnl
        self.peak_day_profit = max(self.peak_day_profit, self.daily_realized_pnl)

    def on_eod_close(self) -> None:
        self.peak_eod_balance = max(float(self.peak_eod_balance), float(self.balance))
        self.mll_floor = self._compute_mll_floor()
        self.daily_realized_pnl = 0.0
        self.peak_day_profit = 0.0

    def check(self, now: datetime | time | str | None = None) -> Action:
        if self.live_equity <= self.mll_floor:
            return Action.DEAD
        if self.live_equity <= self.mll_floor + self.config.kill_cushion:
            return Action.FLATTEN_NOW
        if self.daily_realized_loss >= self.config.daily_buffer:
            return Action.STOP_DAY
        if (
            self.peak_day_profit >= self.config.protect_green_at
            and self.daily_realized_pnl <= self.peak_day_profit * 0.5
        ):
            return Action.STOP_DAY
        if now is not None and self._is_session_flatten_due(now):
            return Action.FLATTEN_NOW
        return Action.OK

    def allowed_size(self, tick_value: float, stop_ticks: int | float) -> int:
        tick_value = self._valid_money(tick_value, "tick_value")
        stop_ticks = self._valid_money(stop_ticks, "stop_ticks")
        risk_per_contract = tick_value * stop_ticks
        if risk_per_contract <= 0:
            raise ValueError("tick_value * stop_ticks must be positive")
        return max(0, int(floor(self.config.daily_buffer / risk_per_contract)))

    def _compute_mll_floor(self) -> float:
        raw_floor = float(self.peak_eod_balance) - self.config.max_loss_limit
        if not self.config.lock_trailing:
            return raw_floor
        lock_floor = self.config.trail_lock_floor
        if lock_floor is None:
            lock_floor = self.starting_balance
        return min(raw_floor, float(lock_floor))

    def _is_session_flatten_due(self, now: datetime | time | str) -> bool:
        current = _clock_time(now)
        flatten_at = _clock_time(self.config.session_flatten)
        return current >= flatten_at

    @staticmethod
    def _valid_money(value: float, name: str) -> float:
        out = float(value)
        if not isfinite(out):
            raise ValueError(f"{name} must be finite")
        return out


def _clock_time(value: datetime | time | str) -> time:
    if isinstance(value, datetime):
        dt = value if value.tzinfo is not None else value.replace(tzinfo=EASTERN)
        return dt.astimezone(EASTERN).time().replace(tzinfo=None)
    if isinstance(value, time):
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        cleaned = (
            value.upper()
            .replace("AMERICA/NEW_YORK", "")
            .replace("EASTERN", "")
            .replace("EST", "")
            .replace("EDT", "")
            .replace("ET", "")
            .strip()
        )
        parts = cleaned.split(":")
        if len(parts) != 2:
            raise ValueError(f"Unsupported clock string: {value!r}")
        return time(hour=int(parts[0]), minute=int(parts[1]))
    raise TypeError(f"Unsupported time input: {type(value)!r}")


__all__ = ["Action", "PropRiskConfig", "PropRiskEngine"]
