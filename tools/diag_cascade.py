"""Diagnose Binance liquidation-cascade mean reversion.

Measurement only. This script does not mutate core strategy logic.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zipfile import ZipFile

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
HOUR_MS = 60 * 60 * 1000
FAPI_BASE = "https://fapi.binance.com"
DATA_BASE = "https://data.binance.vision"
USER_AGENT = "heimdall-cascade-diag/1.0"
SANITY_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "funding_rate_8h",
    "open_interest",
    "open_interest_value",
)
HORIZONS = (1, 4, 12, 24)


@dataclass(frozen=True)
class EndpointSpec:
    name: str
    method: str
    url: str
    params: dict[str, object] | None = None


def main() -> int:
    args = parse_args()
    start = parse_utc(args.start).floor("h")
    end = parse_utc(args.end).floor("h")
    if end <= start:
        raise ValueError("--end must be after --start")

    symbols = [symbol.upper() for symbol in args.symbols]
    print_endpoint_specs(symbols, start, end)
    print()

    frames: dict[str, pd.DataFrame] = {}
    stopped = False
    for symbol in symbols:
        print(f"STEP 0 DATA SANITY {symbol}")
        df = load_binance_hourly(symbol, start, end, max_workers=args.max_workers, refresh=args.refresh)
        frames[symbol] = df
        ok = print_sanity(symbol, df, start, end)
        print()
        if not ok:
            stopped = True

    if stopped:
        print("STOP: at least one symbol has gaps > 1% of rows or < 18 months continuous coverage.")
        return 1

    print("STEP 1 CASCADE EVENT STUDY")
    for symbol in symbols:
        rows = event_study(
            frames[symbol],
            p_hi=args.p_hi,
            p_lo=args.p_lo,
            z=args.z,
            rolling_hours=args.rolling_hours,
            min_periods=args.min_periods,
            seed=args.seed,
        )
        print_event_table(symbol, rows, p_hi=args.p_hi, p_lo=args.p_lo, z=args.z)
        print()

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure liquidation-cascade mean reversion on Binance native data.")
    parser.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    parser.add_argument("--start", default="2024-12-01T00:00:00Z")
    parser.add_argument("--end", default="2026-06-30T23:00:00Z")
    parser.add_argument("--refresh", action="store_true", help="Ignore processed parquet cache and pull endpoints again.")
    parser.add_argument("--max-workers", type=int, default=12, help="Concurrent workers for daily OI metric zip downloads.")
    parser.add_argument("--rolling-hours", type=int, default=24 * 180, help="Trailing window for percentiles and return Z.")
    parser.add_argument("--min-periods", type=int, default=24 * 90, help="Minimum trailing observations before a signal is eligible.")
    parser.add_argument("--p-hi", type=float, default=95.0)
    parser.add_argument("--p-lo", type=float, default=5.0)
    parser.add_argument("--z", type=float, default=2.0)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()


def print_endpoint_specs(symbols: list[str], start: pd.Timestamp, end: pd.Timestamp) -> None:
    print("BINANCE ENDPOINTS AND PARAMS")
    for symbol in symbols:
        specs = [
            EndpointSpec(
                "price_ohlcv",
                "GET",
                f"{FAPI_BASE}/fapi/v1/klines",
                {
                    "symbol": symbol,
                    "interval": "1h",
                    "startTime": to_ms(start),
                    "endTime": to_ms(end),
                    "limit": 1500,
                },
            ),
            EndpointSpec(
                "funding",
                "GET",
                f"{FAPI_BASE}/fapi/v1/fundingRate",
                {
                    "symbol": symbol,
                    "startTime": to_ms(start - pd.Timedelta(hours=8)),
                    "endTime": to_ms(end),
                    "limit": 1000,
                },
            ),
            EndpointSpec(
                "open_interest_metrics",
                "GET",
                f"{DATA_BASE}/data/futures/um/daily/metrics/{symbol}/{symbol}-metrics-YYYY-MM-DD.zip",
                {
                    "date_start": start.date().isoformat(),
                    "date_end": end.date().isoformat(),
                    "resample": "5m metrics grouped by floor(create_time, 1h), last value per hour",
                },
            ),
        ]
        print(symbol)
        for spec in specs:
            params = "" if spec.params is None else f" params={spec.params}"
            print(f"  {spec.name}: {spec.method} {spec.url}{params}")


def load_binance_hourly(symbol: str, start: pd.Timestamp, end: pd.Timestamp, *, max_workers: int, refresh: bool) -> pd.DataFrame:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = DATA_DIR / f"binance_native_{symbol}_1h_{date_key(start)}_{date_key(end)}.parquet"
    if cache_path.exists() and not refresh:
        df = pd.read_parquet(cache_path)
        df.index = pd.to_datetime(df.index, utc=True)
        return df

    price = fetch_klines(symbol, start, end)
    funding = fetch_funding(symbol, start, end)
    oi = fetch_open_interest_metrics(symbol, start, end, max_workers=max_workers)

    expected = pd.date_range(start, end, freq="1h", tz="UTC")
    df = price.join(funding, how="outer").join(oi, how="outer").sort_index()
    df = df.reindex(expected)
    df.index.name = "timestamp"
    df["ret_1h"] = df["close"].pct_change()
    df.to_parquet(cache_path)
    return df


def fetch_klines(symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    rows: list[list[object]] = []
    since_ms = to_ms(start)
    end_ms = to_ms(end)
    while since_ms <= end_ms:
        params = {
            "symbol": symbol,
            "interval": "1h",
            "startTime": since_ms,
            "endTime": end_ms,
            "limit": 1500,
        }
        batch = request_json(f"{FAPI_BASE}/fapi/v1/klines", params)
        if not batch:
            break
        rows.extend(batch)
        last_open = int(batch[-1][0])
        next_since = last_open + HOUR_MS
        if next_since <= since_ms:
            break
        since_ms = next_since
        if last_open >= end_ms:
            break

    if not rows:
        raise RuntimeError(f"No kline rows returned for {symbol}")

    cols = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "count",
        "taker_buy_volume",
        "taker_buy_quote_volume",
        "ignore",
    ]
    df = pd.DataFrame(rows, columns=cols)
    df["timestamp"] = pd.to_datetime(df["open_time"].astype("int64"), unit="ms", utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    out = df.drop_duplicates("timestamp", keep="last").set_index("timestamp")
    return out.loc[:, ["open", "high", "low", "close", "volume"]].sort_index()


def fetch_funding(symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    since_ms = to_ms(start - pd.Timedelta(hours=8))
    end_ms = to_ms(end)
    while since_ms <= end_ms:
        params = {
            "symbol": symbol,
            "startTime": since_ms,
            "endTime": end_ms,
            "limit": 1000,
        }
        batch = request_json(f"{FAPI_BASE}/fapi/v1/fundingRate", params)
        if not batch:
            break
        rows.extend(batch)
        last_time = int(batch[-1]["fundingTime"])
        next_since = last_time + 1
        if next_since <= since_ms:
            break
        since_ms = next_since
        if last_time >= end_ms:
            break

    if not rows:
        raise RuntimeError(f"No funding rows returned for {symbol}")

    raw = pd.DataFrame(rows)
    raw["timestamp"] = pd.to_datetime(raw["fundingTime"].astype("int64"), unit="ms", utc=True).dt.floor("h")
    raw["funding_rate_8h"] = pd.to_numeric(raw["fundingRate"], errors="coerce")
    raw = raw.dropna(subset=["funding_rate_8h"]).drop_duplicates("timestamp", keep="last")
    raw = raw.set_index("timestamp").sort_index()
    expected = pd.date_range(start, end, freq="1h", tz="UTC")
    out = raw.loc[:, ["funding_rate_8h"]].reindex(expected).ffill()
    out.index.name = "timestamp"
    return out


def fetch_open_interest_metrics(symbol: str, start: pd.Timestamp, end: pd.Timestamp, *, max_workers: int) -> pd.DataFrame:
    days = list(date_range(start.date(), end.date()))
    frames: list[pd.DataFrame] = []
    workers = max(1, int(max_workers))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_day = {
            pool.submit(fetch_oi_metric_day, symbol, day): day
            for day in days
        }
        for future in as_completed(future_to_day):
            day = future_to_day[future]
            try:
                frames.append(future.result())
            except HTTPError as exc:
                if exc.code == 404:
                    raise RuntimeError(f"Missing Binance OI metrics zip for {symbol} {day}") from exc
                raise

    if not frames:
        raise RuntimeError(f"No OI metric rows returned for {symbol}")

    raw = pd.concat(frames, ignore_index=True)
    raw["timestamp"] = pd.to_datetime(raw["create_time"], utc=True).dt.floor("h")
    raw["open_interest"] = pd.to_numeric(raw["sum_open_interest"], errors="coerce")
    raw["open_interest_value"] = pd.to_numeric(raw["sum_open_interest_value"], errors="coerce")
    raw = raw.dropna(subset=["open_interest", "open_interest_value"])
    raw = raw.sort_values(["timestamp", "create_time"]).drop_duplicates("timestamp", keep="last")
    raw = raw.set_index("timestamp")
    expected = pd.date_range(start, end, freq="1h", tz="UTC")
    out = raw.loc[:, ["open_interest", "open_interest_value"]].reindex(expected)
    out.index.name = "timestamp"
    return out


def fetch_oi_metric_day(symbol: str, day: date) -> pd.DataFrame:
    url = f"{DATA_BASE}/data/futures/um/daily/metrics/{symbol}/{symbol}-metrics-{day.isoformat()}.zip"
    raw = request_bytes(url)
    with ZipFile(BytesIO(raw)) as zf:
        names = zf.namelist()
        if not names:
            raise RuntimeError(f"Empty Binance OI metrics zip: {url}")
        with zf.open(names[0]) as fh:
            return pd.read_csv(fh)


def request_json(url: str, params: dict[str, object], retries: int = 4) -> object:
    query = urlencode(params)
    raw = request_bytes(f"{url}?{query}", retries=retries)
    return json.loads(raw.decode("utf-8"))


def request_bytes(url: str, retries: int = 4) -> bytes:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=30) as resp:
                return resp.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            last_exc = exc
            if isinstance(exc, HTTPError) and exc.code == 404:
                raise
            if attempt >= retries:
                break
            time.sleep(0.5 * (2 ** attempt))
    raise RuntimeError(f"Request failed after retries: {url}") from last_exc


def print_sanity(symbol: str, df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> bool:
    expected_rows = int(((end - start) / pd.Timedelta(hours=1))) + 1
    complete = df.loc[:, SANITY_COLUMNS].dropna(how="any")
    missing_hours = expected_rows - len(complete)
    gap_pct = 100.0 * missing_hours / expected_rows if expected_rows else 100.0
    duration_days = (end - start) / pd.Timedelta(days=1)
    continuous_18m = len(complete) == expected_rows and duration_days >= 365.2425 * 1.5

    print(f"rows: {len(df)} expected_rows: {expected_rows}")
    print(f"start: {df.index[0].isoformat()} end: {df.index[-1].isoformat()}")
    print(f"duration_days: {duration_days:.2f} continuous_18m_or_more: {continuous_18m}")
    print(f"gaps_missing_hours: {missing_hours} gap_pct: {gap_pct:.4f}%")
    print(f"nan_counts: {df.loc[:, SANITY_COLUMNS].isna().sum().to_dict()}")
    print("min_max:")
    for column in SANITY_COLUMNS:
        series = df[column]
        print(f"  {column}: min={fmt_float(series.min())} max={fmt_float(series.max())}")

    ok = gap_pct <= 1.0 and continuous_18m
    verdict = "OK" if ok else "FAIL"
    print(f"sanity_verdict {symbol}: {verdict}")
    return ok


def event_study(
    df: pd.DataFrame,
    *,
    p_hi: float,
    p_lo: float,
    z: float,
    rolling_hours: int,
    min_periods: int,
    seed: int,
) -> list[dict[str, object]]:
    work = df.copy()
    work["funding_pct"] = trailing_percentile(work["funding_rate_8h"].to_numpy(float), rolling_hours, min_periods)
    work["oi_pct"] = trailing_percentile(work["open_interest"].to_numpy(float), rolling_hours, min_periods)
    ret = work["close"].pct_change()
    ret_mean = ret.shift(1).rolling(rolling_hours, min_periods=min_periods).mean()
    ret_std = ret.shift(1).rolling(rolling_hours, min_periods=min_periods).std(ddof=1)
    work["ret_z"] = (ret - ret_mean) / ret_std.replace(0.0, np.nan)

    long_event = (work["funding_pct"] >= p_hi) & (work["ret_z"] <= -z)
    short_event = (work["funding_pct"] <= p_lo) & (work["ret_z"] >= z)
    eligible = work["funding_pct"].notna() & work["ret_z"].notna()
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []

    specs = [
        ("long_liq_bounce_up", long_event, work["ret_z"] <= -z, 1.0),
        ("short_liq_snap_down", short_event, work["ret_z"] >= z, -1.0),
    ]
    for direction, event_mask, shock_mask, sign in specs:
        event_idx = work.index[event_mask.fillna(False)]
        baseline_pool = work.index[(eligible & shock_mask & ~long_event & ~short_event).fillna(False)]
        baseline_idx = sample_index(baseline_pool, len(event_idx), rng)
        rows.append(summarize_sample(work, direction, "event", event_idx, sign))
        rows.append(summarize_sample(work, direction, "random_non_event_same_shock", baseline_idx, sign))
    return rows


def trailing_percentile(values: np.ndarray, window: int, min_periods: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    out = np.full(len(values), np.nan, dtype=float)
    for idx, value in enumerate(values):
        if not np.isfinite(value):
            continue
        start = max(0, idx - window)
        hist = values[start:idx]
        hist = hist[np.isfinite(hist)]
        if len(hist) < min_periods:
            continue
        out[idx] = 100.0 * float(np.mean(hist <= value))
    return out


def sample_index(pool: pd.Index, n: int, rng: np.random.Generator) -> pd.Index:
    if n <= 0 or len(pool) == 0:
        return pool[:0]
    replace = len(pool) < n
    locs = rng.choice(np.arange(len(pool)), size=n, replace=replace)
    return pool[np.sort(locs)]


def summarize_sample(work: pd.DataFrame, direction: str, sample: str, idx: pd.Index, sign: float) -> dict[str, object]:
    row: dict[str, object] = {
        "direction": direction,
        "sample": sample,
        "events": len(idx),
        "mean_funding_pct": safe_mean(work.loc[idx, "funding_pct"]) if len(idx) else math.nan,
        "mean_oi_pct": safe_mean(work.loc[idx, "oi_pct"]) if len(idx) else math.nan,
        "mean_ret_z": safe_mean(work.loc[idx, "ret_z"]) if len(idx) else math.nan,
    }
    close = work["close"]
    for horizon in HORIZONS:
        fwd = close.shift(-horizon).div(close).sub(1.0).loc[idx]
        signed = sign * fwd.dropna()
        row[f"n_{horizon}h"] = int(len(signed))
        row[f"mean_{horizon}h"] = safe_mean(signed)
        row[f"median_{horizon}h"] = safe_median(signed)
        row[f"hit_{horizon}h"] = safe_mean(signed > 0.0) * 100.0 if len(signed) else math.nan
    return row


def print_event_table(symbol: str, rows: list[dict[str, object]], *, p_hi: float, p_lo: float, z: float) -> None:
    print(f"{symbol} cascade event table")
    print(f"event definition: long=funding_pct>={p_hi:g} and ret_z<=-{z:g}; short=funding_pct<={p_lo:g} and ret_z>={z:g}")
    print("baseline: fixed-seed random non-event bars with the same 1h shock sign and same sample size")
    headers = [
        "direction",
        "sample",
        "events",
        "fund_pct",
        "oi_pct",
        "ret_z",
    ]
    for horizon in HORIZONS:
        headers.extend([f"n{horizon}", f"mean{horizon}", f"med{horizon}", f"hit{horizon}"])
    table = [headers]
    for row in rows:
        line = [
            str(row["direction"]),
            str(row["sample"]),
            str(row["events"]),
            fmt_float(row["mean_funding_pct"], 2),
            fmt_float(row["mean_oi_pct"], 2),
            fmt_float(row["mean_ret_z"], 2),
        ]
        for horizon in HORIZONS:
            line.extend(
                [
                    str(row[f"n_{horizon}h"]),
                    bps(row[f"mean_{horizon}h"]),
                    bps(row[f"median_{horizon}h"]),
                    pct(row[f"hit_{horizon}h"]),
                ]
            )
        table.append(line)
    print_table(table)


def parse_utc(value: str) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def to_ms(ts: pd.Timestamp) -> int:
    return int(ts.timestamp() * 1000)


def date_key(ts: pd.Timestamp) -> str:
    return ts.strftime("%Y%m%d%H")


def date_range(start: date, end: date):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def safe_mean(values) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if len(arr) else math.nan


def safe_median(values) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(np.median(arr)) if len(arr) else math.nan


def fmt_float(value, digits: int = 8) -> str:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not np.isfinite(val):
        return "nan"
    return f"{val:.{digits}f}"


def bps(value) -> str:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not np.isfinite(val):
        return "nan"
    return f"{val * 1e4:.2f}"


def pct(value) -> str:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not np.isfinite(val):
        return "nan"
    return f"{val:.2f}%"


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(cell).rjust(widths[i]) for i, cell in enumerate(row)))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


if __name__ == "__main__":
    sys.exit(main())
