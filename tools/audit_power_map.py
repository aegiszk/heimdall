"""V2 validation audit: positive/negative-control POWER MAP of the production gate.

Feeds synthetic per-trade dollar PnL streams with KNOWN true expectancy (set
analytically before sampling) through the unmodified ``core.validation.battery.
run_gate`` exactly as Heimdall's validators call it, and measures:

  accept rate for null/negative controls  -> false-positive rate
  accept rate for positive controls       -> power (1 - false-negative rate)
  which individual gate rejected          -> failure attribution

Two production call conventions are audited:
  A: nb_trials=1, sr_trials_var=0.0   (validate_inversion_model / okala / fabio / orderflow / intraday)
  B: nb_trials=2, sr_trials_var=1.0   (validate_research_candidates: LuxAlgo POC, Casper FVG)

Thresholds are read from core.config.DEFAULT_GATE_CFG and NOT modified.
Returns are pnl / 50,000 exactly as the validators pass them.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import DEFAULT_GATE_CFG
from core.validation.battery import run_gate

CAPITAL = 50_000.0
SD_DOLLARS = 20.0  # ~1 MNQ contract with a 10-point stop
EDGES = [-0.10, 0.0, 0.05, 0.10, 0.20, 0.30]  # true per-trade Sharpe (mean / sd)
NS = [10, 20, 30, 50, 100, 200, 500]
SHAPES = ["coin_1to1", "low_win_4to1", "high_win_1to4", "pos_skew", "neg_skew", "fat_tail_t3", "ar1_0.3", "regime_blocks"]
REPS = 400
CONVENTIONS = {"A_nb1_var0": (1, 0.0), "B_nb2_var1": (2, 1.0)}
GATES = ["dsr", "nw_t", "boot_lo", "max_dd", "min_trades", "max_params", "wf_min", "pbo", "mc"]


def _binary_p(s: float, w: float) -> float:
    """Win probability p such that binary {+w, -1} has mean/sd == s."""
    f = lambda p: (p * w - (1 - p)) / ((w + 1) * np.sqrt(p * (1 - p))) - s
    return brentq(f, 1e-6, 1 - 1e-6)


def sample(shape: str, s: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Standardised stream with true mean s and true sd 1, then scaled to dollars."""
    if shape in ("coin_1to1", "low_win_4to1", "high_win_1to4"):
        w = {"coin_1to1": 1.0, "low_win_4to1": 4.0, "high_win_1to4": 0.25}[shape]
        p = _binary_p(s, w)
        raw = np.where(rng.random(n) < p, w, -1.0)
        mu, sd = p * w - (1 - p), (w + 1) * np.sqrt(p * (1 - p))
        x = (raw - mu) / sd + s
    elif shape in ("pos_skew", "neg_skew"):
        sig = 0.8
        m, v = np.exp(sig**2 / 2), (np.exp(sig**2) - 1) * np.exp(sig**2)
        z = (np.exp(sig * rng.standard_normal(n)) - m) / np.sqrt(v)
        x = (z if shape == "pos_skew" else -z) + s
    elif shape == "fat_tail_t3":
        x = rng.standard_t(3, n) / np.sqrt(3.0) + s
    elif shape == "ar1_0.3":
        phi = 0.3
        e = rng.standard_normal(n) * np.sqrt(1 - phi**2)
        z = np.empty(n)
        z[0] = rng.standard_normal()
        for i in range(1, n):
            z[i] = phi * z[i - 1] + e[i]
        x = z + s
    elif shape == "regime_blocks":
        # edge lives in half of 10-trade blocks (2s there, 0 elsewhere); unconditional mean = s
        blocks = int(np.ceil(n / 10))
        on = rng.permutation(np.arange(blocks) % 2 == 0)
        mean = np.repeat(np.where(on, 2 * s, 0.0), 10)[:n]
        x = rng.standard_normal(n) + mean
    else:
        raise ValueError(shape)
    return x * SD_DOLLARS


def _cell(args):
    shape, s, n, seed = args
    rng = np.random.default_rng(seed)
    out = {c: {"accept": 0, "fail": {g: 0 for g in GATES}} for c in CONVENTIONS}
    for _ in range(REPS):
        r = sample(shape, s, n, rng) / CAPITAL
        for c, (nb, var) in CONVENTIONS.items():
            g = run_gate(r, DEFAULT_GATE_CFG, nb, var, active_returns=r, n_params=3)
            out[c]["accept"] += int(g.passed)
            for reason in g.reasons:
                out[c]["fail"][reason] += 1
    return {
        "shape": shape, "true_sr": s, "n": n,
        **{c: {"accept_rate": v["accept"] / REPS, "fail_rate_by_gate": {k: x / REPS for k, x in v["fail"].items() if x}}
           for c, v in out.items()},
    }


def main() -> int:
    jobs = [(sh, s, n, 1_000_000 + i) for i, (sh, s, n) in
            enumerate((sh, s, n) for sh in SHAPES for s in EDGES for n in NS)]
    with ProcessPoolExecutor(max_workers=18) as pool:
        cells = list(pool.map(_cell, jobs, chunksize=2))
    out_dir = ROOT / "data" / "validation_audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"reps_per_cell": REPS, "gate_cfg": DEFAULT_GATE_CFG, "capital": CAPITAL,
               "sd_dollars": SD_DOLLARS, "conventions": CONVENTIONS, "cells": cells}
    path = out_dir / "power_map_2026-09-22.json"
    path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")

    for conv in CONVENTIONS:
        print(f"\n=== ACCEPT RATE, convention {conv} (rows=shape, cols=N) ===")
        for s in EDGES:
            print(f"-- true per-trade Sharpe {s:+.2f}")
            print(f"{'shape':15s}" + "".join(f"{n:>7d}" for n in NS))
            for sh in SHAPES:
                row = [c for c in cells if c["shape"] == sh and c["true_sr"] == s]
                row.sort(key=lambda c: c["n"])
                print(f"{sh:15s}" + "".join(f"{c[conv]['accept_rate']:7.3f}" for c in row))
    print("\n=== FAILURE ATTRIBUTION, convention A, coin_1to1 (fraction of samples failing each gate) ===")
    for s in EDGES:
        for n in NS:
            c = next(c for c in cells if c["shape"] == "coin_1to1" and c["true_sr"] == s and c["n"] == n)
            print(f"sr={s:+.2f} n={n:4d} " + " ".join(f"{k}={v:.2f}" for k, v in sorted(c['A_nb1_var0']['fail_rate_by_gate'].items())))
    print(f"\nsaved={path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
