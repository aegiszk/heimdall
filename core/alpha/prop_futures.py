"""LucidFlex MES/ES RTH strategy candidates.

These models are design specs plus deterministic backtest mechanics. They do
not place orders. ``strategy_returns`` emits one-contract net dollar PnL on the
bar where a trade exits, so ``trade_pnls(df)`` can be written to CSV and passed
to ``tools/prop_montecarlo.py --trade-pnls-file`` when real Agent 1 data lands.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time
import numpy as np
import pandas as pd

from core.alpha.base import QuantModel, Signal


TICK_SIZE = 0.25
CONTRACTS = {
    "MES": {"point_value": 5.0, "commission_rt": 1.0},
    "ES": {"point_value": 50.0, "commission_rt": 3.5},
    "MNQ": {"point_value": 2.0, "commission_rt": 1.0},
    "NQ": {"point_value": 20.0, "commission_rt": 3.5},
}


@dataclass(frozen=True)
class Trade:
    entry_ts: pd.Timestamp
    exit_ts: pd.Timestamp
    side: int
    entry_price: float
    exit_price: float
    stop_price: float
    target_price: float
    pnl: float
    reason: str


@dataclass(frozen=True)
class EntryPlan:
    side: int
    stop_price: float
    target_price: float


class FuturesRTHModel(QuantModel):
    """Shared OHLC stop/target simulator for one-contract MES/ES RTH specs."""

    strategy_params: tuple[str, ...] = ()
    entry_start = time(9, 45)
    entry_end = time(15, 30)
    flatten_time = time(16, 45)

    def __init__(self, contract: str = "MES"):
        contract = contract.upper()
        if contract not in CONTRACTS:
            raise ValueError(f"unsupported contract {contract!r}; expected MES or ES")
        self.contract = contract
        self.point_value = CONTRACTS[contract]["point_value"]
        self.commission_rt = CONTRACTS[contract]["commission_rt"]

    def predict(self, asset, ts, data) -> Signal:
        return self._neutral(asset, ts)

    def strategy_returns(self, df):
        frame = self._prepare_frame(df)
        pnl, pos, market, _ = self._simulate(frame)
        return pnl, pos, market

    def trade_pnls(self, df) -> np.ndarray:
        frame = self._prepare_frame(df)
        _, _, _, trades = self._simulate(frame)
        return np.asarray([trade.pnl for trade in trades], dtype=float)

    def prop_montecarlo_frame(self, df) -> pd.DataFrame:
        frame = self._prepare_frame(df)
        _, _, _, trades = self._simulate(frame)
        return pd.DataFrame(
            {
                "entry_ts": [trade.entry_ts for trade in trades],
                "exit_ts": [trade.exit_ts for trade in trades],
                "side": [trade.side for trade in trades],
                "pnl": [trade.pnl for trade in trades],
                "reason": [trade.reason for trade in trades],
            }
        )

    def _entry_plan(self, frame: pd.DataFrame, i: int) -> EntryPlan | None:
        raise NotImplementedError

    def _max_trades_day(self) -> int:
        raise NotImplementedError

    def _prepare_frame(self, df) -> pd.DataFrame:
        frame = pd.DataFrame(df).copy()
        required = {"open", "high", "low", "close", "vwap"}
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise ValueError(f"missing required columns: {missing}")

        if "ts" in frame.columns:
            ts = pd.to_datetime(frame["ts"])
        elif isinstance(frame.index, pd.DatetimeIndex):
            ts = pd.to_datetime(frame.index)
        else:
            raise ValueError("provide a ts column or DatetimeIndex for RTH session rules")
        ts = pd.Series(ts, index=frame.index)
        if getattr(ts.dt, "tz", None) is not None:
            ts = ts.dt.tz_convert("America/New_York").dt.tz_localize(None)

        frame["_ts"] = ts
        frame = frame.sort_values("_ts").reset_index(drop=True)
        frame["_session"] = frame["_ts"].dt.date
        frame["_time"] = frame["_ts"].dt.time

        for col in ("open", "high", "low", "close", "vwap"):
            frame[col] = frame[col].astype(float)
            if not np.isfinite(frame[col]).all():
                raise ValueError(f"{col} contains non-finite values")

        if "prior_close" in frame.columns:
            frame["prior_close"] = frame["prior_close"].astype(float)
        else:
            close_by_session = frame.groupby("_session")["close"].last()
            previous_close = close_by_session.shift(1)
            frame["prior_close"] = frame["_session"].map(previous_close)
        return frame

    def _simulate(self, frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[Trade]]:
        n = len(frame)
        pnl = np.zeros(n, dtype=float)
        pos = np.zeros(n, dtype=float)
        market = np.zeros(n, dtype=float)
        if n > 1:
            market[1:] = np.diff(frame["close"].to_numpy(float)) * self.point_value

        trades: list[Trade] = []
        for _, session_frame in frame.groupby("_session", sort=True):
            open_trade: dict[str, float | int | pd.Timestamp] | None = None
            trades_today = 0
            session_indices = list(session_frame.index)
            last_session_i = session_indices[-1]

            for i in session_indices:
                row = frame.loc[i]
                if open_trade is not None:
                    pos[i] = float(open_trade["side"])
                    exit_price, reason = self._exit_price(open_trade, row, i == last_session_i)
                    if exit_price is not None:
                        trade = self._close_trade(open_trade, row, exit_price, reason)
                        pnl[i] += trade.pnl
                        trades.append(trade)
                        open_trade = None
                        continue

                if (
                    open_trade is None
                    and trades_today < self._max_trades_day()
                    and self._entry_window(row["_time"])
                    and i != last_session_i
                ):
                    plan = self._entry_plan(frame, i)
                    if plan is None:
                        continue
                    entry_price = self._market_entry_price(int(plan.side), float(row["close"]))
                    open_trade = {
                        "entry_i": i,
                        "entry_ts": row["_ts"],
                        "side": int(plan.side),
                        "entry_price": entry_price,
                        "stop_price": float(plan.stop_price),
                        "target_price": float(plan.target_price),
                    }
                    pos[i] = float(plan.side)
                    trades_today += 1

        return pnl, pos, market, trades

    def _entry_window(self, t: time) -> bool:
        return self.entry_start <= t <= self.entry_end

    def _market_entry_price(self, side: int, trigger_price: float) -> float:
        return float(trigger_price + side * TICK_SIZE)

    def _exit_price(
        self,
        open_trade: dict[str, float | int | pd.Timestamp],
        row: pd.Series,
        is_last_session_bar: bool,
    ) -> tuple[float | None, str]:
        side = int(open_trade["side"])
        stop = float(open_trade["stop_price"])
        target = float(open_trade["target_price"])
        high = float(row["high"])
        low = float(row["low"])
        open_ = float(row["open"])

        if side > 0:
            if open_ <= stop:
                return min(open_, stop - TICK_SIZE), "gap_stop"
            stop_hit = low <= stop
            target_hit = high >= target
        else:
            if open_ >= stop:
                return max(open_, stop + TICK_SIZE), "gap_stop"
            stop_hit = high >= stop
            target_hit = low <= target

        if stop_hit:
            return stop - side * TICK_SIZE, "stop"
        if target_hit:
            return target, "target"
        if row["_time"] >= self.flatten_time or is_last_session_bar:
            return float(row["close"]) - side * TICK_SIZE, "session_flatten"
        return None, ""

    def _close_trade(
        self,
        open_trade: dict[str, float | int | pd.Timestamp],
        row: pd.Series,
        exit_price: float,
        reason: str,
    ) -> Trade:
        side = int(open_trade["side"])
        entry = float(open_trade["entry_price"])
        pnl = side * (exit_price - entry) * self.point_value - self.commission_rt
        return Trade(
            entry_ts=open_trade["entry_ts"],
            exit_ts=row["_ts"],
            side=side,
            entry_price=entry,
            exit_price=float(exit_price),
            stop_price=float(open_trade["stop_price"]),
            target_price=float(open_trade["target_price"]),
            pnl=float(pnl),
            reason=reason,
        )


class VWAPReversionHardStopModel(FuturesRTHModel):
    """Mean-reversion candidate for stretched MES/ES RTH moves.

    Mechanical rules:
    - Data: intraday RTH OHLCV bars with ``vwap`` and optional ``prior_close``.
    - Session filter: entries only 09:45-15:30 ET; any open trade exits on the
      first bar at/after 16:45 ET, or the last available RTH bar if earlier.
    - Entry: choose the nearest qualifying anchor from current VWAP and prior
      RTH close. If price is at least ``stretch_ticks`` above that anchor, enter
      short at bar close. If price is at least ``stretch_ticks`` below, enter
      long at bar close.
    - Stop: hard fixed stop ``stop_ticks`` beyond entry. No adding, no averaging
      down, one open trade at a time.
    - Target: the selected VWAP/prior-close anchor. Defaults make target
      distance greater than hard stop distance, instead of accepting a small
      mean-reversion target with a larger tail.
    - Max trades/day: ``max_trades_day``.

    Expected skew sign: mild positive to near-neutral, not raw negative
    reversion skew. Mean reversion wins often, but the known death mode is a
    runaway trend. The mandatory fixed stop caps that left tail, and the
    default target is farther than the stop.

    Lucid fit: small, repeated reversion wins can help build >=$150 profit days,
    while the hard stop keeps one wrong fade from consuming the $325 internal
    daily buffer. This is a candidate only if real data confirms the stop is
    honored without slippage blow-through.

    Free strategy params: ``stretch_ticks``, ``stop_ticks``, ``max_trades_day``.
    Contract selection is a sizing constant, not an optimized strategy knob.
    """

    strategy_params = ("stretch_ticks", "stop_ticks", "max_trades_day")

    def __init__(
        self,
        stretch_ticks: int = 24,
        stop_ticks: int = 18,
        max_trades_day: int = 3,
        *,
        contract: str = "MES",
    ):
        super().__init__(contract)
        if stretch_ticks <= 0 or stop_ticks <= 0 or max_trades_day <= 0:
            raise ValueError("strategy params must be positive")
        self.stretch_ticks = int(stretch_ticks)
        self.stop_ticks = int(stop_ticks)
        self.max_trades_day = int(max_trades_day)

    @property
    def name(self):
        return "vwap_reversion_hard_stop"

    def _max_trades_day(self) -> int:
        return self.max_trades_day

    def _entry_plan(self, frame: pd.DataFrame, i: int) -> EntryPlan | None:
        row = frame.loc[i]
        close = float(row["close"])
        anchors = self._finite_anchors(row["vwap"], row["prior_close"])
        threshold = self.stretch_ticks * TICK_SIZE
        candidates = [
            (abs(close - anchor), anchor)
            for anchor in anchors
            if abs(close - anchor) >= threshold
        ]
        if not candidates:
            return None
        _, anchor = min(candidates, key=lambda item: item[0])
        side = -1 if close > anchor else 1
        stop = close - side * self.stop_ticks * TICK_SIZE
        target = anchor
        if side * (target - close) <= 0:
            return None
        return EntryPlan(side=side, stop_price=stop, target_price=target)

    @staticmethod
    def _finite_anchors(*values: float) -> list[float]:
        anchors: list[float] = []
        for value in values:
            value = float(value)
            if np.isfinite(value):
                anchors.append(value)
        return anchors


class TrendPullbackContinuationModel(FuturesRTHModel):
    """Trend-pullback continuation candidate for MES/ES RTH.

    Mechanical rules:
    - Session filter: entries only 09:45-15:30 ET; flat by 16:45 ET or the
      last available RTH bar.
    - Trend: using only prior bars, an uptrend exists when prior close is above
      VWAP and has advanced at least ``2 * pullback_ticks`` over
      ``trend_lookback_bars``. A downtrend is the mirror image.
    - Entry: in an uptrend, enter long when the current bar pulls back at least
      ``pullback_ticks`` from the prior rolling high, closes green, and remains
      above VWAP. In a downtrend, enter short on the mirror pullback, red close,
      and below VWAP.
    - Stop: beyond the pullback extreme by one tick, but skip the trade if that
      distance exceeds ``max_stop_ticks``.
    - Target: fixed 2R from entry. No same-bar exit after entry; if both stop
      and target touch on a later bar, stop wins as a conservative tie-break.
    - Max trades/day: 3.

    Expected skew sign: positive if the continuation premise is real, because
    losers are fixed at the pullback stop while winners are allowed to reach 2R.
    It should be closer to neutral than breakout ORB because entry is after a
    pullback, not at the stretched impulse high/low.

    Lucid fit: a few 2R continuation wins can create controlled >=$150 days
    without needing many fills. ``max_stop_ticks`` prevents one wide pullback
    from burning the $325 internal daily buffer.

    Free strategy params: ``trend_lookback_bars``, ``pullback_ticks``,
    ``max_stop_ticks``. Contract selection is a sizing constant, not an
    optimized strategy knob.
    """

    strategy_params = ("trend_lookback_bars", "pullback_ticks", "max_stop_ticks")
    max_trades_day = 3

    def __init__(
        self,
        trend_lookback_bars: int = 12,
        pullback_ticks: int = 8,
        max_stop_ticks: int = 20,
        *,
        contract: str = "MES",
    ):
        super().__init__(contract)
        if trend_lookback_bars < 2 or pullback_ticks <= 0 or max_stop_ticks <= 0:
            raise ValueError("invalid trend-pullback params")
        self.trend_lookback_bars = int(trend_lookback_bars)
        self.pullback_ticks = int(pullback_ticks)
        self.max_stop_ticks = int(max_stop_ticks)

    @property
    def name(self):
        return "trend_pullback_continuation"

    def _max_trades_day(self) -> int:
        return self.max_trades_day

    def _entry_plan(self, frame: pd.DataFrame, i: int) -> EntryPlan | None:
        if i < self.trend_lookback_bars:
            return None
        row = frame.loc[i]
        window = frame.iloc[i - self.trend_lookback_bars : i]
        if window["_session"].iloc[0] != row["_session"]:
            return None

        close = float(row["close"])
        open_ = float(row["open"])
        vwap = float(row["vwap"])
        prior_close = float(window["close"].iloc[-1])
        trend_move = prior_close - float(window["close"].iloc[0])
        trend_threshold = 2.0 * self.pullback_ticks * TICK_SIZE
        pullback_distance = self.pullback_ticks * TICK_SIZE

        if prior_close > vwap and trend_move >= trend_threshold:
            recent_high = float(window["high"].max())
            if recent_high - float(row["low"]) < pullback_distance:
                return None
            if not (close > open_ and close >= vwap):
                return None
            stop = float(row["low"]) - TICK_SIZE
            return self._risk_capped_plan(1, close, stop)

        if prior_close < vwap and trend_move <= -trend_threshold:
            recent_low = float(window["low"].min())
            if float(row["high"]) - recent_low < pullback_distance:
                return None
            if not (close < open_ and close <= vwap):
                return None
            stop = float(row["high"]) + TICK_SIZE
            return self._risk_capped_plan(-1, close, stop)

        return None

    def _risk_capped_plan(self, side: int, entry: float, stop: float) -> EntryPlan | None:
        risk = side * (entry - stop)
        if risk <= 0:
            return None
        if risk > self.max_stop_ticks * TICK_SIZE:
            return None
        target = entry + side * 2.0 * risk
        return EntryPlan(side=side, stop_price=stop, target_price=target)


class TimeStructuredScalpModel(FuturesRTHModel):
    """Time-structured 1R scalp candidate for MES/ES RTH.

    Mechanical rules:
    - Session filter: entries only during controlled liquid windows
      10:00-11:30 ET and 13:30-15:30 ET; flat by 16:45 ET or the last RTH bar.
    - Entry clock: only consider bars stamped on 30-minute boundaries. This is
      intentionally time-structured, not a parameter search across every bar.
    - Direction: long when close is above VWAP and above the prior bar close;
      short when close is below VWAP and below the prior bar close.
    - Stop: ``scalp_ticks`` from entry.
    - Target: ``scalp_ticks`` from entry, approximately 1R.
    - Max trades/day: ``max_trades_day`` with at least ``cooldown_bars`` between
      entries. One open trade at a time.

    Expected skew sign: neutral by construction. Stop and target are symmetric,
    trade count is capped, and forced session flatten removes overnight/gap
    tails. The edge requirement is simply a true >=50% hit rate after costs.

    Lucid fit: this is the "grind" candidate for $150/day over 5+ profit days:
    many small, bounded risks, each much smaller than the $325 internal daily
    buffer on MES. It should fail honestly if commissions/slippage erase 1R.

    Free strategy params: ``scalp_ticks``, ``max_trades_day``,
    ``cooldown_bars``. Contract selection is a sizing constant, not an
    optimized strategy knob.
    """

    strategy_params = ("scalp_ticks", "max_trades_day", "cooldown_bars")
    entry_start = time(10, 0)
    entry_end = time(15, 30)

    def __init__(
        self,
        scalp_ticks: int = 8,
        max_trades_day: int = 6,
        cooldown_bars: int = 3,
        *,
        contract: str = "MES",
    ):
        super().__init__(contract)
        if scalp_ticks <= 0 or max_trades_day <= 0 or cooldown_bars < 0:
            raise ValueError("invalid scalp params")
        self.scalp_ticks = int(scalp_ticks)
        self.max_trades_day = int(max_trades_day)
        self.cooldown_bars = int(cooldown_bars)
        self._last_entry_i = -10**9

    @property
    def name(self):
        return "time_structured_scalp"

    def strategy_returns(self, df):
        self._last_entry_i = -10**9
        return super().strategy_returns(df)

    def trade_pnls(self, df) -> np.ndarray:
        self._last_entry_i = -10**9
        return super().trade_pnls(df)

    def prop_montecarlo_frame(self, df) -> pd.DataFrame:
        self._last_entry_i = -10**9
        return super().prop_montecarlo_frame(df)

    def _max_trades_day(self) -> int:
        return self.max_trades_day

    def _entry_window(self, t: time) -> bool:
        morning = time(10, 0) <= t <= time(11, 30)
        afternoon = time(13, 30) <= t <= self.entry_end
        return morning or afternoon

    def _entry_plan(self, frame: pd.DataFrame, i: int) -> EntryPlan | None:
        if i == 0 or i - self._last_entry_i <= self.cooldown_bars:
            return None
        row = frame.loc[i]
        if row["_ts"].minute not in (0, 30):
            return None
        close = float(row["close"])
        prior_close = float(frame.loc[i - 1, "close"])
        vwap = float(row["vwap"])

        if close > vwap and close > prior_close:
            side = 1
        elif close < vwap and close < prior_close:
            side = -1
        else:
            return None

        distance = self.scalp_ticks * TICK_SIZE
        self._last_entry_i = i
        return EntryPlan(
            side=side,
            stop_price=close - side * distance,
            target_price=close + side * distance,
        )


class SwingTrendModel(QuantModel):
    """Multi-day ES trend-continuation candidate.

    Mechanical rules:
    - Data: ES intraday OHLCV bars. Bars are folded into CME-style daily
      sessions where the 18:00 ET evening reopen belongs to the next session.
    - Entry: if the prior session closes above the previous ``breakout_days``
      high, buy the next session open. If it closes below the previous
      ``breakout_days`` low, sell the next session open. The breakout window
      excludes the breakout session itself, so there is no lookahead.
    - Stop: one prior-session ATR away from entry, using ``atr_days`` sessions.
    - Target: fixed ``reward_r`` times the stop distance. Conservative tie
      break: if stop and target both print in a daily bar, stop wins.
    - Hold: multi-day. No session flatten, no same-day max-trade loop, no
      adding, no averaging down. Open trades exit only on stop, target, or the
      final available session.

    Expected skew sign: positive if continuation exists, because loss is capped
    near 1R while target is 2-3R. Gap-through-stop remains the left-tail risk.

    Lucid fit: fewer ES trades means the $3.50 round-turn commission is small
    versus the intended daily-swing target. It is a candidate only if overnight
    holding is explicitly allowed for the exact account and the risk engine is
    upgraded for open-position/gap risk.

    Max trades/day: not applicable; one open swing trade at a time.

    Free strategy params: ``breakout_days``, ``atr_days``, ``reward_r``.
    Contract selection is a sizing constant, not an optimized strategy knob.
    """

    strategy_params = ("breakout_days", "atr_days", "reward_r")

    def __init__(
        self,
        breakout_days: int = 20,
        atr_days: int = 14,
        reward_r: float = 2.5,
        *,
        contract: str = "ES",
    ):
        contract = contract.upper()
        if contract not in CONTRACTS:
            raise ValueError(f"unsupported contract {contract!r}; expected MES or ES")
        if breakout_days < 2 or atr_days < 2 or not (2.0 <= float(reward_r) <= 3.0):
            raise ValueError("invalid swing trend params")
        self.contract = contract
        self.point_value = CONTRACTS[contract]["point_value"]
        self.commission_rt = CONTRACTS[contract]["commission_rt"]
        self.breakout_days = int(breakout_days)
        self.atr_days = int(atr_days)
        self.reward_r = float(reward_r)

    @property
    def name(self):
        return "swing_trend"

    def predict(self, asset, ts, data) -> Signal:
        return self._neutral(asset, ts)

    def strategy_returns(self, df):
        daily = self._prepare_daily_frame(df)
        pnl, pos, market, _ = self._simulate_daily(daily)
        return pnl, pos, market

    def trade_pnls(self, df) -> np.ndarray:
        daily = self._prepare_daily_frame(df)
        _, _, _, trades = self._simulate_daily(daily)
        return np.asarray([trade.pnl for trade in trades], dtype=float)

    def prop_montecarlo_frame(self, df) -> pd.DataFrame:
        daily = self._prepare_daily_frame(df)
        _, _, _, trades = self._simulate_daily(daily)
        return pd.DataFrame(
            {
                "entry_ts": [trade.entry_ts for trade in trades],
                "exit_ts": [trade.exit_ts for trade in trades],
                "side": [trade.side for trade in trades],
                "pnl": [trade.pnl for trade in trades],
                "reason": [trade.reason for trade in trades],
            }
        )

    def _prepare_daily_frame(self, df) -> pd.DataFrame:
        frame = pd.DataFrame(df).copy()
        required = {"open", "high", "low", "close"}
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise ValueError(f"missing required columns: {missing}")

        if "ts" in frame.columns:
            ts = pd.to_datetime(frame["ts"])
        elif isinstance(frame.index, pd.DatetimeIndex):
            ts = pd.Series(pd.to_datetime(frame.index), index=frame.index)
        else:
            raise ValueError("provide a ts column or DatetimeIndex for session rules")

        if getattr(ts.dt, "tz", None) is None:
            ts = ts.dt.tz_localize("UTC")
        else:
            ts = ts.dt.tz_convert("UTC")

        et = ts.dt.tz_convert("America/New_York")
        et_naive = et.dt.tz_localize(None)
        session = et_naive.dt.normalize()
        evening = et_naive.dt.time >= time(18, 0)
        session = session + pd.to_timedelta(evening.astype(int), unit="D")

        frame["_ts"] = ts
        frame["_session"] = session
        for col in ("open", "high", "low", "close"):
            frame[col] = frame[col].astype(float)
            if not np.isfinite(frame[col]).all():
                raise ValueError(f"{col} contains non-finite values")
        frame = frame.sort_values("_ts")
        frame = frame[frame["_session"].dt.weekday < 5].copy()

        grouped = frame.groupby("_session", sort=True)
        daily = grouped.agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            open_ts=("_ts", "first"),
            close_ts=("_ts", "last"),
        ).reset_index(drop=False)

        previous_close = daily["close"].shift(1)
        tr = pd.concat(
            [
                daily["high"] - daily["low"],
                (daily["high"] - previous_close).abs(),
                (daily["low"] - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        daily["atr"] = tr.rolling(self.atr_days, min_periods=self.atr_days).mean()
        daily["range_high"] = daily["high"].shift(1).rolling(
            self.breakout_days, min_periods=self.breakout_days
        ).max()
        daily["range_low"] = daily["low"].shift(1).rolling(
            self.breakout_days, min_periods=self.breakout_days
        ).min()
        return daily

    def _simulate_daily(self, daily: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[Trade]]:
        n = len(daily)
        pnl = np.zeros(n, dtype=float)
        pos = np.zeros(n, dtype=float)
        market = np.zeros(n, dtype=float)
        if n > 1:
            market[1:] = np.diff(daily["close"].to_numpy(float)) * self.point_value

        trades: list[Trade] = []
        open_trade: dict[str, float | int | pd.Timestamp] | None = None
        for i in range(1, n):
            row = daily.iloc[i]
            if open_trade is not None:
                pos[i] = float(open_trade["side"])
                exit_price, reason = self._daily_exit_price(open_trade, row, i == n - 1)
                if exit_price is not None:
                    trade = self._close_trade(open_trade, row, exit_price, reason)
                    pnl[i] += trade.pnl
                    trades.append(trade)
                    open_trade = None

            if open_trade is None:
                plan = self._daily_entry_plan(daily, i - 1, float(row["open"]))
                if plan is None:
                    continue
                entry_price = float(row["open"] + plan.side * TICK_SIZE)
                risk = abs(entry_price - plan.stop_price)
                open_trade = {
                    "entry_i": i,
                    "entry_ts": row["open_ts"],
                    "side": int(plan.side),
                    "entry_price": entry_price,
                    "stop_price": float(plan.stop_price),
                    "target_price": float(entry_price + plan.side * self.reward_r * risk),
                }
                pos[i] = float(plan.side)

        return pnl, pos, market, trades

    def _daily_entry_plan(self, daily: pd.DataFrame, signal_i: int, next_open: float) -> EntryPlan | None:
        signal = daily.iloc[signal_i]
        close = float(signal["close"])
        atr = float(signal["atr"])
        range_high = float(signal["range_high"])
        range_low = float(signal["range_low"])
        if not all(np.isfinite(x) for x in (close, atr, range_high, range_low)):
            return None

        if close > range_high:
            side = 1
        elif close < range_low:
            side = -1
        else:
            return None

        entry = next_open + side * TICK_SIZE
        stop = entry - side * atr
        return EntryPlan(side=side, stop_price=float(stop), target_price=0.0)

    def _daily_exit_price(
        self,
        open_trade: dict[str, float | int | pd.Timestamp],
        row: pd.Series,
        is_last_session: bool,
    ) -> tuple[float | None, str]:
        side = int(open_trade["side"])
        stop = float(open_trade["stop_price"])
        target = float(open_trade["target_price"])
        high = float(row["high"])
        low = float(row["low"])
        open_ = float(row["open"])

        if side > 0:
            if open_ <= stop:
                return min(open_, stop - TICK_SIZE), "gap_stop"
            stop_hit = low <= stop
            target_hit = high >= target
        else:
            if open_ >= stop:
                return max(open_, stop + TICK_SIZE), "gap_stop"
            stop_hit = high >= stop
            target_hit = low <= target

        if stop_hit:
            return stop - side * TICK_SIZE, "stop"
        if target_hit:
            return target, "target"
        if is_last_session:
            return float(row["close"]), "last_session"
        return None, ""

    def _close_trade(
        self,
        open_trade: dict[str, float | int | pd.Timestamp],
        row: pd.Series,
        exit_price: float,
        reason: str,
    ) -> Trade:
        side = int(open_trade["side"])
        entry = float(open_trade["entry_price"])
        pnl = side * (exit_price - entry) * self.point_value - self.commission_rt
        return Trade(
            entry_ts=open_trade["entry_ts"],
            exit_ts=row["close_ts"],
            side=side,
            entry_price=entry,
            exit_price=float(exit_price),
            stop_price=float(open_trade["stop_price"]),
            target_price=float(open_trade["target_price"]),
            pnl=float(pnl),
            reason=reason,
        )


class FabioORBDeltaModel(QuantModel):
    """Fabio-style NQ/MNQ ORB + candle-delta long candidate.

    This is a mechanical rebuild from the summarized EasyLanguage rules in the
    work order, not a trusted vendor trade log. The actual PDF appendix was not
    present in the repo when this class was added, so do not call this a
    verbatim appendix port until the appendix is supplied and diffed.

    Mechanical rules:
    - Data: MNQ/NQ 1-minute OHLCV bars.
    - ORB window: 08:30-09:00 ET, using that window's high and low.
    - Signal bars: 5-minute bars after the ORB.
    - Entry: one long entry per session when a 5-minute close is above the ORB
      high and approximate volume delta is above ``delta_threshold``.
    - Delta approximation: each 1-minute bar contributes +volume if
      close > open, -volume if close < open, otherwise 0. This candle-delta
      heuristic is common in public TradingView-style ORB/delta clones, but it
      is not tick/bid-ask volume delta. Treat it as an explicit limitation.
    - Stop: ORB low.
    - Target: ``tp_rr`` times the ORB range width, default 1.0R.
    - Exit: target, stop, or flatten at 14:00 ET. If stop and target both print
      on a later bar, stop wins.
    - Slippage/friction: one adverse tick on market entry, stop, and flatten;
      Lucid round-turn commission from ``CONTRACTS``.

    Expected skew sign: near-neutral if the 1R premise is real; negative if
    ORB stop gap-throughs dominate.

    Lucid fit: MNQ is the intended contract because full NQ does not fit the
    50K FLEX $2,000 MLL / $325 internal buffer.

    Max trades/day: 1.

    Free strategy params: ``orb_minutes``, ``tp_rr``, ``delta_threshold``.
    Defaults mirror the work-order summary: ORB_Dur=30, TP_RR=1.0, and a
    non-tuned positive candle-delta threshold of 0.
    """

    strategy_params = ("orb_minutes", "tp_rr", "delta_threshold")
    entry_start = time(9, 0)
    flatten_time = time(14, 0)

    def __init__(
        self,
        orb_minutes: int = 30,
        tp_rr: float = 1.0,
        delta_threshold: float = 0.0,
        *,
        contract: str = "MNQ",
    ):
        contract = contract.upper()
        if contract not in CONTRACTS:
            raise ValueError(f"unsupported contract {contract!r}; expected MES/ES/MNQ/NQ")
        if orb_minutes != 30:
            raise ValueError("Fabio spec is fixed at ORB_Dur=30; no retuning")
        if float(tp_rr) != 1.0:
            raise ValueError("Fabio spec is fixed at TP_RR=1.0; no retuning")
        self.contract = contract
        self.point_value = CONTRACTS[contract]["point_value"]
        self.commission_rt = CONTRACTS[contract]["commission_rt"]
        self.orb_minutes = int(orb_minutes)
        self.tp_rr = float(tp_rr)
        self.delta_threshold = float(delta_threshold)

    @property
    def name(self):
        return "fabio_orb_delta"

    def predict(self, asset, ts, data) -> Signal:
        return self._neutral(asset, ts)

    def strategy_returns(self, df):
        frame = self._prepare_5m_frame(df)
        pnl, pos, market, _ = self._simulate_5m(frame)
        return pnl, pos, market

    def trade_pnls(self, df) -> np.ndarray:
        frame = self._prepare_5m_frame(df)
        _, _, _, trades = self._simulate_5m(frame)
        return np.asarray([trade.pnl for trade in trades], dtype=float)

    def prop_montecarlo_frame(self, df) -> pd.DataFrame:
        frame = self._prepare_5m_frame(df)
        _, _, _, trades = self._simulate_5m(frame)
        return pd.DataFrame(
            {
                "entry_ts": [trade.entry_ts for trade in trades],
                "exit_ts": [trade.exit_ts for trade in trades],
                "side": [trade.side for trade in trades],
                "pnl": [trade.pnl for trade in trades],
                "reason": [trade.reason for trade in trades],
            }
        )

    def _prepare_5m_frame(self, df) -> pd.DataFrame:
        frame = pd.DataFrame(df).copy()
        required = {"open", "high", "low", "close", "volume"}
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise ValueError(f"missing required columns: {missing}")

        if "ts" in frame.columns:
            ts = pd.to_datetime(frame["ts"])
        elif isinstance(frame.index, pd.DatetimeIndex):
            ts = pd.Series(pd.to_datetime(frame.index), index=frame.index)
        else:
            raise ValueError("provide a ts column or DatetimeIndex for ORB session rules")

        if getattr(ts.dt, "tz", None) is None:
            ts = ts.dt.tz_localize("UTC")
        else:
            ts = ts.dt.tz_convert("UTC")

        et = ts.dt.tz_convert("America/New_York")
        frame["_ts"] = ts
        frame["_ts_et"] = et.dt.tz_localize(None)
        frame["_session"] = frame["_ts_et"].dt.date
        frame["_time"] = frame["_ts_et"].dt.time
        for col in ("open", "high", "low", "close", "volume"):
            frame[col] = frame[col].astype(float)
            if not np.isfinite(frame[col]).all():
                raise ValueError(f"{col} contains non-finite values")
        frame["_delta"] = np.select(
            [frame["close"] > frame["open"], frame["close"] < frame["open"]],
            [frame["volume"], -frame["volume"]],
            default=0.0,
        )
        frame = frame.sort_values("_ts_et")

        rows: list[pd.DataFrame] = []
        for _, session_frame in frame.groupby("_session", sort=True):
            if pd.Timestamp(session_frame["_ts_et"].iloc[0]).weekday() >= 5:
                continue
            orb_start = time(8, 30)
            orb_end = time(9, 0)
            in_window = (session_frame["_time"] >= orb_start) & (session_frame["_time"] < self.flatten_time)
            session_frame = session_frame.loc[in_window].copy()
            if session_frame.empty:
                continue
            bars = (
                session_frame.set_index("_ts_et")
                .resample("5min", label="right", closed="right")
                .agg(
                    open=("open", "first"),
                    high=("high", "max"),
                    low=("low", "min"),
                    close=("close", "last"),
                    volume=("volume", "sum"),
                    approx_delta=("_delta", "sum"),
                    ts=("_ts", "last"),
                    session=("_session", "last"),
                )
                .dropna(subset=["open", "high", "low", "close", "ts", "session"])
            )
            if bars.empty:
                continue
            bars["_ts_et"] = bars.index
            bars["_time"] = bars.index.time
            rows.append(bars.reset_index(drop=True))

        if not rows:
            return pd.DataFrame(
                columns=["open", "high", "low", "close", "volume", "approx_delta", "ts", "session", "_ts_et", "_time"]
            )
        return pd.concat(rows, ignore_index=True)

    def _simulate_5m(self, frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[Trade]]:
        n = len(frame)
        pnl = np.zeros(n, dtype=float)
        pos = np.zeros(n, dtype=float)
        market = np.zeros(n, dtype=float)
        if n > 1:
            market[1:] = np.diff(frame["close"].to_numpy(float)) * self.point_value

        trades: list[Trade] = []
        for _, session_frame in frame.groupby("session", sort=True):
            session_indices = list(session_frame.index)
            if not session_indices:
                continue
            session = frame.loc[session_indices]
            orb_rows = session[(session["_time"] >= time(8, 30)) & (session["_time"] < time(9, 0))]
            if orb_rows.empty:
                continue
            orb_high = float(orb_rows["high"].max())
            orb_low = float(orb_rows["low"].min())
            if not np.isfinite(orb_high) or not np.isfinite(orb_low) or orb_high <= orb_low:
                continue

            open_trade: dict[str, float | int | pd.Timestamp] | None = None
            entered = False
            last_i = session_indices[-1]
            for i in session_indices:
                row = frame.loc[i]
                if open_trade is not None:
                    pos[i] = 1.0
                    exit_price, reason = self._exit_price(open_trade, row, i == last_i)
                    if exit_price is not None:
                        trade = self._close_trade(open_trade, row, exit_price, reason)
                        pnl[i] += trade.pnl
                        trades.append(trade)
                        open_trade = None
                        continue

                if (
                    open_trade is None
                    and not entered
                    and self.entry_start < row["_time"] < self.flatten_time
                    and float(row["close"]) > orb_high
                    and float(row["approx_delta"]) > self.delta_threshold
                ):
                    entry_price = float(row["close"] + TICK_SIZE)
                    orb_range = orb_high - orb_low
                    if orb_range <= 0 or entry_price <= orb_low:
                        continue
                    open_trade = {
                        "entry_i": i,
                        "entry_ts": row["ts"],
                        "side": 1,
                        "entry_price": entry_price,
                        "stop_price": orb_low,
                        "target_price": entry_price + self.tp_rr * orb_range,
                    }
                    pos[i] = 1.0
                    entered = True

        return pnl, pos, market, trades

    def _exit_price(
        self,
        open_trade: dict[str, float | int | pd.Timestamp],
        row: pd.Series,
        is_last_session_bar: bool,
    ) -> tuple[float | None, str]:
        stop = float(open_trade["stop_price"])
        target = float(open_trade["target_price"])
        open_ = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        if open_ <= stop:
            return min(open_, stop - TICK_SIZE), "gap_stop"
        if low <= stop:
            return stop - TICK_SIZE, "stop"
        if high >= target:
            return target, "target"
        if row["_time"] >= self.flatten_time or is_last_session_bar:
            return float(row["close"] - TICK_SIZE), "session_flatten"
        return None, ""

    def _close_trade(
        self,
        open_trade: dict[str, float | int | pd.Timestamp],
        row: pd.Series,
        exit_price: float,
        reason: str,
    ) -> Trade:
        entry = float(open_trade["entry_price"])
        pnl = (float(exit_price) - entry) * self.point_value - self.commission_rt
        return Trade(
            entry_ts=open_trade["entry_ts"],
            exit_ts=row["ts"],
            side=1,
            entry_price=entry,
            exit_price=float(exit_price),
            stop_price=float(open_trade["stop_price"]),
            target_price=float(open_trade["target_price"]),
            pnl=float(pnl),
            reason=reason,
        )


__all__ = [
    "Trade",
    "EntryPlan",
    "FuturesRTHModel",
    "VWAPReversionHardStopModel",
    "TrendPullbackContinuationModel",
    "TimeStructuredScalpModel",
    "SwingTrendModel",
    "FabioORBDeltaModel",
]
