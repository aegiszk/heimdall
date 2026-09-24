"""Offline synthetic market with an embedded funding-carry edge, for testing the pipeline."""
from __future__ import annotations
import numpy as np, pandas as pd
def make_market(T=800, seed=0, carry_edge=True):
    rng = np.random.default_rng(seed)
    ret = rng.normal(0, 0.012, T)                       # market returns (no free directional edge)
    if carry_edge:
        funding = rng.normal(0.0003, 0.00015, T)         # ~3bps/period positive funding
    else:
        funding = rng.normal(0.0, 0.000005, T)           # near-zero funding, no threshold carry edge
    basis_noise = rng.normal(0, 0.0006, T)               # execution/basis noise on the carry leg
    oi = rng.uniform(0, 100, T)
    return pd.DataFrame({"ret": ret, "funding": funding, "basis_noise": basis_noise, "oi_pct": oi})
