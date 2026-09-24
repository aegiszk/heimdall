"""Phase 2: Microstructure Response Atlas.
Evaluates the 8 pre-declared microstructure features across 6 primary CME futures:
NQ, ES, GC, CL, RTY, YM.
Measures forward markouts at horizons h in [1, 2, 5, 15, 30] minutes.
Reports effect size, standard error, t-stat, Q10-Q1 spread, and sub-period stability (H1 vs H2).
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

SIERRA_DIR = Path("data/sierra")
OUT_DIR = Path("workspace/sierra_atlas_2026-09-23")

PRIMARY_INSTRUMENTS = [
    ("NQ", "NQ_continuous_1m_latest_90d.parquet", 0.25, 20.0),
    ("ES", "ES_continuous_1m_latest_90d.parquet", 0.25, 50.0),
    ("GC", "GC_continuous_1m_latest_90d.parquet", 0.10, 100.0),
    ("CL", "CL_continuous_1m_latest_90d.parquet", 0.01, 1000.0),
    ("RTY", "RTY_continuous_1m_latest_90d.parquet", 0.10, 50.0),
    ("YM", "YM_continuous_1m_latest_90d.parquet", 1.0, 5.0),
]

HORIZONS = [1, 2, 5, 15, 30]

def compute_features(df, tick_size):
    """Pre-declared 8 features:
    A: signed aggressor imbalance: delta / volume
    B: normalized delta: delta / (rolling 60m std of delta)
    C: trade intensity: volume / (rolling 60m mean of volume)
    D: volume concentration: volume / (high - low + tick_size)
    E: price impact per signed volume: (close - open) / (delta.replace(0, np.nan))
    F: absorption proxy: high volume (intensity > 1.5) with small bar body relative to range.
       Signed by delta: sign(delta) * (1 - abs(close - open) / (high - low + tick_size))
    G: return continuation: (close - open) / close
    H: illiquidity proxy (Amihud): abs(close - open) / (volume * close + 1e-6)
    """
    vol = df["volume"].astype(float)
    delta = df["delta"].astype(float)
    c = df["close"].astype(float)
    o = df["open"].astype(float)
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    
    features = pd.DataFrame(index=df.index)
    
    # A. Aggressor imbalance
    features["F_A_imbalance"] = delta / np.maximum(vol, 1.0)
    
    # B. Normalized delta (trailing 60 bars)
    roll_delta_std = delta.rolling(60, min_periods=20).std().replace(0, np.nan)
    features["F_B_norm_delta"] = (delta / roll_delta_std).clip(-5.0, 5.0)
    
    # C. Trade intensity
    roll_vol_mean = vol.rolling(60, min_periods=20).mean().replace(0, np.nan)
    features["F_C_intensity"] = (vol / roll_vol_mean).clip(0.0, 10.0)
    
    # D. Volume concentration
    bar_range = (h - l) + tick_size
    features["F_D_vol_conc"] = vol / bar_range
    # Normalized concentration
    roll_conc_mean = features["F_D_vol_conc"].rolling(60, min_periods=20).mean().replace(0, np.nan)
    features["F_D_norm_conc"] = (features["F_D_vol_conc"] / roll_conc_mean).clip(0.0, 10.0)
    
    # E. Price impact per signed unit: tick move per 100 contracts delta
    price_change_ticks = (c - o) / tick_size
    features["F_E_impact"] = np.where(delta.abs() >= 10, price_change_ticks / (delta / 100.0), np.nan)
    features["F_E_impact"] = features["F_E_impact"].clip(-20.0, 20.0)
    
    # F. Absorption proxy:
    # High volume (intensity > 1.5) with small body (exhaustion / absorption)
    body_ratio = (c - o).abs() / bar_range
    features["F_F_absorption"] = np.where(
        features["F_C_intensity"] > 1.5,
        np.sign(delta) * (1.0 - body_ratio),
        0.0
    )
    
    # G. Return continuation: bar return in basis points
    features["F_G_bar_ret_bps"] = ((c - o) / o) * 10000.0
    
    # H. Amihud illiquidity: basis points moved per 1,000 contracts
    features["F_H_illiquidity"] = (features["F_G_bar_ret_bps"].abs() / np.maximum(vol / 1000.0, 0.01)).clip(0, 100.0)
    
    return features

def evaluate_response(series_feat, forward_ret, n_subsets=2):
    """Computes correlation, regression t-stat, Q10-Q1 spread, and sub-period stability."""
    mask = series_feat.notna() & forward_ret.notna() & np.isfinite(series_feat) & np.isfinite(forward_ret)
    x = series_feat[mask]
    y = forward_ret[mask]
    n = len(x)
    if n < 500:
        return None
    
    corr, pval = stats.spearmanr(x, y)
    
    # OLS slope and robust t-stat
    slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
    t_stat = slope / (std_err + 1e-12)
    
    # Decile spread: top 10% vs bottom 10%
    q10_cut = x.quantile(0.90)
    q1_cut = x.quantile(0.10)
    y_q10 = y[x >= q10_cut].mean()
    y_q1 = y[x <= q1_cut].mean()
    q_spread = y_q10 - y_q1
    
    # Sub-period stability (H1 vs H2)
    half = n // 2
    x_h1, y_h1 = x.iloc[:half], y.iloc[:half]
    x_h2, y_h2 = x.iloc[half:], y.iloc[half:]
    corr_h1, _ = stats.spearmanr(x_h1, y_h1)
    corr_h2, _ = stats.spearmanr(x_h2, y_h2)
    stable = (np.sign(corr_h1) == np.sign(corr_h2)) and (abs(corr_h1) > 0.005) and (abs(corr_h2) > 0.005)
    
    return {
        "n": int(n),
        "spearman_rho": round(float(corr), 4),
        "p_value": float(pval),
        "t_stat": round(float(t_stat), 2),
        "q10_mean_bps": round(float(y_q10), 3),
        "q1_mean_bps": round(float(y_q1), 3),
        "q_spread_bps": round(float(q_spread), 3),
        "rho_h1": round(float(corr_h1), 4),
        "rho_h2": round(float(corr_h2), 4),
        "stable_sign": bool(stable),
    }

def main():
    atlas = {}
    print("Computing Microstructure Response Atlas for 6 CME Futures...")
    
    for sym, fname, tick, pt in PRIMARY_INSTRUMENTS:
        print(f"\nProcessing {sym}...")
        df = pd.read_parquet(SIERRA_DIR / fname)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Forward returns in basis points
        c = df["close"].astype(float)
        fwd_returns = {}
        for h in HORIZONS:
            # Shift backwards: close(t+h) / close(t) - 1
            fwd_returns[h] = ((c.shift(-h) - c) / c) * 10000.0
        
        features = compute_features(df, tick)
        
        sym_res = {}
        for f_name in features.columns:
            sym_res[f_name] = {}
            for h in HORIZONS:
                res = evaluate_response(features[f_name], fwd_returns[h])
                if res is not None:
                    sym_res[f_name][f"h_{h}m"] = res
                    if h in (1, 5, 15):
                        print(f"  {f_name:18s} h={h:2d}m: rho={res['spearman_rho']:+.4f} (t={res['t_stat']:+5.1f}), spread={res['q_spread_bps']:+5.2f} bps, stable={res['stable_sign']}")
        atlas[sym] = sym_res

    out_file = OUT_DIR / "phase2_response_atlas.json"
    with open(out_file, "w") as f:
        json.dump(atlas, f, indent=2)
    print(f"\nResponse atlas saved to {out_file}")

if __name__ == "__main__":
    main()
