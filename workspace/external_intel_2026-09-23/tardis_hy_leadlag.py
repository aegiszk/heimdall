"""Hayashi-Yoshida (Hoffmann-Rosenbaum-Yoshida) lead-lag on asynchronous tick returns.

Why: HL prints ~10x fewer trades than Binance. Forward-filled last-price grids make the sparser series
look late (non-synchronous trading / Epps effect). HY uses each series' own tick intervals, so a lag
that survives HY is not a sampling artifact.

rho(theta) = sum_ij rB_i rH_j 1{(sB_i+theta, eB_i+theta] overlaps (sH_j, eH_j]} / sqrt(sum rB^2 sum rH^2)
theta > 0  =>  Binance leads Hyperliquid by theta.
Computed for trades in EVENT time (exchange timestamp) and RECEIVE time (Tardis local_timestamp).
Input: cached files from tardis_leadlag_all.py.  Output: tardis_hy_results.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "tardis_free"
OUT = Path(__file__).with_name("tardis_hy_results.json")
COINS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
THETAS_MS = np.arange(-1000, 2501, 50)


def tick_returns(df: pd.DataFrame, clock: str):
    """Log returns between consecutive price CHANGES, with (start, end] intervals in microseconds."""
    d = df.sort_values(clock, kind="stable")
    t, p = d[clock].to_numpy(np.int64), d["price"].to_numpy(float)
    keep = np.r_[True, p[1:] != p[:-1]]
    t, p = t[keep], p[keep]
    return t[:-1], t[1:], np.diff(np.log(p))


def hy_curve(b, h) -> dict:
    sb, eb, rb = b
    sh, eh, rh = h
    csum = np.r_[0.0, np.cumsum(rh)]
    denom = np.sqrt(np.sum(rb**2) * np.sum(rh**2))
    out = {}
    for theta in THETAS_MS:
        lo = np.searchsorted(eh, sb + theta * 1000, side="right")   # first H interval ending after start
        hi = np.searchsorted(sh, eb + theta * 1000, side="left")    # H intervals starting before end
        hi = np.maximum(hi, lo)
        out[int(theta)] = float(np.sum(rb * (csum[hi] - csum[lo])) / denom)
    return out


def summarize(curve: dict) -> dict:
    best = max(curve, key=curve.get)
    return {"best_lag_ms": best, "rho_best": round(curve[best], 4), "rho_0": round(curve[0], 4),
            "curve": {k: round(v, 4) for k, v in curve.items()}}


def main() -> None:
    results = {}
    days = sorted(p.name for p in (CACHE / "hyperliquid" / "trades").iterdir())
    for day in days:
        for coin, bsym in COINS.items():
            hp = CACHE / "hyperliquid" / "trades" / day / f"{coin}.csv.gz"
            bp = CACHE / "binance-futures" / "trades" / day / f"{bsym}.csv.gz"
            if not (hp.exists() and bp.exists()):
                continue
            cols = ["timestamp", "local_timestamp", "price"]
            hl, bn = pd.read_csv(hp, usecols=cols), pd.read_csv(bp, usecols=cols)
            r = {"hl_price_changes": None}
            for clock, label in (("timestamp", "event"), ("local_timestamp", "receive")):
                b, h = tick_returns(bn, clock), tick_returns(hl, clock)
                r["hl_price_changes"], r["bn_price_changes"] = int(len(h[2])), int(len(b[2]))
                r[label] = summarize(hy_curve(b, h))
            results[f"{day}|{coin}"] = r
            print(day, coin, "HY event", r["event"]["best_lag_ms"], r["event"]["rho_best"],
                  "| receive", r["receive"]["best_lag_ms"], r["receive"]["rho_best"])
            OUT.write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
