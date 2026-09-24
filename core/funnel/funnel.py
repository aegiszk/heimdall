"""Two-stage funnel. Screen in-sample only; firewall; gate survivors on untouched holdout."""
from __future__ import annotations
import numpy as np
from core.validation import metrics as m
from core.validation.battery import run_gate

def _split(df, train_frac=0.5):
    n = len(df); cut = int(n * train_frac)
    tr, ho = df.iloc[:cut], df.iloc[cut:]
    if set(tr.index) & set(ho.index): raise ValueError("FIREWALL: train/holdout overlap")
    return tr, ho

def screen(families, df, top_k=None, train_frac=0.5):
    """Rank families by in-sample Sharpe. Returns (shortlist, nb_trials, sr_trials_var, holdout)."""
    train, holdout = _split(df, train_frac)
    scored = []
    for fam in families:
        r, _, _ = fam.strategy_returns(train)
        scored.append((m.sharpe(r), fam))
    sr_vals = np.array([s for s, _ in scored])
    sr_trials_var = float(np.var(sr_vals)) if len(sr_vals) > 1 else 0.0
    scored.sort(key=lambda x: x[0], reverse=True)
    k = top_k or len(scored)
    shortlist = [fam for _, fam in scored[:k]]
    return shortlist, len(families), sr_trials_var, holdout

def gate(shortlist, holdout, cfg, nb_trials, sr_trials_var):
    """Run the battery on each survivor's HOLDOUT returns. Returns list of (family, GateResult)."""
    out = []
    for fam in shortlist:
        r, pos, mkt = fam.strategy_returns(holdout)
        active_r = r[np.asarray(pos, float) != 0.0]
        res = run_gate(r, cfg, nb_trials, sr_trials_var,
                       positions=pos, active_returns=active_r,
                       market_returns=mkt, n_params=2)
        out.append((fam, res))
    return out
