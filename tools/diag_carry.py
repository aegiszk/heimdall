"""Diagnose carry PnL decomposition on real Heimdall history.

Measurement only. This script does not mutate core strategy logic.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.carry import FundingCarryModel
from core.alpha.oi_extreme import OIExtremeModel
from core.alpha.vol_momentum import VolRegimeMomentumModel
from core.data.history import REQUIRED_COLUMNS, load_history
from core.validation import metrics as m
from loop import run_paper_backtest


PERIODS_PER_YEAR = 24 * 365
ENTER_BPS_SWEEP = [1.0, 0.5, 0.25, 0.1, 0.0]


def main() -> None:
    args = parse_args()
    df, source = load_frame(args)

    carry = FundingCarryModel(enter_bps=args.enter_bps, fee=args.fee)
    enter_bps = carry._enter
    fee = carry._fee
    pos = (df["funding"].to_numpy(float) * 1e4 >= enter_bps).astype(float)

    funding_term = pd.Series(pos * (df["funding"].to_numpy(float) - fee), index=df.index)
    basis_term = pd.Series(pos * df["basis_noise"].to_numpy(float), index=df.index)
    carry_returns, _, _ = carry.strategy_returns(df)
    combined = pd.Series(carry_returns, index=df.index)
    basis_change = pd.Series(
        pos * df["basis_noise"].diff().fillna(0.0).to_numpy(float),
        index=df.index,
    )

    print_header(df, source, enter_bps, fee, pos)
    print_stats_table(
        [
            ("FUNDING_ONLY", funding_term),
            ("BASIS_TERM", basis_term),
            ("COMBINED_CURRENT", combined),
            ("BASIS_CHANGE_ALT", basis_change),
        ]
    )
    corr = funding_term.corr(basis_term)
    print()
    print(f"Correlation funding_term_vs_basis_term: {fmt(corr, 6)}")
    print_largest_combined(df, funding_term, basis_term, combined)
    print_fire_rate_table(df, args.fee)
    print_funnel_verdicts(df, args.fee)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure carry PnL components on real BTC history.")
    parser.add_argument("--asset", default="BTC")
    parser.add_argument("--timeframe", default=os.environ.get("HEIMDALL_HISTORY_TIMEFRAME", "1h"))
    parser.add_argument("--venue-perp", default=os.environ.get("HEIMDALL_HISTORY_VENUE_PERP", "binanceusdm"))
    parser.add_argument("--venue-spot", default=os.environ.get("HEIMDALL_HISTORY_VENUE_SPOT", "binance"))
    parser.add_argument("--path", default=None, help="Optional parquet/csv path. Defaults to data/{asset}_{venue}_{timeframe}.parquet if present.")
    parser.add_argument("--refresh", action="store_true", help="Fetch via load_history(asset, venues...) instead of reading cached parquet.")
    parser.add_argument("--enter-bps", type=float, default=1.0)
    parser.add_argument("--fee", type=float, default=2e-5)
    return parser.parse_args()


def load_frame(args: argparse.Namespace) -> tuple[pd.DataFrame, str]:
    if args.path:
        path = Path(args.path)
    else:
        venue = args.venue_perp if args.venue_perp == args.venue_spot else f"{args.venue_perp}_{args.venue_spot}"
        path = ROOT / "data" / f"{args.asset.upper()}_{venue}_{args.timeframe}.parquet"

    if not args.refresh and path.exists():
        df = read_cached(path)
        return df, str(path)

    df = load_history(
        args.asset,
        venue_perp=args.venue_perp,
        venue_spot=args.venue_spot,
        timeframe=args.timeframe,
    )
    return df, f"load_history({args.asset}, {args.venue_perp}, {args.venue_spot}, {args.timeframe})"


def read_cached(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported history file type: {path}")

    if not isinstance(df.index, pd.DatetimeIndex):
        timestamp_col = next((name for name in ["timestamp", "ts", "datetime", "date", "time"] if name in df.columns), None)
        if timestamp_col is None:
            df.index = pd.to_datetime(df.index, utc=True)
        else:
            df.index = pd.to_datetime(df.pop(timestamp_col), utc=True)
    elif df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"History file is missing required columns: {missing}")
    out = df[REQUIRED_COLUMNS].copy()
    for column in REQUIRED_COLUMNS:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    if out.isna().any().any():
        raise ValueError(f"History file has NaNs in required columns: {out.isna().sum().to_dict()}")
    return out.sort_index()


def print_header(
    df: pd.DataFrame,
    source: str,
    enter_bps: float,
    fee: float,
    pos: np.ndarray,
) -> None:
    rows_total = len(df)
    rows_in_pos = int(pos.sum())
    pct_in_pos = 100.0 * rows_in_pos / rows_total if rows_total else 0.0
    print("Carry diagnostic")
    print(f"source: {source}")
    print(f"range: {df.index[0].isoformat()} -> {df.index[-1].isoformat()}")
    print(f"enter_bps: {enter_bps:.4f}")
    print(f"fee_per_bar: {fee:.8f}")
    print()
    print(f"rows_total: {rows_total}")
    print(f"rows_in_position: {rows_in_pos}")
    print(f"pct_time_in_position: {pct_in_pos:.2f}%")
    print()


def print_stats_table(rows: list[tuple[str, pd.Series]]) -> None:
    headers = [
        "series",
        "mean/bar",
        "ann_mean_bps",
        "std",
        "sharpe_bar",
        "sharpe_ann",
        "NWt",
        "maxDD",
        "min",
        "max",
    ]
    table = [headers]
    for name, series in rows:
        stats = describe(series)
        table.append(
            [
                name,
                fmt(stats["mean"], 8),
                fmt(stats["ann_mean_bps"], 2),
                fmt(stats["std"], 8),
                fmt(stats["sharpe_bar"], 4),
                fmt(stats["sharpe_ann"], 2),
                fmt(stats["nw_t"], 2),
                fmt(stats["max_dd"], 6),
                fmt(stats["min"], 8),
                fmt(stats["max"], 8),
            ]
        )
    print_table(table)


def describe(series: pd.Series) -> dict[str, float]:
    arr = series.to_numpy(float)
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))
    sharpe_bar = m.sharpe(arr)
    return {
        "mean": mean,
        "ann_mean_bps": mean * PERIODS_PER_YEAR * 10_000,
        "std": std,
        "sharpe_bar": sharpe_bar,
        "sharpe_ann": sharpe_bar * np.sqrt(PERIODS_PER_YEAR),
        "nw_t": m.newey_west_tstat(arr),
        "max_dd": m.max_drawdown(arr),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def print_largest_combined(
    df: pd.DataFrame,
    funding_term: pd.Series,
    basis_term: pd.Series,
    combined: pd.Series,
) -> None:
    top = combined.abs().sort_values(ascending=False).head(5).index
    rows = [[
        "timestamp",
        "combined",
        "funding_term",
        "basis_term_pos",
        "basis_noise_raw",
        "funding_raw",
    ]]
    for ts in top:
        rows.append(
            [
                ts.isoformat(),
                fmt(combined.loc[ts], 8),
                fmt(funding_term.loc[ts], 8),
                fmt(basis_term.loc[ts], 8),
                fmt(df.loc[ts, "basis_noise"], 8),
                fmt(df.loc[ts, "funding"], 8),
            ]
        )
    print()
    print("Top 5 |COMBINED_CURRENT| bars")
    print_table(rows)


def print_fire_rate_table(df: pd.DataFrame, fee: float) -> None:
    rows = [[
        "enter_bps",
        "rows_in_position",
        "pct_time_in_position",
        "ann_funding_captured_bps",
        "ann_net_after_fee_bps",
    ]]
    funding = df["funding"].to_numpy(float)
    for enter_bps in ENTER_BPS_SWEEP:
        pos = (funding * 1e4 >= enter_bps).astype(float)
        rows.append(
            [
                fmt(enter_bps, 2),
                str(int(pos.sum())),
                f"{100.0 * pos.mean():.2f}%",
                fmt(float(np.mean(pos * funding) * PERIODS_PER_YEAR * 10_000), 2),
                fmt(float(np.mean(pos * (funding - fee)) * PERIODS_PER_YEAR * 10_000), 2),
            ]
        )
    print()
    print("Fire-rate sweep")
    print_table(rows)


def print_funnel_verdicts(df: pd.DataFrame, fee: float) -> None:
    rows = [["enter_bps", "family", "passed", "dsr", "nw_t", "n_trades", "reasons"]]
    for enter_bps in ENTER_BPS_SWEEP:
        families = [
            FundingCarryModel(enter_bps=enter_bps, fee=fee),
            OIExtremeModel(),
            VolRegimeMomentumModel(),
        ]
        for fam, res in run_paper_backtest(df=df, families=families):
            if fam.name != "carry":
                continue
            rows.append(
                [
                    fmt(enter_bps, 2),
                    fam.name,
                    str(res.passed),
                    fmt(res.dsr, 3),
                    fmt(res.nw_t, 2),
                    str(res.n_trades),
                    ",".join(res.reasons) if res.reasons else "[]",
                ]
            )
    print()
    print("Carry funnel verdicts")
    print_table(rows)


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(cell).rjust(widths[i]) for i, cell in enumerate(row)))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


def fmt(value: float, digits: int) -> str:
    if value is None or not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


if __name__ == "__main__":
    main()
