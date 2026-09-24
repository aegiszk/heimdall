"""Check whether the HL-Binance funding spread edge is decaying by 6-month regime."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ASSETS = ("btc", "eth")
PERIODS_PER_YEAR = 24 * 365
REQUIRED_COLUMNS = ("ts", "hl_hr", "bn_hr", "spread_hr")


def main() -> int:
    overall_stable = True
    for asset in ASSETS:
        df = load_spread(asset)
        rows = bucket_stats(df)
        verdict, detail = judge_decay(rows)
        print_asset(asset, rows, verdict, detail)
        if verdict != "STABLE":
            overall_stable = False
    return 0 if overall_stable else 1


def load_spread(asset: str) -> pd.DataFrame:
    path = DATA_DIR / f"funding_spread_{asset.lower()}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_parquet(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"{path} missing columns: {missing}")
    out = df.loc[:, REQUIRED_COLUMNS].copy()
    out["ts"] = pd.to_datetime(out["ts"], utc=True)
    for column in ("hl_hr", "bn_hr", "spread_hr"):
        out[column] = pd.to_numeric(out[column], errors="coerce")
    if out.isna().any().any():
        raise ValueError(f"{path} contains NaNs: {out.isna().sum().to_dict()}")
    return out.sort_values("ts").reset_index(drop=True)


def bucket_stats(df: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    start = df["ts"].iloc[0]
    end = df["ts"].iloc[-1]
    idx = 1
    while start <= end:
        stop = start + pd.DateOffset(months=6)
        mask = (df["ts"] >= start) & (df["ts"] < stop)
        bucket = df.loc[mask]
        if not bucket.empty:
            spread = bucket["spread_hr"]
            ac1h = spread.autocorr(lag=1) if len(spread) > 2 else 0.0
            rows.append(
                {
                    "bucket": idx,
                    "start": bucket["ts"].iloc[0],
                    "end": bucket["ts"].iloc[-1],
                    "rows": len(bucket),
                    "mean": float(spread.mean()),
                    "ann": float(spread.mean() * PERIODS_PER_YEAR),
                    "pct_positive": float((spread > 0.0).mean() * 100.0),
                    "std": float(spread.std(ddof=1)),
                    "ac1h": finite_or(ac1h, 0.0),
                }
            )
            idx += 1
        start = stop
    return rows


def judge_decay(rows: list[dict[str, object]]) -> tuple[str, str]:
    means = np.array([row["mean"] for row in rows], dtype=float)
    positives = np.array([row["pct_positive"] for row in rows], dtype=float)
    first = means[0] if len(means) else 0.0
    if len(means) < 2 or first <= 0:
        return "DECAYING", "edge collapsed by bucket 1"

    monotonic_shrink = bool(np.all(np.diff(means) <= 0.0))
    halved = np.where(means <= first * 0.5)[0]
    collapsed = np.where((means <= 0.0) | (positives < 55.0))[0]
    if monotonic_shrink and len(halved):
        return "DECAYING", f"edge halved by bucket {int(halved[0]) + 1}"
    if len(collapsed):
        return "DECAYING", f"edge collapsed by bucket {int(collapsed[0]) + 1}"
    return "STABLE", "bucket means/%positive did not show monotonic halving or collapse"


def print_asset(asset: str, rows: list[dict[str, object]], verdict: str, detail: str) -> None:
    print(f"{asset.upper()} funding-spread regime check")
    table = [[
        "bucket",
        "start",
        "end",
        "rows",
        "mean_bps_hr",
        "ann_bps",
        "pct_positive",
        "std_bps_hr",
        "ac1h",
    ]]
    for row in rows:
        table.append(
            [
                str(row["bucket"]),
                row["start"].strftime("%Y-%m-%d"),
                row["end"].strftime("%Y-%m-%d"),
                str(row["rows"]),
                fmt(row["mean"] * 1e4, 4),
                fmt(row["ann"] * 1e4, 2),
                f"{row['pct_positive']:.2f}%",
                fmt(row["std"] * 1e4, 4),
                fmt(row["ac1h"], 4),
            ]
        )
    print_table(table)
    print(f"VERDICT {asset.upper()}: {verdict} ({detail})")
    print()


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(cell).rjust(widths[i]) for i, cell in enumerate(row)))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


def finite_or(value: float, fallback: float) -> float:
    value = float(value)
    return value if np.isfinite(value) else fallback


def fmt(value: float, digits: int) -> str:
    value = float(value)
    if not np.isfinite(value):
        value = 0.0
    return f"{value:.{digits}f}"


if __name__ == "__main__":
    sys.exit(main())
