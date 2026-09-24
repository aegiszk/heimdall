"""
Sierra Chart CSV ingestion -> Heimdall standard schema.
Drop-in alongside core/data/history.py (Databento path). Produces the SAME columns
so downstream funnel/battery code doesn't care which source fed it.

Observed Sierra ``Export Bar Data to Text File`` columns:
  Date, Time, Open, High, Low, Last, Volume, NumberOfTrades, BidVolume, AskVolume

Bar-data timestamps follow the chart time zone. This POC chart was verified to
be UTC; callers can override ``tz_source`` if the chart setting changes.

Output schema (matches core/data/history.py convention):
  ts (UTC), open, high, low, close, volume, bid_volume, ask_volume, delta (=ask-bid)
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path

# Adjust these to match your ACTUAL Sierra export header row -- do not assume.
COLMAP = {
    "Date": "date", "Time": "time",
    "Open": "open", "High": "high", "Low": "low", "Last": "close",
    "Volume": "volume", "BidVolume": "bid_volume", "AskVolume": "ask_volume",
}

def load_sierra_csv(path: str, tz_source: str = "UTC") -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Sierra export not found: {path}")
    df = pd.read_csv(p, skipinitialspace=True)
    missing = [c for c in COLMAP if c not in df.columns]
    if missing:
        raise ValueError(
            f"Sierra CSV missing expected columns {missing}. "
            f"Actual columns found: {list(df.columns)}. "
            f"Fix COLMAP in this file to match your real export header before trusting any output."
        )
    df = df.rename(columns=COLMAP)
    df["ts"] = pd.to_datetime(df["date"] + " " + df["time"])
    df["ts"] = df["ts"].dt.tz_localize(tz_source).dt.tz_convert("UTC")
    df = df.drop(columns=["date", "time"]).set_index("ts").sort_index()

    if not {"bid_volume", "ask_volume"}.issubset(df.columns):
        raise ValueError("No real bid_volume/ask_volume columns present -- export did NOT "
                         "give split buy/sell data. This POC has failed; do not scale up.")

    df["delta"] = df["ask_volume"] - df["bid_volume"]
    # Sanity: bid+ask should roughly equal total volume (small mismatches ok, big ones = bad export)
    recon_err = (df["bid_volume"] + df["ask_volume"] - df["volume"]).abs()
    bad_pct = (recon_err > df["volume"] * 0.05).mean() * 100
    print(f"[sanity] rows={len(df)} range={df.index.min()}->{df.index.max()} "
          f"bid+ask vs total volume mismatch >5%: {bad_pct:.2f}% of rows "
          f"(should be near 0%; if high, the export is NOT reliable delta data)")
    return df[
        ["open", "high", "low", "close", "volume", "bid_volume", "ask_volume", "delta"]
    ]

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python sierra_csv_loader.py <path_to_export.csv>")
        sys.exit(1)
    df = load_sierra_csv(sys.argv[1])
    print(df.head(10))
    print(f"\nTotal rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
