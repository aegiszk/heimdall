"""Extend the 2026-09-22 power map: N needed for 80% acceptance of the PRODUCTION gate (convention A)
and of the proposed DISCOVERY rule, per-trade Sharpe 0.05/0.10/0.20/0.30. Read-only use of core/tools.

Discovery rule simulated here (proposal, not production):
  t = Newey-West t of per-trade net PnL (production metrics.newey_west_tstat)
  PASS if t > z_{0.90} = 1.2816 (one-sided alpha 0.10), FAIL if the one-sided 95% upper bound of the
  per-trade Sharpe (sr_hat + 1.645/sqrt(N)) < s_min, else INCONCLUSIVE.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from core.config import DEFAULT_GATE_CFG  # noqa: E402
from core.validation.battery import run_gate  # noqa: E402
from core.validation import metrics as m  # noqa: E402
from tools.audit_power_map import sample  # noqa: E402

CAP = 50_000.0
SD = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0  # per-trade sd in USD
GRID = {0.05: [1000, 2000, 3000, 4500, 6500], 0.10: [300, 500, 800, 1200, 2000],
        0.20: [100, 200, 300, 500], 0.30: [50, 100, 150, 200, 300], 0.0: [30, 100, 500, 2000]}
REPS = 150


def cell(shape, s, n, s_min, rng):
    acc = disc_pass = disc_fail = 0
    for _ in range(REPS):
        x = sample(shape, s, n, rng) * (SD / 20.0) / CAP  # sample() already returns sd=$20
        g = run_gate(x, DEFAULT_GATE_CFG, 1, 0.0, active_returns=x, n_params=3)
        acc += g.passed
        t = m.newey_west_tstat(x)
        sr = m.sharpe(x)
        if t > 1.2816:
            disc_pass += 1
        elif sr + 1.645 / np.sqrt(n) < s_min:
            disc_fail += 1
    return {"shape": shape, "true_sr": s, "n": n, "gate_A_accept": acc / REPS,
            "discovery_pass": disc_pass / REPS, "discovery_fail": disc_fail / REPS}


if __name__ == "__main__":
    rng = np.random.default_rng(20260923)
    out = []
    for s, ns in GRID.items():
        for n in ns:
            for shape in (["coin_1to1", "ar1_0.3"] if s in (0.0, 0.20) else ["coin_1to1"]):
                r = cell(shape, s, n, s_min=max(s, 0.10), rng=rng)
                out.append(r)
                print(json.dumps(r), flush=True)
    (HERE / f"power_extend_sd{int(SD)}.json").write_text(json.dumps({"reps": REPS, "sd_dollars": SD, "cells": out}, indent=1))
