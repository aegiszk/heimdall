"""Okala 80/20 Nasdaq model, mechanically pre-registered.

MNQ only. Pure OHLCV price action from local one-minute bars. The source rule
sheet uses 10-minute structure and 200-second entry candles; because the owned
data is one-minute OHLCV, 200-second candles are reconstructed by resampling
one-minute bars with ``label="right", closed="right"``. Each 200-second candle
therefore contains the available one-minute bars whose timestamps fall inside
that right-closed bin; no sub-minute path is inferred.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import time
from math import ceil, floor
from typing import Any

import numpy as np
import pandas as pd

from core.alpha.base import QuantModel, Signal
from core.risk.prop_engine import PropRiskConfig, PropRiskEngine


EASTERN = "America/New_York"
TICK_SIZE = 0.25
POINT_VALUE = 2.0
TICK_VALUE = 0.50
COMMISSION_RT = 1.0
DAILY_BUFFER = 325.0
STARTING_BALANCE = 50_000.0
ENTRY_START = time(9, 30)
ENTRY_END = time(11, 30)
SESSION_START = time(9, 30)
SESSION_FLATTEN = time(16, 45)
STOP_POINTS = 10.0
TARGET1_POINTS = 15.0
STRONG_MOVE_POINTS = 20.0
LARGE_BODY_MULT = 1.5
MEDIAN_BODY_BARS = 20
MICRO_MAX_CONTRACTS = 40
LEVEL_MISS_MIN_TICKS = 1
LEVEL_MISS_MAX_TICKS = 10
ZONE_TOUCH_TICKS = 2

SETUP_A = "A_FORK"
SETUP_B = "B_CROSS_SECTION"
SETUP_C = "C_DROPPED"


@dataclass(frozen=True)
class StructurePoint:
    ts: pd.Timestamp
    confirmed_ts: pd.Timestamp
    session: object
    kind: str
    price: float


@dataclass(frozen=True)
class PendingZone:
    setup: str
    created_i: int
    side: int
    zone_low: float
    zone_high: float
    level: float
    session: object


@dataclass(frozen=True)
class EntrySignal:
    setup: str
    side: int
    signal_price: float
    ts: pd.Timestamp


@dataclass(frozen=True)
class OkalaTrade:
    entry_ts: pd.Timestamp
    exit_ts: pd.Timestamp
    session: object
    setup: str
    side: int
    entry_price: float
    exit_price: float
    stop_price: float
    tp1_price: float
    runner_target_price: float
    contracts: int
    tp1_contracts: int
    runner_contracts: int
    risk_dollars: float
    pnl: float
    gross_pnl: float
    tp1_hit: bool
    tp1_gross_pnl: float
    runner_gross_pnl: float
    reason: str
    r_mult: float


@dataclass
class OkalaBacktestResult:
    frame: pd.DataFrame
    pnl: np.ndarray
    pos: np.ndarray
    market: np.ndarray
    trades: list[OkalaTrade]
    diagnostics: Counter[str] = field(default_factory=Counter)


class Okala8020Model(QuantModel):
    """Okala 80/20 Nasdaq model.

    Mechanical rules:
    - Market: MNQ only.
    - Levels: integer price levels whose last two digits are 20 or 80.
    - Session: entries 09:30-11:30 ET. Open trades flatten at 16:45 ET or the
      last available bar before then.
    - Structure: 10-minute OHLC bars from one-minute data, resampled with
      ``label="right", closed="right"``. Confirmed 3-bar 10m swing highs/lows
      are used only as runner target candidates.
    - Entry bars: 200-second OHLC bars from one-minute data, resampled with
      ``label="right", closed="right"``.
    - A FORK: prior five 200s bars net at least 20 points in one direction;
      the next 200s candle has a directional wick at least 2x body and stops
      1 to 10 MNQ ticks short of the next 80/20 level; the following candle
      tests within one tick of that wick extreme, fails to break it, and closes
      in reversal direction. Entry is that second candle close.
    - B CROSS-SECTION: two consecutive same-direction 200s candles have bodies
      at least 1.5x the prior 20-bar median body and leave a strict open/close
      gap between candle1 close and candle2 open. The gap zone must contain an
      80/20 level. Entry is the first later retrace that comes within two MNQ
      ticks of that zone in the original direction.
    - C h PATTERN: intentionally dropped. The text requires a bounce/rollover
      rejection of cross-section or 80/20 level, which cannot be encoded from
      the supplied wording without inventing extra pivots, bounce sizes, or
      rejection thresholds.
    - Stop: fixed 10 points.
    - Management: TP1 at 15 points, exits the integer majority nearest 2/3 of
      contracts, moves runner stop to breakeven, runner targets the next 80/20
      level or prior confirmed 10m opposing structure, then session flatten.
    - Friction: $1.00 round-turn per MNQ contract, one tick adverse entry,
      stop, and flatten; gap-through stops fill through the gap.

    Expected skew sign: positive if TP1 plus 80/20/structure runners work;
    otherwise neutral-to-negative from fixed stops and stop slippage.

    Lucid fit: fixed 10-point stop sizes through PropRiskEngine.allowed_size
    against the $325 buffer; no overnight hold.

    Max trades/day: no explicit Okala cap was supplied. The simulator permits
    one open trade at a time during 09:30-11:30 ET.
    """

    strategy_params: tuple[str, ...] = ()

    @property
    def name(self) -> str:
        return "okala_8020"

    def predict(self, asset: str, ts: str, data) -> Signal:
        return self._neutral(asset, ts)

    def strategy_returns(self, df):
        result = self._run_backtest(df)
        return result.pnl, result.pos, result.market

    def trade_pnls(self, df) -> np.ndarray:
        return np.asarray([trade.pnl for trade in self._run_backtest(df).trades], dtype=float)

    def prop_montecarlo_frame(self, df) -> pd.DataFrame:
        return self.trades_frame(self._run_backtest(df).trades)

    @staticmethod
    def discretion_gaps() -> list[str]:
        return [
            "C h-pattern dropped: bounce/rollover rejection needs extra pivot and rejection thresholds not supplied in the rule sheet.",
            "200-second candles are reconstructed from one-minute OHLCV using pandas resample('200s', label='right', closed='right'); no sub-minute path is inferred.",
            "A FORK level failure is the pre-registered 1-to-10-tick miss proxy: the wick stops short of the next 80/20 level without touching it.",
            "A FORK wick retest is within one MNQ tick of the wick extreme without breaking that extreme.",
            "B CROSS-SECTION imbalance is a strict open/close gap between candle1 close and candle2 open; overlap means no imbalance.",
            "The 20-bar median body for B uses only the 20 completed 200-second candles before candle1.",
            "Runner 'opposing structure' is the nearest prior confirmed 3-bar 10-minute swing high for longs or swing low for shorts, if beyond TP1.",
            "TP1 exits integer contracts by ceil(2/3 * contracts) so the exited quantity is a true majority.",
        ]

    @staticmethod
    def trades_frame(trades: list[OkalaTrade]) -> pd.DataFrame:
        columns = [
            "entry_ts",
            "exit_ts",
            "session",
            "setup",
            "side",
            "entry_price",
            "exit_price",
            "stop_price",
            "tp1_price",
            "runner_target_price",
            "contracts",
            "tp1_contracts",
            "runner_contracts",
            "risk_dollars",
            "pnl",
            "gross_pnl",
            "tp1_hit",
            "tp1_gross_pnl",
            "runner_gross_pnl",
            "reason",
            "r_mult",
        ]
        if not trades:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame([{col: getattr(trade, col) for col in columns} for trade in trades])

    def _run_backtest(self, df) -> OkalaBacktestResult:
        raw = self._prepare_raw(df)
        bars_200s = self._resample(raw, "200s")
        bars_10m = self._resample(raw, "10min")
        n = len(bars_200s)
        pnl = np.zeros(n, dtype=float)
        pos = np.zeros(n, dtype=float)
        market = np.zeros(n, dtype=float)
        if n > 1:
            market[1:] = np.diff(bars_200s["close"].to_numpy(float)) * POINT_VALUE
        if bars_200s.empty:
            return OkalaBacktestResult(bars_200s, pnl, pos, market, [], Counter())

        structures = self._build_structure_points(bars_10m)
        structures_by_session: dict[object, list[StructurePoint]] = {}
        for point in structures:
            structures_by_session.setdefault(point.session, []).append(point)

        trades: list[OkalaTrade] = []
        diagnostics: Counter[str] = Counter()
        for session, day in bars_200s.groupby("session", sort=True):
            session_indices = list(day.index)
            if not session_indices:
                continue
            levels = okala_levels(float(day["low"].min()), float(day["high"].max()))
            session_structures = structures_by_session.get(session, [])
            pending: list[PendingZone] = []
            open_trade: dict[str, Any] | None = None
            body = (day["close"] - day["open"]).abs()
            last_session_i = session_indices[-1]

            for local_pos, i in enumerate(session_indices):
                row = bars_200s.loc[i]
                if open_trade is not None and i > int(open_trade["entry_i"]):
                    trade = self._maybe_close_trade(open_trade, row, i == last_session_i)
                    if trade is not None:
                        trades.append(trade)
                        self._mark_trade_arrays(bars_200s, pnl, pos, trade)
                        open_trade = None
                    else:
                        pos[i] = float(open_trade["side"]) * float(open_trade["contracts"])

                touched_zones = self._touched_zones(pending, row, local_pos)
                pending = [zone for zone in pending if zone not in touched_zones]

                if open_trade is None and self._entry_window(row["_time"]):
                    signal = self._fork_signal(day, body, local_pos, levels, diagnostics)
                    if signal is None and touched_zones:
                        signal = self._cross_section_signal(touched_zones[0], row)
                        diagnostics["B_zone_touch"] += 1
                    if signal is not None:
                        open_trade = self._open_trade(signal, i, session, bars_200s, levels, session_structures)
                        if open_trade is not None:
                            diagnostics[f"{signal.setup}_entries"] += 1
                            pos[i] = float(open_trade["side"]) * float(open_trade["contracts"])

                new_zone = self._new_cross_section_zone(day, body, local_pos, levels, diagnostics)
                if new_zone is not None:
                    pending.append(new_zone)

        return OkalaBacktestResult(bars_200s, pnl, pos, market, trades, diagnostics)

    def _prepare_raw(self, df) -> pd.DataFrame:
        frame = pd.DataFrame(df).copy()
        required = {"open", "high", "low", "close", "volume"}
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise ValueError(f"missing required columns: {missing}")
        if "ts" in frame.columns:
            ts = pd.Series(pd.to_datetime(frame["ts"]), index=frame.index)
        elif isinstance(frame.index, pd.DatetimeIndex):
            ts = pd.Series(pd.to_datetime(frame.index), index=frame.index)
        else:
            raise ValueError("provide a ts column or DatetimeIndex")
        if getattr(ts.dt, "tz", None) is None:
            ts = ts.dt.tz_localize("UTC")
        else:
            ts = ts.dt.tz_convert("UTC")
        frame["_ts_utc"] = ts
        frame["_ts_et"] = ts.dt.tz_convert(EASTERN)
        frame["_session"] = frame["_ts_et"].dt.date
        frame["_time"] = frame["_ts_et"].dt.time
        for col in ("open", "high", "low", "close", "volume"):
            frame[col] = frame[col].astype(float)
            if not np.isfinite(frame[col]).all():
                raise ValueError(f"{col} contains non-finite values")
        mask = (
            (frame["_ts_et"].dt.weekday < 5)
            & (frame["_time"] >= SESSION_START)
            & (frame["_time"] <= SESSION_FLATTEN)
        )
        return frame.loc[mask].sort_values("_ts_et").copy()

    @staticmethod
    def _resample(raw: pd.DataFrame, freq: str) -> pd.DataFrame:
        rows: list[pd.DataFrame] = []
        for _, day in raw.groupby("_session", sort=True):
            bars = (
                day.set_index("_ts_et")
                .resample(freq, label="right", closed="right")
                .agg(
                    open=("open", "first"),
                    high=("high", "max"),
                    low=("low", "min"),
                    close=("close", "last"),
                    volume=("volume", "sum"),
                    session=("_session", "last"),
                )
                .dropna(subset=["open", "high", "low", "close", "session"])
            )
            if bars.empty:
                continue
            bars["ts"] = bars.index
            bars["_time"] = bars.index.time
            rows.append(bars.reset_index(drop=True))
        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume", "session", "ts", "_time"])
        return pd.concat(rows, ignore_index=True)

    @staticmethod
    def _entry_window(clock: time) -> bool:
        return ENTRY_START <= clock <= ENTRY_END

    def _fork_signal(
        self,
        day: pd.DataFrame,
        body: pd.Series,
        local_pos: int,
        levels: list[float],
        diagnostics: Counter[str],
    ) -> EntrySignal | None:
        if local_pos < 6:
            return None
        confirm = day.iloc[local_pos]
        candidate = day.iloc[local_pos - 1]
        move_start = day.iloc[local_pos - 6]
        prior_move = float(day.iloc[local_pos - 2]["close"] - move_start["open"])
        if abs(prior_move) < STRONG_MOVE_POINTS:
            return None
        diagnostics["A_strong_move"] += 1
        direction = 1 if prior_move > 0 else -1
        candidate_body = float(body.iloc[local_pos - 1])
        upper_wick = float(candidate["high"] - max(candidate["open"], candidate["close"]))
        lower_wick = float(min(candidate["open"], candidate["close"]) - candidate["low"])

        if direction > 0:
            if not (upper_wick > 0.0 and upper_wick >= 2.0 * candidate_body):
                return None
            if not missed_level_by_allowed_ticks(float(candidate["high"]), levels, side=1):
                return None
            diagnostics["A_wick_level_miss"] += 1
            tested = float(confirm["high"]) >= float(candidate["high"]) - TICK_SIZE
            failed_break = float(confirm["high"]) <= float(candidate["high"])
            reversed_ = float(confirm["close"]) < float(confirm["open"]) and float(confirm["close"]) < float(candidate["close"])
            if tested and failed_break and reversed_:
                diagnostics["A_second_candle_confirm"] += 1
                return EntrySignal(SETUP_A, -1, float(confirm["close"]), confirm["ts"])
            return None

        if not (lower_wick > 0.0 and lower_wick >= 2.0 * candidate_body):
            return None
        if not missed_level_by_allowed_ticks(float(candidate["low"]), levels, side=-1):
            return None
        diagnostics["A_wick_level_miss"] += 1
        tested = float(confirm["low"]) <= float(candidate["low"]) + TICK_SIZE
        failed_break = float(confirm["low"]) >= float(candidate["low"])
        reversed_ = float(confirm["close"]) > float(confirm["open"]) and float(confirm["close"]) > float(candidate["close"])
        if tested and failed_break and reversed_:
            diagnostics["A_second_candle_confirm"] += 1
            return EntrySignal(SETUP_A, 1, float(confirm["close"]), confirm["ts"])
        return None

    def _new_cross_section_zone(
        self,
        day: pd.DataFrame,
        body: pd.Series,
        local_pos: int,
        levels: list[float],
        diagnostics: Counter[str],
    ) -> PendingZone | None:
        if local_pos < MEDIAN_BODY_BARS + 1:
            return None
        c1 = day.iloc[local_pos - 1]
        c2 = day.iloc[local_pos]
        history = body.iloc[local_pos - MEDIAN_BODY_BARS - 1 : local_pos - 1]
        if len(history) < MEDIAN_BODY_BARS:
            return None
        median_body = float(history.median())
        if median_body <= 0.0:
            return None
        body1 = float(body.iloc[local_pos - 1])
        body2 = float(body.iloc[local_pos])
        dir1 = candle_direction(c1)
        dir2 = candle_direction(c2)
        if dir1 == 0 or dir1 != dir2:
            return None
        if body1 < LARGE_BODY_MULT * median_body or body2 < LARGE_BODY_MULT * median_body:
            return None
        diagnostics["B_large_body_pair"] += 1

        if dir1 > 0:
            if float(c2["open"]) <= float(c1["close"]):
                return None
            zone_low = float(c1["close"])
            zone_high = float(c2["open"])
        else:
            if float(c2["open"]) >= float(c1["close"]):
                return None
            zone_low = float(c2["open"])
            zone_high = float(c1["close"])
        diagnostics["B_gap_imbalance"] += 1
        zone_levels = [level for level in levels if zone_low <= level <= zone_high]
        if not zone_levels:
            return None
        diagnostics["B_zone_has_8020"] += 1
        level = min(zone_levels, key=lambda value: abs(value - (zone_low + zone_high) / 2.0))
        return PendingZone(SETUP_B, local_pos, dir1, zone_low, zone_high, float(level), c2["session"])

    @staticmethod
    def _touched_zones(pending: list[PendingZone], row: pd.Series, local_pos: int) -> list[PendingZone]:
        touched: list[PendingZone] = []
        high = float(row["high"])
        low = float(row["low"])
        touch_pad = ZONE_TOUCH_TICKS * TICK_SIZE
        for zone in pending:
            if local_pos <= zone.created_i:
                continue
            if low <= zone.zone_high + touch_pad and high >= zone.zone_low - touch_pad:
                touched.append(zone)
        return touched

    @staticmethod
    def _cross_section_signal(zone: PendingZone, row: pd.Series) -> EntrySignal:
        signal_price = (
            zone.zone_high + ZONE_TOUCH_TICKS * TICK_SIZE
            if zone.side > 0
            else zone.zone_low - ZONE_TOUCH_TICKS * TICK_SIZE
        )
        return EntrySignal(zone.setup, zone.side, float(signal_price), row["ts"])

    def _open_trade(
        self,
        signal: EntrySignal,
        entry_i: int,
        session: object,
        bars: pd.DataFrame,
        levels: list[float],
        structures: list[StructurePoint],
    ) -> dict[str, Any] | None:
        side = int(signal.side)
        entry_price = float(signal.signal_price + side * TICK_SIZE)
        stop_price = entry_price - side * STOP_POINTS
        stop_ticks = STOP_POINTS / TICK_SIZE
        contracts = self._allowed_contracts(stop_ticks)
        if contracts <= 0:
            return None
        tp1_contracts = int(ceil(contracts * 2.0 / 3.0))
        runner_contracts = contracts - tp1_contracts
        tp1_price = entry_price + side * TARGET1_POINTS
        runner_target = self._runner_target(entry_price, tp1_price, side, levels, structures, signal.ts)
        return {
            "entry_i": entry_i,
            "entry_ts": signal.ts,
            "session": session,
            "setup": signal.setup,
            "side": side,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "runner_stop": stop_price,
            "tp1_price": tp1_price,
            "runner_target_price": runner_target,
            "contracts": contracts,
            "tp1_contracts": tp1_contracts,
            "runner_contracts": runner_contracts,
            "risk_dollars": contracts * STOP_POINTS * POINT_VALUE,
            "tp1_hit": False,
            "tp1_gross": 0.0,
        }

    @staticmethod
    def _runner_target(
        entry: float,
        tp1: float,
        side: int,
        levels: list[float],
        structures: list[StructurePoint],
        entry_ts: pd.Timestamp,
    ) -> float:
        if side > 0:
            candidates = [level for level in levels if level > tp1]
            candidates.extend(
                point.price
                for point in structures
                if point.kind == "high" and point.confirmed_ts <= entry_ts and point.price > tp1
            )
            if candidates:
                return float(min(candidates))
            return float(next_okala_level(max(entry, tp1), side=1))
        candidates = [level for level in levels if level < tp1]
        candidates.extend(
            point.price
            for point in structures
            if point.kind == "low" and point.confirmed_ts <= entry_ts and point.price < tp1
        )
        if candidates:
            return float(max(candidates))
        return float(next_okala_level(min(entry, tp1), side=-1))

    def _maybe_close_trade(
        self,
        open_trade: dict[str, Any],
        row: pd.Series,
        is_last_session_bar: bool,
    ) -> OkalaTrade | None:
        side = int(open_trade["side"])
        if not bool(open_trade["tp1_hit"]):
            stop_exit, stop_reason = stop_exit_price(side, float(open_trade["stop_price"]), row)
            if stop_exit is not None:
                gross = int(open_trade["contracts"]) * side * (stop_exit - float(open_trade["entry_price"])) * POINT_VALUE
                return self._close_trade(open_trade, row, stop_exit, gross, 0.0, False, stop_reason)
            if target_hit(side, float(open_trade["tp1_price"]), row):
                tp1_gross = int(open_trade["tp1_contracts"]) * side * (
                    float(open_trade["tp1_price"]) - float(open_trade["entry_price"])
                ) * POINT_VALUE
                open_trade["tp1_hit"] = True
                open_trade["tp1_gross"] = float(tp1_gross)
                open_trade["runner_stop"] = float(open_trade["entry_price"])
                if not (row["_time"] >= SESSION_FLATTEN or is_last_session_bar):
                    return None
            else:
                if row["_time"] >= SESSION_FLATTEN or is_last_session_bar:
                    exit_price = float(row["close"] - side * TICK_SIZE)
                    gross = int(open_trade["contracts"]) * side * (
                        exit_price - float(open_trade["entry_price"])
                    ) * POINT_VALUE
                    return self._close_trade(
                        open_trade,
                        row,
                        exit_price,
                        gross,
                        0.0,
                        False,
                        "session_flatten",
                    )
                return None

        runner_contracts = int(open_trade["runner_contracts"])
        if runner_contracts <= 0:
            return self._close_trade(
                open_trade,
                row,
                float(open_trade["tp1_price"]),
                float(open_trade["tp1_gross"]),
                0.0,
                True,
                "tp1_no_runner",
            )
        stop_exit, stop_reason = stop_exit_price(side, float(open_trade["runner_stop"]), row)
        if stop_exit is not None:
            runner_gross = runner_contracts * side * (stop_exit - float(open_trade["entry_price"])) * POINT_VALUE
            return self._close_trade(
                open_trade,
                row,
                stop_exit,
                float(open_trade["tp1_gross"]) + runner_gross,
                runner_gross,
                True,
                f"runner_{stop_reason}",
            )
        runner_target = float(open_trade["runner_target_price"])
        if target_hit(side, runner_target, row):
            runner_gross = runner_contracts * side * (runner_target - float(open_trade["entry_price"])) * POINT_VALUE
            return self._close_trade(
                open_trade,
                row,
                runner_target,
                float(open_trade["tp1_gross"]) + runner_gross,
                runner_gross,
                True,
                "runner_target",
            )
        if row["_time"] >= SESSION_FLATTEN or is_last_session_bar:
            exit_price = float(row["close"] - side * TICK_SIZE)
            runner_gross = runner_contracts * side * (exit_price - float(open_trade["entry_price"])) * POINT_VALUE
            return self._close_trade(
                open_trade,
                row,
                exit_price,
                float(open_trade["tp1_gross"]) + runner_gross,
                runner_gross,
                True,
                "runner_session_flatten",
            )
        return None

    def _close_trade(
        self,
        open_trade: dict[str, Any],
        row: pd.Series,
        exit_price: float,
        gross: float,
        runner_gross: float,
        tp1_hit: bool,
        reason: str,
    ) -> OkalaTrade:
        contracts = int(open_trade["contracts"])
        pnl = float(gross) - contracts * COMMISSION_RT
        risk = float(open_trade["risk_dollars"])
        return OkalaTrade(
            entry_ts=open_trade["entry_ts"],
            exit_ts=row["ts"],
            session=open_trade["session"],
            setup=open_trade["setup"],
            side=int(open_trade["side"]),
            entry_price=float(open_trade["entry_price"]),
            exit_price=float(exit_price),
            stop_price=float(open_trade["stop_price"]),
            tp1_price=float(open_trade["tp1_price"]),
            runner_target_price=float(open_trade["runner_target_price"]),
            contracts=contracts,
            tp1_contracts=int(open_trade["tp1_contracts"]),
            runner_contracts=int(open_trade["runner_contracts"]),
            risk_dollars=risk,
            pnl=pnl,
            gross_pnl=float(gross),
            tp1_hit=bool(tp1_hit),
            tp1_gross_pnl=float(open_trade["tp1_gross"]) if tp1_hit else 0.0,
            runner_gross_pnl=float(runner_gross),
            reason=reason,
            r_mult=pnl / risk if risk > 0 else 0.0,
        )

    @staticmethod
    def _mark_trade_arrays(frame: pd.DataFrame, pnl: np.ndarray, pos: np.ndarray, trade: OkalaTrade) -> None:
        entry = np.flatnonzero((frame["ts"] == trade.entry_ts).to_numpy())
        exit_ = np.flatnonzero((frame["ts"] == trade.exit_ts).to_numpy())
        if len(entry) == 0 or len(exit_) == 0:
            return
        entry_i = int(entry[0])
        exit_i = int(exit_[0])
        if exit_i >= entry_i:
            pos[entry_i : exit_i + 1] = trade.side * trade.contracts
            pnl[exit_i] += trade.pnl

    @staticmethod
    def _allowed_contracts(stop_ticks: float) -> int:
        engine = PropRiskEngine(config=PropRiskConfig(daily_buffer=DAILY_BUFFER))
        return min(engine.allowed_size(TICK_VALUE, stop_ticks), MICRO_MAX_CONTRACTS)

    @staticmethod
    def _build_structure_points(bars_10m: pd.DataFrame) -> list[StructurePoint]:
        points: list[StructurePoint] = []
        if len(bars_10m) < 3:
            return points
        for i in range(1, len(bars_10m) - 1):
            prev_row = bars_10m.iloc[i - 1]
            row = bars_10m.iloc[i]
            next_row = bars_10m.iloc[i + 1]
            if row["session"] != prev_row["session"] or row["session"] != next_row["session"]:
                continue
            if float(row["high"]) > float(prev_row["high"]) and float(row["high"]) >= float(next_row["high"]):
                points.append(
                    StructurePoint(row["ts"], next_row["ts"], row["session"], "high", float(row["high"]))
                )
            if float(row["low"]) < float(prev_row["low"]) and float(row["low"]) <= float(next_row["low"]):
                points.append(
                    StructurePoint(row["ts"], next_row["ts"], row["session"], "low", float(row["low"]))
                )
        return points


def okala_levels(low: float, high: float) -> list[float]:
    if high < low:
        low, high = high, low
    start = int(floor(low / 100.0)) * 100
    end = int(ceil(high / 100.0)) * 100
    levels: list[float] = []
    for base in range(start - 100, end + 101, 100):
        for suffix in (20, 80):
            level = float(base + suffix)
            if low <= level <= high:
                levels.append(level)
    return sorted(set(levels))


def next_okala_level(price: float, side: int) -> float:
    base = int(floor(price / 100.0)) * 100
    candidates: list[float] = []
    for offset in range(-2, 4):
        for suffix in (20, 80):
            candidates.append(float(base + offset * 100 + suffix))
    if side > 0:
        above = [level for level in candidates if level > price]
        return min(above)
    below = [level for level in candidates if level < price]
    return max(below)


def missed_level_by_allowed_ticks(price: float, levels: list[float], side: int) -> bool:
    min_miss = LEVEL_MISS_MIN_TICKS * TICK_SIZE
    max_miss = LEVEL_MISS_MAX_TICKS * TICK_SIZE
    if side > 0:
        candidates = [level for level in levels if level > price]
        if not candidates:
            level = next_okala_level(price, side=1)
        else:
            level = min(candidates)
        miss = level - price
        return min_miss - 1e-12 <= miss <= max_miss + 1e-12
    candidates = [level for level in levels if level < price]
    if not candidates:
        level = next_okala_level(price, side=-1)
    else:
        level = max(candidates)
    miss = price - level
    return min_miss - 1e-12 <= miss <= max_miss + 1e-12


def candle_direction(row: pd.Series) -> int:
    close = float(row["close"])
    open_ = float(row["open"])
    if close > open_:
        return 1
    if close < open_:
        return -1
    return 0


def stop_exit_price(side: int, stop: float, row: pd.Series) -> tuple[float | None, str]:
    open_ = float(row["open"])
    high = float(row["high"])
    low = float(row["low"])
    if side > 0:
        if open_ <= stop:
            return min(open_, stop - TICK_SIZE), "gap_stop"
        if low <= stop:
            return stop - TICK_SIZE, "stop"
    else:
        if open_ >= stop:
            return max(open_, stop + TICK_SIZE), "gap_stop"
        if high >= stop:
            return stop + TICK_SIZE, "stop"
    return None, ""


def target_hit(side: int, target: float, row: pd.Series) -> bool:
    if side > 0:
        return float(row["high"]) >= target
    return float(row["low"]) <= target


__all__ = [
    "Okala8020Model",
    "OkalaTrade",
    "OkalaBacktestResult",
    "StructurePoint",
    "PendingZone",
    "okala_levels",
    "next_okala_level",
    "missed_level_by_allowed_ticks",
]
