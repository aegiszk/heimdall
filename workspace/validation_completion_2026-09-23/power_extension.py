"""Task 3 evidence (project .venv). No core/ edits.

(a) Extends the 2026-09-22 power map to larger N for the UNMODIFIED production gate, convention A
    (nb_trials=1, sr_trials_var=0), using the audit's own synthetic generator (tools/audit_power_map.sample).
(b) Operating characteristics of the proposed DISCOVERY gate (discovery_gate below; not wired into core).
Output: power_extension.json
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from core.config import DEFAULT_GATE_CFG  # noqa: E402
from core.validation.battery import run_gate  # noqa: E402
from core.validation.metrics import newey_west_tstat  # noqa: E402
from tools.audit_power_map import CAPITAL, sample  # noqa: E402

PROD_REPS = 200
DISC_REPS = 1000


def discovery_gate(pnl: np.ndarray, delta: float, alpha: float = 0.10, k_batch: int = 1,
                   n_min_pass: int = 30, power: float = 0.80) -> dict:
    """PASS / FAIL / INCONCLUSIVE / N/A on ONE dependence-aware statistic (NW HAC t of per-trade PnL).

    delta: pre-declared minimum useful per-trade Sharpe. alpha: one-sided discovery level,
    Bonferroni-split over the k_batch candidates evaluated together.
    """
    x = np.asarray(pnl, float)
    n = len(x)
    if n == 0:
        return {"verdict": "N/A", "n": 0}
    if n < 3 or np.std(x, ddof=1) == 0:
        return {"verdict": "INCONCLUSIVE", "n": n}
    t = newey_west_tstat(x)
    sr_hat = t / np.sqrt(n)  # HAC-scaled per-trade Sharpe estimate
    z_pass = stats.norm.ppf(1 - alpha / k_batch)
    z_fail = stats.norm.ppf(1 - alpha)  # upper confidence bound excludes the useful edge
    upper = sr_hat + z_fail / np.sqrt(n)
    n_needed = int(np.ceil(((z_pass + stats.norm.ppf(power)) / delta) ** 2))
    if upper < delta:
        verdict = "FAIL"
    elif t > z_pass and n >= n_min_pass:
        verdict = "PASS"
    else:
        verdict = "INCONCLUSIVE"
    return {"verdict": verdict, "n": n, "t_hac": float(t), "sr_hat": float(sr_hat), "sr_upper": float(upper),
            "n_needed_80": n_needed, "power_at_delta_now": float(stats.norm.cdf(delta * np.sqrt(n) - z_pass))}


def _prod_cell(args):
    shape, s, n, seed = args
    rng = np.random.default_rng(seed)
    acc = 0
    fails: dict[str, int] = {}
    for _ in range(PROD_REPS):
        r = sample(shape, s, n, rng) / CAPITAL
        g = run_gate(r, DEFAULT_GATE_CFG, 1, 0.0, active_returns=r, n_params=3)
        acc += bool(g.passed)
        for reason in g.reasons:
            fails[reason] = fails.get(reason, 0) + 1
    return {"shape": shape, "true_sr": s, "n": n, "accept_rate": acc / PROD_REPS,
            "fail_rate_by_gate": {k: v / PROD_REPS for k, v in fails.items()}}


def _disc_cell(args):
    shape, s, n, seed, delta = args
    rng = np.random.default_rng(seed)
    counts = {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0, "N/A": 0}
    for _ in range(DISC_REPS):
        counts[discovery_gate(sample(shape, s, n, rng), delta)["verdict"]] += 1
    return {"shape": shape, "true_sr": s, "n": n, "delta": delta, **{k: v / DISC_REPS for k, v in counts.items()}}


def main() -> None:
    prod_args = []
    seed = 7000
    for shape in ("coin_1to1", "neg_skew"):
        for s, ns in ((0.05, (1000, 2000, 3500)), (0.10, (800, 1200, 2000)), (0.20, (300,)), (0.0, (1000, 3500))):
            for n in ns:
                seed += 1
                prod_args.append((shape, s, n, seed))
    disc_args = []
    for shape in ("coin_1to1", "neg_skew", "ar1_0.3", "fat_tail_t3"):
        for s in (-0.10, 0.0, 0.05, 0.10, 0.20, 0.30):
            for n in (10, 30, 50, 100, 200, 500, 1000):
                seed += 1
                disc_args.append((shape, s, n, seed, 0.10))
    with ProcessPoolExecutor() as ex:
        prod = list(ex.map(_prod_cell, prod_args))
        disc = list(ex.map(_disc_cell, disc_args))
    out = {"prod_reps": PROD_REPS, "disc_reps": DISC_REPS, "gate_cfg": DEFAULT_GATE_CFG,
           "production_convention_A_large_n": prod, "discovery_gate_delta_0.10_alpha_0.10": disc}
    (HERE / "power_extension.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for row in prod:
        print("PROD", row["shape"], row["true_sr"], row["n"], row["accept_rate"])


if __name__ == "__main__":
    main()
