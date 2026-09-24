"""Gate = AND of the whole battery (truth/VALIDATION_BATTERY.md). Deterministic. No /meta."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from core.validation import metrics as m

@dataclass
class GateResult:
    passed: bool
    reasons: list = field(default_factory=list)     # which gates failed
    dsr: float | None = None; pbo: float | None = None; mc_p: float | None = None
    boot_lo: float | None = None; nw_t: float | None = None; max_dd: float | None = None
    n_trades: int | None = None; n_params: int | None = None; wf_min: float | None = None

def _finite_or(value, fallback: float) -> float:
    value = float(value)
    return value if np.isfinite(value) else fallback

def _max_drawdown_safe(returns: np.ndarray) -> float:
    return 0.0 if len(returns) == 0 else _finite_or(m.max_drawdown(returns), 0.0)

def _active_return_series(returns: np.ndarray, positions=None, active_returns=None) -> np.ndarray:
    if active_returns is not None:
        return np.asarray(active_returns, float)
    if positions is None:
        return returns[np.asarray(returns, float) != 0.0]
    pos = np.asarray(positions, float)
    return returns[pos != 0.0]

def _active_return_mc_p(active_returns: np.ndarray, n: int = 2000, seed: int = 0) -> float:
    """Monte Carlo null on compressed active-bar returns: random sign flips imply no edge."""
    r = np.asarray(active_returns, float)
    if len(r) < 3:
        return 1.0
    obs = m.sharpe(r)
    if not np.isfinite(obs):
        return 1.0
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        signs = rng.choice(np.array([-1.0, 1.0]), size=len(r))
        sim = m.sharpe(r * signs)
        if np.isfinite(sim) and sim >= obs:
            cnt += 1
    return float(cnt / n)

def run_gate(returns, cfg, nb_trials, sr_trials_var, *, positions=None, active_returns=None,
             market_returns=None, candidate_matrix=None, n_params=1) -> GateResult:
    r = np.asarray(returns, float)
    active = _active_return_series(r, positions=positions, active_returns=active_returns)
    mdd = _max_drawdown_safe(r)
    n_tr = int(len(active))  # nonzero-position bars in the compressed trade-return series
    pbo = (_finite_or(m.cscv_pbo(candidate_matrix, cfg["pbo_S"]), 1.0)
           if candidate_matrix is not None else None)

    if n_tr < cfg["min_trades"]:
        reasons = ["min_trades"]
        if n_params > cfg["max_params"]:
            reasons.append("max_params")
        if mdd <= -cfg["max_dd_max"]:
            reasons.append("max_dd")
        mc = 1.0 if positions is not None and market_returns is not None else None
        return GateResult(False, reasons, 0.0, pbo, mc, 0.0, 0.0, mdd, n_tr, n_params, 0.0)

    dsr = _finite_or(m.deflated_sharpe_ratio(active, sr_trials_var, nb_trials), 0.0)
    nw = _finite_or(m.newey_west_tstat(active), 0.0)
    boot_lo, _ = m.bootstrap_sharpe_ci(active)
    boot_lo = _finite_or(boot_lo, 0.0)
    wf = [_finite_or(x, 0.0) for x in m.walk_forward(active, cfg["wf_splits"])]
    wf_min = min(wf) if wf else 0.0
    mc = (_finite_or(_active_return_mc_p(active), 1.0)
          if positions is not None and market_returns is not None else None)
    reasons = []
    def chk(name, ok):
        if not ok: reasons.append(name)
        return ok
    passed = all([
        chk("dsr", dsr > cfg["dsr_min"]),
        chk("nw_t", nw > cfg["nw_t_min"]),
        chk("boot_lo", boot_lo > cfg["boot_lo_min"]),
        chk("max_dd", mdd > -cfg["max_dd_max"]),
        chk("min_trades", n_tr >= cfg["min_trades"]),
        chk("max_params", n_params <= cfg["max_params"]),
        chk("wf_min", wf_min > cfg["wf_min_sharpe"]),
        chk("pbo", pbo is None or pbo < cfg["pbo_max"]),
        chk("mc", mc is None or mc < cfg["mc_p_max"]),
    ])
    return GateResult(passed, reasons, dsr, pbo, mc, boot_lo, nw, mdd, n_tr, n_params, wf_min)
