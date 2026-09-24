"""Isolated risk monitor. Reads state, returns breaches + actions. Cannot be overridden by makers."""
from __future__ import annotations
def check_invariants(net_delta_usd, mmr, funding_bps, drawdown, cfg) -> list[dict]:
    b = []
    if abs(net_delta_usd) > cfg["epsilon_delta"]: b.append({"kind":"delta_breach","action":"flatten_sleeve"})
    if mmr > cfg["mmr_ceiling"]:                    b.append({"kind":"margin","action":"deleverage"})
    if funding_bps <= cfg["funding_flip_bps"]:      b.append({"kind":"funding_flip","action":"unwind"})
    if drawdown <= -cfg["kill_switch_dd"]:          b.append({"kind":"dd_kill","action":"flatten_all"})
    return b
DEFAULT_RISK_CFG = {"epsilon_delta":50.0,"mmr_ceiling":0.5,"funding_flip_bps":-1.0,"kill_switch_dd":0.05}
