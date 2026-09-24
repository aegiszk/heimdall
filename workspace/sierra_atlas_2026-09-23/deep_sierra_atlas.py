"""Deep Sierra Information Content Atlas.
Analyzes the unexploited information in:
1. NQ 1-Tick records: Trade Size Stratification (Retail 1-lot vs Institutional >=10-lot Delta)
2. NQ 1m Footprint records: Volume Point of Control (POC) location & Trapped Traders at Extremes
3. Multi-Market 1m Series: Strict session-masked Cross-Asset Lead-Lag with Newey-West HAC
4. Non-linear tail threshold effects (99th percentile order flow extremes).
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

SIERRA_DIR = Path("data/sierra")
TICK_DIR = SIERRA_DIR / "tick"
OUT_DIR = Path("workspace/sierra_atlas_2026-09-23")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# MODULE 1: TRADE SIZE STRATIFICATION (TICK DATA)
# ---------------------------------------------------------------------------
def analyze_trade_size_stratification():
    """Extracts trade size distribution and separates retail vs block delta.
    Uses NQU26_CME_1tick_2026-08-23_to_expiry.parquet (7.08M ticks).
    Aggregates to 1m bars to measure whether Block Delta (>=10 lots) carries
    different information than Retail Delta (1-2 lots).
    """
    print("\n--- MODULE 1: Trade Size Stratification (Tick Data) ---")
    tick_file = TICK_DIR / "NQU26_CME_1tick_2026-08-23_to_expiry.parquet"
    if not tick_file.exists():
        return {"error": "Tick file not found"}
        
    df = pd.read_parquet(tick_file)
    print(f"Loaded {len(df):,} tick records.")
    
    # Classify trades by size
    v = df["volume"].values
    bid_v = df["bid_volume"].values
    ask_v = df["ask_volume"].values
    delta = ask_v - bid_v
    
    # Categories:
    # Small: 1 contract
    # Medium: 2-9 contracts
    # Large: >= 10 contracts
    is_small = (v == 1)
    is_med = (v >= 2) & (v <= 9)
    is_large = (v >= 10)
    
    df["delta_small"] = np.where(is_small, delta, 0)
    df["delta_med"] = np.where(is_med, delta, 0)
    df["delta_large"] = np.where(is_large, delta, 0)
    df["vol_small"] = np.where(is_small, v, 0)
    df["vol_large"] = np.where(is_large, v, 0)
    
    if not isinstance(df.index, pd.DatetimeIndex):
        df.set_index(pd.to_datetime(df["ts"]), inplace=True)
        
    # Aggregate to 1-minute bars
    print("Aggregating ticks to 1-minute bars...")
    agg_dict = {
        "close": "last",
        "volume": "sum",
        "bid_volume": "sum",
        "ask_volume": "sum",
        "delta_small": "sum",
        "delta_med": "sum",
        "delta_large": "sum",
        "vol_small": "sum",
        "vol_large": "sum",
    }
    bars = df.resample("1min").agg(agg_dict).dropna(subset=["close"])
    bars = bars[bars["volume"] > 0].copy()
    
    bars["delta_total"] = bars["ask_volume"] - bars["bid_volume"]
    c = bars["close"].astype(float)
    
    # Session-aware forward returns (mask gaps > 5m)
    dt_diff = bars.index.to_series().diff()
    bars["gap_prior"] = dt_diff > pd.Timedelta(minutes=5)
    
    # Forward 1m, 5m, 15m returns
    fwd_1m = ((c.shift(-1) - c) / c) * 10000.0
    fwd_5m = ((c.shift(-5) - c) / c) * 10000.0
    
    # Mask forward returns that cross session gaps
    dt_fwd5 = (bars.index.to_series().shift(-5) - bars.index.to_series()).dt.total_seconds() / 60.0
    fwd_5m = np.where(dt_fwd5 <= 6.0, fwd_5m, np.nan)
    
    # Evaluate information content of small delta vs large delta
    results = {
        "n_ticks_analyzed": len(df),
        "n_bars_created": len(bars),
        "trade_size_shares": {
            "small_1lot_contract_pct": round(float(is_small.mean() * 100.0), 2),
            "small_1lot_volume_pct": round(float(df["vol_small"].sum() / df["volume"].sum() * 100.0), 2),
            "large_10plus_contract_pct": round(float(is_large.mean() * 100.0), 2),
            "large_10plus_volume_pct": round(float(df["vol_large"].sum() / df["volume"].sum() * 100.0), 2),
        }
    }
    
    # Correlations
    for h_name, fwd in [("h_1m", fwd_1m), ("h_5m", fwd_5m)]:
        valid = np.isfinite(fwd)
        fwd_valid = fwd[valid] if isinstance(fwd, np.ndarray) else fwd[valid].values
        delta_tot_v = bars.loc[valid, "delta_total"].values
        delta_sml_v = bars.loc[valid, "delta_small"].values
        delta_lrg_v = bars.loc[valid, "delta_large"].values
        
        rho_tot, _ = stats.spearmanr(delta_tot_v, fwd_valid)
        rho_sml, _ = stats.spearmanr(delta_sml_v, fwd_valid)
        rho_lrg, _ = stats.spearmanr(delta_lrg_v, fwd_valid)
        
        # Regression: fwd_ret ~ delta_small + delta_large
        y = fwd_valid
        X = np.column_stack([
            np.ones(len(y)),
            delta_sml_v / 100.0,
            delta_lrg_v / 100.0,
        ])
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        resid = y - X @ beta
        s2 = np.sum(resid**2) / (len(y) - 3)
        cov = s2 * np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(cov))
        t_stats = beta / (se + 1e-12)
        
        results[h_name] = {
            "rho_delta_total": round(float(rho_tot), 4),
            "rho_delta_small_1lot": round(float(rho_sml), 4),
            "rho_delta_large_10plus": round(float(rho_lrg), 4),
            "beta_small": round(float(beta[1]), 5),
            "t_stat_small": round(float(t_stats[1]), 2),
            "beta_large": round(float(beta[2]), 5),
            "t_stat_large": round(float(t_stats[2]), 2),
        }
        print(f"  {h_name}: rho_total={rho_tot:+.4f} | rho_small={rho_sml:+.4f} (t={t_stats[1]:+5.2f}) | rho_large={rho_lrg:+.4f} (t={t_stats[2]:+5.2f})")
        
    return results

# ---------------------------------------------------------------------------
# MODULE 2: FOOTPRINT INTRA-BAR POC & TRAPPED LEVEL IMBALANCE
# ---------------------------------------------------------------------------
def analyze_footprint_structure():
    """Analyzes 3.85M footprint cells to measure:
    1. POC Location within the bar: relative vertical position [0 = bar low, 1 = bar high].
       Does extreme POC location (e.g. POC in top 15% on a bull bar vs bottom 15%) predict continuation or rejection?
    2. Trapped Traders at Extremes: Delta at the top 2 ticks vs bottom 2 ticks of the bar.
       If top 2 ticks have strong positive delta but bar closes below them, do trapped buyers cause downward reversal?
    """
    print("\n--- MODULE 2: Footprint Intra-Bar POC & Trapped Levels ---")
    fp_file = TICK_DIR / "NQ_continuous_1m_footprint.parquet"
    if not fp_file.exists():
        return {"error": "Footprint file not found"}
        
    # Sample last 30 RTH sessions to run deep analytics with high speed
    print("Loading footprint cells...")
    df = pd.read_parquet(fp_file)
    sessions = df["session"].unique()
    recent_sessions = sessions[-30:] # last 30 completed sessions
    df = df[df["session"].isin(recent_sessions)].copy()
    print(f"Loaded {len(df):,} footprint cells across 30 sessions.")
    
    # Compute per-bar footprint features
    # Group by minute
    records = []
    for minute_ts, g in df.groupby("minute"):
        bar_o = g["bar_open"].iloc[0]
        bar_h = g["bar_high"].iloc[0]
        bar_l = g["bar_low"].iloc[0]
        bar_c = g["bar_close"].iloc[0]
        bar_range = (bar_h - bar_l)
        if bar_range <= 0:
            continue
            
        # 1. Volume Point of Control (POC)
        poc_idx = g["volume"].idxmax()
        poc_price = g.loc[poc_idx, "price"]
        poc_loc = (poc_price - bar_l) / bar_range # 0 = low, 1 = high
        
        # 2. Extreme level delta: top 2 ticks vs bottom 2 ticks
        top_cut = bar_h - 0.50 # top 2 ticks
        bot_cut = bar_l + 0.50 # bottom 2 ticks
        
        g_top = g[g["price"] >= top_cut]
        g_bot = g[g["price"] <= bot_cut]
        
        delta_top = (g_top["ask_volume"] - g_top["bid_volume"]).sum()
        delta_bot = (g_bot["ask_volume"] - g_bot["bid_volume"]).sum()
        vol_total = g["volume"].sum()
        
        # Trapped buyers condition: high positive delta at the top, but close is lower than the top
        trapped_buyers = (delta_top > 0) and (bar_c < bar_h - 1.0)
        trapped_sellers = (delta_bot < 0) and (bar_c > bar_l + 1.0)
        
        records.append({
            "ts": minute_ts,
            "open": bar_o,
            "high": bar_h,
            "low": bar_l,
            "close": bar_c,
            "range": bar_range,
            "poc_loc": poc_loc,
            "delta_top": delta_top,
            "delta_bot": delta_bot,
            "vol_total": vol_total,
            "trapped_buyers": trapped_buyers,
            "trapped_sellers": trapped_sellers,
        })
        
    bar_df = pd.DataFrame(records)
    bar_df.set_index(pd.to_datetime(bar_df["ts"]), inplace=True)
    bar_df.sort_index(inplace=True)
    
    # Forward returns
    c = bar_df["close"].astype(float)
    fwd_1m = ((c.shift(-1) - c) / c) * 10000.0
    fwd_5m = ((c.shift(-5) - c) / c) * 10000.0
    
    # Mask gaps
    dt_fwd5 = (bar_df.index.to_series().shift(-5) - bar_df.index.to_series()).dt.total_seconds() / 60.0
    valid_5m = dt_fwd5 <= 6.0
    
    # Analysis 1: POC Location Effect
    # Does high POC (>0.80) predict upward continuation or reversal?
    poc = bar_df["poc_loc"]
    v_mask = valid_5m & poc.notna()
    rho_poc_1m, _ = stats.spearmanr(poc[v_mask], fwd_1m[v_mask])
    rho_poc_5m, _ = stats.spearmanr(poc[v_mask], fwd_5m[v_mask])
    
    # Quantile spread of POC location on forward 5m return
    high_poc_ret = fwd_5m[v_mask & (poc >= 0.80)].mean()
    low_poc_ret = fwd_5m[v_mask & (poc <= 0.20)].mean()
    poc_spread = high_poc_ret - low_poc_ret
    
    # Analysis 2: Trapped Traders at Extremes
    tb_mask = v_mask & bar_df["trapped_buyers"] & (bar_df["delta_top"] >= 50)
    ts_mask = v_mask & bar_df["trapped_sellers"] & (bar_df["delta_bot"] <= -50)
    
    ret_trapped_buyers = fwd_5m[tb_mask].mean()
    ret_trapped_sellers = fwd_5m[ts_mask].mean()
    trapped_reversal_spread = ret_trapped_sellers - ret_trapped_buyers
    
    res = {
        "n_bars_analyzed": len(bar_df),
        "poc_location": {
            "rho_poc_vs_fwd1m": round(float(rho_poc_1m), 4),
            "rho_poc_vs_fwd5m": round(float(rho_poc_5m), 4),
            "high_poc_top20pct_mean_5m_bps": round(float(high_poc_ret), 3),
            "low_poc_bot20pct_mean_5m_bps": round(float(low_poc_ret), 3),
            "poc_spread_5m_bps": round(float(poc_spread), 3),
        },
        "trapped_traders_at_extremes": {
            "n_trapped_buyer_events": int(tb_mask.sum()),
            "mean_fwd5m_trapped_buyers_bps": round(float(ret_trapped_buyers), 3),
            "n_trapped_seller_events": int(ts_mask.sum()),
            "mean_fwd5m_trapped_sellers_bps": round(float(ret_trapped_sellers), 3),
            "reversal_spread_bps": round(float(trapped_reversal_spread), 3),
        }
    }
    print(f"  POC Location 5m spread (High POC vs Low POC): {poc_spread:+.3f} bps")
    print(f"  Trapped Traders Reversal spread (Trapped Sellers minus Trapped Buyers): {trapped_reversal_spread:+.3f} bps")
    print(f"  Trapped Buyer events: {tb_mask.sum()}, Trapped Seller events: {ts_mask.sum()}")
    return res

# ---------------------------------------------------------------------------
# MODULE 3: RIGOROUS CROSS-ASSET LEAD-LAG (SESSION-MASKED + NEWEY-WEST)
# ---------------------------------------------------------------------------
def analyze_cross_asset_lead_lag():
    """Evaluates cross-market lead-lag with STRICT session masking (no gap leakage)
    and Newey-West HAC standard errors on NQ, ES, RTY, YM.
    """
    print("\n--- MODULE 3: Cross-Asset Lead-Lag (Session-Masked + HAC) ---")
    files = {
        "NQ": "NQ_continuous_1m_latest_90d.parquet",
        "ES": "ES_continuous_1m_latest_90d.parquet",
        "RTY": "RTY_continuous_1m_latest_90d.parquet",
        "YM": "YM_continuous_1m_latest_90d.parquet",
    }
    data = {}
    for sym, f in files.items():
        d = pd.read_parquet(SIERRA_DIR / f)
        if not isinstance(d.index, pd.DatetimeIndex):
            d.index = pd.to_datetime(d.index)
        d.sort_index(inplace=True)
        data[sym] = d
        
    common_idx = data["NQ"].index.intersection(data["ES"].index).intersection(data["RTY"].index).intersection(data["YM"].index)
    print(f"Common aligned bars: {len(common_idx):,}")
    
    # Align
    for s in data:
        data[s] = data[s].loc[common_idx]
        
    # Check session gaps: only evaluate within continuous intraday runs (time step == 1m)
    dt_diff = common_idx.to_series().diff()
    is_continuous_5m = (common_idx.to_series().shift(-5) - common_idx.to_series()).dt.total_seconds() <= 300.0
    
    results = {}
    pairs = [("ES", "NQ"), ("NQ", "ES"), ("ES", "RTY"), ("YM", "ES")]
    
    for src_sym, tgt_sym in pairs:
        c_tgt = data[tgt_sym]["close"].astype(float)
        ret_tgt_1m = ((c_tgt - data[tgt_sym]["open"].astype(float)) / data[tgt_sym]["open"].astype(float)) * 10000.0
        ret_tgt_fwd5 = ((c_tgt.shift(-5) - c_tgt) / c_tgt) * 10000.0
        
        # Delta normalized strictly trailing
        d_tgt = data[tgt_sym]["delta"].astype(float)
        std_d_tgt = d_tgt.shift(1).rolling(60, min_periods=20).std()
        norm_d_tgt = (d_tgt / std_d_tgt).clip(-5, 5)
        
        d_src = data[src_sym]["delta"].astype(float)
        std_d_src = d_src.shift(1).rolling(60, min_periods=20).std()
        norm_d_src = (d_src / std_d_src).clip(-5, 5)
        
        valid = is_continuous_5m & ret_tgt_fwd5.notna() & norm_d_tgt.notna() & norm_d_src.notna() & ret_tgt_1m.notna()
        
        y = ret_tgt_fwd5[valid].values
        X = np.column_stack([
            np.ones(len(y)),
            ret_tgt_1m[valid].values,
            norm_d_tgt[valid].values,
            norm_d_src[valid].values,
        ])
        
        # OLS
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        resid = y - X @ beta
        n, k = X.shape
        r2 = 1.0 - np.sum(resid**2) / np.sum((y - np.mean(y))**2)
        
        # Newey-West HAC with Bartlett lag = 5
        G0 = (X.T * resid) @ (X * resid[:, None]) / n
        G = G0.copy()
        for l in range(1, 6):
            w = 1.0 - l / 6.0
            Gl = (X[l:].T * resid[l:]) @ (X[:-l] * resid[:-l, None]) / n
            G += w * (Gl + Gl.T)
        invXX = np.linalg.inv(X.T @ X / n)
        cov_hac = (invXX @ G @ invXX) / n
        se_hac = np.sqrt(np.diag(cov_hac))
        t_hac = beta / (se_hac + 1e-12)
        
        results[f"{src_sym}->{tgt_sym}"] = {
            "n_valid_bars": int(n),
            "r2": round(float(r2), 6),
            "beta_src_delta": round(float(beta[3]), 5),
            "se_hac": round(float(se_hac[3]), 5),
            "t_stat_hac": round(float(t_hac[3]), 2),
            "is_stat_sig_hac": bool(abs(t_hac[3]) >= 2.0),
        }
        print(f"  {src_sym}->{tgt_sym} fwd 5m: beta_src={beta[3]:+.5f}, HAC t-stat={t_hac[3]:+5.2f}, sig={abs(t_hac[3]) >= 2.0}")
        
    return results

def main():
    atlas_deep = {}
    atlas_deep["module_1_trade_size"] = analyze_trade_size_stratification()
    atlas_deep["module_2_footprint_structure"] = analyze_footprint_structure()
    atlas_deep["module_3_cross_asset_lead_lag"] = analyze_cross_asset_lead_lag()
    
    out_file = OUT_DIR / "deep_sierra_atlas_results.json"
    with open(out_file, "w") as f:
        json.dump(atlas_deep, f, indent=2)
    print(f"\nAll deep analysis complete! Saved to {out_file}")

if __name__ == "__main__":
    main()
