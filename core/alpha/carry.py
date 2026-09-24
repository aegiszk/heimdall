"""Funding carry: short perp + long spot, delta-neutral, collect funding. Thresholds from config."""
from __future__ import annotations
import numpy as np
from core.alpha.base import QuantModel, Signal

class FundingCarryModel(QuantModel):
    def __init__(self, enter_bps=1.0, exit_bps=-1.0, fee=2e-5):
        self._enter=enter_bps; self._exit=exit_bps; self._fee=fee
    @property
    def name(self): return "carry"
    def strategy_returns(self, df):
        f = df["funding"].to_numpy(float)
        pos = (f * 1e4 >= self._enter).astype(float)     # in-position when funding rich
        ret = pos * (f - self._fee)                       # collect funding only while in position
        return ret, pos, f
    def predict(self, asset, ts, data) -> Signal:
        fb = self._safe_float(data.funding_bps(asset, ts))
        if fb >= self._enter:
            return Signal(self.name, asset, ts, -1.0, f"funding {fb:.2f}bps",
                          {"leg": "short_perp_long_spot"})
        if fb <= self._exit:
            return Signal(self.name, asset, ts, 0.0, "funding-flip unwind (I3)")
        return self._neutral(asset, ts)
