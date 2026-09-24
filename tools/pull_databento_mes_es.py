"""Pull CME MES/ES 1-minute continuous front-month bars from Databento.

Requires DATABENTO_API_KEY. Uses GLBX.MDP3, ohlcv-1m, continuous symbology:
MES.v.0 and ES.v.0. Saves data/MES_1m.parquet and data/ES_1m.parquet, then
prints Step-0 sanity.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EASTERN = ZoneInfo("America/New_York")
DATASET = "GLBX.MDP3"
SCHEMA = "ohlcv-1m"
SYMBOLS = {"MES": "MES.v.0", "ES": "ES.v.0"}


def main() -> int:
    args = parse_args()
    if not os.getenv("DATABENTO_API_KEY"):
        print("BLOCKED: DATABENTO_API_KEY is not set; cannot authenticate Databento Historical API.")
        print("Expected pull:")
        print(f"  dataset={DATASET} schema={SCHEMA} stype_in=continuous start={args.start} end={args.end}")
        for symbol, continuous in SYMBOLS.items():
            print(f"  {symbol}: symbols={continuous} -> data/{symbol}_1m.parquet")
        return 2

    import databento as db

    client = db.Historical()
    print("DATABENTO REQUEST")
    print(f"dataset={DATASET} schema={SCHEMA} stype_in=continuous start={args.start} end={args.end}")

    frames: dict[str, pd.DataFrame] = {}
    costs: dict[str, float] = {}
    for symbol, continuous in SYMBOLS.items():
        cost = client.metadata.get_cost(
            dataset=DATASET,
            symbols=continuous,
            schema=SCHEMA,
            stype_in="continuous",
            start=args.start,
            end=args.end,
        )
        costs[symbol] = float(cost)
        print(f"{symbol} estimated_cost_usd={cost:.6f}")
        if args.cost_only:
            continue

        data = client.timeseries.get_range(
            dataset=DATASET,
            symbols=continuous,
            schema=SCHEMA,
            stype_in="continuous",
            start=args.start,
            end=args.end,
        )
        df = normalize_databento_df(data.to_df(), symbol=symbol)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path = DATA_DIR / f"{symbol}_1m.parquet"
        df.to_parquet(path)
        frames[symbol] = df
        print(f"{symbol} saved={path} rows={len(df)}")

    if args.cost_only:
        print(f"total_estimated_cost_usd={sum(costs.values()):.6f}")
        return 0

    print_step0(frames, costs)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pull Databento MES/ES continuous 1m OHLCV.")
    parser.add_argument("--start", default="2024-07-01T00:00:00Z")
    parser.add_argument("--end", default="2026-07-01T00:00:00Z")
    parser.add_argument("--cost-only", action="store_true")
    return parser.parse_args()


def normalize_databento_df(raw: pd.DataFrame, *, symbol: str) -> pd.DataFrame:
    df = raw.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        ts_col = "ts_event" if "ts_event" in df.columns else df.columns[0]
        df.index = pd.to_datetime(df.pop(ts_col), utc=True)
    elif df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    keep = [column for column in ["open", "high", "low", "close", "volume", "symbol", "instrument_id"] if column in df.columns]
    out = df.loc[:, keep].copy()
    for column in ["open", "high", "low", "close", "volume"]:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    if "symbol" not in out.columns:
        out["symbol"] = symbol
    out.index.name = "ts_event"
    return out.sort_index()


def print_step0(frames: dict[str, pd.DataFrame], costs: dict[str, float]) -> None:
    print("STEP 0 DATA SANITY")
    print("source=Databento Historical API")
    print("endpoint=https://hist.databento.com/v0/timeseries.get_range")
    print(f"params=dataset:{DATASET}, schema:{SCHEMA}, stype_in:continuous, symbols:MES.v.0/ES.v.0")
    print("session=ETH Sun 18:00-Fri 17:00 ET with daily 17:00-18:00 ET break; RTH 09:30-16:00 ET")
    rows = [[
        "symbol",
        "rows",
        "start_utc",
        "end_utc",
        "months",
        "gaps_eth_1m",
        "gap_pct",
        "rth_rows",
        "eth_non_rth_rows",
        "nan_open",
        "nan_high",
        "nan_low",
        "nan_close",
        "nan_volume",
        "cost_usd",
    ]]
    for symbol, df in frames.items():
        idx_et = df.index.tz_convert(EASTERN)
        expected = expected_eth_index(idx_et[0], idx_et[-1])
        observed = pd.DatetimeIndex(idx_et.floor("min").unique())
        gaps = expected.difference(observed)
        rth_mask = is_rth_index(idx_et)
        months = (df.index[-1] - df.index[0]).total_seconds() / (86400 * 30.4375)
        rows.append([
            symbol,
            str(len(df)),
            df.index[0].isoformat(),
            df.index[-1].isoformat(),
            f"{months:.2f}",
            str(len(gaps)),
            f"{100 * len(gaps) / max(len(df), 1):.3f}%",
            str(int(rth_mask.sum())),
            str(int((~rth_mask).sum())),
            str(int(df["open"].isna().sum())),
            str(int(df["high"].isna().sum())),
            str(int(df["low"].isna().sum())),
            str(int(df["close"].isna().sum())),
            str(int(df["volume"].isna().sum())),
            f"{costs[symbol]:.6f}",
        ])
    print_table(rows)
    for symbol, df in frames.items():
        print(f"{symbol} min/max:")
        for column in ["open", "high", "low", "close", "volume"]:
            print(f"  {column}: min={df[column].min():.4f} max={df[column].max():.4f}")
        print("  sample:")
        print(df.head(3).to_string())


def expected_eth_index(start_et: pd.Timestamp, end_et: pd.Timestamp) -> pd.DatetimeIndex:
    grid = pd.date_range(start=start_et.floor("min"), end=end_et.ceil("min"), freq="1min", tz=EASTERN)
    return pd.DatetimeIndex([ts for ts in grid if is_eth_open(ts)])


def is_eth_open(ts: pd.Timestamp) -> bool:
    weekday = ts.weekday()
    clock = ts.time()
    if weekday == 5:
        return False
    if weekday == 6:
        return clock >= pd.Timestamp("18:00").time()
    if weekday == 4 and clock > pd.Timestamp("17:00").time():
        return False
    if pd.Timestamp("17:01").time() <= clock < pd.Timestamp("18:00").time():
        return False
    return True


def is_rth_index(index_et: pd.DatetimeIndex) -> np.ndarray:
    weekdays = index_et.weekday < 5
    times = pd.Series(index_et.time, index=index_et)
    return (weekdays & (times >= pd.Timestamp("09:30").time()) & (times <= pd.Timestamp("16:00").time())).to_numpy()


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(row[i]).rjust(widths[i]) for i in range(len(row))))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


if __name__ == "__main__":
    sys.exit(main())
