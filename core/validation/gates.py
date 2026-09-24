"""Split validator: DISCOVERY gate (earns more data, never capital) and DEPLOYMENT gate (capital).

Pure numpy/pandas/scipy. Deterministic (seeded). No /meta import. New code only: the legacy
`core.validation.battery.run_gate` and every function in `core.validation.metrics` are unchanged and
still callable; past verdicts are not re-scored by this module.

Source of the design: VALIDATION_COMPLETION_2026-09-23.md sections 4-7, VALIDATION_AUDIT_2026-09-22.md
sections 2, 6, 10, 11.

QUARANTINED LEGACY DEFECTS (documented here, not changed in legacy code):
  * N5 / "walk_forward drops a fold": `metrics.walk_forward(r, n)` splits into n+1 folds and scores only
    folds 1..n, so the first 1/(n+1) of trades is never scored. QUARANTINED: legacy `run_gate` keeps using
    it; the deployment gate here uses `subperiod_consistency_all_folds`, which scores every trade.
  * N2 / "max_dd scale pathology": legacy `max_drawdown` compounds pnl/capital, so for high-variance
    trade streams its failure rate RISES with N even for a positive edge. QUARANTINED: the deployment
    gate never uses max drawdown as an ALPHA condition; it is reported on a separate RISK axis, in units
    of per-trade risk (R) and of declared capital. The legacy 8% check (cfg["max_dd_max"]) is kept,
    unchanged, as a RISK condition only.
  * D1 / trial counting: nb_trials / sr_trials_var are supplied by the caller from the trials ledger
    (tools/trials_ledger.py). sr_trials_var is floored at 1/N (per-trade sampling variance).

References: Bailey & Lopez de Prado (2012, 2014) PSR/DSR; Bailey, Borwein, Lopez de Prado & Zhu (2016)
CSCV/PBO; Kunsch (1989) moving-block bootstrap; Cameron, Gelbach & Miller (2008) cluster bootstrap;
Kish (1965) design effect; Benjamini & Hochberg (1995) FDR; Newey & West (1987, 1994).
"""
from __future__ import annotations

import math
from typing import Any, Callable, Iterable

import numpy as np
from scipy import stats

from core.config import DEFAULT_GATE_CFG
from core.validation import metrics as m

VERDICTS = ("PASS", "FAIL", "INCONCLUSIVE", "N/A")
DEPLOYABLE_WINDOW_STATUSES = ("FRESH", "PROSPECTIVE")
KNOWN_WINDOW_STATUSES = ("DEV", "REUSED_HOLDOUT", "FRESH", "PROSPECTIVE")


# --------------------------------------------------------------------------- resampling core
def _default_block_len(n: int) -> int:
    """Moving-block length ~ n^(1/3) (Hall, Horowitz & Jing 1995 rate for variance estimation)."""
    return max(1, int(math.ceil(n ** (1.0 / 3.0))))


def _resample_index_sets(n: int, clusters, n_boot: int, seed: int, block_len: int | None):
    """Yield n_boot index arrays. Cluster bootstrap if clusters given, else moving-block bootstrap."""
    rng = np.random.default_rng(seed)
    if clusters is not None:
        codes, _ = _cluster_codes(clusters, n)
        members = [np.flatnonzero(codes == g) for g in range(codes.max() + 1)]
        G = len(members)
        for _ in range(n_boot):
            pick = rng.integers(0, G, G)
            yield np.concatenate([members[g] for g in pick])
    else:
        b = block_len or _default_block_len(n)
        b = min(b, n)
        k = int(math.ceil(n / b))
        offs = np.arange(b)
        for _ in range(n_boot):
            starts = rng.integers(0, n - b + 1, k)
            yield (starts[:, None] + offs[None, :]).ravel()[:n]


def _cluster_codes(clusters, n: int):
    c = np.asarray(clusters)
    if c.shape[0] != n:
        raise ValueError(f"clusters length {c.shape[0]} != values length {n}")
    uniq, codes = np.unique(c, return_inverse=True)
    return codes.astype(int), len(uniq)


def _boot_means(values: np.ndarray, clusters, n_boot: int, seed: int, block_len: int | None) -> np.ndarray:
    """Fast bootstrap distribution of the mean (cluster sums / counts, or moving blocks)."""
    x = np.asarray(values, float)
    n = len(x)
    rng = np.random.default_rng(seed)
    if clusters is not None:
        codes, G = _cluster_codes(clusters, n)
        sums = np.bincount(codes, weights=x, minlength=G)
        cnts = np.bincount(codes, minlength=G).astype(float)
        pick = rng.integers(0, G, (n_boot, G))
        return sums[pick].sum(axis=1) / cnts[pick].sum(axis=1)
    b = min(block_len or _default_block_len(n), n)
    k = int(math.ceil(n / b))
    starts = rng.integers(0, n - b + 1, (n_boot, k))
    idx = (starts[:, :, None] + np.arange(b)[None, None, :]).reshape(n_boot, -1)[:, :n]
    return x[idx].mean(axis=1)


def cluster_bootstrap_mean_ci(values, clusters=None, n_boot: int = 2000, seed: int = 0,
                              alpha: float = 0.10, block_len: int | None = None) -> dict:
    """Dependence-aware bootstrap of the mean.

    clusters given  -> resample whole clusters (e.g. sessions, wallets, tokens) with replacement.
    clusters None   -> moving-block bootstrap over time order (block_len default ceil(n^(1/3))).

    Returns the one-sided bounds at level `alpha` each: ci_lo = q_alpha, ci_hi = q_(1-alpha) of the
    bootstrap mean distribution (equivalently a two-sided 1-2*alpha percentile interval).
    design_effect = var_boot(mean) / var_iid(mean), with var_iid = s^2/n (ddof=1) (Kish 1965).
    n_eff = n / design_effect.
    """
    x = np.asarray(values, float)
    n = len(x)
    if n == 0:
        return {"n": 0, "mean": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"),
                "n_clusters": 0, "design_effect": float("nan"), "n_eff": 0.0, "boot_sd": float("nan"),
                "method": "none", "alpha": alpha}
    n_clusters = _cluster_codes(clusters, n)[1] if clusters is not None else None
    bm = _boot_means(x, clusters, n_boot, seed, block_len)
    var_boot = float(bm.var(ddof=1)) if n_boot > 1 else float("nan")
    var_iid = float(x.var(ddof=1) / n) if n > 1 else float("nan")
    deff = var_boot / var_iid if (np.isfinite(var_iid) and var_iid > 0) else float("nan")
    lo, hi = np.quantile(bm, [alpha, 1.0 - alpha])
    return {
        "n": n, "mean": float(x.mean()), "ci_lo": float(lo), "ci_hi": float(hi),
        "n_clusters": int(n_clusters) if n_clusters is not None else None,
        "block_len": None if clusters is not None else int(min(block_len or _default_block_len(n), n)),
        "design_effect": float(deff),
        "n_eff": float(n / deff) if np.isfinite(deff) and deff > 0 else float("nan"),
        "boot_sd": float(np.sqrt(var_boot)) if np.isfinite(var_boot) else float("nan"),
        "method": "cluster" if clusters is not None else "moving_block",
        "alpha": alpha,
        "_boot_means": bm,
    }


def required_n(min_useful_sr: float, alpha_one_sided: float = 0.10, power: float = 0.80,
               design_effect: float = 1.0) -> int:
    """N needed so a one-sided test at alpha detects per-trade SR = min_useful_sr with `power`.

    N80_iid = ((z_(1-alpha) + z_power) / s)^2  (normal approx; VALIDATION_COMPLETION section 6: 451 at s=0.10).
    Inflated by the design effect, floored at 1 so clustering can never reduce the requirement.
    """
    s = float(min_useful_sr)
    if not s > 0:
        raise ValueError("min_useful_sr must be > 0")
    z = stats.norm.ppf(1.0 - alpha_one_sided) + stats.norm.ppf(power)
    deff = float(design_effect) if np.isfinite(design_effect) else 1.0
    return int(math.ceil((z / s) ** 2 * max(deff, 1.0)))


def benjamini_hochberg(pvalues: Iterable[float], q: float = 0.10) -> np.ndarray:
    """BH (1995) step-up: boolean mask of discoveries at FDR q, in input order."""
    p = np.asarray(list(pvalues), float)
    k = len(p)
    if k == 0:
        return np.zeros(0, bool)
    order = np.argsort(p)
    thresh = q * np.arange(1, k + 1) / k
    passed = p[order] <= thresh
    out = np.zeros(k, bool)
    if passed.any():
        last = int(np.max(np.flatnonzero(passed)))
        out[order[: last + 1]] = True
    return out


# --------------------------------------------------------------------------- discovery gate
def discovery_gate(per_trade_returns, clusters=None, min_useful_edge: float | None = None, alpha: float = 0.10,
                   power: float = 0.80, *, min_useful_sr: float | None = None, alpha_fail: float = 0.05,
                   n_boot: int = 2000, seed: int = 0, block_len: int | None = None, min_n: int = 10,
                   require_half_edge: bool = False) -> dict:
    """DISCOVERY verdict: does this hypothesis earn more data / prospective paper trading? Never capital.

    PASS         one-sided (1-alpha) lower bound of the dependence-aware bootstrap mean > 0
                 (and, only if require_half_edge, point estimate >= min_useful_edge/2).
    FAIL         one-sided (1-alpha_fail) upper bound < min_useful_edge (a useful edge is excluded).
    INCONCLUSIVE otherwise; flag UNDERPOWERED when n_eff < required_n.
    N/A          n < min_n (default 10, the recommendation's frequency floor; n == 0 always N/A)
                 or fewer than 2 clusters.
    min_useful_edge is in the SAME units as per_trade_returns (e.g. net $/trade). min_useful_sr (per-trade
    Sharpe) is used for required_n; if not supplied it is derived as min_useful_edge / sample sd and flagged.
    """
    if min_useful_edge is None or not min_useful_edge > 0:
        raise ValueError("min_useful_edge (> 0, in return units) must be pre-declared")
    x = np.asarray(per_trade_returns, float)
    n = len(x)
    base = {"gate": "DISCOVERY", "authorizes_capital": False, "n": n, "alpha": alpha,
            "alpha_fail": alpha_fail, "power": power, "min_useful_edge": float(min_useful_edge),
            "flags": [], "reasons": []}
    n_clusters = _cluster_codes(clusters, n)[1] if (clusters is not None and n) else None
    if n == 0 or n < min_n:
        return {**base, "verdict": "N/A", "reasons": ["n_zero" if n == 0 else "n_below_min_n"]}
    if clusters is not None and n_clusters < 2:
        return {**base, "verdict": "N/A", "reasons": ["fewer_than_2_clusters"]}

    ci = cluster_bootstrap_mean_ci(x, clusters, n_boot=n_boot, seed=seed, alpha=alpha, block_len=block_len)
    bm = ci.pop("_boot_means")
    upper_fail = float(np.quantile(bm, 1.0 - alpha_fail))
    p_one_sided = float((np.sum(bm <= 0.0) + 1) / (len(bm) + 1))

    sd = float(x.std(ddof=1)) if n > 1 else float("nan")
    flags = []
    if min_useful_sr is None:
        min_useful_sr = float(min_useful_edge / sd) if sd > 0 else float("nan")
        flags.append("min_useful_sr_derived_from_sample_sd")
    deff = ci["design_effect"]
    req = required_n(min_useful_sr, alpha, power, deff) if np.isfinite(min_useful_sr) and min_useful_sr > 0 else None
    n_eff = ci["n_eff"]
    if req is not None and (not np.isfinite(n_eff) or n_eff < required_n(min_useful_sr, alpha, power, 1.0)):
        flags.append("UNDERPOWERED")
    half_edge_ok = ci["mean"] >= min_useful_edge / 2.0

    reasons = []
    if ci["ci_lo"] > 0 and (half_edge_ok or not require_half_edge):
        verdict = "PASS"
    elif upper_fail < min_useful_edge:
        verdict = "FAIL"
        reasons.append("upper_bound_below_min_useful_edge")
    else:
        verdict = "INCONCLUSIVE"
        reasons.append("ci_contains_zero_and_useful_edge" if ci["ci_lo"] <= 0 else "half_edge_not_met")
    return {**base, "verdict": verdict, "reasons": reasons, "flags": flags,
            "mean": ci["mean"], "lower_one_sided": ci["ci_lo"], "upper_one_sided": ci["ci_hi"],
            "upper_one_sided_fail": upper_fail, "p_one_sided": p_one_sided,
            "point_ge_half_edge": bool(half_edge_ok), "require_half_edge": require_half_edge,
            "n_clusters": ci["n_clusters"], "block_len": ci["block_len"], "method": ci["method"],
            "design_effect": deff, "n_eff": n_eff, "min_useful_sr": min_useful_sr,
            "required_n": req, "required_n_iid": (required_n(min_useful_sr, alpha, power, 1.0)
                                                    if req is not None else None)}


# --------------------------------------------------------------------------- sub-period consistency
def subperiod_consistency_all_folds(values, n_splits: int = 5) -> dict:
    """Split the chronological trade series into n_splits contiguous folds and score EVERY fold.

    Replacement for the quarantined legacy `metrics.walk_forward`, which splits into n_splits+1 folds and
    silently drops the first. This is a sub-period consistency check, not a refit walk-forward.
    """
    x = np.asarray(values, float)
    n = len(x)
    k = max(1, min(int(n_splits), n)) if n else 0
    folds = np.array_split(x, k) if k else []
    srs = [float(m.sharpe(f)) if len(f) > 1 else 0.0 for f in folds]
    srs = [s if np.isfinite(s) else 0.0 for s in srs]
    return {"n": n, "n_splits": k, "fold_sizes": [int(len(f)) for f in folds],
            "n_scored": int(sum(len(f) for f in folds)), "fold_sharpes": srs,
            "min_sharpe": float(min(srs)) if srs else 0.0}


# --------------------------------------------------------------------------- risk axis helpers
def _additive_max_drawdown(pnl: np.ndarray) -> float:
    """Max peak-to-trough of cumulative additive PnL (starting at 0). Returns a non-negative amount."""
    if len(pnl) == 0:
        return 0.0
    eq = np.concatenate([[0.0], np.cumsum(pnl)])
    return float(np.max(np.maximum.accumulate(eq) - eq))


def _worst_window_drawdown(pnl: np.ndarray, window: int = 100) -> float | None:
    if len(pnl) < window:
        return None
    return float(max(_additive_max_drawdown(pnl[i:i + window]) for i in range(len(pnl) - window + 1)))


def _stat_boot(x: np.ndarray, stat: Callable[[np.ndarray], float], clusters, n_boot: int, seed: int,
               block_len: int | None) -> np.ndarray:
    out = np.empty(n_boot)
    for i, idx in enumerate(_resample_index_sets(len(x), clusters, n_boot, seed, block_len)):
        v = stat(x[idx])
        out[i] = v if np.isfinite(v) else 0.0
    return out


def _combine(parts: list[str]) -> str:
    if "FAIL" in parts:
        return "FAIL"
    if "INCONCLUSIVE" in parts:
        return "INCONCLUSIVE"
    if parts and all(p == "N/A" for p in parts):
        return "N/A"
    return "PASS"


# --------------------------------------------------------------------------- deployment gate
def deployment_gate(per_trade_pnl, *, clusters=None, window_status: str, nb_trials: int,
                    ledger_sr_trials_var: float | None, cfg: dict | None = None, candidate_matrix=None,
                    n_params: int = 1, execution: dict | None = None, risk_per_trade: float | None = None,
                    declared_capital: float | None = None, deployed_size: float = 1.0,
                    max_tail_loss: float | None = None, n_boot: int = 2000, seed: int = 0,
                    block_len: int | None = None) -> dict:
    """DEPLOYMENT verdict (authorizes capital only if every axis PASSes).

    per_trade_pnl: chronological NET per-trade PnL at the deployed size (Sharpe-based checks are scale
    free; the RISK axis uses the $ scale). Convention-A thresholds come from cfg (DEFAULT_GATE_CFG)
    UNCHANGED. Differences vs legacy run_gate (all documented in the review packet):
      * window provenance: window_status must be FRESH or PROSPECTIVE (from tools/trials_ledger.py),
        else ALPHA FAIL "reused_window";
      * DSR uses caller-supplied ledger nb_trials and sr_trials_var = max(ledger var, 1/N);
      * boot_lo = dependence-aware (cluster / moving-block) bootstrap Sharpe, two-sided 95% lower (as legacy);
      * mc = dependence-aware recentred-bootstrap p-value of the Sharpe (replaces symmetric sign-flip);
      * wf_min = min Sharpe over ALL cfg["wf_splits"] folds (no dropped fold);
      * PBO required: no candidate_matrix -> ALPHA capped at INCONCLUSIVE ("pbo_unavailable");
      * min_trades shortfall -> INCONCLUSIVE (audit section 6), not FAIL;
      * max drawdown is NOT an alpha condition; it lives on the RISK axis.
    """
    cfg = dict(DEFAULT_GATE_CFG if cfg is None else cfg)
    x = np.asarray(per_trade_pnl, float)
    n = len(x)
    alpha_reasons: list[str] = []
    alpha_parts: list[str] = []

    def mark(ok: bool, reason: str, level: str = "FAIL"):
        alpha_parts.append("PASS" if ok else level)
        if not ok:
            alpha_reasons.append(reason)
        return ok

    status = str(window_status).upper()
    mark(status in DEPLOYABLE_WINDOW_STATUSES,
         "reused_window" if status in KNOWN_WINDOW_STATUSES else "unknown_window_status")

    metrics_out: dict[str, Any] = {"n": n, "window_status": status, "nb_trials": int(nb_trials)}
    if n == 0:
        alpha = "N/A" if status in DEPLOYABLE_WINDOW_STATUSES else "FAIL"
        alpha_reasons.append("n_zero")
    else:
        mark(n_params <= cfg["max_params"], "max_params")
        mark(n >= cfg["min_trades"], "min_trades", level="INCONCLUSIVE")
        if n >= 3:
            sr_var = max(float(ledger_sr_trials_var or 0.0), 1.0 / n)
            dsr = float(m.deflated_sharpe_ratio(x, sr_var, int(nb_trials)))
            dsr = dsr if np.isfinite(dsr) else 0.0
            sr0 = float(m.expected_max_sharpe(sr_var, int(nb_trials)))
            nw = float(m.newey_west_tstat(x))
            nw = nw if np.isfinite(nw) else 0.0
            sboot = _stat_boot(x, m.sharpe, clusters, n_boot, seed, block_len)
            boot_lo = float(np.quantile(sboot, 0.025))
            sr_obs = float(m.sharpe(x))
            null = _stat_boot(x - x.mean(), m.sharpe, clusters, n_boot, seed + 1, block_len)
            mc_p = float((np.sum(null >= sr_obs) + 1) / (n_boot + 1))
            wf = subperiod_consistency_all_folds(x, cfg["wf_splits"])
            mark(dsr > cfg["dsr_min"], "dsr")
            mark(nw > cfg["nw_t_min"], "nw_t")
            mark(boot_lo > cfg["boot_lo_min"], "boot_lo")
            mark(wf["min_sharpe"] > cfg["wf_min_sharpe"], "wf_min")
            mark(mc_p < cfg["mc_p_max"], "mc")
            metrics_out.update({"sharpe_per_trade": sr_obs, "sr_trials_var_used": sr_var,
                                "sr_trials_var_ledger": ledger_sr_trials_var, "sr0": sr0, "dsr": dsr,
                                "nw_t": nw, "boot_lo": boot_lo, "boot_method": "cluster" if clusters is not None
                                else "moving_block", "mc_p": mc_p, "subperiod": wf})
        else:
            alpha_parts.append("INCONCLUSIVE")
            alpha_reasons.append("n_below_3")
        if candidate_matrix is not None:
            pbo = float(m.cscv_pbo(candidate_matrix, cfg["pbo_S"]))
            pbo = pbo if np.isfinite(pbo) else 1.0
            metrics_out["pbo"] = pbo
            mark(pbo < cfg["pbo_max"], "pbo")
        else:
            metrics_out["pbo"] = None
            mark(False, "pbo_unavailable", level="INCONCLUSIVE")
        alpha = _combine(alpha_parts)

    # EXECUTION axis
    ex_reasons: list[str] = []
    ex = execution or {}
    cm = ex.get("cost_model_id")
    cap = ex.get("capacity_estimate")
    tail = ex.get("tail_loss_estimate")
    missing = []
    if not (isinstance(cm, str) and cm.strip()):
        missing.append("missing_cost_model_id")
    if cap is None or not np.isfinite(float(cap)) or float(cap) <= 0:
        missing.append("missing_capacity_estimate")
    if tail is None or not np.isfinite(float(tail)) or float(tail) < 0:
        missing.append("missing_tail_loss_estimate")
    if missing:
        execution_v = "INCONCLUSIVE"
        ex_reasons += missing
    else:
        execution_v = "PASS"
        if float(cap) < deployed_size:
            execution_v = "FAIL"
            ex_reasons.append("capacity_below_deployed_size")
        if max_tail_loss is not None and float(tail) > max_tail_loss:
            execution_v = "FAIL"
            ex_reasons.append("tail_loss_exceeds_max")

    # RISK axis (never an alpha condition)
    risk_reasons: list[str] = []
    dd_amt = _additive_max_drawdown(x)
    risk = {"max_dd_amount": dd_amt, "max_dd_R": None, "max_dd_frac_capital": None,
            "worst_100_trade_dd_amount": _worst_window_drawdown(x, 100), "worst_100_trade_dd_R": None,
            "legacy_compounding_max_dd": None, "legacy_max_dd_max": cfg["max_dd_max"]}
    if risk_per_trade is not None and risk_per_trade > 0:
        risk["max_dd_R"] = dd_amt / risk_per_trade
        if risk["worst_100_trade_dd_amount"] is not None:
            risk["worst_100_trade_dd_R"] = risk["worst_100_trade_dd_amount"] / risk_per_trade
    else:
        risk_reasons.append("missing_risk_per_trade")
    if declared_capital is not None and declared_capital > 0:
        risk["max_dd_frac_capital"] = dd_amt / declared_capital
        legacy = float(m.max_drawdown(x / declared_capital)) if n else 0.0
        risk["legacy_compounding_max_dd"] = legacy if np.isfinite(legacy) else -1.0
        if risk["legacy_compounding_max_dd"] <= -cfg["max_dd_max"]:
            risk_reasons.append("max_dd")
    else:
        risk_reasons.append("missing_declared_capital")
    if "max_dd" in risk_reasons:
        risk_v = "FAIL"
    elif risk_reasons:
        risk_v = "INCONCLUSIVE"
    else:
        risk_v = "PASS"
    risk["verdict"] = risk_v
    risk["reasons"] = risk_reasons

    deployment = _combine([alpha if alpha != "N/A" else "INCONCLUSIVE", execution_v, risk_v])
    return {
        "gate": "DEPLOYMENT",
        "axes": {
            "ALPHA": {"verdict": alpha, "reasons": alpha_reasons},
            "EXECUTION": {"verdict": execution_v, "reasons": ex_reasons,
                          "cost_model_id": cm, "capacity_estimate": cap, "tail_loss_estimate": tail,
                          "deployed_size": deployed_size},
            "DEPLOYMENT": {"verdict": deployment,
                           "reasons": [f"ALPHA:{r}" for r in alpha_reasons] + [f"EXECUTION:{r}" for r in ex_reasons]
                           + [f"RISK:{r}" for r in risk_reasons]},
        },
        "RISK": risk,
        "metrics": metrics_out,
        "thresholds": {k: cfg[k] for k in sorted(cfg)},
        "deployment_eligible": deployment == "PASS",
    }
