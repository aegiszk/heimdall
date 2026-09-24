from __future__ import annotations
import numpy as np
from core.alpha.base import QuantModel, Signal
from core.features.regime import vol_regime

class VolRegimeMomentumModel(QuantModel):
    def __init__(self, k: int = 20, fee: float = 2e-5): self._k=k; self._fee=fee
    @property
    def name(self): return "vol_momentum"
    def strategy_returns(self, df):
        mkt = df["ret"].to_numpy(float)
        mom = np.sign(np.convolve(mkt, np.ones(self._k)/self._k, "same"))
        pos = mom * vol_regime(mkt, self._k)            # trend only when regime on
        return pos * mkt - np.abs(pos) * self._fee, pos, mkt
    def predict(self, asset, ts, data) -> Signal:
        return self._neutral(asset, ts)
