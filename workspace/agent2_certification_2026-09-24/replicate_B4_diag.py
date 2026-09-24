"""B4 fidelity diagnostic (NOT blind: written after reading Agent 1's trader_mayne/strategy.py to locate the
divergence found by the blind build replicate_B4.py). Own code, Agent 1's disclosed structural choices:
  - swing = LAST confirmed k=1 pivot (overwritten by each new pivot); MSB = close beyond it (then cleared)
  - leg extreme over [swing_i, msb_i]; OB = <=3 consecutive opposite candles ending at/<=2 bars before leg bar,
    OB edges = wick extremes; range target = first pivot confirmed after (p >= msb_i)
Variants:
  a) expiry = 30 HTF bars only                       (Agent 1 ob_limit path)
  b) expiry = 30 bars OR HTF close beyond range extreme OR target traded before fill   (PREREGISTRATION B4 row)
Placebo: every (b)-variant... no: every variant-(a) trade re-entered at MARKET at a random minute (seeded) with the
same side, stop distance, target distance and +2R break-even -> is the entry better than random?
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a2_engine import MNQ, Ord, Tape, cluster_ci, load_cme, sequence, strict_pivots, fill  # noqa: E402
from compare_trades import compare  # noqa: E402
from replicate_B4 import bars4h  # noqa: E402

HERE = Path(__file__).resolve().parent
THEIRS = HERE.parents[0] / "external_strategies" / "trader_mayne" / "results" / "trades_B4_H4_OB_limit_MNQ.csv"


def ob(O, C, H, L, leg, side):
    bad = (C < O) if side > 0 else (C > O)
    j = leg
    while j >= 0 and not bad[j] and leg - j < 3:
        j -= 1
    if j < 0 or not bad[j]:
        return None
    k = j
    while k - 1 >= 0 and bad[k - 1] and j - (k - 1) < 3:
        k -= 1
    return float(L[k:j + 1].min()), float(H[k:j + 1].max())


def setups(b):
    O, H, L, C = (b[c].to_numpy() for c in ("open", "high", "low", "close"))
    end = pd.DatetimeIndex(b["end"])
    ph, pl = strict_pivots(H, L, 1)
    n, out = len(C), []
    sh = sl = None
    pend = {1: None, -1: None}
    for j in range(n):
        p = j - 1
        if p >= 1 and ph[p]:
            sh = (H[p], p)
            pe = pend[1]
            if pe and p >= pe["m"]:
                out.append((1, pe["lo"], H[p], pe["ob"], j)); pend[1] = None
        if p >= 1 and pl[p]:
            sl = (L[p], p)
            pe = pend[-1]
            if pe and p >= pe["m"]:
                out.append((-1, pe["lo"], L[p], pe["ob"], j)); pend[-1] = None
        if sh is not None and C[j] > sh[0]:
            leg = sh[1] + int(np.argmin(L[sh[1]:j + 1])); o_ = ob(O, C, H, L, leg, 1)
            if o_:
                pend[1] = dict(m=j, lo=float(L[leg]), ob=o_)
            sh = None
        if sl is not None and C[j] < sl[0]:
            leg = sl[1] + int(np.argmax(H[sl[1]:j + 1])); o_ = ob(O, C, H, L, leg, -1)
            if o_:
                pend[-1] = dict(m=j, lo=float(H[leg]), ob=o_)
            sl = None
    return out, C, H, L, end


def orders(b, prereg_expiry: bool):
    st, C, H, L, end = setups(b)
    n, ods = len(C), []
    for side, lo, hi, (olo, ohi), j in st:
        px = ohi if side > 0 else olo
        stop = olo - .25 if side > 0 else ohi + .25
        if abs(hi - px) < 2 * abs(px - stop) or (side > 0 and px > (lo + hi) / 2) or (side < 0 and px < (lo + hi) / 2):
            continue
        ex = min(n - 1, j + 30)
        if prereg_expiry:
            for q in range(j + 1, ex + 1):
                if (side > 0 and (C[q] < lo or H[q] >= hi)) or (side < 0 and (C[q] > lo or L[q] <= hi)):
                    ex = q
                    break
        ods.append(Ord(side, end[j], "limit", px, stop, [(hi, 1.0)], end[ex], None,
                       meta=dict(t_signal=end[j], tgt=hi), be_level=px + side * 2 * abs(px - stop)))
    return ods


def summ(df):
    lo, hi = cluster_ci(df)
    return dict(n=len(df), mean_R=round(float(df.R.mean()), 3), win=round(float((df.R > 0).mean()), 3),
                ci95=[round(lo, 3), round(hi, 3)], reasons=df.reason.value_counts().to_dict())


def placebo(tp: Tape, trades: pd.DataFrame, reps: int = 50, seed: int = 3):
    rng = np.random.default_rng(seed)
    n = len(tp.t)
    means = []
    for _ in range(reps):
        rs = []
        for _, t in trades.iterrows():
            side, risk = int(t.side), abs(t.entry - t.stop0)
            tdist = abs(t.tgt - t.entry)
            i = int(rng.integers(1, n - 20000))
            e = tp.o[i] + side * .25
            od = Ord(side, tp.ix[i], "close_at", None, e - side * risk, [(e + side * tdist, 1.0)], None, None,
                     meta=dict(t_signal=tp.ix[i]), be_level=e + side * 2 * risk)
            od.t0 = tp.ix[i]          # close_at at minute i-1 close ~ market at i
            r = fill(tp, od)
            if r is not None:
                rs.append(r["R"])
        means.append(np.mean(rs))
    return dict(reps=reps, placebo_mean_R=round(float(np.mean(means)), 3),
                placebo_p05_p95=[round(float(np.percentile(means, 5)), 3), round(float(np.percentile(means, 95)), 3)])


if __name__ == "__main__":
    m1 = load_cme("MNQ")
    b = bars4h(m1)
    tp = Tape(m1, MNQ)
    res = {}
    a = sequence(tp, orders(b, False))
    res["a_agent1_expiry"] = summ(a) | {"vs_agent1": compare(a, pd.read_csv(THEIRS))}
    bb = sequence(tp, orders(b, True))
    res["b_prereg_expiry"] = summ(bb)
    res["placebo_random_entry_same_geometry"] = placebo(tp, a)
    print(json.dumps(res, indent=1, default=str))
    (HERE / "replicate_B4_diag_result.json").write_text(json.dumps(res, indent=1, default=str))
