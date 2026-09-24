"""Paper broker (S0). Refuses real orders while LIVE_TRADING_ENABLED=false (I7)."""
from __future__ import annotations
import os

class PaperBroker:
    def __init__(self): self.fills = []
    @staticmethod
    def _live_enabled() -> bool:
        return os.getenv("LIVE_TRADING_ENABLED", "false").lower() == "true"
    def send(self, venue, leg, side, qty, price, is_paper=True):
        if not is_paper and not self._live_enabled():
            raise PermissionError("I7: real order blocked while LIVE_TRADING_ENABLED=false")
        self.fills.append(dict(venue=venue, leg=leg, side=side, qty=qty, price=price, is_paper=is_paper))
        return self.fills[-1]
