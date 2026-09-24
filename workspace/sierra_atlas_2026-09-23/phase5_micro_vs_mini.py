"""Phase 5: Micro vs Mini Information & Lead-Lag Analysis.
Compares 6 pairs of CME futures contracts:
NQ vs MNQ, ES vs MES, GC vs MGC, CL vs MCL, RTY vs M2K, YM vs MYM.
Analyzes:
1. Contract & notional volume shares
2. Contemporaneous return & signed delta correlation
3. Asymmetric cross-lag: Does Mini lead Micro or Micro lead Mini?
4. Incremental information: Does Micro flow predict forward Mini returns beyond Mini flow?
5. Noise & basis tracking error.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

SIERRA_DIR = Path("data/sierra")
OUT_DIR = Path("workspace/sierra_atlas_2026-09-23")

MINI_MICRO_PAIRS = [
    ("NQ", "MNQ", "NQ_continuous_1m_latest_90d.parquet", "MNQ_continuous_1m_latest_90d.parquet", 0.25, 0.1),
    ("ES", "MES", "ES_continuous_1m_latest_90d.parquet", "MES_continuous_1m_latest_90d.parquet", 0.25, 0.1),
    ("GC", "MGC", "GC_continuous_1m_latest_90d.parquet", "MGC_continuous_1m_latest_90d.parquet", 0.10, 0.1),
    ("CL", "MCL", "CL_continuous_1m_latest_90d.parquet", "MCL_continuous_1m_latest_90d.parquet", 0.01, 0.1),
    ("RTY", "M2K", "RTY_continuous_1m_latest_90d.parquet", "M2K_continuous_1m_latest_90d.parquet", 0.10, 0.1),
    ("YM", "MYM", "YM_continuous_1m_latest_90d.parquet", "MYM_continuous_1m_latest_90d.parquet", 1.0, 0.1),
]

def analyze_pair(mini_sym, micro_sym, mini_file, micro_file, tick_size, micro_ratio):
    df_mini = pd.read_parquet(SIERRA_DIR / mini_file)
    df_micro = pd.read_parquet(SIERRA_DIR / micro_file)
    
    if not isinstance(df_mini.index, pd.DatetimeIndex):
        df_mini.index = pd.to_datetime(df_mini.index)
    if not isinstance(df_micro.index, pd.DatetimeIndex):
        df_micro.index = pd.to_datetime(df_micro.index)
        
    common_idx = df_mini.index.intersection(df_micro.index)
    m = df_mini.loc[common_idx]
    u = df_micro.loc[common_idx]
    
    n_common = len(common_idx)
    
    vol_mini = float(m["volume"].sum())
    vol_micro = float(u["volume"].sum())
    contract_share_micro = vol_micro / (vol_mini + vol_micro) * 100.0
    
    # Notional volume share (micro is micro_ratio of mini notional)
    notional_mini = vol_mini * 1.0
    notional_micro = vol_micro * micro_ratio
    notional_share_micro = notional_micro / (notional_mini + notional_micro) * 100.0
    
    # Returns
    r_mini = ((m["close"] - m["open"]) / m["open"]) * 10000.0
    r_micro = ((u["close"] - u["open"]) / u["open"]) * 10000.0
    ret_corr, _ = stats.pearsonr(r_mini, r_micro)
    
    # Deltas
    d_mini = m["delta"].astype(float)
    d_micro = u["delta"].astype(float)
    delta_corr, _ = stats.spearmanr(d_mini, d_micro)
    
    # Tracking error (Close differences in ticks)
    diff_ticks = (m["close"] - u["close"]).abs() / tick_size
    mean_diff_ticks = float(diff_ticks.mean())
    p95_diff_ticks = float(diff_ticks.quantile(0.95))
    
    # Lead-lag: Cross-correlation of delta(t) and forward return(t+1)
    fwd_r_mini = ((m["close"].shift(-1) - m["close"]) / m["close"]) * 10000.0
    fwd_r_micro = ((u["close"].shift(-1) - u["close"]) / u["close"]) * 10000.0
    
    valid = fwd_r_mini.notna() & fwd_r_micro.notna() & d_mini.notna() & d_micro.notna()
    
    # Does Mini delta lead Micro return?
    rho_mini_lead, p_mini_lead = stats.spearmanr(d_mini[valid], fwd_r_micro[valid])
    # Does Micro delta lead Mini return?
    rho_micro_lead, p_micro_lead = stats.spearmanr(d_micro[valid], fwd_r_mini[valid])
    
    # Incremental information test:
    # Regression of Mini forward return on Mini delta (M0) vs Mini delta + Micro delta (M1)
    y = fwd_r_mini[valid].values
    X0 = np.column_stack([np.ones(len(y)), d_mini[valid].values])
    X1 = np.column_stack([np.ones(len(y)), d_mini[valid].values, d_micro[valid].values])
    
    beta0 = np.linalg.lstsq(X0, y, rcond=None)[0]
    beta1 = np.linalg.lstsq(X1, y, rcond=None)[0]
    
    r2_0 = 1.0 - np.sum((y - X0 @ beta0)**2) / np.sum((y - np.mean(y))**2)
    r2_1 = 1.0 - np.sum((y - X1 @ beta1)**2) / np.sum((y - np.mean(y))**2)
    delta_r2 = max(0.0, r2_1 - r2_0)
    
    # Micro delta t-stat in M1
    resid1 = y - X1 @ beta1
    s2 = np.sum(resid1**2) / (len(y) - 3)
    cov1 = s2 * np.linalg.inv(X1.T @ X1)
    se_micro = np.sqrt(cov1[2, 2])
    t_micro = beta1[2] / (se_micro + 1e-12)
    
    return {
        "pair": f"{mini_sym}_vs_{micro_sym}",
        "n_common_bars": int(n_common),
        "vol_mini_contracts": int(vol_mini),
        "vol_micro_contracts": int(vol_micro),
        "contract_share_micro_pct": round(contract_share_micro, 2),
        "notional_share_micro_pct": round(notional_share_micro, 2),
        "return_correlation": round(float(ret_corr), 4),
        "delta_correlation": round(float(delta_corr), 4),
        "mean_diff_ticks": round(mean_diff_ticks, 3),
        "p95_diff_ticks": round(p95_diff_ticks, 3),
        "mini_leads_micro_rho": round(float(rho_mini_lead), 4),
        "micro_leads_mini_rho": round(float(rho_micro_lead), 4),
        "micro_incremental_delta_r2": round(float(delta_r2), 7),
        "micro_incremental_t": round(float(t_micro), 2),
        "verdict": "MICRO_FOLLOWS_MINI" if abs(rho_mini_lead) >= abs(rho_micro_lead) and delta_r2 < 0.0001 else "MICRO_CONTAINS_INDEPENDENT_INFO",
    }

def main():
    print("Running Phase 5 Mini vs Micro Information Analysis...")
    results = {}
    for mini_s, micro_s, mini_f, micro_f, tick, ratio in MINI_MICRO_PAIRS:
        pair_res = analyze_pair(mini_s, micro_s, mini_f, micro_f, tick, ratio)
        results[f"{mini_s}_{micro_s}"] = pair_res
        print(f"\n{pair_res['pair']}:")
        print(f"  Vol share: {pair_res['contract_share_micro_pct']:.1f}% contracts, {pair_res['notional_share_micro_pct']:.1f}% notional")
        print(f"  Return corr: {pair_res['return_correlation']:.4f} | Delta corr: {pair_res['delta_correlation']:.4f}")
        print(f"  Tracking error: mean {pair_res['mean_diff_ticks']:.2f} ticks, p95 {pair_res['p95_diff_ticks']:.2f} ticks")
        print(f"  Mini leads Micro rho: {pair_res['mini_leads_micro_rho']:+.4f} vs Micro leads Mini rho: {pair_res['micro_leads_mini_rho']:+.4f}")
        print(f"  Micro incremental delta R^2: {pair_res['micro_incremental_delta_r2']:.7f} (t={pair_res['micro_incremental_t']:+5.2f})")
        print(f"  Verdict: {pair_res['verdict']}")
        
    out_file = OUT_DIR / "phase5_micro_vs_mini.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nPhase 5 results saved to {out_file}")

if __name__ == "__main__":
    main()
