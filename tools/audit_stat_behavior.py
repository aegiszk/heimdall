"""V3 validation audit: small-sample / dependence behaviour of individual gates.

Measures, on synthetic streams whose truth is known:
  1. sign-flip MC p (battery._active_return_mc_p) false-positive rate under ZERO-MEAN SKEWED nulls
     (the sign-flip null assumes a symmetric distribution);
  2. per-gate standalone false-positive rate at true SR = 0 (nw_t > 2, boot_lo > 0, dsr > 0.95);
  3. iid bootstrap Sharpe 95% CI coverage under AR(1) dependence.
No thresholds are changed; production functions are called as-is.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.validation import metrics as m
from core.validation.battery import _active_return_mc_p
from tools.audit_power_map import sample

REPS = 300


def _null_cell(args):
    shape, n, seed = args
    rng = np.random.default_rng(seed)
    hits = {"mc_signflip_p<0.05": 0, "nw_t>2": 0, "boot_lo>0": 0, "dsr_nb1>0.95": 0}
    for _ in range(REPS):
        r = sample(shape, 0.0, n, rng) / 50_000
        hits["mc_signflip_p<0.05"] += _active_return_mc_p(r, n=1000, seed=int(rng.integers(1 << 30))) < 0.05
        hits["nw_t>2"] += m.newey_west_tstat(r) > 2.0
        hits["boot_lo>0"] += m.bootstrap_sharpe_ci(r, B=1000, seed=int(rng.integers(1 << 30)))[0] > 0.0
        hits["dsr_nb1>0.95"] += m.deflated_sharpe_ratio(r, 0.0, 1) > 0.95
    return {"shape": shape, "n": n, **{k: v / REPS for k, v in hits.items()}}


def _coverage_cell(args):
    phi, n, seed = args
    rng = np.random.default_rng(seed)
    true_sr, cover = 0.1, 0
    for _ in range(REPS):
        e = rng.standard_normal(n) * np.sqrt(1 - phi**2)
        z = np.empty(n)
        z[0] = rng.standard_normal()
        for i in range(1, n):
            z[i] = phi * z[i - 1] + e[i]
        lo, hi = m.bootstrap_sharpe_ci(z + true_sr, B=1000, seed=int(rng.integers(1 << 30)))
        cover += lo <= true_sr <= hi
    return {"phi": phi, "n": n, "coverage_95": cover / REPS}


def main() -> int:
    null_jobs = [(sh, n, 7_000 + i) for i, (sh, n) in enumerate(
        (sh, n) for sh in ["coin_1to1", "low_win_4to1", "high_win_1to4", "pos_skew", "neg_skew", "fat_tail_t3", "ar1_0.3"]
        for n in [10, 20, 30, 100])]
    cov_jobs = [(phi, n, 9_000 + i) for i, (phi, n) in enumerate((phi, n) for phi in [0.0, 0.3, 0.6] for n in [30, 100, 300])]
    with ProcessPoolExecutor(max_workers=18) as pool:
        nulls = list(pool.map(_null_cell, null_jobs))
        cover = list(pool.map(_coverage_cell, cov_jobs))
    out = ROOT / "data" / "validation_audit" / "stat_behavior_2026-09-22.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"reps": REPS, "null_false_positive": nulls, "bootstrap_coverage": cover}, indent=1) + "\n")
    print("NULL (true SR = 0) standalone false-positive rate per gate  [nominal ~0.025-0.05]")
    for row in nulls:
        print(f"{row['shape']:14s} n={row['n']:4d} " + " ".join(f"{k}={row[k]:.3f}" for k in row if k not in ('shape', 'n')))
    print("\niid bootstrap Sharpe 95% CI coverage (nominal 0.95)")
    for row in cover:
        print(f"phi={row['phi']:.1f} n={row['n']:4d} coverage={row['coverage_95']:.3f}")
    print(f"saved={out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
