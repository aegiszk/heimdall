from __future__ import annotations
import numpy as np
from core.alpha.base import QuantModel, Signal

class OIExtremeModel(QuantModel):
    def __init__(self, z: float = 2.0, fee: float = 2e-5): self._z=z; self._fee=fee
    @property
    def name(self): return "oi_extreme"
    def strategy_returns(self, df):
        f = df["funding"].to_numpy(float); mkt = df["ret"].to_numpy(float)
        z = (f - f.mean()) / (f.std(ddof=1) + 1e-12)
        pos = -np.sign(z) * (np.abs(z) > self._z)      # fade crowded funding
        return pos * mkt - np.abs(pos) * self._fee, pos, mkt
    def predict(self, asset, ts, data) -> Signal:
        return self._neutral(asset, ts)  # live wiring in S5
