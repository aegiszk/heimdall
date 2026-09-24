"""Agent 2 independent replication of Family A (liquidity trap), from PREREGISTRATION.md + SOURCE_MATRIX.md.
Also re-runs A1 with the preregistered order wording ('stop order 1 tick beyond' = trigger -> market) to measure
whether the post-result choice of a LIMIT order in BUGFIX_A_ENTRY changes anything."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a2_engine import ET, MNQ, Ord, Tape, bars, cluster_ci, load_cme, sequence, strict_pivots  # noqa: E402

HERE = Path(__file__).resolve().parent
A1DIR = HERE.parents[0] / "external_strategies" / "liquidity_trap" / "results"


def signals(m1: pd.DataFrame, k: int, targets: str, kind: str, tick=0.25, stop_ticks=2):
    b = bars(m1, 5)
    H, L, C = b["high"].to_numpy(), b["low"].to_numpy(), b["close"].to_numpy()
    ph, pl = strict_pivots(H, L, k)
    end = pd.DatetimeIndex(b["end"])
    sday = (pd.DatetimeIndex(b["key"]) + pd.Timedelta(hours=6)).normalize().to_numpy()
    ud = np.unique(sday)
    prev = {ud[i]: ud[i - 1] for i in range(1, len(ud))}
    book = {1: [], -1: []}   # side of level: +1 highs, -1 lows; entries: [price, i, day, anchor, taken]
    orders, seen = [], set()
    for j in range(len(b)):
        for s in book[1]:
            if s[4] is None and H[j] > s[0]:
                s[4] = j
        for s in book[-1]:
            if s[4] is None and L[j] < s[0]:
                s[4] = j
        p = j - k
        if p >= k:
            for flag, lvl, sgn in ((ph[p], H[p], 1), (pl[p], L[p], -1)):
                if flag:
                    anc = any(s[4] is not None and p - k <= s[4] <= p and s[1] < p for s in book[sgn])
                    book[sgn].append([lvl, p, sday[p], anc, None])
        cur = sday[j]
        keep = {cur, prev.get(cur, cur)}
        for sgn in (1, -1):
            book[sgn] = [s for s in book[sgn] if s[2] in keep]
        et = end[j].tz_convert(ET).tz_localize(None)
        d0 = et.normalize()
        wo, wc, fl = d0 + pd.Timedelta(hours=9, minutes=30), d0 + pd.Timedelta(hours=11, minutes=30), d0 + pd.Timedelta(hours=12)
        if not (wo - pd.Timedelta(minutes=5) <= et < wc):
            continue
        for side, sgn in ((-1, 1), (1, -1)):
            live = [s for s in book[sgn] if s[4] is None]
            opp_live = [s for s in book[-sgn] if s[4] is None]
            for a in live:
                if not a[3]:
                    continue
                for h in live:
                    if h[1] <= a[1] or not ((h[0] < a[0]) if side < 0 else (h[0] > a[0])):
                        continue
                    key = (side, a[1], h[1])
                    if key in seen:
                        continue
                    opp = [s for s in opp_live if ((s[0] < h[0]) if side < 0 else (s[0] > h[0]))]
                    if not opp:
                        continue
                    seen.add(key)
                    opp.sort(key=lambda s: abs(s[0] - h[0]))
                    P = h[0] + tick if side < 0 else h[0] - tick
                    stop = a[0] + stop_ticks * tick if side < 0 else a[0] - stop_ticks * tick
                    tg = [(opp[0][0], .5), (opp[1][0], .5)] if targets == "split" and len(opp) >= 2 else [(opp[0][0], 1.0)]
                    t0 = max(end[j], wo.tz_localize(ET).tz_convert("UTC"))
                    meta = dict(t_signal=t0, internal=h[0], anchor=a[0])
                    od = Ord(side, t0, kind, P, stop, tg, wc.tz_localize(ET).tz_convert("UTC"),
                             fl.tz_localize(ET).tz_convert("UTC"), be_after_first=(targets == "split"), meta=meta)
                    if kind == "close_at":
                        od = close_confirm(od, h[0], H, L, C, end, j)
                        if od is None:
                            continue
                    orders.append(od)
    return orders


def close_confirm(od, lvl, H, L, C, end, j0):
    for j in range(j0 + 1, len(H)):
        if end[j] > od.expiry:
            return None
        if od.side < 0:
            if H[j] >= od.stop:
                return None
            if H[j] > lvl:
                return Ord(od.side, end[j], "close_at", None, od.stop, od.targets, None, od.flat, od.be_after_first, od.meta) if C[j] < lvl else None
        else:
            if L[j] <= od.stop:
                return None
            if L[j] < lvl:
                return Ord(od.side, end[j], "close_at", None, od.stop, od.targets, None, od.flat, od.be_after_first, od.meta) if C[j] > lvl else None
    return None


def compare(mine: pd.DataFrame, theirs: pd.DataFrame) -> dict:
    a = mine.assign(k=pd.to_datetime(mine["t_entry"]).astype("int64") // 10**9 * 10 + mine["side"])
    t = theirs.assign(k=pd.to_datetime(theirs["t_entry"]).astype("int64") // 10**9 * 10 + theirs["side"])
    j = a.merge(t, on="k", suffixes=("_a2", "_a1"))
    fld = {}
    for c in ("entry", "stop0", "R"):
        fld[c] = int((~np.isclose(j[f"{c}_a2"], j[f"{c}_a1"], atol=1e-6)).sum())
    fld["t_exit"] = int((pd.to_datetime(j["t_exit_a2"]) != pd.to_datetime(j["t_exit_a1"])).sum())
    fld["reason"] = int((j["reason_a2"] != j["reason_a1"]).sum())
    return dict(n_a2=len(a), n_a1=len(t), matched=len(j), only_a2=len(a) - len(j), only_a1=len(t) - len(j),
                field_mismatch_on_matched=fld)


def summ(df):
    lo, hi = cluster_ci(df)
    return dict(n=len(df), mean_R=round(float(df.R.mean()), 4), win=round(float((df.R > 0).mean()), 3),
                ci95=[round(lo, 3), round(hi, 3)])


if __name__ == "__main__":
    m1 = load_cme("MNQ")
    tp = Tape(m1, MNQ)
    runs = {"A1_k1_spike_nearest_fix1": (1, "nearest", "limit"), "A2_k2_spike_nearest_fix1": (2, "nearest", "limit"),
            "A3_k1_spike_split_fix1": (1, "split", "limit"), "A4_k1_close_nearest": (1, "nearest", "close_at"),
            "A1_PREREG_WORDING_trigger_market": (1, "nearest", "trigger")}
    res = {}
    for name, (k, tg, kind) in runs.items():
        df = sequence(tp, signals(m1, k, tg, kind))
        df.to_csv(HERE / f"a2_trades_{name}_MNQ.csv", index=False)
        r = summ(df)
        f = A1DIR / f"trades_{name}_MNQ.csv"
        if f.exists():
            r["vs_agent1"] = compare(df, pd.read_csv(f))
        res[name] = r
        print(name, json.dumps(r), flush=True)
    (HERE / "replicate_A_result.json").write_text(json.dumps(res, indent=1, default=str))
