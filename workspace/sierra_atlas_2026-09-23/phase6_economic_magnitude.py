"""Phase 6: Economic Magnitude & Friction Comparison.
Compares observed forward displacement (Q10 - Q1 decile spread in bps)
against realistic round-turn entry/exit friction across all 6 primary instruments.
Classifies each relationship into:
- INFORMATION EXISTS BUT TOO SMALL TO TRADE
- POTENTIALLY ECONOMIC
- NO MEASURABLE INFORMATION
- DATA INSUFFICIENT
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

OUT_DIR = Path("workspace/sierra_atlas_2026-09-23")

# Realistic friction in basis points (commission + 1-2 ticks slippage)
# Formula: (commission_RT + slippage_ticks * tick_value) / notional * 10000
FRICTIONS = {
    "NQ": 2.25,    # $3.50 + 2 ticks ($10) on $600k = 2.25 bps
    "MNQ": 3.33,   # $1.00 + 2 ticks ($1) on $60k = 3.33 bps
    "ES": 5.33,    # $3.50 + 1 tick ($12.50) on $300k = 5.33 bps
    "MES": 7.50,   # $1.00 + 1 tick ($1.25) on $30k = 7.50 bps
    "GC": 5.19,    # $3.50 + 1 tick ($10) on $260k = 5.19 bps
    "CL": 18.00,   # $3.50 + 1 tick ($10) on $75k = 18.00 bps
    "RTY": 7.39,   # $3.50 + 1 tick ($5) on $115k = 7.39 bps
    "YM": 3.95,    # $3.50 + 1 tick ($5) on $215k = 3.95 bps
}

def main():
    with open(OUT_DIR / "phase2_response_atlas.json") as f:
        atlas = json.load(f)
    with open(OUT_DIR / "phase3_session_dependence.json") as f:
        sess = json.load(f)
        
    records = []
    
    # 1. Full-sample features
    for sym, feats in atlas.items():
        friction = FRICTIONS[sym]
        for f_name, h_dict in feats.items():
            for h_str, metrics in h_dict.items():
                spread = abs(metrics["q_spread_bps"])
                t_stat = abs(metrics["t_stat"])
                rho = metrics["spearman_rho"]
                stable = metrics["stable_sign"]
                
                ratio = spread / friction
                
                if t_stat < 2.0 or abs(rho) < 0.005:
                    classification = "NO MEASURABLE INFORMATION"
                elif ratio >= 1.0 and stable:
                    classification = "POTENTIALLY ECONOMIC"
                else:
                    classification = "INFORMATION EXISTS BUT TOO SMALL TO TRADE"
                    
                records.append({
                    "symbol": sym,
                    "scope": "full_sample",
                    "feature": f_name,
                    "horizon": h_str,
                    "spearman_rho": rho,
                    "t_stat": metrics["t_stat"],
                    "spread_bps": metrics["q_spread_bps"],
                    "friction_bps": friction,
                    "spread_to_friction_ratio": round(ratio, 3),
                    "stable": stable,
                    "classification": classification,
                })
                
    # 2. Session-specific features (NQ & ES)
    for sym, s_dict in sess.items():
        friction = FRICTIONS[sym]
        for sess_name, f_dict in s_dict.items():
            for f_name, h_dict in f_dict.items():
                for h_str, metrics in h_dict.items():
                    spread = abs(metrics["spread_bps"])
                    rho = abs(metrics["rho"])
                    pval = metrics["p_value"]
                    ratio = spread / friction
                    
                    if pval > 0.05 or rho < 0.01:
                        classification = "NO MEASURABLE INFORMATION"
                    elif ratio >= 1.0:
                        classification = "POTENTIALLY ECONOMIC"
                    else:
                        classification = "INFORMATION EXISTS BUT TOO SMALL TO TRADE"
                        
                    records.append({
                        "symbol": sym,
                        "scope": sess_name,
                        "feature": f_name,
                        "horizon": h_str,
                        "spearman_rho": metrics["rho"],
                        "t_stat": None,
                        "spread_bps": metrics["spread_bps"],
                        "friction_bps": friction,
                        "spread_to_friction_ratio": round(ratio, 3),
                        "stable": None,
                        "classification": classification,
                    })

    df_out = pd.DataFrame(records)
    
    # Summary by classification
    summary = df_out["classification"].value_counts().to_dict()
    print("Economic Magnitude Classification Summary:")
    for k, v in summary.items():
        print(f"  {k:45s}: {v:3d} cells")
        
    # Check if ANY cell was classified POTENTIALLY ECONOMIC
    pot_econ = df_out[df_out["classification"] == "POTENTIALLY ECONOMIC"]
    print(f"\nPotentially economic cells: {len(pot_econ)}")
    if len(pot_econ) > 0:
        print(pot_econ[["symbol", "scope", "feature", "horizon", "spread_bps", "friction_bps", "spread_to_friction_ratio"]])
        
    out_file = OUT_DIR / "phase6_economic_magnitude.json"
    with open(out_file, "w") as f:
        json.dump(records, f, indent=2)
    print(f"\nWrote economic magnitude results to {out_file}")

if __name__ == "__main__":
    main()
