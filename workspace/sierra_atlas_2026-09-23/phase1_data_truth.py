"""Phase 1: Sierra Archive Data Truth Audit.
Analyzes all 12 futures instruments + BTC Deribit + NQ tick/footprint.
Outputs detailed table and JSON summary.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

SIERRA_DIR = Path("data/sierra")
OUT_DIR = Path("workspace/sierra_atlas_2026-09-23")
OUT_DIR.mkdir(parents=True, exist_ok=True)

INSTRUMENTS = [
    ("NQ", "NQ_continuous_1m_latest_90d.parquet", 0.25, 20.0),
    ("MNQ", "MNQ_continuous_1m_latest_90d.parquet", 0.25, 2.0),
    ("ES", "ES_continuous_1m_latest_90d.parquet", 0.25, 50.0),
    ("MES", "MES_continuous_1m_latest_90d.parquet", 0.25, 5.0),
    ("GC", "GC_continuous_1m_latest_90d.parquet", 0.10, 100.0),
    ("MGC", "MGC_continuous_1m_latest_90d.parquet", 0.10, 10.0),
    ("CL", "CL_continuous_1m_latest_90d.parquet", 0.01, 1000.0),
    ("MCL", "MCL_continuous_1m_latest_90d.parquet", 0.01, 100.0),
    ("RTY", "RTY_continuous_1m_latest_90d.parquet", 0.10, 50.0),
    ("M2K", "M2K_continuous_1m_latest_90d.parquet", 0.10, 5.0),
    ("YM", "YM_continuous_1m_latest_90d.parquet", 1.0, 5.0),
    ("MYM", "MYM_continuous_1m_latest_90d.parquet", 1.0, 0.5),
    ("BTC_DERIBIT", "BTC_DERIBIT_perpetual_1m_latest_90d.parquet", 0.5, 1.0),
]

def audit_file(sym, fname, tick_size, point_val):
    fpath = SIERRA_DIR / fname
    if not fpath.exists():
        return {"symbol": sym, "error": f"File not found: {fname}"}
    
    df = pd.read_parquet(fpath)
    if not isinstance(df.index, pd.DatetimeIndex):
        if "ts" in df.columns:
            df["ts"] = pd.to_datetime(df["ts"])
            df.set_index("ts", inplace=True)
        else:
            df.index = pd.to_datetime(df.index)
    
    df = df.sort_index()
    n_rows = len(df)
    start_ts = df.index[0]
    end_ts = df.index[-1]
    
    # Missingness
    dt_diff = df.index.to_series().diff()
    gaps_gt_1m = (dt_diff > pd.Timedelta(minutes=1)).sum()
    max_gap_hours = dt_diff.max().total_seconds() / 3600.0 if not dt_diff.empty else 0.0
    
    # Sessions: CME trade date rolls at 17:00 or 18:00 ET. In UTC, 22:00 or 23:00.
    # Group by date of (ts - 18h) to get Globex session date
    sessions = (df.index - pd.Timedelta(hours=18)).date
    n_sessions = len(np.unique(sessions))
    
    # Bid / Ask reconciliation
    reconciled_exact = (df["bid_volume"] + df["ask_volume"] == df["volume"]).all()
    pct_exact = (df["bid_volume"] + df["ask_volume"] == df["volume"]).mean() * 100.0
    delta_exact = (df["delta"] == (df["ask_volume"] - df["bid_volume"])).all()
    
    # Volume statistics
    total_vol = int(df["volume"].sum())
    total_bid_vol = int(df["bid_volume"].sum())
    total_ask_vol = int(df["ask_volume"].sum())
    total_delta = int(df["delta"].sum())
    
    # Zero volume bars
    zero_vol_bars = (df["volume"] == 0).sum()
    zero_vol_pct = (zero_vol_bars / n_rows) * 100.0
    
    # Session volume distribution (UTC hours)
    # Overnight/Asia: 22:00-06:00 UTC
    # European/US Overlap: 07:00-13:30 UTC
    # US RTH: 13:30-20:00 UTC
    # Maintenance/Closed: 20:00-22:00 UTC
    utc_hours = df.index.hour
    utc_mins = df.index.minute
    
    is_overnight = (utc_hours >= 22) | (utc_hours < 7)
    is_europe = (utc_hours >= 7) & ((utc_hours < 13) | ((utc_hours == 13) & (utc_mins < 30)))
    is_rth = ((utc_hours == 13) & (utc_mins >= 30)) | ((utc_hours > 13) & (utc_hours < 20))
    is_maint = (utc_hours >= 20) & (utc_hours < 22)
    
    vol_overnight = df.loc[is_overnight, "volume"].sum()
    vol_europe = df.loc[is_europe, "volume"].sum()
    vol_rth = df.loc[is_rth, "volume"].sum()
    vol_maint = df.loc[is_maint, "volume"].sum()
    
    # Contract rolls check: look for large price jumps across 1m bars
    # In continuous volume-based rollover, roll occurs when volume in next contract exceeds front
    ret = df["close"].pct_change()
    extreme_jumps = (ret.abs() > 0.02).sum() # >2% 1m return
    
    return {
        "symbol": sym,
        "rows": n_rows,
        "start_utc": str(start_ts),
        "end_utc": str(end_ts),
        "sessions": int(n_sessions),
        "total_volume": total_vol,
        "total_delta": total_delta,
        "zero_vol_bars": int(zero_vol_bars),
        "zero_vol_pct": round(zero_vol_pct, 2),
        "reconciled_exact": bool(reconciled_exact),
        "pct_exact": round(pct_exact, 4),
        "delta_exact": bool(delta_exact),
        "gaps_gt_1m": int(gaps_gt_1m),
        "max_gap_hours": round(max_gap_hours, 2),
        "vol_shares_pct": {
            "overnight_asia": round(vol_overnight / max(1, total_vol) * 100.0, 2),
            "europe_premarket": round(vol_europe / max(1, total_vol) * 100.0, 2),
            "us_rth": round(vol_rth / max(1, total_vol) * 100.0, 2),
            "maint_close": round(vol_maint / max(1, total_vol) * 100.0, 2),
        },
        "extreme_jumps_gt_2pct": int(extreme_jumps),
        "tick_size": tick_size,
        "point_val": point_val,
    }

def main():
    results = []
    print("Auditing 1m series...")
    for sym, fname, tick, pt in INSTRUMENTS:
        res = audit_file(sym, fname, tick, pt)
        results.append(res)
        print(f"  {sym:12s}: {res['rows']} rows, {res['sessions']} sessions, {res['total_volume']:,} vol, exact: {res['reconciled_exact']}")
    
    # Also audit NQ tick files & footprint
    print("\nAuditing NQ tick & footprint files...")
    tick_dir = SIERRA_DIR / "tick"
    tick_files = [
        ("NQM26_tick", "NQM26_CME_1tick_full.parquet"),
        ("NQU26_tick", "NQU26_CME_1tick_full.parquet"),
        ("NQZ26_tick", "NQZ26_CME_1tick_full.parquet"),
        ("NQ_cont_fp", "NQ_continuous_1m_footprint.parquet"),
    ]
    tick_res = {}
    for name, f in tick_files:
        p = tick_dir / f
        if p.exists():
            df_t = pd.read_parquet(p)
            tick_res[name] = {
                "records": len(df_t),
                "cols": list(df_t.columns),
                "start": str(df_t.index[0]) if isinstance(df_t.index, pd.DatetimeIndex) else str(df_t.iloc[0, 0]),
                "end": str(df_t.index[-1]) if isinstance(df_t.index, pd.DatetimeIndex) else str(df_t.iloc[-1, 0]),
            }
            print(f"  {name:12s}: {len(df_t):,} records, cols: {list(df_t.columns)}")
    
    out_data = {
        "bar_series": results,
        "nq_tick_and_footprint": tick_res,
    }
    
    out_file = OUT_DIR / "phase1_data_truth.json"
    with open(out_file, "w") as f:
        json.dump(out_data, f, indent=2)
    print(f"\nWrote results to {out_file}")

if __name__ == "__main__":
    main()
