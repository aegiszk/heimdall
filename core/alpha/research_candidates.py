"""Pre-registered LuxAlgo and YouTube research candidates.

These models are offline-only. They reproduce source signals, add the fixed
execution wrappers documented in the matching pre-registration files, and do
not place orders.
"""

from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

from core.alpha.prop_futures import EntryPlan, FuturesRTHModel, TICK_SIZE


RTH_START = time(9, 30)
RTH_END = time(16, 0)


def _with_vwap(df: pd.DataFrame) -> pd.DataFrame:
    frame = pd.DataFrame(df).copy()
    if "vwap" not in frame.columns and "close" in frame.columns:
        frame["vwap"] = frame["close"]
    return frame


def _rth_only(frame: pd.DataFrame) -> pd.DataFrame:
    mask = frame["_time"].map(lambda value: RTH_START <= value < RTH_END)
    return frame.loc[mask].reset_index(drop=True)


def _pine_proxy_poc(group: pd.DataFrame) -> float:
    """Replay LuxAlgo's running volume-at-sub-bar-close POC tie behavior."""
    volume_at_price: dict[float, float] = {}
    max_volume = -1.0
    poc = np.nan
    for row in group.itertuples(index=False):
        price = float(row.close)
        new_volume = volume_at_price.get(price, 0.0) + float(row.volume)
        volume_at_price[price] = new_volume
        if new_volume > max_volume:
            max_volume = new_volume
            poc = price
    return float(poc)


class PocSweepReclaimModel(FuturesRTHModel):
    """LuxAlgo POC Sweep Reclaim signal with Heimdall's frozen 1R wrapper."""

    strategy_params = ("parent_minutes=5", "target_r=1", "max_trades_day=1")
    entry_start = time(9, 40)
    entry_end = time(15, 30)
    flatten_time = time(15, 55)

    def __init__(self, contract: str = "MNQ"):
        super().__init__(contract)

    @property
    def name(self) -> str:
        return "luxalgo_poc_sweep_reclaim"

    def _max_trades_day(self) -> int:
        return 1

    def _prepare_frame(self, df) -> pd.DataFrame:
        minute = super()._prepare_frame(_with_vwap(df))
        minute = _rth_only(minute)
        minute["_bucket"] = minute["_ts"].dt.floor("5min")

        rows: list[dict[str, object]] = []
        for (session, bucket), group in minute.groupby(["_session", "_bucket"], sort=True):
            rows.append(
                {
                    "ts": bucket,
                    "open": float(group.iloc[0]["open"]),
                    "high": float(group["high"].max()),
                    "low": float(group["low"].min()),
                    "close": float(group.iloc[-1]["close"]),
                    "volume": float(group["volume"].sum()),
                    "vwap": float(np.average(group["close"], weights=group["volume"]))
                    if float(group["volume"].sum()) > 0
                    else float(group.iloc[-1]["close"]),
                    "poc": _pine_proxy_poc(group[["close", "volume"]]),
                    "session": session,
                }
            )

        parent = super()._prepare_frame(pd.DataFrame(rows))
        grouped = parent.groupby("_session", sort=False)
        parent["_poc_1"] = grouped["poc"].shift(1)
        parent["_poc_2"] = grouped["poc"].shift(2)
        body_high = parent[["open", "close"]].max(axis=1)
        body_low = parent[["open", "close"]].min(axis=1)
        parent["_buyside_sweep"] = (parent["high"] > parent["_poc_1"]) & (
            body_high < parent["_poc_1"]
        )
        parent["_sellside_sweep"] = (parent["low"] < parent["_poc_1"]) & (
            body_low > parent["_poc_1"]
        )
        parent["_long_signal"] = grouped["_buyside_sweep"].shift(1).fillna(False).astype(bool) & (
            parent["close"] > parent["_poc_2"]
        )
        parent["_short_signal"] = grouped["_sellside_sweep"].shift(1).fillna(False).astype(bool) & (
            parent["close"] < parent["_poc_2"]
        )
        return parent

    def _entry_plan(self, frame: pd.DataFrame, i: int) -> EntryPlan | None:
        row = frame.loc[i]
        long_signal = bool(row["_long_signal"])
        short_signal = bool(row["_short_signal"])
        if long_signal == short_signal:
            return None
        side = 1 if long_signal else -1
        swept_level = float(row["_poc_2"])
        stop = swept_level - side * TICK_SIZE
        entry = float(row["close"]) + side * TICK_SIZE
        risk = side * (entry - stop)
        if not np.isfinite(risk) or risk <= 0:
            return None
        return EntryPlan(side=side, stop_price=stop, target_price=entry + side * risk)


class OpeningFvgScalpModel(FuturesRTHModel):
    """Casper opening-range FVG scalp with frozen mechanical interpretations."""

    strategy_params = ("opening_range_minutes=5", "target_r=3", "max_trades_day=1")
    entry_start = time(9, 35)
    entry_end = time(11, 0)
    flatten_time = time(15, 55)

    def __init__(self, contract: str = "MNQ"):
        super().__init__(contract)

    @property
    def name(self) -> str:
        return "youtube_opening_fvg_scalp"

    def _max_trades_day(self) -> int:
        return 1

    def _prepare_frame(self, df) -> pd.DataFrame:
        frame = super()._prepare_frame(_with_vwap(df))
        frame = _rth_only(frame)
        frame["_signal_side"] = 0
        frame["_signal_stop"] = np.nan

        for _, session in frame.groupby("_session", sort=True):
            indices = list(session.index)
            opening = session[(session["_time"] >= time(9, 30)) & (session["_time"] < time(9, 35))]
            if len(opening) != 5:
                continue
            opening_high = float(opening["high"].max())
            opening_low = float(opening["low"].min())
            fvg: tuple[int, float, float] | None = None
            retest_i: int | None = None

            for position, i in enumerate(indices):
                row = frame.loc[i]
                if row["_time"] < self.entry_start or row["_time"] > self.entry_end:
                    continue
                if fvg is None and position >= 2:
                    prior2 = frame.loc[indices[position - 2]]
                    if float(row["low"]) > float(prior2["high"]) and float(row["close"]) > opening_high:
                        fvg = (1, float(prior2["high"]), float(row["low"]))
                        continue
                    if float(row["high"]) < float(prior2["low"]) and float(row["close"]) < opening_low:
                        fvg = (-1, float(row["high"]), float(prior2["low"]))
                        continue
                if fvg is None:
                    continue

                side, gap_low, gap_high = fvg
                if retest_i is None:
                    if float(row["low"]) <= gap_high and float(row["high"]) >= gap_low:
                        retest_i = i
                    continue

                retest = frame.loc[retest_i]
                row_body_high = max(float(row["open"]), float(row["close"]))
                row_body_low = min(float(row["open"]), float(row["close"]))
                retest_body_high = max(float(retest["open"]), float(retest["close"]))
                retest_body_low = min(float(retest["open"]), float(retest["close"]))
                if side > 0:
                    engulf = (
                        float(row["close"]) > float(row["open"])
                        and row_body_high > retest_body_high
                        and row_body_low <= retest_body_low
                    )
                else:
                    engulf = (
                        float(row["close"]) < float(row["open"])
                        and row_body_low < retest_body_low
                        and row_body_high >= retest_body_high
                    )
                if not engulf:
                    continue

                path = frame.loc[retest_i:i]
                stop = (
                    float(path["low"].min()) - TICK_SIZE
                    if side > 0
                    else float(path["high"].max()) + TICK_SIZE
                )
                frame.at[i, "_signal_side"] = side
                frame.at[i, "_signal_stop"] = stop
                break
        return frame

    def _entry_plan(self, frame: pd.DataFrame, i: int) -> EntryPlan | None:
        row = frame.loc[i]
        side = int(row["_signal_side"])
        if side == 0:
            return None
        stop = float(row["_signal_stop"])
        entry = float(row["close"]) + side * TICK_SIZE
        risk = side * (entry - stop)
        if not np.isfinite(risk) or risk <= 0:
            return None
        return EntryPlan(side=side, stop_price=stop, target_price=entry + side * 3.0 * risk)
