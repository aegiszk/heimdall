"""Heimdall orchestration. run_paper_backtest wires screen->firewall->gate for the graduation check.
Live sub-loops (ingest/execute/risk) are wired to connectors on real infra (S5)."""
from __future__ import annotations
from core.config import DEFAULT_GATE_CFG
from core.funnel.funnel import screen, gate
from core.alpha.carry import FundingCarryModel
from core.alpha.oi_extreme import OIExtremeModel
from core.alpha.vol_momentum import VolRegimeMomentumModel
from core.data.synthetic import make_market

def default_families():
    return [FundingCarryModel(), OIExtremeModel(), VolRegimeMomentumModel()]

def run_paper_backtest(df=None, families=None, cfg=None):
    df = make_market() if df is None else df
    families = families or default_families()
    cfg = cfg or DEFAULT_GATE_CFG
    shortlist, nb_trials, sr_var, holdout = screen(families, df)
    results = gate(shortlist, holdout, cfg, nb_trials, sr_var)
    return results

if __name__ == "__main__":
    for fam, res in run_paper_backtest():
        status = "PASS -> $1-5k rung" if res.passed else f"KILLED ({','.join(res.reasons)})"
        print(f"{fam.name:14s} DSR={res.dsr:.3f} NWt={res.nw_t:5.2f} "
              f"maxDD={res.max_dd:+.3f} -> {status}")
