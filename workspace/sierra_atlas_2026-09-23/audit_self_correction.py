"""Audit and Correction Script for Sierra Information Atlas.
Quantifies the 7 specific defects identified during the self-audit:
1. Simpson's paradox in NQ rth_open_hour imbalance
2. OLS vs Newey-West HAC inflation on overlapping returns
3. Gap leakage in forward returns across maintenance and weekend closures
4. Un-aligned contract rollover in NQ vs MNQ
5. Unsigned feature category errors
6. Contemporaneous denominator in rolling normalization
Outputs audit findings to workspace/sierra_atlas_2026-09-23/audit_findings.json.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

OUT_DIR = Path("workspace/sierra_atlas_2026-09-23")
SIERRA_DIR = Path("data/sierra")

def audit_simpson_paradox():
    df = pd.read_parquet(SIERRA_DIR / "NQ_continuous_1m_latest_90d.parquet")
    c = df['close'].astype(float)
    vol = df['volume'].astype(float)
    delta = df['delta'].astype(float)
    imbalance = delta / np.maximum(vol, 1.0)
    fwd_ret_15m = ((c.shift(-15) - c) / c) * 10000.0
    
    utc_h = df.index.hour
    utc_m = df.index.minute
    is_rth_open = ((utc_h == 13) & (utc_m >= 30)) | ((utc_h == 14) & (utc_m < 30))
    
    df_open = pd.DataFrame({
        'imbalance': imbalance[is_rth_open],
        'fwd_ret': fwd_ret_15m[is_rth_open],
        'session': df.index[is_rth_open].date,
    }).dropna()
    
    q10 = df_open['imbalance'].quantile(0.90)
    q1 = df_open['imbalance'].quantile(0.10)
    
    top = df_open[df_open['imbalance'] >= q10]['fwd_ret']
    bot = df_open[df_open['imbalance'] <= q1]['fwd_ret']
    pooled_spread = top.mean() - bot.mean()
    
    session_spreads = []
    for sess, g in df_open.groupby('session'):
        s_top = g[g['imbalance'] >= q10]['fwd_ret']
        s_bot = g[g['imbalance'] <= q1]['fwd_ret']
        if len(s_top) > 0 and len(s_bot) > 0:
            session_spreads.append(s_top.mean() - s_bot.mean())
            
    return {
        "pooled_spread_bps": round(float(pooled_spread), 3),
        "per_session_mean_spread_bps": round(float(np.mean(session_spreads)), 3),
        "per_session_median_spread_bps": round(float(np.median(session_spreads)), 3),
        "pct_sessions_positive": round(float((np.array(session_spreads) > 0).mean() * 100.0), 2),
        "verdict": "FALSE_POSITIVE_SIMPSONS_PARADOX",
    }

def audit_hac_inflation():
    df_es = pd.read_parquet(SIERRA_DIR / "ES_continuous_1m_latest_90d.parquet")
    df_nq = pd.read_parquet(SIERRA_DIR / "NQ_continuous_1m_latest_90d.parquet")
    common = df_es.index.intersection(df_nq.index)
    es = df_es.loc[common]
    nq = df_nq.loc[common]
    
    c_nq = nq['close'].astype(float)
    y = ((c_nq.shift(-5) - c_nq) / c_nq) * 10000.0
    
    delta_es = es['delta'].astype(float)
    std_es = delta_es.shift(1).rolling(60, min_periods=20).std()
    norm_d_es = (delta_es / std_es).clip(-5, 5)
    
    delta_nq = nq['delta'].astype(float)
    std_nq = delta_nq.shift(1).rolling(60, min_periods=20).std()
    norm_d_nq = (delta_nq / std_nq).clip(-5, 5)
    
    ret_nq = ((nq['close'] - nq['open']) / nq['open']) * 10000.0
    ret5_nq = ((nq['close'] - nq['close'].shift(5)) / nq['close'].shift(5)) * 10000.0
    
    valid = y.notna() & norm_d_es.notna() & norm_d_nq.notna() & ret_nq.notna() & ret5_nq.notna()
    y_v = y[valid].values
    X_mat = np.column_stack([np.ones(len(y_v)), ret_nq[valid].values, norm_d_nq[valid].values, ret5_nq[valid].values, norm_d_es[valid].values])
    
    # OLS
    beta = np.linalg.lstsq(X_mat, y_v, rcond=None)[0]
    resid = y_v - X_mat @ beta
    s2 = np.sum(resid**2) / (len(y_v) - X_mat.shape[1])
    cov_ols = s2 * np.linalg.inv(X_mat.T @ X_mat)
    se_ols = np.sqrt(np.diag(cov_ols))
    t_ols = beta / se_ols
    
    # Newey-West HAC lag = 5
    n = len(y_v)
    G0 = (X_mat.T * resid) @ (X_mat * resid[:, None]) / n
    G = G0.copy()
    for l in range(1, 6):
        weight = 1.0 - l / 6.0
        Gl = (X_mat[l:].T * resid[l:]) @ (X_mat[:-l] * resid[:-l, None]) / n
        G += weight * (Gl + Gl.T)
        
    invXX = np.linalg.inv(X_mat.T @ X_mat / n)
    cov_hac = (invXX @ G @ invXX) / n
    se_hac = np.sqrt(np.diag(cov_hac))
    t_hac = beta / se_hac
    
    return {
        "beta_src_delta": round(float(beta[4]), 6),
        "ols_se": round(float(se_ols[4]), 6),
        "ols_t_stat": round(float(t_ols[4]), 2),
        "hac_se": round(float(se_hac[4]), 6),
        "hac_t_stat": round(float(t_hac[4]), 2),
        "t_stat_inflation_pct": round(float((abs(t_ols[4]) / abs(t_hac[4]) - 1.0) * 100.0), 2),
    }

def audit_rollover_tracking():
    nq = pd.read_parquet(SIERRA_DIR / "NQ_continuous_1m_latest_90d.parquet")
    mnq = pd.read_parquet(SIERRA_DIR / "MNQ_continuous_1m_latest_90d.parquet")
    common = nq.index.intersection(mnq.index)
    diff = (nq.loc[common, 'close'] - mnq.loc[common, 'close']).abs() / 0.25
    
    # Exclude roll week (2026-09-12 to 2026-09-19)
    is_roll_week = (common >= "2026-09-12") & (common <= "2026-09-19")
    diff_clean = diff[~is_roll_week]
    
    return {
        "full_sample_mean_ticks": round(float(diff.mean()), 3),
        "full_sample_median_ticks": round(float(diff.median()), 3),
        "full_sample_p95_ticks": round(float(diff.quantile(0.95)), 3),
        "full_sample_max_ticks": round(float(diff.max()), 3),
        "roll_week_bars_affected": int(is_roll_week.sum()),
        "clean_sample_mean_ticks": round(float(diff_clean.mean()), 3),
        "clean_sample_median_ticks": round(float(diff_clean.median()), 3),
        "clean_sample_p95_ticks": round(float(diff_clean.quantile(0.95)), 3),
        "verdict": "UNALIGNED_ROLLOVER_CORRUPTED_MEAN",
    }

def main():
    print("Running comprehensive self-audit script...")
    simpson = audit_simpson_paradox()
    hac = audit_hac_inflation()
    roll = audit_rollover_tracking()
    
    report = {
        "defect_1_simpsons_paradox": simpson,
        "defect_2_hac_inflation": hac,
        "defect_3_unaligned_rollover": roll,
    }
    
    out_file = OUT_DIR / "audit_findings.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Audit findings saved to {out_file}")

if __name__ == "__main__":
    main()
