import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from loop import run_paper_backtest, default_families
from core.funnel.funnel import screen, _split
from core.data.synthetic import make_market
from core.alpha.carry import FundingCarryModel

def test_carry_passes_gate_on_carry_edge_data():
    res = {f.name: r for f, r in run_paper_backtest()}
    assert res["carry"].passed, res["carry"].reasons

def test_carry_killed_when_no_edge():
    df = make_market(carry_edge=False)
    res = {f.name: r for f, r in run_paper_backtest(df=df)}
    assert not res["carry"].passed          # no funding edge -> gate kills it

def test_firewall_blocks_overlap():
    df = make_market()
    tr, ho = _split(df)
    assert set(tr.index).isdisjoint(set(ho.index))

def test_directional_families_dont_free_pass():
    # vol_momentum / oi_extreme have no embedded edge in synthetic mkt -> should not all pass
    res = {f.name: r for f, r in run_paper_backtest()}
    assert not (res["oi_extreme"].passed and res["vol_momentum"].passed)
