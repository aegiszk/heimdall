"""Market intraday momentum, frozen in INTRADAY_MOMENTUM_PREREGISTRATION.md.

Baltussen, Da, Lammers & Martens (JFE 2021): the return from the previous RTH
close to 15:30 ET sets the direction of a 15:30 -> 16:00 trade. No parameters.
One-minute bars are stamped at bar start, so the price at 15:30 is the close of
the 15:29 bar and the price at 16:00 is the close of the 15:59 bar.
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd


EASTERN = "America/New_York"
RTH_START = time(9, 30)
RTH_LAST = time(15, 59)
SIGNAL_BAR = time(15, 29)
EXIT_BAR = time(15, 59)
ONFH_BAR = time(9, 59)

# point_value, tick_size, round-turn commission. M2K/MYM commissions are the
# micro rate assumed by analogy (reported instruments only, never gating).
CONTRACTS = {
    "MNQ": (2.0, 0.25, 1.00),
    "MES": (5.0, 0.25, 1.00),
    "ES": (50.0, 0.25, 3.50),
    "NQ": (20.0, 0.25, 3.50),
    "M2K": (5.0, 0.10, 1.00),
    "MYM": (0.5, 1.00, 1.00),
}


def daily_trades(df: pd.DataFrame, contract: str, slip_ticks: int = 1) -> pd.DataFrame:
    """One row per eligible RTH session with the frozen signal and net PnL."""
    point_value, tick, commission = CONTRACTS[contract]
    idx = pd.DatetimeIndex(df.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    et = idx.tz_convert(EASTERN)
    frame = pd.DataFrame({"close": df["close"].to_numpy(float), "session": et.date, "t": et.time,
                          "weekday": et.weekday})
    frame = frame[(frame["weekday"] < 5) & (frame["t"] >= RTH_START) & (frame["t"] <= RTH_LAST)]

    rows = []
    prev_close = None
    for session, day in frame.groupby("session", sort=True):
        at = dict(zip(day["t"], day["close"]))
        c0 = prev_close
        prev_close = float(day["close"].iloc[-1])
        if c0 is None or SIGNAL_BAR not in at or EXIT_BAR not in at:
            continue
        p1530, p1600 = float(at[SIGNAL_BAR]), float(at[EXIT_BAR])
        r_rod = p1530 / c0 - 1.0
        side = int(np.sign(r_rod))
        cost = 2 * slip_ticks * tick * point_value + commission
        gross = side * (p1600 - p1530) * point_value
        pnl = gross - cost if side else 0.0
        long_pnl = (p1600 - p1530) * point_value - cost
        r_onfh = float(at[ONFH_BAR]) / c0 - 1.0 if ONFH_BAR in at else np.nan
        onfh_side = int(np.sign(r_onfh)) if np.isfinite(r_onfh) else 0
        onfh_pnl = onfh_side * (p1600 - p1530) * point_value - cost if onfh_side else 0.0
        rows.append({"session": session, "c0": c0, "p1530": p1530, "p1600": p1600, "r_rod": r_rod,
                     "side": side, "gross": gross if side else 0.0, "pnl": pnl, "traded": bool(side),
                     "always_long_pnl": long_pnl, "r_onfh": r_onfh, "onfh_pnl": onfh_pnl,
                     "notional": p1530 * point_value})
    return pd.DataFrame(rows)
