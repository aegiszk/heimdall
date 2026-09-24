"""Phase 3: Session Dependence Atlas.
Measures microstructure feature responses across 5 distinct structural trading sessions:
1. Overnight / Asia (22:00 - 07:00 UTC)
2. Europe / US Pre-market (07:00 - 13:30 UTC)
3. US RTH Open (13:30 - 14:30 UTC)
4. US RTH Midday (15:00 - 18:00 UTC)
5. US RTH Final Hour (19:00 - 20:00 UTC)
Focuses on NQ and ES at horizons h in [1, 5, 15] minutes.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

SIERRA_DIR = Path("data/sierra")
OUT_DIR = Path("workspace/sierra_atlas_2026-09-23")

TARGET_INSTRUMENTS = [
    ("NQ", "NQ_continuous_1m_latest_90d.parquet", 0.25, 20.0),
    ("ES", "ES_continuous_1m_latest_90d.parquet", 0.25, 50.0),
]

SESSIONS = {
    "overnight_asia": lambda h, m: (h >= 22) | (h < 7),
    "europe_premarket": lambda h, m: (h >= 7) & ((h < 13) | ((h == 13) & (m < 30))),
    "rth_open_hour": lambda h, m: ((h == 13) & (m >= 30)) | ((h == 14) & (m < 30)),
    "rth_midday": lambda h, m: (h >= 15) & (h < 18),
    "rth_final_hour": lambda h, m: (h == 19),
}

HORIZONS = [1, 5, 15]

def compute_core_features(df, tick_size):
    vol = df["volume"].astype(float)
    delta = df["delta"].astype(float)
    c = df["close"].astype(float)
    o = df["open"].astype(float)
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    bar_range = (h - l) + tick_size
    
    roll_vol = vol.rolling(60, min_periods=20).mean().replace(0, np.nan)
    roll_delta_std = delta.rolling(60, min_periods=20).std().replace(0, np.nan)
    
    features = pd.DataFrame(index=df.index)
    features["imbalance"] = delta / np.maximum(vol, 1.0)
    features["norm_delta"] = (delta / roll_delta_std).clip(-5.0, 5.0)
    features["intensity"] = (vol / roll_vol).clip(0.0, 10.0)
    body_ratio = (c - o).abs() / bar_range
    features["absorption"] = np.where(features["intensity"] > 1.5, np.sign(delta) * (1.0 - body_ratio), 0.0)
    features["bar_ret_bps"] = ((c - o) / o) * 10000.0
    return features

def run_session_analysis():
    session_results = {}
    print("Running Session Dependence Analysis for NQ and ES...")
    
    for sym, fname, tick, pt in TARGET_INSTRUMENTS:
        df = pd.read_parquet(SIERRA_DIR / fname)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        c = df["close"].astype(float)
        fwd_returns = {h: ((c.shift(-h) - c) / c) * 10000.0 for h in HORIZONS}
        features = compute_core_features(df, tick)
        
        utc_h = df.index.hour
        utc_m = df.index.minute
        
        sym_dict = {}
        for sess_name, sess_func in SESSIONS.items():
            sess_mask = sess_func(utc_h, utc_m)
            sess_dict = {}
            for feat_name in features.columns:
                sess_dict[feat_name] = {}
                feat_s = features[feat_name][sess_mask]
                for h in HORIZONS:
                    ret_s = fwd_returns[h][sess_mask]
                    valid = feat_s.notna() & ret_s.notna() & np.isfinite(feat_s) & np.isfinite(ret_s)
                    x = feat_s[valid]
                    y = ret_s[valid]
                    if len(x) < 200:
                        continue
                    
                    rho, pval = stats.spearmanr(x, y)
                    q10_cut = x.quantile(0.90)
                    q1_cut = x.quantile(0.10)
                    q_spread = y[x >= q10_cut].mean() - y[x <= q1_cut].mean()
                    
                    sess_dict[feat_name][f"h_{h}m"] = {
                        "n": int(len(x)),
                        "rho": round(float(rho), 4),
                        "p_value": float(pval),
                        "spread_bps": round(float(q_spread), 3),
                    }
            sym_dict[sess_name] = sess_dict
        session_results[sym] = sym_dict
    
    out_file = OUT_DIR / "phase3_session_dependence.json"
    with open(out_file, "w") as f:
        json.dump(session_results, f, indent=2)
    print(f"Session dependence saved to {out_file}")

if __name__ == "__main__":
    run_session_analysis()
