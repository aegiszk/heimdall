"""Pre-PnL frequency funnels (COUNTS ONLY; no outcome is computed). Agent 2 own code.
PO3 (C): days -> NQ sweeps its 09:00-hour high or low during 10:00-11:00 -> ES did NOT sweep its own same-side
          09:00-hour extreme during 10:00-11:00 (SMT) .
Trident (E1): EURUSD 30m bars, DEV 2022-2024: bullish FVGs with middle candle 03:00-06:30 -> a later in-window doji
          (body<=25% range) -> doji low < FVG 50% -> doji open&close >= FVG top -> next bar closes < doji high
          (in window) -> EMA 5>9>13>21 -> close > EMA200.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a2_engine import ET, load_cme  # noqa: E402
from replicate_F1 import load_dev  # noqa: E402

HERE = Path(__file__).resolve().parent


def hour_ext(m1):
    et = m1.index.tz_convert(ET).tz_localize(None)
    d = pd.DataFrame({"h": m1["high"].to_numpy(), "l": m1["low"].to_numpy(), "day": et.normalize(), "hr": et.hour},
                     index=m1.index)
    d = d[(d.day.dt.dayofweek < 5) & d.hr.isin([9, 10])]
    return d.groupby(["day", "hr"]).agg(h=("h", "max"), l=("l", "min")).unstack("hr")


def po3():
    nq, es = hour_ext(load_cme("MNQ")), hour_ext(load_cme("ES"))
    j = nq.join(es, lsuffix="_nq", rsuffix="_es", how="inner").dropna()
    nq_hi = j[("h_nq", 10)] > j[("h_nq", 9)] if ("h_nq", 10) in j else None
    # column names after join are tuples; rebuild simply
    j.columns = [f"{a}{b}" for a, b in j.columns]
    up_nq, dn_nq = j.h_nq10 > j.h_nq9, j.l_nq10 < j.l_nq9
    up_es, dn_es = j.h_es10 > j.h_es9, j.l_es10 < j.l_es9
    days = len(j)
    yrs = days / 252
    sweep_any = (up_nq | dn_nq).sum()
    smt_short = (up_nq & ~up_es).sum()
    smt_long = (dn_nq & ~dn_es).sum()
    return dict(sessions=days, nq_sweeps_09h_extreme_in_10h=int(sweep_any),
                smt_bear=int(smt_short), smt_bull=int(smt_long),
                smt_setups_per_year_upper_bound=round((smt_short + smt_long) / yrs, 1),
                agent1_C1_trades_per_year=22.1)


def trident():
    m1 = load_dev("EURUSD")
    et = m1.index.tz_convert(ET).tz_localize(None)
    g = m1.assign(k=et.floor("30min")).groupby("k", sort=True)
    b = pd.DataFrame({"o": g["open"].first(), "h": g["high"].max(), "l": g["low"].min(), "c": g["close"].last()})
    key = b.index; b = b.reset_index(drop=True)
    O, H, L, C = (b[c].to_numpy() for c in "ohlc")
    tod = key.hour * 60 + key.minute
    inw = (tod >= 180) & (tod < 390)
    e = {n: pd.Series(C).ewm(span=n, adjust=False).mean().to_numpy() for n in (5, 9, 13, 21, 200)}
    f = dict(fvg=0, doji=0, wick_ce=0, body_above=0, confirm=0, ema_stack=0, ema200=0)
    for i in range(2, len(C) - 2):
        if not (L[i] > H[i - 2] and inw[i - 1]):
            continue
        f["fvg"] += 1
        top, bot = L[i], H[i - 2]
        ce = (top + bot) / 2
        best = 0
        for d in range(i + 1, min(i + 8, len(C) - 1)):
            if not (inw[d] and inw[d + 1]):
                break
            rng = H[d] - L[d]
            lvl = 0
            if rng > 0 and abs(C[d] - O[d]) <= .25 * rng:
                lvl = 1
                if L[d] < ce:
                    lvl = 2
                    if min(O[d], C[d]) >= top:
                        lvl = 3
                        if C[d + 1] < H[d]:
                            lvl = 4
                            if e[5][d + 1] > e[9][d + 1] > e[13][d + 1] > e[21][d + 1]:
                                lvl = 5
                                if C[d + 1] > e[200][d + 1]:
                                    lvl = 6
            best = max(best, lvl)
            if lvl == 6:
                break
        for n_, k_ in enumerate(("doji", "wick_ce", "body_above", "confirm", "ema_stack", "ema200"), start=1):
            if best >= n_:
                f[k_] += 1
    return {k: round(v / 3, 1) for k, v in f.items()} | {"unit": "per year, EURUSD, DEV 2022-2024",
                                                         "agent1_E1_EURUSD_trades_total": 2}


if __name__ == "__main__":
    res = {"PO3": po3(), "Trident_EURUSD": trident()}
    print(json.dumps(res, indent=1, default=str))
    (HERE / "frequency_funnels_result.json").write_text(json.dumps(res, indent=1, default=str))
