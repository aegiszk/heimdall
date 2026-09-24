"""Real historical market loader for the four-column Heimdall funnel schema.

Schema convention:
- ret: spot log return per output bar.
- funding: funding fraction per output bar, not bps. Funding history rates are
  treated as rates for their native funding interval and scaled to the bar
  duration before forward-fill. For OKX BTC 1h this means an 8h funding print is
  divided by 8 and used from its settlement timestamp until the next print.
- basis_noise: real basis, (perp_close - spot_close) / spot_close.
- oi_pct: rolling open-interest percentile from information available through
  the current bar, or 0.0 for rows where OI is unavailable.

No synthetic values are generated. Price gaps are reported and not filled.
"""
from __future__ import annotations

import logging
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["ret", "funding", "basis_noise", "oi_pct"]

log = logging.getLogger(__name__)


def load_history(
    asset: str | Path,
    venue_perp: str = "okx",
    venue_spot: str = "okx",
    start: str = "2024-01-01",
    timeframe: str = "1h",
) -> pd.DataFrame:
    """Load real history into the synthetic.py-compatible funnel schema.

    If ``asset`` is a local CSV/parquet path, that file is loaded and converted.
    Otherwise public ccxt endpoints are queried for spot OHLCV, perp OHLCV,
    funding history, and best-effort open-interest history.
    """

    maybe_path = Path(asset).expanduser()
    if maybe_path.exists():
        df = _load_local_history(maybe_path, timeframe=timeframe)
        out_path = _output_path(maybe_path.stem, venue_perp, venue_spot, timeframe)
        _save_history(df, out_path)
        _log_coverage(df, source=str(maybe_path))
        return df

    asset_code = str(asset).upper()
    df = _load_ccxt_history(
        asset=asset_code,
        venue_perp=venue_perp,
        venue_spot=venue_spot,
        start=start,
        timeframe=timeframe,
    )
    out_path = _output_path(asset_code, venue_perp, venue_spot, timeframe)
    _save_history(df, out_path)
    _log_coverage(df, source=f"{asset_code} {venue_spot}/{venue_perp} {timeframe}")
    return df


def _load_ccxt_history(
    *,
    asset: str,
    venue_perp: str,
    venue_spot: str,
    start: str,
    timeframe: str,
) -> pd.DataFrame:
    ccxt = _import_ccxt()
    period_ms = _timeframe_ms(timeframe)
    start_ms = _parse_utc_ms(start)
    end_ms = _floor_ms(int(time.time() * 1000) - period_ms, period_ms)

    spot_ex = _make_exchange(ccxt, venue_spot)
    perp_ex = spot_ex if venue_perp == venue_spot else _make_exchange(ccxt, venue_perp)
    _with_retries(lambda: spot_ex.load_markets(), f"{venue_spot}.load_markets")
    if perp_ex is not spot_ex:
        _with_retries(lambda: perp_ex.load_markets(), f"{venue_perp}.load_markets")

    spot_symbol = _resolve_symbol(spot_ex, asset, perp=False)
    perp_symbol = _resolve_symbol(perp_ex, asset, perp=True)

    spot = _fetch_ohlcv_frame(spot_ex, spot_symbol, timeframe, start_ms, end_ms, "spot")
    perp = _fetch_ohlcv_frame(perp_ex, perp_symbol, timeframe, start_ms, end_ms, "perp")
    funding = _fetch_funding_frame(perp_ex, perp_symbol, start_ms, end_ms, period_ms)
    oi = _fetch_open_interest_frame(perp_ex, perp_symbol, timeframe, start_ms, end_ms)

    return _assemble_history(
        spot=spot,
        perp=perp,
        funding=funding,
        oi=oi,
        period_ms=period_ms,
    )


def _load_local_history(path: Path, *, timeframe: str) -> pd.DataFrame:
    if path.suffix.lower() in {".parquet", ".pq"}:
        raw = pd.read_parquet(path)
    elif path.suffix.lower() == ".csv":
        raw = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported history file type: {path.suffix}")

    raw = _with_datetime_index(raw)
    if all(column in raw.columns for column in REQUIRED_COLUMNS):
        df = raw[REQUIRED_COLUMNS].apply(pd.to_numeric, errors="coerce")
        before = len(df)
        df = df.dropna(subset=REQUIRED_COLUMNS)
        dropped = before - len(df)
        if dropped:
            log.warning("Dropped %d local rows with NaNs in required columns.", dropped)
        return _finalize_schema(df)

    if {"spot_close", "perp_close"}.issubset(raw.columns):
        spot = pd.DataFrame({"close": pd.to_numeric(raw["spot_close"], errors="coerce")}, index=raw.index)
        perp = pd.DataFrame({"close": pd.to_numeric(raw["perp_close"], errors="coerce")}, index=raw.index)
        funding_col = _first_existing(raw, ["funding", "funding_rate", "fundingRate"])
        if funding_col is None:
            raise ValueError("Local raw history must include funding/funding_rate/fundingRate.")
        funding = pd.DataFrame(
            {"funding": pd.to_numeric(raw[funding_col], errors="coerce")},
            index=raw.index,
        )
        oi_col = _first_existing(raw, ["open_interest", "openInterest", "oi"])
        oi = None if oi_col is None else pd.DataFrame(
            {"open_interest": pd.to_numeric(raw[oi_col], errors="coerce")},
            index=raw.index,
        )
        return _assemble_history(
            spot=spot,
            perp=perp,
            funding=funding,
            oi=oi,
            period_ms=_timeframe_ms(timeframe),
        )

    raise ValueError(
        "Local history must either contain required columns "
        f"{REQUIRED_COLUMNS} or raw spot_close/perp_close/funding columns."
    )


def _assemble_history(
    *,
    spot: pd.DataFrame,
    perp: pd.DataFrame,
    funding: pd.DataFrame,
    oi: pd.DataFrame | None,
    period_ms: int,
) -> pd.DataFrame:
    prices = spot[["close"]].rename(columns={"close": "spot_close"}).join(
        perp[["close"]].rename(columns={"close": "perp_close"}),
        how="inner",
    )
    _report_time_gaps(prices.index, period_ms, "aligned spot/perp price bars")

    if funding.empty:
        raise ValueError("No funding history returned; refusing to fabricate funding.")

    aligned_funding = funding["funding"].sort_index().reindex(prices.index, method="ffill")
    missing_funding = int(aligned_funding.isna().sum())
    log.info(
        "Forward-filled %d funding prints onto %d price bars; %d rows had no prior funding print.",
        len(funding),
        len(prices),
        missing_funding,
    )
    if missing_funding:
        log.warning(
            "Dropped %d rows before first knowable funding print; no funding was invented.",
            missing_funding,
        )

    out = pd.DataFrame(index=prices.index)
    out["ret"] = np.log(prices["spot_close"]).diff()
    out["funding"] = aligned_funding
    out["basis_noise"] = (prices["perp_close"] - prices["spot_close"]) / prices["spot_close"]
    out["oi_pct"] = _align_oi_percentile(oi, prices.index)

    before = len(out)
    out = out.replace([np.inf, -np.inf], np.nan).dropna(subset=["ret", "funding", "basis_noise"])
    dropped = before - len(out)
    if dropped:
        log.warning("Dropped %d rows with unavailable ret/funding/basis.", dropped)

    return _finalize_schema(out)


def _fetch_ohlcv_frame(
    exchange: Any,
    symbol: str,
    timeframe: str,
    start_ms: int,
    end_ms: int,
    label: str,
) -> pd.DataFrame:
    rows: list[list[Any]] = []
    since = start_ms
    while since <= end_ms:
        batch = _with_retries(
            lambda: exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=300),
            f"{exchange.id}.fetch_ohlcv({symbol},{label})",
        )
        batch = [row for row in batch if row and int(row[0]) >= since]
        if not batch:
            break
        rows.extend(batch)
        last_ts = int(batch[-1][0])
        next_since = last_ts + _timeframe_ms(timeframe)
        if next_since <= since:
            break
        since = next_since
        if last_ts >= end_ms:
            break

    if not rows:
        raise ValueError(f"No {label} OHLCV rows returned for {symbol}.")

    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df = _indexed_numeric_frame(df, value_columns=["open", "high", "low", "close", "volume"])
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df[(df.index >= _to_dt(start_ms)) & (df.index <= _to_dt(end_ms))]
    _report_time_gaps(df.index, _timeframe_ms(timeframe), f"{label} OHLCV")
    return df


def _fetch_funding_frame(
    exchange: Any,
    symbol: str,
    start_ms: int,
    end_ms: int,
    period_ms: int,
) -> pd.DataFrame:
    if not exchange.has.get("fetchFundingRateHistory"):
        raise ValueError(f"{exchange.id} does not expose funding-rate history via ccxt.")

    rows: list[dict[str, Any]] = []
    since = start_ms
    while since <= end_ms:
        batch = _with_retries(
            lambda: exchange.fetch_funding_rate_history(symbol, since=since, limit=100),
            f"{exchange.id}.fetch_funding_rate_history({symbol})",
        )
        batch = [row for row in batch if row.get("timestamp") is not None and int(row["timestamp"]) >= since]
        if not batch:
            break
        rows.extend(batch)
        last_ts = int(batch[-1]["timestamp"])
        if last_ts + 1 <= since:
            break
        since = last_ts + 1
        if last_ts >= end_ms:
            break

    if not rows:
        raise ValueError(f"No funding rows returned for {symbol}.")

    raw = pd.DataFrame(rows)
    raw = raw.dropna(subset=["timestamp", "fundingRate"])
    raw["timestamp"] = pd.to_datetime(raw["timestamp"].astype("int64"), unit="ms", utc=True)
    raw["fundingRate"] = pd.to_numeric(raw["fundingRate"], errors="coerce")
    raw = raw.dropna(subset=["fundingRate"]).drop_duplicates(subset=["timestamp"], keep="last")
    raw = raw.sort_values("timestamp").set_index("timestamp")
    interval_ms = _infer_interval_ms(raw.index, default_ms=8 * 60 * 60 * 1000)
    if interval_ms != period_ms:
        log.info(
            "Scaled funding rates from native %.2fh interval to %.2fh bars.",
            interval_ms / 3_600_000,
            period_ms / 3_600_000,
        )
    _report_time_gaps(raw.index, interval_ms, "funding prints")
    return pd.DataFrame({"funding": raw["fundingRate"] * (period_ms / interval_ms)}, index=raw.index)


def _fetch_open_interest_frame(
    exchange: Any,
    symbol: str,
    timeframe: str,
    start_ms: int,
    end_ms: int,
) -> pd.DataFrame | None:
    if not exchange.has.get("fetchOpenInterestHistory"):
        log.warning("%s has no ccxt open-interest history; oi_pct will be 0.0.", exchange.id)
        return None

    rows: list[dict[str, Any]] = []
    since = start_ms
    period_ms = _timeframe_ms(timeframe)
    try:
        while since <= end_ms:
            batch = _with_retries(
                lambda: exchange.fetch_open_interest_history(symbol, timeframe=timeframe, since=since, limit=300),
                f"{exchange.id}.fetch_open_interest_history({symbol})",
            )
            batch = [row for row in batch if row.get("timestamp") is not None and int(row["timestamp"]) >= since]
            if not batch:
                break
            rows.extend(batch)
            last_ts = int(batch[-1]["timestamp"])
            next_since = last_ts + period_ms
            if next_since <= since:
                break
            since = next_since
            if last_ts >= end_ms:
                break
    except Exception as exc:  # public OI is optional in this funnel schema
        log.warning("Open-interest history unavailable (%s); oi_pct will be 0.0.", exc)
        return None

    if not rows:
        log.warning("No open-interest rows returned; oi_pct will be 0.0.")
        return None

    raw = pd.DataFrame(rows)
    value_col = _first_existing(raw, ["openInterestAmount", "openInterestValue", "openInterest"])
    if value_col is None:
        log.warning("Open-interest rows have no recognized value column; oi_pct will be 0.0.")
        return None

    raw["timestamp"] = pd.to_datetime(raw["timestamp"].astype("int64"), unit="ms", utc=True)
    raw["open_interest"] = pd.to_numeric(raw[value_col], errors="coerce")
    raw = raw.dropna(subset=["open_interest"]).drop_duplicates(subset=["timestamp"], keep="last")
    raw = raw.sort_values("timestamp").set_index("timestamp")
    _report_time_gaps(raw.index, period_ms, "open-interest prints")
    return raw[["open_interest"]]


def _align_oi_percentile(oi: pd.DataFrame | None, index: pd.DatetimeIndex) -> pd.Series:
    if oi is None or oi.empty:
        log.warning("Filled oi_pct with 0.0 for %d rows because OI is unavailable.", len(index))
        return pd.Series(0.0, index=index)

    known = oi["open_interest"].dropna()
    window = min(max(24 * 90, 1), len(known))
    pct = known.rolling(window=window, min_periods=1).apply(
        lambda x: float((x <= x[-1]).mean() * 100.0),
        raw=True,
    )
    aligned = pct.reindex(index)
    missing = int(aligned.isna().sum())
    if missing:
        log.warning(
            "Filled oi_pct with 0.0 for %d rows without exact OI timestamps; OI values were not interpolated.",
            missing,
        )
    return aligned.fillna(0.0)


def _make_exchange(ccxt: Any, venue: str) -> Any:
    try:
        cls = getattr(ccxt, venue)
    except AttributeError as exc:
        raise ValueError(f"Unknown ccxt venue: {venue}") from exc
    return cls({"enableRateLimit": True, "timeout": 30_000})


def _resolve_symbol(exchange: Any, asset: str, *, perp: bool) -> str:
    candidates = (
        [f"{asset}/USDT:USDT", f"{asset}/USDT:USDT-241227", f"{asset}-USDT-SWAP"]
        if perp
        else [f"{asset}/USDT", f"{asset}/USDC"]
    )
    for symbol in candidates:
        if symbol in exchange.markets:
            return symbol
    market_type = "perpetual swap" if perp else "spot"
    raise ValueError(f"No {market_type} market found on {exchange.id} for {asset}.")


def _with_retries(fn: Any, label: str, attempts: int = 4) -> Any:
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt == attempts - 1:
                break
            sleep_s = min(2.0 ** attempt, 8.0)
            log.warning("%s failed on attempt %d/%d: %s; retrying in %.1fs", label, attempt + 1, attempts, exc, sleep_s)
            time.sleep(sleep_s)
    raise RuntimeError(f"{label} failed after {attempts} attempts: {last_exc}") from last_exc


def _with_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    timestamp_col = _first_existing(out, ["timestamp", "ts", "datetime", "date", "time"])
    if timestamp_col is not None:
        out.index = pd.to_datetime(out.pop(timestamp_col), utc=True)
    elif not isinstance(out.index, pd.DatetimeIndex):
        out.index = pd.to_datetime(out.index, utc=True)
    elif out.index.tz is None:
        out.index = out.index.tz_localize("UTC")
    else:
        out.index = out.index.tz_convert("UTC")
    return out.sort_index()


def _indexed_numeric_frame(df: pd.DataFrame, *, value_columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"].astype("int64"), unit="ms", utc=True)
    out = out.set_index("timestamp")
    for column in value_columns:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    return out.dropna(subset=value_columns)


def _finalize_schema(df: pd.DataFrame) -> pd.DataFrame:
    out = df[REQUIRED_COLUMNS].copy()
    for column in REQUIRED_COLUMNS:
        out[column] = pd.to_numeric(out[column], errors="coerce").astype(float)
    out = out.replace([np.inf, -np.inf], np.nan).dropna(subset=REQUIRED_COLUMNS)
    out.index.name = "timestamp"
    return out.sort_index()


def _save_history(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)
    log.info("Saved %d rows to %s.", len(df), path)


def _output_path(asset: str, venue_perp: str, venue_spot: str, timeframe: str) -> Path:
    venue = venue_perp if venue_perp == venue_spot else f"{venue_perp}_{venue_spot}"
    safe_asset = asset.upper().replace("/", "-").replace(":", "-")
    return Path("data") / f"{safe_asset}_{venue}_{timeframe}.parquet"


def _report_time_gaps(index: pd.DatetimeIndex, period_ms: int, label: str) -> None:
    if len(index) < 2:
        return
    deltas = pd.Series(index).diff().dropna().dt.total_seconds() * 1000
    gaps = deltas[deltas > period_ms * 1.5]
    if not gaps.empty:
        log.warning(
            "%s has %d timestamp gaps larger than expected period; max gap %.2fh. Gaps were not filled.",
            label,
            len(gaps),
            gaps.max() / 3_600_000,
        )


def _log_coverage(df: pd.DataFrame, *, source: str) -> None:
    if df.empty:
        log.warning("%s produced empty history.", source)
        return
    days = (df.index[-1] - df.index[0]).total_seconds() / 86_400
    log.info(
        "%s coverage: %d rows, %s -> %s (%.1f days).",
        source,
        len(df),
        df.index[0].isoformat(),
        df.index[-1].isoformat(),
        days,
    )


def _infer_interval_ms(index: pd.DatetimeIndex, *, default_ms: int) -> int:
    if len(index) < 2:
        return default_ms
    deltas = pd.Series(index).diff().dropna().dt.total_seconds() * 1000
    median = float(deltas.median())
    if not math.isfinite(median) or median <= 0:
        return default_ms
    return int(median)


def _timeframe_ms(timeframe: str) -> int:
    unit = timeframe[-1]
    try:
        value = int(timeframe[:-1])
    except ValueError as exc:
        raise ValueError(f"Unsupported timeframe: {timeframe}") from exc
    multipliers = {
        "m": 60_000,
        "h": 3_600_000,
        "d": 86_400_000,
    }
    if unit not in multipliers:
        raise ValueError(f"Unsupported timeframe unit: {timeframe}")
    return value * multipliers[unit]


def _parse_utc_ms(value: str) -> int:
    return int(pd.Timestamp(value, tz="UTC").timestamp() * 1000)


def _floor_ms(value: int, period_ms: int) -> int:
    return value - (value % period_ms)


def _to_dt(value_ms: int) -> pd.Timestamp:
    return pd.to_datetime(value_ms, unit="ms", utc=True)


def _first_existing(df: pd.DataFrame, names: list[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def _import_ccxt() -> Any:
    try:
        import ccxt  # type: ignore
    except ImportError as exc:
        raise RuntimeError("ccxt is required for exchange history loading.") from exc
    return ccxt
