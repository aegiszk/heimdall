"""Phase 4: Cross-Instrument Information & Lead-Lag Atlas.
Measures whether source market flow at minute t adds incremental predictive power
for target market forward return r(t -> t+h) beyond target market's own state at t.
Strict lagging: all features are known at the close of minute t. Target return is close(t+h) - close(t).
Includes time-shift / shuffle placebo controls.
Pairs tested:
NQ -> ES, ES -> NQ
RTY -> ES, ES -> RTY
YM -> ES, YM -> NQ
CL -> GC, GC -> CL
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

SIERRA_DIR = Path("data/sierra")
OUT_DIR = Path("workspace/sierra_atlas_2026-09-23")

PAIRS = [
    ("NQ", "ES", "NQ_continuous_1m_latest_90d.parquet", "ES_continuous_1m_latest_90d.parquet", 0.25, 0.25),
    ("ES", "NQ", "ES_continuous_1m_latest_90d.parquet", "NQ_continuous_1m_latest_90d.parquet", 0.25, 0.25),
    ("RTY", "ES", "RTY_continuous_1m_latest_90d.parquet", "ES_continuous_1m_latest_90d.parquet", 0.10, 0.25),
    ("ES", "RTY", "ES_continuous_1m_latest_90d.parquet", "RTY_continuous_1m_latest_90d.parquet", 0.25, 0.10),
    ("YM", "ES", "YM_continuous_1m_latest_90d.parquet", "ES_continuous_1m_latest_90d.parquet", 1.0, 0.25),
    ("YM", "NQ", "YM_continuous_1m_latest_90d.parquet", "NQ_continuous_1m_latest_90d.parquet", 1.0, 0.25),
    ("CL", "GC", "CL_continuous_1m_latest_90d.parquet", "GC_continuous_1m_latest_90d.parquet", 0.01, 0.10),
    ("GC", "CL", "GC_continuous_1m_latest_90d.parquet", "CL_continuous_1m_latest_90d.parquet", 0.10, 0.01),
]

HORIZONS = [1, 2, 5]

def get_clean_series(fname):
    df = pd.read_parquet(SIERRA_DIR / fname)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    
    vol = df["volume"].astype(float)
    delta = df["delta"].astype(float)
    c = df["close"].astype(float)
    o = df["open"].astype(float)
    
    roll_delta_std = delta.rolling(60, min_periods=20).std().replace(0, np.nan)
    norm_delta = (delta / roll_delta_std).clip(-5.0, 5.0)
    bar_ret = ((c - o) / o) * 10000.0
    ret_5m = ((c - c.shift(5)) / c.shift(5)) * 10000.0
    
    res = pd.DataFrame(index=df.index)
    res["close"] = c
    res["bar_ret"] = bar_ret
    res["ret_5m"] = ret_5m
    res["norm_delta"] = norm_delta
    return res

def fit_ols(y, X):
    """Fit OLS using numpy QR decomposition. Return R^2, coefs, t-stats."""
    # Add constant
    X_mat = np.column_stack([np.ones(len(y)), X])
    q, r = np.linalg.qr(X_mat)
    beta = np.linalg.solve(r, q.T @ y)
    
    y_hat = X_mat @ beta
    resid = y - y_hat
    n, k = X_mat.shape
    r2 = 1.0 - (np.sum(resid**2) / np.sum((y - np.mean(y))**2))
    
    s2 = np.sum(resid**2) / (n - k)
    cov = s2 * np.linalg.inv(r.T @ r)
    se = np.sqrt(np.diag(cov))
    t_stats = beta / (se + 1e-12)
    return r2, beta, t_stats

def test_pair(src_sym, tgt_sym, src_file, tgt_file, h_list):
    src = get_clean_series(src_file)
    tgt = get_clean_series(tgt_file)
    
    # Intersect timestamps
    common_idx = src.index.intersection(tgt.index)
    src = src.loc[common_idx]
    tgt = tgt.loc[common_idx]
    
    pair_res = {}
    
    for h in h_list:
        y = ((tgt["close"].shift(-h) - tgt["close"]) / tgt["close"]) * 10000.0
        
        # M0 features (target's own state)
        X0 = np.column_stack([tgt["bar_ret"], tgt["norm_delta"], tgt["ret_5m"]])
        
        # M1 features (target's own state + source's state)
        X1 = np.column_stack([tgt["bar_ret"], tgt["norm_delta"], tgt["ret_5m"], src["bar_ret"], src["norm_delta"]])
        
        valid = (
            np.isfinite(y) &
            np.all(np.isfinite(X0), axis=1) &
            np.all(np.isfinite(X1), axis=1)
        )
        
        y_v = y[valid].values
        X0_v = X0[valid]
        X1_v = X1[valid]
        n = len(y_v)
        
        r2_0, b0, t0 = fit_ols(y_v, X0_v)
        r2_1, b1, t1 = fit_ols(y_v, X1_v)
        delta_r2 = max(0.0, r2_1 - r2_0)
        
        # Source coefs are index 4 and 5 in X1 (beta 0 is intercept, 1=tgt_ret, 2=tgt_delta, 3=tgt_5m, 4=src_ret, 5=src_delta)
        src_ret_t = float(t1[4])
        src_delta_t = float(t1[5])
        
        # Placebo test: shuffle source features
        np.random.seed(42)
        X1_placebo = X1_v.copy()
        X1_placebo[:, 3] = np.random.permutation(X1_placebo[:, 3])
        X1_placebo[:, 4] = np.random.permutation(X1_placebo[:, 4])
        r2_p, _, t_p = fit_ols(y_v, X1_placebo)
        delta_r2_placebo = max(0.0, r2_p - r2_0)
        
        pair_res[f"h_{h}m"] = {
            "n": int(n),
            "r2_M0": round(float(r2_0), 6),
            "r2_M1": round(float(r2_1), 6),
            "delta_r2": round(float(delta_r2), 6),
            "delta_r2_placebo": round(float(delta_r2_placebo), 6),
            "src_ret_t": round(src_ret_t, 2),
            "src_delta_t": round(src_delta_t, 2),
            "passes_placebo": bool(delta_r2 > delta_r2_placebo and abs(src_delta_t) > 2.0),
        }
        
    return pair_res

def main():
    print("Running Phase 4 Cross-Instrument Information & Lead-Lag Analysis...")
    all_pairs = {}
    for src_sym, tgt_sym, src_f, tgt_f, _, _ in PAIRS:
        pair_name = f"{src_sym}->{tgt_sym}"
        print(f"Testing {pair_name}...")
        res = test_pair(src_sym, tgt_sym, src_f, tgt_f, HORIZONS)
        all_pairs[pair_name] = res
        for h in [1, 5]:
            hr = res[f"h_{h}m"]
            print(f"  h={h}m: delta_R2={hr['delta_r2']:.6f} vs plac={hr['delta_r2_placebo']:.6f} | src_delta_t={hr['src_delta_t']:+5.2f} | passes={hr['passes_placebo']}")
    
    out_file = OUT_DIR / "phase4_cross_instrument.json"
    with open(out_file, "w") as f:
        json.dump(all_pairs, f, indent=2)
    print(f"\nCross-instrument results saved to {out_file}")

if __name__ == "__main__":
    main()
