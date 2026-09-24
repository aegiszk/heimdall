from __future__ import annotations
import numpy as np

def inverse_vol_weights(returns_by_strat: dict) -> dict:
    inv = {k: 1.0 / (np.std(v, ddof=1) + 1e-12) for k, v in returns_by_strat.items()}
    s = sum(inv.values()) or 1.0
    return {k: v / s for k, v in inv.items()}

def vol_target_scale(portfolio_ret: np.ndarray, target_ann_vol=0.10, ppy=252) -> float:
    realized = np.std(portfolio_ret, ddof=1) * np.sqrt(ppy)
    return float(min(3.0, target_ann_vol / (realized + 1e-12)))  # capped at gross leverage 3x
