"""Agent 2 independent replication of B4_H4_OB_limit (Trader Mayne direct HTF OB entry) + matched random-entry
placebo. Built from PREREGISTRATION.md B4 row + SOURCE_MATRIX.md definitions (long; short mirrors):
  4h bars anchored 18:00 ET; k=1 strict pivots (confirmed at i+1).
  MSB: bar m closes above the most recent confirmed, still-untaken swing high S.
  Range low = lowest low in (S.i, m]; range high = first pivot high confirmed after m.
  OB = up to 3 consecutive bearish candles ending at the range-low bar; OB top/bottom = body extremes.
  Order at range-high confirmation: BUY LIMIT at OB top, stop OB bottom - 1 tick, target range high;
  require OB top <= 50% of range and (target - entry) >= 2 * (entry - stop).
  Expiry: 30 HTF bars, or an HTF close below range low, or price reaching range high before the fill.
  Management: stop -> entry once +2R is touched; 12-day max hold.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a2_engine import ET, MNQ, Ord, Tape, cluster_ci, load_cme, sequence, strict_pivots  # noqa: E402
from compare_trades import compare  # noqa: E402

HERE = Path(__file__).resolve().parent
THEIRS = HERE.parents[0] / "external_strategies" / "trader_mayne" / "results" / "trades_B4_H4_OB_limit_MNQ.csv"


def bars4h(m1):
    et = m1.index.tz_convert(ET).tz_localize(None)
    key = (et - pd.Timedelta(hours=18)).floor("4h") + pd.Timedelta(hours=18)
    g = m1.assign(k=key, t=m1.index).groupby("k", sort=True)
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "end": g["t"].max() + pd.Timedelta(minutes=1)})
    return b.reset_index(drop=True)


def setups(b: pd.DataFrame, side: int, tick=0.25):
    s = side
    O, H, L, C = (b[c].to_numpy() for c in ("open", "high", "low", "close"))
    if s < 0:  # mirror by negation
        O, H, L, C = -O, -L, -H, -C
    end = pd.DatetimeIndex(b["end"])
    ph, _ = strict_pivots(H, L, 1)
    out = []
    swings = []            # [price, i, taken]
    for j in range(len(C)):
        for sw in swings:
            if not sw[2] and H[j] > sw[0]:
                sw[2] = True if C[j] <= sw[0] else "msb"
        # MSB on bar j: close above most recent confirmed untaken swing high
        live = [sw for sw in swings if sw[2] in (False, "msb")]
        cand = [sw for sw in live if sw[2] == "msb"]
        for sw in cand:
            sw[2] = True
            si, m = sw[1], j
            seg = np.arange(si + 1, m + 1)
            li = int(seg[np.argmin(L[seg])])
            ob = []
            x = li
            while x > si and len(ob) < 3 and C[x] < O[x]:
                ob.append(x); x -= 1
            if not ob:
                continue
            ob_top = max(O[x_] for x_ in ob); ob_bot = min(C[x_] for x_ in ob)
            # range high = first pivot high confirmed after m
            rh = next((p for p in range(m + 1, len(C) - 1) if ph[p]), None)
            if rh is None:
                continue
            conf = rh + 1
            lo, hi = L[li], H[rh]
            entry, stop = ob_top, ob_bot - tick
            if not (entry <= (lo + hi) / 2 and (hi - entry) >= 2 * (entry - stop) and entry > stop):
                continue
            # expiry: 30 HTF bars after confirmation, earlier if HTF close < range low or high >= target
            exp = min(conf + 30, len(C) - 1)
            for q in range(conf + 1, exp + 1):
                if C[q] < lo or H[q] >= hi:
                    exp = q
                    break
            f = (lambda v: v) if s > 0 else (lambda v: -v)
            out.append(Ord(s, end[conf], "limit", f(entry), f(stop), [(f(hi), 1.0)], end[exp], None,
                           meta=dict(t_signal=end[conf], rng_lo=f(lo), rng_hi=f(hi), ob_top=f(entry), be2R=f(entry + 2 * (entry - stop)))))
        p = j - 1
        if p >= 1 and ph[p]:
            swings.append([H[p], p, False])
    return out


if __name__ == "__main__":
    m1 = load_cme("MNQ")
    b = bars4h(m1)
    ods = setups(b, 1) + setups(b, -1)
    tp = Tape(m1, MNQ)
    df = sequence(tp, ods)
    df.to_csv(HERE / "a2_trades_B4_MNQ.csv", index=False)
    lo, hi = cluster_ci(df) if len(df) > 5 else (None, None)
    res = dict(n_orders=len(ods), n=len(df), mean_R=float(df.R.mean()) if len(df) else None, ci95=[lo, hi],
               vs_agent1=compare(df, pd.read_csv(THEIRS)) if len(df) else None)
    print(json.dumps(res, default=str))
    (HERE / "replicate_B4_result.json").write_text(json.dumps(res, indent=1, default=str))
