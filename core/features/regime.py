"""Deterministic regime feature (money path). LLM regime advisory is separate, in /meta."""
from __future__ import annotations
import numpy as np
def vol_regime(ret: np.ndarray, k: int = 20) -> np.ndarray:
    """1 = calm/trend-on, 0 = choppy. Rolling realized vol below its median = trend-on."""
    r = np.asarray(ret, float); n = len(r)
    rv = np.array([r[max(0,i-k):i+1].std(ddof=1) if i >= 2 else 0.0 for i in range(n)])
    med = np.median(rv[rv > 0]) if np.any(rv > 0) else 0.0
    return (rv <= med).astype(float)
