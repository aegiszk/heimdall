"""Dhesi/Chart Fanatics inversion model, mechanically pre-registered.

This module intentionally uses only OHLCV price action. It does not import data
connectors, execution adapters, or /meta. The discretion in the source material
is reduced to fixed proxies and those proxies are exposed by
``discretion_gaps()`` for reporting.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time
import math

import numpy as np
import pandas as pd

from core.alpha.base import QuantModel, Signal
from core.risk.prop_engine import PropRiskConfig, PropRiskEngine


EASTERN = "America/New_York"
TICK_SIZE = 0.25
STARTING_BALANCE = 50_000.0
DAILY_BUFFER = 325.0
RTH_OPEN = time(9, 30)
ENTRY_START = time(10, 0)
SESSION_CLOSE = time(16, 0)
HTF_DISPLACEMENT_MIN_POINTS = 30.0
FVG_LOOKBACK_SESSIONS = 20
EQUAL_TOLERANCE = 0.0005
TP1_MIN_R = 1.5
MICRO_MAX_CONTRACTS = 40
MINI_MAX_CONTRACTS = 4

CONTRACTS = {
    "MES": {"point_value": 5.0, "tick_value": 1.25, "commission_rt": 1.0, "max_contracts": MICRO_MAX_CONTRACTS},
    "MNQ": {"point_value": 2.0, "tick_value": 0.50, "commission_rt": 1.0, "max_contracts": MICRO_MAX_CONTRACTS},
    "ES": {"point_value": 50.0, "tick_value": 12.50, "commission_rt": 3.50, "max_contracts": MINI_MAX_CONTRACTS},
}


@dataclass(frozen=True)
class Pool:
    level: float
    kind: str
    count: int = 1


@dataclass(frozen=True)
class FVG:
    idx: int
    timeframe: str
    formed_ts: pd.Timestamp
    session: object
    direction: int
    zone_low: float
    zone_high: float
    inverted_ts: pd.Timestamp | None = None


@dataclass(frozen=True)
class InversionEvent:
    ts: pd.Timestamp
    session: object
    bias: int
    timeframe: str
    zone_low: float
    zone_high: float
    fvg_direction: int
    fvg_formed_ts: pd.Timestamp
    close: float
    displacement_points: float


@dataclass(frozen=True)
class LTFEvent:
    formed_ts: pd.Timestamp
    inverted_ts: pd.Timestamp
    session: object
    bias: int
    zone_low: float
    zone_high: float
    formation_low: float
    formation_high: float
    close: float


@dataclass(frozen=True)
class SweepEvent:
    ts: pd.Timestamp
    session: object
    bias: int
    level: float
    pool_kind: str


@dataclass(frozen=True)
class SwingPoint:
    ts: pd.Timestamp
    confirmed_ts: pd.Timestamp
    session: object
    kind: str
    price: float


@dataclass(frozen=True)
class Trade:
    entry_ts: pd.Timestamp
    exit_ts: pd.Timestamp
    session: object
    side: int
    entry_price: float
    exit_price: float
    stop_price: float
    tp1_price: float
    runner_target_price: float | None
    contracts: int
    risk_dollars: float
    pnl: float
    gross_pnl: float
    tp1_hit: bool
    tp1_gross_pnl: float
    runner_gross_pnl: float
    reason: str
    htf_timeframe: str
    sweep_pool: str
    tp1_pool: str
    runner_pool: str
    r_mult: float


@dataclass
class BacktestResult:
    frame: pd.DataFrame
    pnl: np.ndarray
    pos: np.ndarray
    market: np.ndarray
    trades: list[Trade]


class InversionModel(QuantModel):
    """Long/short liquidity-sweep -> HTF inversion -> LTF retracement model.

    Mechanical rules:
    - Session: RTH-only 09:30-16:00 ET. Entries are blocked before 10:00 ET.
    - Liquidity sweep: prior RTH high/low, prior full ET day high/low, rolling
      20-RTH-session high/low, or prior-session equal highs/lows. A sweep must
      trade through the pool and close back inside within 3 one-minute bars.
    - HTF inversion: use 4H FVGs when a formed 4H FVG exists within the
      20-session lookback at sweep time; otherwise use 1H. Bullish FVGs invert
      on a close below the zone, bearish FVGs invert on a close above the zone.
      The HTF inversion bar body must displace at least 30 raw points.
    - LTF retracement: a 15m bar must overlap the HTF inversion FVG zone.
    - Entry trigger: a 5m opposite-direction FVG forms during the retracement
      and then inverts in the new HTF-bias direction. Entry is at that 5m close.
    - Stop: one tick beyond the most recent confirmed 15m fractal swing in the
      stop direction after HTF inversion. If no such swing exists, skip.
    - TP1/runner: TP1 is the nearest opposing pool, promoted to at least 1.5R.
      Half exits at TP1 and runner stop moves to breakeven. Runner targets the
      next major pool: rolling 20-session extreme or stacked equal highs/lows.
    - Risk/friction: size is delegated to PropRiskEngine.allowed_size with
      daily_buffer=325. Entries/stops/session-flatten get one adverse tick;
      gap-through stops fill through the gap.

    Expected skew sign: positive if the runner reaches major pools often enough;
    otherwise neutral-to-negative from stop-market slippage.

    Lucid fit: one entry per RTH session, no overnight hold, hard daily-buffer
    sizing, and all trades flatten by the RTH close used by this offline test.

    Max trades/day: 1 by model rule; the two-loss daily stop is still encoded
    but cannot normally bind because of the one-entry cap.
    """

    strategy_params: tuple[str, ...] = ()

    def __init__(self, *, contract: str = "MES"):
        contract = contract.upper()
        if contract not in CONTRACTS:
            raise ValueError(f"unsupported contract {contract!r}; expected one of {sorted(CONTRACTS)}")
        self.contract = contract
        self.point_value = float(CONTRACTS[contract]["point_value"])
        self.tick_value = float(CONTRACTS[contract]["tick_value"])
        self.commission_rt = float(CONTRACTS[contract]["commission_rt"])
        self.max_contracts = int(CONTRACTS[contract]["max_contracts"])

    @property
    def name(self) -> str:
        return "inversion_model"

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
    def trades_frame(trades: list[Trade]) -> pd.DataFrame:
        columns = [
            "entry_ts",
            "exit_ts",
            "session",
            "side",
            "entry_price",
            "exit_price",
            "stop_price",
            "tp1_price",
            "runner_target_price",
            "contracts",
            "risk_dollars",
            "pnl",
            "gross_pnl",
            "tp1_hit",
            "tp1_gross_pnl",
            "runner_gross_pnl",
            "reason",
            "htf_timeframe",
            "sweep_pool",
            "tp1_pool",
            "runner_pool",
            "r_mult",
        ]
        if not trades:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame([{col: getattr(trade, col) for col in columns} for trade in trades])

    @staticmethod
    def discretion_gaps() -> list[str]:
        return [
            "Monthly liquidity is the fixed rolling 20-RTH-session high/low proxy from the prompt.",
            "Equal highs/lows use prior confirmed 3-bar fractal swings from the previous 20 RTH sessions; same-session equal levels are ignored as a stricter no-lookahead proxy.",
            "Equal-high sweep level is the max of the equal-high cluster and equal-low sweep level is the min of the equal-low cluster, so price must trade through the whole cluster.",
            "Cleanest timeframe discretion is fixed: use 4H only if a formed 4H FVG exists within 20 sessions at sweep time; otherwise use 1H.",
            "When several FVGs invert on the same HTF close, the most recently formed matching FVG supplies the inversion zone.",
            "Dhesi's displacement filter is encoded as the stricter HTF inversion candle body proxy: abs(close - open) must be at least 30 raw points.",
            "15m retracement is a bar-range overlap with the HTF inversion FVG zone after the HTF inversion close.",
            "A 5m FVG is considered formed during retracement only when its third candle overlaps the HTF zone and its later inversion close is in the HTF-bias direction.",
            "The swing that caused the LTF inversion is proxied by the most recent confirmed 15m fractal swing in the stop direction after HTF inversion; no confirmed swing means no trade.",
            "TP1 closer than 1.5R is promoted to exactly 1.5R rather than taking a sub-1.5R pool target.",
            "Major runner pools are only rolling 20-session extremes or stacked equal-high/low clusters with at least 3 prior swing points.",
            "This offline implementation uses RTH 09:30-16:00 ET as the session and flatten time, which is stricter than using the 16:45 Lucid risk-engine clock.",
        ]

    def _run_backtest(self, df) -> BacktestResult:
        frame = self._prepare_frame(df)
        n = len(frame)
        pnl = np.zeros(n, dtype=float)
        pos = np.zeros(n, dtype=float)
        market = np.zeros(n, dtype=float)
        if n > 1:
            market[1:] = np.diff(frame["close"].to_numpy(float)) * self.point_value
        if frame.empty:
            return BacktestResult(frame, pnl, pos, market, [])

        sessions = list(frame["_session"].drop_duplicates())
        session_ord = {session: idx for idx, session in enumerate(sessions)}
        pools_by_session = self._build_session_pools(frame, session_ord)
        htf_4h = self._resample_bars(frame, "4h")
        htf_1h = self._resample_bars(frame, "1h")
        bars_15m = self._resample_bars(frame, "15min")
        bars_5m = self._resample_bars(frame, "5min")
        fvgs_4h, inversions_4h = self._build_inversion_events(htf_4h, "4H", session_ord)
        _, inversions_1h = self._build_inversion_events(htf_1h, "1H", session_ord)
        ltf_events = self._build_ltf_events(bars_5m)
        swings_15m = self._build_swings(bars_15m)
        idx_by_ts = {ts: idx for idx, ts in enumerate(frame["_ts_et"])}
        inv4_by_key = self._events_by_session_bias(inversions_4h)
        inv1_by_key = self._events_by_session_bias(inversions_1h)
        ltf_by_key = self._ltf_by_session_bias(ltf_events)
        bars15_by_session = {session: day.reset_index(drop=True) for session, day in bars_15m.groupby("session", sort=True)}
        swings15_by_session: dict[object, list[SwingPoint]] = {}
        for swing in swings_15m:
            swings15_by_session.setdefault(swing.session, []).append(swing)

        trades: list[Trade] = []
        for session in sessions:
            day = frame[frame["_session"] == session]
            if day.empty:
                continue
            sweeps = self._detect_sweeps(day, pools_by_session.get(session, {"high": [], "low": []}))
            daily_losses = 0
            entered = False
            for sweep in sweeps:
                if entered or daily_losses >= 2:
                    break
                if pd.Timestamp(sweep.ts).time() < ENTRY_START:
                    continue
                timeframe = "4H" if self._has_4h_fvg(fvgs_4h, sweep.ts, session, session_ord) else "1H"
                inversion = self._first_inversion(
                    (inv4_by_key if timeframe == "4H" else inv1_by_key).get((session, sweep.bias), []),
                    sweep.ts,
                )
                if inversion is None:
                    continue
                if inversion.displacement_points < HTF_DISPLACEMENT_MIN_POINTS:
                    continue
                retrace = self._first_retracement(bars15_by_session.get(session), inversion)
                if retrace is None:
                    continue
                trade = self._first_entry_trade(
                    frame,
                    idx_by_ts,
                    ltf_by_key.get((session, sweep.bias), []),
                    swings15_by_session.get(session, []),
                    pools_by_session.get(session, {"high": [], "low": [], "major_high": [], "major_low": []}),
                    sweep,
                    inversion,
                    retrace,
                )
                if trade is None:
                    continue
                trades.append(trade)
                self._mark_trade_arrays(frame, pnl, pos, trade)
                if trade.pnl < 0:
                    daily_losses += 1
                entered = True

        return BacktestResult(frame, pnl, pos, market, trades)

    @staticmethod
    def _events_by_session_bias(events: list[InversionEvent]) -> dict[tuple[object, int], list[InversionEvent]]:
        out: dict[tuple[object, int], list[InversionEvent]] = {}
        for event in events:
            out.setdefault((event.session, event.bias), []).append(event)
        for values in out.values():
            values.sort(key=lambda item: item.ts)
        return out

    @staticmethod
    def _ltf_by_session_bias(events: list[LTFEvent]) -> dict[tuple[object, int], list[LTFEvent]]:
        out: dict[tuple[object, int], list[LTFEvent]] = {}
        for event in events:
            out.setdefault((event.session, event.bias), []).append(event)
        for values in out.values():
            values.sort(key=lambda item: item.inverted_ts)
        return out

    def _prepare_frame(self, df) -> pd.DataFrame:
        raw = pd.DataFrame(df).copy()
        required = {"open", "high", "low", "close", "volume"}
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
        raw["_et_day"] = raw["_session"]
        for col in ("open", "high", "low", "close", "volume"):
            raw[col] = raw[col].astype(float)
            if not np.isfinite(raw[col]).all():
                raise ValueError(f"{col} contains non-finite values")

        daily = raw.groupby("_et_day", sort=True).agg(day_high=("high", "max"), day_low=("low", "min"))
        daily["prior_day_high"] = daily["day_high"].shift(1)
        daily["prior_day_low"] = daily["day_low"].shift(1)
        raw["prior_day_high"] = raw["_et_day"].map(daily["prior_day_high"])
        raw["prior_day_low"] = raw["_et_day"].map(daily["prior_day_low"])

        rth_mask = (
            (raw["_ts_et"].dt.weekday < 5)
            & (raw["_time"] >= RTH_OPEN)
            & (raw["_time"] <= SESSION_CLOSE)
        )
        frame = raw.loc[rth_mask].copy()
        frame = frame.sort_values("_ts_et").reset_index(drop=True)
        if frame.empty:
            return frame

        rth_daily = frame.groupby("_session", sort=True).agg(rth_high=("high", "max"), rth_low=("low", "min"))
        rth_daily["prior_rth_high"] = rth_daily["rth_high"].shift(1)
        rth_daily["prior_rth_low"] = rth_daily["rth_low"].shift(1)
        rth_daily["rolling20_high"] = rth_daily["rth_high"].shift(1).rolling(
            FVG_LOOKBACK_SESSIONS, min_periods=FVG_LOOKBACK_SESSIONS
        ).max()
        rth_daily["rolling20_low"] = rth_daily["rth_low"].shift(1).rolling(
            FVG_LOOKBACK_SESSIONS, min_periods=FVG_LOOKBACK_SESSIONS
        ).min()
        for col in ("prior_rth_high", "prior_rth_low", "rolling20_high", "rolling20_low"):
            frame[col] = frame["_session"].map(rth_daily[col])
        return frame

    def _build_session_pools(self, frame: pd.DataFrame, session_ord: dict[object, int]) -> dict[object, dict[str, list[Pool]]]:
        swings = self._build_swings(frame)
        out: dict[object, dict[str, list[Pool]]] = {}
        for session, day in frame.groupby("_session", sort=True):
            first = day.iloc[0]
            high_pools = self._fixed_pools(first, "high")
            low_pools = self._fixed_pools(first, "low")
            eq_high, major_high = self._equal_pools(swings, session, session_ord, "high")
            eq_low, major_low = self._equal_pools(swings, session, session_ord, "low")
            high_pools.extend(eq_high)
            low_pools.extend(eq_low)
            major_high = [*major_high, *self._major_fixed_pools(first, "high")]
            major_low = [*major_low, *self._major_fixed_pools(first, "low")]
            out[session] = {
                "high": self._dedupe_pools(high_pools),
                "low": self._dedupe_pools(low_pools),
                "major_high": self._dedupe_pools(major_high),
                "major_low": self._dedupe_pools(major_low),
            }
        return out

    def _fixed_pools(self, row: pd.Series, side: str) -> list[Pool]:
        if side == "high":
            specs = [
                ("prior_rth_high", "prior_rth_high"),
                ("prior_day_high", "prior_day_high"),
                ("rolling20_high", "rolling20_high"),
            ]
        else:
            specs = [
                ("prior_rth_low", "prior_rth_low"),
                ("prior_day_low", "prior_day_low"),
                ("rolling20_low", "rolling20_low"),
            ]
        pools: list[Pool] = []
        for col, kind in specs:
            value = float(row[col])
            if np.isfinite(value):
                pools.append(Pool(value, kind, 1))
        return pools

    def _major_fixed_pools(self, row: pd.Series, side: str) -> list[Pool]:
        col = "rolling20_high" if side == "high" else "rolling20_low"
        value = float(row[col])
        return [Pool(value, col, 1)] if np.isfinite(value) else []

    def _equal_pools(
        self,
        swings: list[SwingPoint],
        session: object,
        session_ord: dict[object, int],
        kind: str,
    ) -> tuple[list[Pool], list[Pool]]:
        current_ord = session_ord.get(session)
        if current_ord is None:
            return [], []
        values = [
            swing.price
            for swing in swings
            if swing.kind == kind
            and swing.session in session_ord
            and 1 <= current_ord - session_ord[swing.session] <= FVG_LOOKBACK_SESSIONS
        ]
        clusters = self._cluster_equal_levels(values)
        pools: list[Pool] = []
        majors: list[Pool] = []
        for cluster in clusters:
            if kind == "high":
                level = max(cluster)
                pool_kind = "equal_high"
                major_kind = "stacked_equal_high"
            else:
                level = min(cluster)
                pool_kind = "equal_low"
                major_kind = "stacked_equal_low"
            pool = Pool(float(level), pool_kind, len(cluster))
            pools.append(pool)
            if len(cluster) >= 3:
                majors.append(Pool(float(level), major_kind, len(cluster)))
        return pools, majors

    @staticmethod
    def _cluster_equal_levels(values: list[float]) -> list[list[float]]:
        if len(values) < 2:
            return []
        clusters: list[list[float]] = []
        current: list[float] = []
        for value in sorted(float(x) for x in values if np.isfinite(x) and x > 0):
            if not current:
                current = [value]
                continue
            anchor = float(np.mean(current))
            if abs(value - anchor) / anchor <= EQUAL_TOLERANCE:
                current.append(value)
            else:
                if len(current) >= 2:
                    clusters.append(current)
                current = [value]
        if len(current) >= 2:
            clusters.append(current)
        return clusters

    @staticmethod
    def _dedupe_pools(pools: list[Pool]) -> list[Pool]:
        out: list[Pool] = []
        seen: set[tuple[str, int]] = set()
        for pool in pools:
            if not np.isfinite(pool.level):
                continue
            key = (pool.kind, int(round(pool.level / TICK_SIZE)))
            if key in seen:
                continue
            seen.add(key)
            out.append(pool)
        return out

    @staticmethod
    def _resample_bars(frame: pd.DataFrame, freq: str) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame()
        bars = (
            frame.set_index("_ts_et")
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
        bars["ts"] = bars.index
        bars["_time"] = bars.index.time
        return bars.reset_index(drop=True)

    def _detect_fvgs(self, bars: pd.DataFrame, timeframe: str) -> dict[int, list[FVG]]:
        by_idx: dict[int, list[FVG]] = {}
        if len(bars) < 3:
            return by_idx
        next_id = 0
        for i in range(2, len(bars)):
            c1 = bars.iloc[i - 2]
            c3 = bars.iloc[i]
            if float(c1["high"]) < float(c3["low"]):
                by_idx.setdefault(i, []).append(
                    FVG(
                        idx=next_id,
                        timeframe=timeframe,
                        formed_ts=c3["ts"],
                        session=c3["session"],
                        direction=1,
                        zone_low=float(c1["high"]),
                        zone_high=float(c3["low"]),
                    )
                )
                next_id += 1
            if float(c1["low"]) > float(c3["high"]):
                by_idx.setdefault(i, []).append(
                    FVG(
                        idx=next_id,
                        timeframe=timeframe,
                        formed_ts=c3["ts"],
                        session=c3["session"],
                        direction=-1,
                        zone_low=float(c3["high"]),
                        zone_high=float(c1["low"]),
                    )
                )
                next_id += 1
        return by_idx

    def _build_inversion_events(
        self,
        bars: pd.DataFrame,
        timeframe: str,
        session_ord: dict[object, int],
    ) -> tuple[list[FVG], list[InversionEvent]]:
        fvgs_by_idx = self._detect_fvgs(bars, timeframe)
        active: list[FVG] = []
        all_fvgs: list[FVG] = []
        inverted: set[int] = set()
        events: list[InversionEvent] = []
        for i, row in bars.iterrows():
            current_session = row["session"]
            current_ord = session_ord.get(current_session)
            close = float(row["close"])
            if current_ord is not None:
                active = [
                    fvg
                    for fvg in active
                    if fvg.idx not in inverted
                    and fvg.session in session_ord
                    and 0 <= current_ord - session_ord[fvg.session] <= FVG_LOOKBACK_SESSIONS
                ]
                matched: list[FVG] = []
                for fvg in active:
                    if fvg.direction == 1 and close < fvg.zone_low:
                        matched.append(fvg)
                    elif fvg.direction == -1 and close > fvg.zone_high:
                        matched.append(fvg)
                for fvg in matched:
                    inverted.add(fvg.idx)
                for bias in (-1, 1):
                    same_bias = [fvg for fvg in matched if -fvg.direction == bias]
                    if not same_bias:
                        continue
                    fvg = max(same_bias, key=lambda item: item.formed_ts)
                    events.append(
                        InversionEvent(
                            ts=row["ts"],
                            session=current_session,
                            bias=bias,
                            timeframe=timeframe,
                            zone_low=fvg.zone_low,
                            zone_high=fvg.zone_high,
                            fvg_direction=fvg.direction,
                            fvg_formed_ts=fvg.formed_ts,
                            close=close,
                            displacement_points=abs(close - float(row["open"])),
                        )
                    )
            for fvg in fvgs_by_idx.get(i, []):
                active.append(fvg)
                all_fvgs.append(fvg)
        return all_fvgs, events

    def _build_ltf_events(self, bars_5m: pd.DataFrame) -> list[LTFEvent]:
        _, events = self._build_inversion_events(bars_5m, "5M", self._session_ord_from_bars(bars_5m))
        out: list[LTFEvent] = []
        fvg_by_key: dict[tuple[pd.Timestamp, int, float, float], tuple[float, float]] = {}
        fvgs_by_idx = self._detect_fvgs(bars_5m, "5M")
        for idx, fvgs in fvgs_by_idx.items():
            c3 = bars_5m.iloc[idx]
            for fvg in fvgs:
                fvg_by_key[(fvg.formed_ts, -fvg.direction, fvg.zone_low, fvg.zone_high)] = (
                    float(c3["low"]),
                    float(c3["high"]),
                )
        for event in events:
            key = (event.fvg_formed_ts, event.bias, event.zone_low, event.zone_high)
            formation_low, formation_high = fvg_by_key.get(key, (event.zone_low, event.zone_high))
            out.append(
                LTFEvent(
                    formed_ts=event.fvg_formed_ts,
                    inverted_ts=event.ts,
                    session=event.session,
                    bias=event.bias,
                    zone_low=event.zone_low,
                    zone_high=event.zone_high,
                    formation_low=formation_low,
                    formation_high=formation_high,
                    close=event.close,
                )
            )
        return sorted(out, key=lambda item: item.inverted_ts)

    @staticmethod
    def _session_ord_from_bars(bars: pd.DataFrame) -> dict[object, int]:
        sessions = list(pd.Series(bars["session"]).dropna().drop_duplicates()) if not bars.empty else []
        return {session: idx for idx, session in enumerate(sessions)}

    @staticmethod
    def _build_swings(bars: pd.DataFrame) -> list[SwingPoint]:
        swings: list[SwingPoint] = []
        if len(bars) < 3:
            return swings
        for i in range(1, len(bars) - 1):
            prev_row = bars.iloc[i - 1]
            row = bars.iloc[i]
            next_row = bars.iloc[i + 1]
            if float(row["high"]) > float(prev_row["high"]) and float(row["high"]) >= float(next_row["high"]):
                swings.append(
                    SwingPoint(
                        ts=row.get("ts", row.get("_ts_et")),
                        confirmed_ts=next_row.get("ts", next_row.get("_ts_et")),
                        session=row.get("session", row.get("_session")),
                        kind="high",
                        price=float(row["high"]),
                    )
                )
            if float(row["low"]) < float(prev_row["low"]) and float(row["low"]) <= float(next_row["low"]):
                swings.append(
                    SwingPoint(
                        ts=row.get("ts", row.get("_ts_et")),
                        confirmed_ts=next_row.get("ts", next_row.get("_ts_et")),
                        session=row.get("session", row.get("_session")),
                        kind="low",
                        price=float(row["low"]),
                    )
                )
        return swings

    def _detect_sweeps(self, day: pd.DataFrame, pools: dict[str, list[Pool]]) -> list[SweepEvent]:
        events: list[SweepEvent] = []
        pending: list[dict[str, object]] = []
        for local_i, (_, row) in enumerate(day.iterrows()):
            ts = row["_ts_et"]
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])
            for pool in pools.get("high", []):
                if high > pool.level:
                    pending.append({"expires": local_i + 3, "pool": pool, "bias": -1})
            for pool in pools.get("low", []):
                if low < pool.level:
                    pending.append({"expires": local_i + 3, "pool": pool, "bias": 1})

            remaining: list[dict[str, object]] = []
            for item in pending:
                pool = item["pool"]
                bias = int(item["bias"])
                if local_i > int(item["expires"]):
                    continue
                closed_inside = close < pool.level if bias < 0 else close > pool.level
                if closed_inside:
                    events.append(
                        SweepEvent(
                            ts=ts,
                            session=row["_session"],
                            bias=bias,
                            level=float(pool.level),
                            pool_kind=pool.kind,
                        )
                    )
                else:
                    remaining.append(item)
            pending = remaining
        events.sort(key=lambda item: item.ts)
        return events

    @staticmethod
    def _has_4h_fvg(
        fvgs: list[FVG],
        ts: pd.Timestamp,
        session: object,
        session_ord: dict[object, int],
    ) -> bool:
        current_ord = session_ord.get(session)
        if current_ord is None:
            return False
        for fvg in fvgs:
            if fvg.formed_ts >= ts:
                continue
            if fvg.session not in session_ord:
                continue
            if 0 <= current_ord - session_ord[fvg.session] <= FVG_LOOKBACK_SESSIONS:
                return True
        return False

    @staticmethod
    def _first_inversion(
        inversions: list[InversionEvent],
        after_ts: pd.Timestamp,
    ) -> InversionEvent | None:
        matches = [
            event
            for event in inversions
            if event.ts > after_ts and event.ts.time() <= SESSION_CLOSE
        ]
        return min(matches, key=lambda item: item.ts) if matches else None

    @staticmethod
    def _first_retracement(
        bars_15m: pd.DataFrame | None,
        inversion: InversionEvent,
    ) -> pd.Series | None:
        if bars_15m is None or bars_15m.empty:
            return None
        candidates = bars_15m[
            (bars_15m["ts"] > inversion.ts)
            & (bars_15m["_time"] <= SESSION_CLOSE)
        ]
        for _, row in candidates.iterrows():
            if ranges_overlap(float(row["low"]), float(row["high"]), inversion.zone_low, inversion.zone_high):
                return row
        return None

    def _first_entry_trade(
        self,
        frame: pd.DataFrame,
        idx_by_ts: dict[pd.Timestamp, int],
        ltf_events: list[LTFEvent],
        swings_15m: list[SwingPoint],
        pools: dict[str, list[Pool]],
        sweep: SweepEvent,
        inversion: InversionEvent,
        retrace: pd.Series,
    ) -> Trade | None:
        for event in ltf_events:
            if event.formed_ts < retrace["ts"] or event.inverted_ts <= retrace["ts"]:
                continue
            if event.inverted_ts.time() < ENTRY_START or event.inverted_ts.time() > SESSION_CLOSE:
                continue
            if not ranges_overlap(event.formation_low, event.formation_high, inversion.zone_low, inversion.zone_high):
                continue
            if event.inverted_ts not in idx_by_ts:
                continue
            entry_i = idx_by_ts[event.inverted_ts]
            stop = self._stop_from_recent_swing(swings_15m, event.bias, inversion.ts, event.inverted_ts, sweep.session)
            if stop is None:
                continue
            signal_close = float(event.close)
            entry = self._entry_price(event.bias, signal_close)
            stop_ticks = abs(entry - stop) / TICK_SIZE
            contracts = self._allowed_contracts(stop_ticks)
            if contracts <= 0:
                continue
            risk_dollars = contracts * abs(entry - stop) * self.point_value
            if risk_dollars <= 0 or risk_dollars > DAILY_BUFFER + 1e-9:
                continue
            targets = self._targets(entry, stop, event.bias, pools)
            if targets is None:
                continue
            tp1, tp1_pool, runner_target, runner_pool = targets
            return self._simulate_trade(
                frame,
                entry_i,
                event.bias,
                entry,
                stop,
                tp1,
                runner_target,
                contracts,
                risk_dollars,
                inversion.timeframe,
                sweep.pool_kind,
                tp1_pool,
                runner_pool,
            )
        return None

    @staticmethod
    def _stop_from_recent_swing(
        swings: list[SwingPoint],
        bias: int,
        after_ts: pd.Timestamp,
        entry_ts: pd.Timestamp,
        session: object,
    ) -> float | None:
        wanted = "low" if bias > 0 else "high"
        candidates = [
            swing
            for swing in swings
            if swing.session == session
            and swing.kind == wanted
            and swing.confirmed_ts <= entry_ts
            and swing.ts >= after_ts
        ]
        if not candidates:
            return None
        swing = max(candidates, key=lambda item: item.ts)
        return swing.price - TICK_SIZE if bias > 0 else swing.price + TICK_SIZE

    def _targets(
        self,
        entry: float,
        stop: float,
        side: int,
        pools: dict[str, list[Pool]],
    ) -> tuple[float, str, float | None, str] | None:
        risk_points = abs(entry - stop)
        if risk_points <= 0:
            return None
        if side > 0:
            opposing = sorted([pool for pool in pools.get("high", []) if pool.level > entry], key=lambda p: p.level)
            major = sorted([pool for pool in pools.get("major_high", []) if pool.level > entry], key=lambda p: p.level)
        else:
            opposing = sorted([pool for pool in pools.get("low", []) if pool.level < entry], key=lambda p: p.level, reverse=True)
            major = sorted([pool for pool in pools.get("major_low", []) if pool.level < entry], key=lambda p: p.level, reverse=True)
        if not opposing:
            return None
        nearest = opposing[0]
        min_tp1 = entry + side * TP1_MIN_R * risk_points
        if side * (nearest.level - entry) >= TP1_MIN_R * risk_points:
            tp1 = nearest.level
            tp1_pool = nearest.kind
        else:
            tp1 = min_tp1
            tp1_pool = f"{nearest.kind}_promoted_to_1.5R"
        runner_candidates = [pool for pool in major if side * (pool.level - tp1) > 0]
        if runner_candidates:
            runner = runner_candidates[0]
            return float(tp1), tp1_pool, float(runner.level), runner.kind
        return float(tp1), tp1_pool, None, "session_close_or_breakeven"

    def _simulate_trade(
        self,
        frame: pd.DataFrame,
        entry_i: int,
        side: int,
        entry: float,
        stop: float,
        tp1: float,
        runner_target: float | None,
        contracts: int,
        risk_dollars: float,
        htf_timeframe: str,
        sweep_pool: str,
        tp1_pool: str,
        runner_pool: str,
    ) -> Trade:
        session = frame.loc[entry_i, "_session"]
        entry_ts = frame.loc[entry_i, "_ts_et"]
        day_indices = list(frame.index[(frame["_session"] == session) & (frame.index > entry_i)])
        if not day_indices:
            row = frame.loc[entry_i]
            exit_price = float(row["close"]) - side * TICK_SIZE
            return self._closed_trade(
                entry_ts,
                row,
                session,
                side,
                entry,
                exit_price,
                stop,
                tp1,
                runner_target,
                contracts,
                risk_dollars,
                False,
                0.0,
                contracts * side * (exit_price - entry) * self.point_value,
                "session_flatten",
                htf_timeframe,
                sweep_pool,
                tp1_pool,
                runner_pool,
            )

        runner_stop = stop
        tp1_hit = False
        tp1_gross = 0.0
        remaining_fraction = 1.0
        last_row = frame.loc[day_indices[-1]]
        for idx in day_indices:
            row = frame.loc[idx]
            exit_price, reason = self._stop_exit_price(side, runner_stop, row)
            if exit_price is not None:
                gross = remaining_fraction * contracts * side * (exit_price - entry) * self.point_value
                return self._closed_trade(
                    entry_ts,
                    row,
                    session,
                    side,
                    entry,
                    exit_price,
                    stop,
                    tp1,
                    runner_target,
                    contracts,
                    risk_dollars,
                    tp1_hit,
                    tp1_gross,
                    gross,
                    reason if not tp1_hit else f"runner_{reason}",
                    htf_timeframe,
                    sweep_pool,
                    tp1_pool,
                    runner_pool,
                )

            if not tp1_hit and self._target_hit(side, tp1, row):
                tp1_hit = True
                half = 0.5
                tp1_gross = half * contracts * side * (tp1 - entry) * self.point_value
                remaining_fraction = 0.5
                runner_stop = entry
                continue

            if tp1_hit and runner_target is not None and self._target_hit(side, runner_target, row):
                runner_gross = remaining_fraction * contracts * side * (runner_target - entry) * self.point_value
                return self._closed_trade(
                    entry_ts,
                    row,
                    session,
                    side,
                    entry,
                    runner_target,
                    stop,
                    tp1,
                    runner_target,
                    contracts,
                    risk_dollars,
                    tp1_hit,
                    tp1_gross,
                    runner_gross,
                    "runner_target",
                    htf_timeframe,
                    sweep_pool,
                    tp1_pool,
                    runner_pool,
                )

            if row["_time"] >= SESSION_CLOSE:
                break

        exit_price = float(last_row["close"]) - side * TICK_SIZE
        runner_gross = remaining_fraction * contracts * side * (exit_price - entry) * self.point_value
        return self._closed_trade(
            entry_ts,
            last_row,
            session,
            side,
            entry,
            exit_price,
            stop,
            tp1,
            runner_target,
            contracts,
            risk_dollars,
            tp1_hit,
            tp1_gross,
            runner_gross,
            "session_flatten" if not tp1_hit else "runner_session_flatten",
            htf_timeframe,
            sweep_pool,
            tp1_pool,
            runner_pool,
        )

    def _closed_trade(
        self,
        entry_ts: pd.Timestamp,
        row: pd.Series,
        session: object,
        side: int,
        entry: float,
        exit_price: float,
        stop: float,
        tp1: float,
        runner_target: float | None,
        contracts: int,
        risk_dollars: float,
        tp1_hit: bool,
        tp1_gross: float,
        runner_gross: float,
        reason: str,
        htf_timeframe: str,
        sweep_pool: str,
        tp1_pool: str,
        runner_pool: str,
    ) -> Trade:
        if not tp1_hit:
            gross = runner_gross
            tp1_gross = 0.0
        else:
            gross = tp1_gross + runner_gross
        pnl = gross - contracts * self.commission_rt
        return Trade(
            entry_ts=entry_ts,
            exit_ts=row["_ts_et"],
            session=session,
            side=side,
            entry_price=float(entry),
            exit_price=float(exit_price),
            stop_price=float(stop),
            tp1_price=float(tp1),
            runner_target_price=None if runner_target is None else float(runner_target),
            contracts=int(contracts),
            risk_dollars=float(risk_dollars),
            pnl=float(pnl),
            gross_pnl=float(gross),
            tp1_hit=bool(tp1_hit),
            tp1_gross_pnl=float(tp1_gross),
            runner_gross_pnl=float(runner_gross),
            reason=reason,
            htf_timeframe=htf_timeframe,
            sweep_pool=sweep_pool,
            tp1_pool=tp1_pool,
            runner_pool=runner_pool,
            r_mult=float(pnl / risk_dollars) if risk_dollars > 0 else 0.0,
        )

    def _mark_trade_arrays(self, frame: pd.DataFrame, pnl: np.ndarray, pos: np.ndarray, trade: Trade) -> None:
        entry_mask = frame["_ts_et"] == trade.entry_ts
        exit_mask = frame["_ts_et"] == trade.exit_ts
        if not entry_mask.any() or not exit_mask.any():
            return
        entry_i = int(np.flatnonzero(entry_mask.to_numpy())[0])
        exit_i = int(np.flatnonzero(exit_mask.to_numpy())[0])
        if exit_i >= entry_i:
            pos[entry_i : exit_i + 1] = trade.side * trade.contracts
            pnl[exit_i] += trade.pnl

    def _allowed_contracts(self, stop_ticks: float) -> int:
        engine = PropRiskEngine(config=PropRiskConfig(daily_buffer=DAILY_BUFFER))
        allowed = engine.allowed_size(self.tick_value, stop_ticks)
        return min(int(allowed), self.max_contracts)

    @staticmethod
    def _entry_price(side: int, close: float) -> float:
        return float(close + side * TICK_SIZE)

    @staticmethod
    def _stop_exit_price(side: int, stop: float, row: pd.Series) -> tuple[float | None, str]:
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

    @staticmethod
    def _target_hit(side: int, target: float, row: pd.Series) -> bool:
        if side > 0:
            return float(row["high"]) >= target
        return float(row["low"]) <= target


def ranges_overlap(low_a: float, high_a: float, low_b: float, high_b: float) -> bool:
    return max(float(low_a), float(low_b)) <= min(float(high_a), float(high_b))


__all__ = [
    "InversionModel",
    "Trade",
    "Pool",
    "FVG",
    "InversionEvent",
    "LTFEvent",
    "SweepEvent",
    "SwingPoint",
]
