"""Dhesi inversion model v3, frozen in DHESI_V3_PREREGISTRATION.md.

v2 (``inversion_model.InversionModel``) is left unchanged. Each v3 fix has a
switch so ablations can attribute any change; the pre-registered v3 result is
the configuration with every switch on.
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

from core.alpha.inversion_model import (
    EASTERN,
    ENTRY_START,
    SESSION_CLOSE,
    HTF_DISPLACEMENT_MIN_POINTS,
    BacktestResult,
    InversionModel,
    Pool,
    SweepEvent,
    Trade,
    ranges_overlap,
)


MAX_ATTEMPTS = 3
MAX_LOSSES = 2
MIN_STOP_POINTS = 10.0
HTF_ANCHOR_HOUR = 18
ASIA_WINDOW = (time(20, 0), time(23, 59))
LONDON_WINDOW = (time(2, 0), time(4, 59))


class InversionModelV3(InversionModel):
    """v2 plus the six pre-registered fidelity/bug fixes."""

    def __init__(
        self,
        *,
        contract: str = "MNQ",
        htf_24h: bool = True,
        early_sweeps: bool = True,
        session_pools: bool = True,
        stop_guard: bool = True,
        attempts: bool = True,
    ):
        super().__init__(contract=contract)
        self.htf_24h = htf_24h
        self.early_sweeps = early_sweeps
        self.session_pools = session_pools
        self.stop_guard = stop_guard
        self.attempts = attempts

    @property
    def name(self) -> str:
        return "inversion_model_v3"

    # ------------------------------------------------------------------ data
    @staticmethod
    def _full_frame(df) -> pd.DataFrame:
        raw = pd.DataFrame(df)[["open", "high", "low", "close", "volume"]].astype(float).copy()
        idx = pd.DatetimeIndex(raw.index)
        idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
        raw["_ts_et"] = idx.tz_convert(EASTERN)
        return raw.sort_values("_ts_et").reset_index(drop=True)

    @staticmethod
    def _htf_bars_24h(full: pd.DataFrame, hours: int) -> pd.DataFrame:
        """Futures-clock bins anchored at 18:00 ET, labelled by bin end."""
        wall = full["_ts_et"].dt.tz_localize(None)
        shifted = wall - pd.Timedelta(hours=HTF_ANCHOR_HOUR)
        start = shifted.dt.normalize() + pd.to_timedelta((shifted.dt.hour // hours) * hours, unit="h")
        start = start + pd.Timedelta(hours=HTF_ANCHOR_HOUR)
        grouped = full.assign(_bin=start).groupby("_bin", sort=True).agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        end_wall = grouped.index + pd.Timedelta(hours=hours)
        bars = grouped.reset_index(drop=True)
        bars["ts"] = pd.DatetimeIndex(end_wall).tz_localize(EASTERN, ambiguous=True, nonexistent="shift_forward")
        bars["session"] = [
            (value - pd.Timedelta(minutes=1) + pd.Timedelta(hours=6)).date() for value in end_wall
        ]
        bars["_time"] = bars["ts"].dt.time
        return bars

    @staticmethod
    def _window_extremes(full: pd.DataFrame, window: tuple[time, time], day_offset: int) -> pd.DataFrame:
        times = full["_ts_et"].dt.time
        inside = full.loc[(times >= window[0]) & (times <= window[1])]
        key = (inside["_ts_et"].dt.tz_localize(None).dt.normalize() + pd.Timedelta(days=day_offset)).dt.date
        return inside.groupby(key).agg(hi=("high", "max"), lo=("low", "min"))

    def _add_session_pools(self, pools_by_session: dict, full: pd.DataFrame) -> None:
        asia = self._window_extremes(full, ASIA_WINDOW, day_offset=1)
        london = self._window_extremes(full, LONDON_WINDOW, day_offset=0)
        for session, pools in pools_by_session.items():
            for table, name in ((asia, "asia"), (london, "london")):
                if session in table.index:
                    row = table.loc[session]
                    pools["high"] = self._dedupe_pools([*pools["high"], Pool(float(row["hi"]), f"{name}_high", 1)])
                    pools["low"] = self._dedupe_pools([*pools["low"], Pool(float(row["lo"]), f"{name}_low", 1)])

    # -------------------------------------------------------------- backtest
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
        full = self._full_frame(df) if (self.htf_24h or self.session_pools) else None
        if self.session_pools:
            self._add_session_pools(pools_by_session, full)
        if self.htf_24h:
            htf_4h = self._htf_bars_24h(full, 4)
            htf_1h = self._htf_bars_24h(full, 1)
        else:
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
        swings15_by_session: dict[object, list] = {}
        for swing in swings_15m:
            swings15_by_session.setdefault(swing.session, []).append(swing)

        max_attempts = MAX_ATTEMPTS if self.attempts else 1
        trades: list[Trade] = []
        for session in sessions:
            day = frame[frame["_session"] == session]
            if day.empty:
                continue
            sweeps = self._detect_sweeps(day, pools_by_session.get(session, {"high": [], "low": []}))
            taken = 0
            losses = 0
            last_exit: pd.Timestamp | None = None
            for sweep in sweeps:
                if taken >= max_attempts or losses >= MAX_LOSSES:
                    break
                if not self.early_sweeps and pd.Timestamp(sweep.ts).time() < ENTRY_START:
                    continue
                if last_exit is not None and sweep.ts < last_exit:
                    continue
                timeframe = "4H" if self._has_4h_fvg(fvgs_4h, sweep.ts, session, session_ord) else "1H"
                inversion = self._first_inversion(
                    (inv4_by_key if timeframe == "4H" else inv1_by_key).get((session, sweep.bias), []),
                    sweep.ts,
                )
                if inversion is None or inversion.displacement_points < HTF_DISPLACEMENT_MIN_POINTS:
                    continue
                retrace = self._first_retracement(bars15_by_session.get(session), inversion)
                if retrace is None:
                    continue
                trade = self._first_entry_trade_v3(
                    frame,
                    idx_by_ts,
                    ltf_by_key.get((session, sweep.bias), []),
                    swings15_by_session.get(session, []),
                    pools_by_session.get(session, {"high": [], "low": [], "major_high": [], "major_low": []}),
                    sweep,
                    inversion,
                    retrace,
                    last_exit,
                )
                if trade is None:
                    continue
                trades.append(trade)
                self._mark_trade_arrays(frame, pnl, pos, trade)
                taken += 1
                if trade.pnl < 0:
                    losses += 1
                last_exit = trade.exit_ts
        return BacktestResult(frame, pnl, pos, market, trades)

    def _first_entry_trade_v3(
        self,
        frame: pd.DataFrame,
        idx_by_ts: dict,
        ltf_events: list,
        swings_15m: list,
        pools: dict,
        sweep: SweepEvent,
        inversion,
        retrace: pd.Series,
        not_before: pd.Timestamp | None,
    ) -> Trade | None:
        for event in ltf_events:
            if event.formed_ts < retrace["ts"] or event.inverted_ts <= retrace["ts"]:
                continue
            if not_before is not None and event.inverted_ts <= not_before:
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
            entry = self._entry_price(event.bias, float(event.close))
            if self.stop_guard and event.bias * (entry - stop) < MIN_STOP_POINTS:
                continue
            stop_ticks = abs(entry - stop) / 0.25
            contracts = self._allowed_contracts(stop_ticks)
            if contracts <= 0:
                continue
            risk_dollars = contracts * abs(entry - stop) * self.point_value
            if risk_dollars <= 0 or risk_dollars > 325.0 + 1e-9:
                continue
            targets = self._targets(entry, stop, event.bias, pools)
            if targets is None:
                continue
            tp1, tp1_pool, runner_target, runner_pool = targets
            return self._simulate_trade(
                frame, entry_i, event.bias, entry, stop, tp1, runner_target, contracts, risk_dollars,
                inversion.timeframe, sweep.pool_kind, tp1_pool, runner_pool,
            )
        return None
