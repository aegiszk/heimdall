"""AlphaModel contract. Views only. NO imports from /meta here (enforced by tools/check_core_purity.py)."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import math

@dataclass(frozen=True)
class Signal:
    model_name: str
    asset: str
    ts: str
    conviction: float            # [-1, +1]; 0.0 = abstain
    reasoning: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not (-1.0 <= self.conviction <= 1.0):
            raise ValueError(f"conviction {self.conviction} out of [-1,1]")

class AlphaModel(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def predict(self, asset: str, ts: str, data) -> Signal: ...
    def _neutral(self, asset: str, ts: str) -> Signal:
        return Signal(self.name, asset, ts, 0.0, "abstain")

class QuantModel(AlphaModel):
    @staticmethod
    def _safe_float(v, default: float = 0.0) -> float:
        try:
            f = float(v)
            return default if (math.isnan(f) or math.isinf(f)) else f
        except (TypeError, ValueError):
            return default
    @staticmethod
    def _percentile_rank(value: float, values: list[float]) -> float:
        if not values: return 50.0
        return 100.0 * sum(1 for x in values if x <= value) / len(values)
