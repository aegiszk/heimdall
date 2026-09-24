"""E3: Binance USD-M vs Hyperliquid lead/lag on every free Tardis first-of-month day.

For each (day, coin) and each price source (trades: last print; quotes: mid, when available)
the lead/lag curve is computed on a 100 ms grid TWICE:
    A. event time   = exchange `timestamp` (Binance match time / HL block time)
    B. receive time = Tardis collector `local_timestamp`
corr(k) = corr(Binance return over bucket t, HL return over bucket t+k); k>0 => Binance leads.

Free files only (datasets.tardis.dev first day of month, no API key). Cached under
data/tardis_free/. Results: workspace/external_intel_2026-09-23/tardis_leadlag_results.json
Usage: python tardis_leadlag_all.py 2025-02-01 2025-03-01 ...
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "tardis_free"
OUT = Path(__file__).with_name("tardis_leadlag_results.json")
COINS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
STEP_US = 100_000
LAGS = range(-30, 31)  # x100 ms


def fetch(exchange: str, dtype: str, day: str, symbol: str) -> Path | None:
    y, m, d = day.split("-")
    path = CACHE / exchange / dtype / day / f"{symbol}.csv.gz"
    if path.exists() and path.stat().st_size > 0:
        return path
    url = f"https://datasets.tardis.dev/v1/{exchange}/{dtype}/{y}/{m}/{d}/{symbol}.csv.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, path)
    except urllib.error.HTTPError:
        path.unlink(missing_ok=True)
        return None
    return path


def load(path: Path, dtype: str) -> pd.DataFrame:
    if dtype == "trades":
        d = pd.read_csv(path, usecols=["timestamp", "local_timestamp", "price"])
        return d.rename(columns={"price": "p"})
    d = pd.read_csv(path, usecols=["timestamp", "local_timestamp", "bid_price", "ask_price"])
    d = d.dropna()
    d = d[(d.bid_price > 0) & (d.ask_price > d.bid_price)]
    return pd.DataFrame({"timestamp": d.timestamp, "local_timestamp": d.local_timestamp,
                         "p": (d.bid_price + d.ask_price) / 2})


def curve(hl: pd.DataFrame, bn: pd.DataFrame, clock: str) -> dict:
    h = hl.sort_values(clock).groupby(hl[clock] // STEP_US).p.last()
    b = bn.sort_values(clock).groupby(bn[clock] // STEP_US).p.last()
    idx = np.arange(max(h.index.min(), b.index.min()), min(h.index.max(), b.index.max()) + 1)
    m = pd.DataFrame({"h": h.reindex(idx).ffill(), "b": b.reindex(idx).ffill()}).dropna()
    rh, rb = np.diff(np.log(m.h.values)), np.diff(np.log(m.b.values))
    out = {}
    for k in LAGS:
        x, y = (rb[: len(rb) - k], rh[k:]) if k >= 0 else (rb[-k:], rh[: len(rh) + k])
        out[k * 100] = float(np.corrcoef(x, y)[0, 1])
    best = max(out, key=out.get)
    lead = sum(v for k, v in out.items() if k > 0)
    lag = sum(v for k, v in out.items() if k < 0)
    return {"best_lag_ms": best, "corr_best": round(out[best], 4), "corr_0": round(out[0], 4),
            "sum_corr_bn_leads": round(lead, 4), "sum_corr_hl_leads": round(lag, 4),
            "n_buckets": int(len(rh)), "curve": {k: round(v, 4) for k, v in out.items()}}


def delivery(df: pd.DataFrame) -> dict:
    lat = (df.local_timestamp - df.timestamp) / 1000
    return {f"p{p}": round(float(np.percentile(lat, p)), 1) for p in (10, 50, 90, 99)}


def main(days: list[str]) -> None:
    results = json.loads(OUT.read_text()) if OUT.exists() else {}
    for day in days:
        for coin, bsym in COINS.items():
            for dtype in ("trades", "quotes"):
                key = f"{day}|{coin}|{dtype}"
                if key in results:
                    continue
                hp, bp = fetch("hyperliquid", dtype, day, coin), fetch("binance-futures", dtype, day, bsym)
                if not (hp and bp):
                    results[key] = {"status": "unavailable", "hl": bool(hp), "bn": bool(bp)}
                    print(key, "unavailable")
                    continue
                hl, bn = load(hp, dtype), load(bp, dtype)
                r = {"status": "ok", "rows_hl": int(len(hl)), "rows_bn": int(len(bn)),
                     "delivery_ms_hl": delivery(hl), "delivery_ms_bn": delivery(bn),
                     "event": curve(hl, bn, "timestamp"), "receive": curve(hl, bn, "local_timestamp")}
                results[key] = r
                print(key, "event", r["event"]["best_lag_ms"], r["event"]["corr_best"],
                      "| receive", r["receive"]["best_lag_ms"], r["receive"]["corr_best"],
                      "| HL deliv p50", r["delivery_ms_hl"]["p50"])
                OUT.write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
