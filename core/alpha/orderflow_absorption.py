"""Pre-registered MNQ bar-level absorption/aggression candidate.

Rules are frozen in ``ORDERFLOW_ABSORPTION_PREREGISTRATION.md`` with SHA-256
86943C07589D8A06C420FC6FD61215FC2B26D8AC86A9C994E58F4CDFEFB6B525.
This module contains no threshold search and no dependency on /meta.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time

import numpy as np
import pandas as pd

from core.alpha.base import QuantModel, Signal


EASTERN = "America/New_York"
TICK_SIZE = 0.25
POINT_VALUE = 2.0
COMMISSION_RT = 1.0
DAILY_BUFFER = 325.0
RTH_OPEN = time(9, 30)
ENTRY_CUTOFF = time(15, 30)
FLATTEN_TIME = time(15, 55)
RTH_CLOSE = time(16, 0)
LOOKBACK_SESSIONS = 20
PROFILE_BUCKET_POINTS = 1.0
VALUE_AREA_FRACTION = 0.68
ABSORPTION_DELTA_QUANTILE = 0.90
CONFIRMATION_DELTA_QUANTILE = 0.75
KEY_LEVEL_TOLERANCE = 1.0
CONFIRMATION_BARS = 3
MIN_BODY_FRACTION = 0.50
TARGET_R = 2.0
BREAKEVEN_R = 1.0


@dataclass(frozen=True)
class EffortBaselines:
    abs_delta_q90: float
    abs_delta_q75: float
    range_median: float


@dataclass(frozen=True)
class Setup:
    absorption_i: int
    confirmation_i: int
    entry_i: int
    side: int
    level_kind: str
    level: float


@dataclass(frozen=True)
class Trade:
    entry_ts: pd.Timestamp
    exit_ts: pd.Timestamp
    session: object
    side: int
    entry_price: float
    exit_price: float
    stop_price: float
    target_price: float
    risk_dollars: float
    pnl: float
    reason: str
    level_kind: str
    level: float
    absorption_ts: pd.Timestamp
    confirmation_ts: pd.Timestamp


@dataclass
class BacktestResult:
    frame: pd.DataFrame
    pnl: np.ndarray
    pos: np.ndarray
    market: np.ndarray
    trades: list[Trade]


class OrderflowAbsorptionModel(QuantModel):
    """One fixed MNQ absorption-to-opposite-aggression reversal candidate."""

    strategy_params: tuple[str, ...] = ()
    preregistration_sha256 = "86943C07589D8A06C420FC6FD61215FC2B26D8AC86A9C994E58F4CDFEFB6B525"

    @property
    def name(self) -> str:
        return "orderflow_absorption_v1"

    def predict(self, asset: str, ts: str, data) -> Signal:
        return self._neutral(asset, ts)

    def strategy_returns(self, df):
        result = self._run_backtest(df)
        return result.pnl, result.pos, result.market

    def trade_pnls(self, df) -> np.ndarray:
        return np.asarray([trade.pnl for trade in self._run_backtest(df).trades], dtype=float)

    def prop_montecarlo_frame(self, df) -> pd.DataFrame:
        trades = self._run_backtest(df).trades
        columns = ["entry_ts", "exit_ts", "side", "pnl", "reason"]
        if not trades:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame(
            {
                "entry_ts": [trade.entry_ts for trade in trades],
                "exit_ts": [trade.exit_ts for trade in trades],
                "side": [trade.side for trade in trades],
                "pnl": [trade.pnl for trade in trades],
                "reason": [trade.reason for trade in trades],
            }
        )

    def trades_frame(self, df) -> pd.DataFrame:
        trades = self._run_backtest(df).trades
        if not trades:
            return pd.DataFrame(columns=[field.name for field in Trade.__dataclass_fields__.values()])
        return pd.DataFrame([trade.__dict__ for trade in trades])

    @staticmethod
    def discretion_gaps() -> list[str]:
        return [
            "One-minute bar delta replaces price-level footprint cells; MBO and queue state are unavailable.",
            "Prior-session volume-at-price is approximated by assigning each bar's full volume to its close rounded to 1.00 point.",
            "High effort is fixed to the trailing 20-session 90th absolute-delta percentile; confirmation uses the 75th percentile.",
            "Low result is fixed to range no larger than the trailing 20-session median range.",
            "The source's discretionary 2R-to-5R management is fixed at 2R with breakeven armed after 1R.",
        ]

    def _run_backtest(self, df) -> BacktestResult:
        frame = self._prepare_frame(df)
        n = len(frame)
        pnl = np.zeros(n, dtype=float)
        pos = np.zeros(n, dtype=float)
        market = np.zeros(n, dtype=float)
        if n > 1:
            market[1:] = np.diff(frame["close"].to_numpy(float)) * POINT_VALUE
        if frame.empty:
            return BacktestResult(frame, pnl, pos, market, [])

        grouped = [(session, day) for session, day in frame.groupby("_session", sort=True)]
        trades: list[Trade] = []
        for session_idx in range(LOOKBACK_SESSIONS, len(grouped)):
            session, day = grouped[session_idx]
            prior_sessions = grouped[session_idx - LOOKBACK_SESSIONS : session_idx]
            previous_day = grouped[session_idx - 1][1]
            val, vah = self._volume_area(previous_day)
            baselines = self._effort_baselines(prior_sessions)
            setup = self._first_setup(frame, day, val, vah, baselines)
            if setup is None:
                continue
            trade = self._simulate_trade(frame, setup, session)
            if trade is None:
                continue
            trades.append(trade)
            start = setup.entry_i
            exit_matches = frame.index[frame["_ts_utc"] == trade.exit_ts].tolist()
            end = exit_matches[0] if exit_matches else start
            pnl[end] += trade.pnl
            pos[start : end + 1] = float(setup.side)
        return BacktestResult(frame, pnl, pos, market, trades)

    @staticmethod
    def _prepare_frame(df) -> pd.DataFrame:
        raw = pd.DataFrame(df).copy()
        required = {"open", "high", "low", "close", "volume", "bid_volume", "ask_volume", "delta"}
        missing = sorted(required.difference(raw.columns))
        if missing:
            raise ValueError(f"missing required columns: {missing}")
        if "ts" in raw.columns:
            ts = pd.Series(pd.to_datetime(raw["ts"]), index=raw.index)
        elif isinstance(raw.index, pd.DatetimeIndex):
            ts = pd.Series(pd.to_datetime(raw.index), index=raw.index)
        else:
            raise ValueError("provide a ts column or DatetimeIndex")
        if getattr(ts.dt, "tz", None) is None:
            ts = ts.dt.tz_localize("UTC")
        else:
            ts = ts.dt.tz_convert("UTC")
        raw["_ts_utc"] = ts
        raw["_ts_et"] = ts.dt.tz_convert(EASTERN)
        raw["_session"] = raw["_ts_et"].dt.date
        raw["_time"] = raw["_ts_et"].dt.time
        for col in required:
            raw[col] = raw[col].astype(float)
            if not np.isfinite(raw[col]).all():
                raise ValueError(f"{col} contains non-finite values")
        for col in ("volume", "bid_volume", "ask_volume"):
            if (raw[col] < 0).any():
                raise ValueError(f"{col} contains negative values")
        mismatch = (raw["ask_volume"] - raw["bid_volume"] - raw["delta"]).abs()
        if (mismatch > 1e-9).any():
            raise ValueError("delta must equal ask_volume - bid_volume")
        mask = (
            (raw["_ts_et"].dt.weekday < 5)
            & (raw["_time"] >= RTH_OPEN)
            & (raw["_time"] <= RTH_CLOSE)
        )
        return raw.loc[mask].sort_values("_ts_utc").reset_index(drop=True)

    @staticmethod
    def _volume_area(day: pd.DataFrame) -> tuple[float, float]:
        if day.empty or float(day["volume"].sum()) <= 0:
            raise ValueError("prior session has no positive volume")
        buckets = (day["close"] / PROFILE_BUCKET_POINTS).round() * PROFILE_BUCKET_POINTS
        profile = day.groupby(buckets, sort=True)["volume"].sum().sort_index()
        max_volume = float(profile.max())
        poc = float(profile[profile == max_volume].index.min())
        prices = [float(price) for price in profile.index]
        volumes = {float(price): float(volume) for price, volume in profile.items()}
        selected = {poc}
        cumulative = volumes[poc]
        target = float(profile.sum()) * VALUE_AREA_FRACTION
        while cumulative < target and len(selected) < len(prices):
            low = min(selected)
            high = max(selected)
            lower = max((price for price in prices if price < low), default=None)
            upper = min((price for price in prices if price > high), default=None)
            lower_volume = volumes[lower] if lower is not None else -1.0
            upper_volume = volumes[upper] if upper is not None else -1.0
            chosen = lower if lower_volume >= upper_volume else upper
            if chosen is None:
                break
            selected.add(chosen)
            cumulative += volumes[chosen]
        return min(selected), max(selected)

    @staticmethod
    def _effort_baselines(prior_sessions: list[tuple[object, pd.DataFrame]]) -> EffortBaselines:
        history = pd.concat([day for _, day in prior_sessions], ignore_index=True)
        abs_delta = history["delta"].abs()
        ranges = history["high"] - history["low"]
        return EffortBaselines(
            abs_delta_q90=float(abs_delta.quantile(ABSORPTION_DELTA_QUANTILE)),
            abs_delta_q75=float(abs_delta.quantile(CONFIRMATION_DELTA_QUANTILE)),
            range_median=float(ranges.median()),
        )

    def _first_setup(
        self,
        frame: pd.DataFrame,
        day: pd.DataFrame,
        val: float,
        vah: float,
        baselines: EffortBaselines,
    ) -> Setup | None:
        indices = list(day.index)
        for local_pos, i in enumerate(indices):
            row = frame.loc[i]
            if row["_time"] > ENTRY_CUTOFF:
                break
            bar_range = float(row["high"] - row["low"])
            if bar_range <= 0 or bar_range > baselines.range_median:
                continue
            side = 0
            kind = ""
            level = 0.0
            if (
                float(row["high"]) >= vah - KEY_LEVEL_TOLERANCE
                and float(row["close"]) <= vah
                and float(row["delta"]) > 0
                and abs(float(row["delta"])) >= baselines.abs_delta_q90
            ):
                side, kind, level = -1, "prior_vah", vah
            elif (
                float(row["low"]) <= val + KEY_LEVEL_TOLERANCE
                and float(row["close"]) >= val
                and float(row["delta"]) < 0
                and abs(float(row["delta"])) >= baselines.abs_delta_q90
            ):
                side, kind, level = 1, "prior_val", val
            if side == 0:
                continue
            midpoint = (float(row["high"]) + float(row["low"])) / 2.0
            for confirm_pos in range(local_pos + 1, min(local_pos + 1 + CONFIRMATION_BARS, len(indices))):
                j = indices[confirm_pos]
                confirm = frame.loc[j]
                confirm_range = float(confirm["high"] - confirm["low"])
                if confirm_range <= 0:
                    continue
                body = abs(float(confirm["close"] - confirm["open"]))
                directional = (
                    side == 1
                    and float(confirm["delta"]) > 0
                    and float(confirm["close"]) > float(confirm["open"])
                    and float(confirm["close"]) > midpoint
                ) or (
                    side == -1
                    and float(confirm["delta"]) < 0
                    and float(confirm["close"]) < float(confirm["open"])
                    and float(confirm["close"]) < midpoint
                )
                if (
                    directional
                    and abs(float(confirm["delta"])) >= baselines.abs_delta_q75
                    and body >= MIN_BODY_FRACTION * confirm_range
                ):
                    entry_pos = confirm_pos + 1
                    if entry_pos >= len(indices):
                        return None
                    entry_i = indices[entry_pos]
                    if frame.loc[entry_i, "_time"] > ENTRY_CUTOFF:
                        return None
                    return Setup(i, j, entry_i, side, kind, float(level))
        return None

    def _simulate_trade(self, frame: pd.DataFrame, setup: Setup, session: object) -> Trade | None:
        absorption = frame.loc[setup.absorption_i]
        confirmation = frame.loc[setup.confirmation_i]
        entry_row = frame.loc[setup.entry_i]
        entry = float(entry_row["open"] + setup.side * TICK_SIZE)
        stop = (
            float(absorption["low"] - TICK_SIZE)
            if setup.side == 1
            else float(absorption["high"] + TICK_SIZE)
        )
        risk_points = (entry - stop) * setup.side
        if risk_points <= 0:
            return None
        worst_stop = stop - setup.side * TICK_SIZE
        risk_dollars = (entry - worst_stop) * setup.side * POINT_VALUE + COMMISSION_RT
        if risk_dollars > DAILY_BUFFER:
            return None
        target = entry + setup.side * TARGET_R * risk_points
        one_r = entry + setup.side * BREAKEVEN_R * risk_points
        day_indices = list(frame.index[frame["_session"] == session])
        start_pos = day_indices.index(setup.entry_i)
        breakeven_active = False
        exit_price: float | None = None
        exit_i = setup.entry_i
        reason = ""
        for i in day_indices[start_pos:]:
            row = frame.loc[i]
            active_stop = entry if breakeven_active else stop
            if setup.side == 1:
                if float(row["open"]) <= active_stop:
                    exit_price, reason = min(float(row["open"]), active_stop - TICK_SIZE), "gap_stop"
                elif float(row["low"]) <= active_stop:
                    exit_price = active_stop - TICK_SIZE
                    reason = "breakeven_stop" if breakeven_active else "stop"
                elif float(row["high"]) >= target:
                    exit_price, reason = target, "target"
                elif row["_time"] >= FLATTEN_TIME:
                    exit_price, reason = float(row["close"] - TICK_SIZE), "session_flatten"
                reached_one_r = float(row["high"]) >= one_r
            else:
                if float(row["open"]) >= active_stop:
                    exit_price, reason = max(float(row["open"]), active_stop + TICK_SIZE), "gap_stop"
                elif float(row["high"]) >= active_stop:
                    exit_price = active_stop + TICK_SIZE
                    reason = "breakeven_stop" if breakeven_active else "stop"
                elif float(row["low"]) <= target:
                    exit_price, reason = target, "target"
                elif row["_time"] >= FLATTEN_TIME:
                    exit_price, reason = float(row["close"] + TICK_SIZE), "session_flatten"
                reached_one_r = float(row["low"]) <= one_r
            exit_i = i
            if exit_price is not None:
                break
            if reached_one_r:
                breakeven_active = True
        if exit_price is None:
            final = frame.loc[day_indices[-1]]
            exit_i = day_indices[-1]
            exit_price = float(final["close"] - setup.side * TICK_SIZE)
            reason = "session_flatten"
        pnl = (exit_price - entry) * setup.side * POINT_VALUE - COMMISSION_RT
        return Trade(
            entry_ts=entry_row["_ts_utc"],
            exit_ts=frame.loc[exit_i, "_ts_utc"],
            session=session,
            side=setup.side,
            entry_price=entry,
            exit_price=float(exit_price),
            stop_price=stop,
            target_price=target,
            risk_dollars=float(risk_dollars),
            pnl=float(pnl),
            reason=reason,
            level_kind=setup.level_kind,
            level=setup.level,
            absorption_ts=absorption["_ts_utc"],
            confirmation_ts=confirmation["_ts_utc"],
        )
