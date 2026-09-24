"""Artifact test for the 'fade after same-side runs / same-ms sweeps' result.

Concern: the aggressor-adjusted mid (px - side*0.5 tick) assumes a 1-tick spread. Right after a sweep the spread can be
wider, which overstates the mid in the sweep direction and would manufacture apparent reversion as the spread closes.
Test: keep only events whose ENTRY (t+250 ms) and EXIT (t+250 ms+h) references are confirmed at a 1-tick spread, where
'confirmed' = the reference trade and the most recent opposite-side trade within the previous 1 s differ by exactly
1 tick. Compare the markout on this verified subset with all events. Same families, thresholds and data as the atlas.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import nq_event_atlas as A

FAMS = ["E1_same_side_run_k8", "E1_same_side_run_k16", "E7_same_ms_sweep_k5", "E7_same_ms_sweep_k10",
        "E6_small_seq_1lot_k20", "E4_large_print_ge100", "BASE_every1000th_trade_dir=aggr"]
H = (10000, 60000)


def spread_ok(us, px, s, j):
    """True if trade j and the latest opposite-side trade within the prior 1 s differ by exactly 1 tick."""
    ok = np.zeros(len(j), bool)
    last_b = pd.Series(np.where(s > 0, np.arange(len(s)), np.nan)).ffill().to_numpy()
    last_s = pd.Series(np.where(s < 0, np.arange(len(s)), np.nan)).ffill().to_numpy()
    opp = np.where(s[j] > 0, last_s[j], last_b[j])
    valid = ~np.isnan(opp)
    o = opp[valid].astype(np.int64)
    jj = j[valid]
    ok[valid] = (us[jj] - us[o] <= 1_000_000) & (np.abs(px[jj] - px[o]) == A.TICK)
    return ok


def main():
    days = []
    for c, lo, hi in A.ROLLS:
        d = A.load_contract(c, lo, hi)
        days += [g.reset_index(drop=True) for _, g in d.groupby("tday") if len(g) > 5000]
    P = json.loads(Path("nq_event_atlas_registry.json").read_text())["thresholds"]
    rows = []
    for g in days:
        us, px, v, s, mid, csv, cnt = A.day_arrays(g)
        E = A.families(us, px, v, s, mid, csv, cnt, P)
        bi = np.arange(0, len(us), 1000)
        E["BASE_every1000th_trade_dir=aggr"] = (bi, s[bi].astype(float))
        for fam in FAMS:
            idx, d = E[fam]
            idx = np.asarray(idx, dtype=np.int64)
            d = np.asarray(d, float)
            if len(idx) == 0:
                continue
            jl = np.searchsorted(us, us[idx] + A.LAT_MS * 1000, side="right") - 1
            ok_in = spread_ok(us, px, s, jl)
            for h in H:
                j2 = np.searchsorted(us, us[idx] + (A.LAT_MS + h) * 1000, side="right") - 1
                x = d * (mid[j2] - mid[jl]) / A.TICK
                ok = ok_in & spread_ok(us, px, s, j2)
                rows.append(pd.DataFrame({"fam": fam, "h": h, "x": x, "verified": ok, "day": str(g.tday.iloc[0])}))
    R = pd.concat(rows, ignore_index=True)
    out = {}
    for (fam, h), g in R.groupby(["fam", "h"]):
        def stat(z):
            dm = z.groupby("day").x.mean()
            return {"n": int(len(z)), "mean": round(float(z.x.mean()), 3), "median": float(z.x.median()),
                    "t_day": round(float(dm.mean() / (dm.std(ddof=1) / np.sqrt(len(dm)))), 2)}
        out[f"{fam}|x{h}"] = {"all": stat(g), "spread_verified_1tick": stat(g[g.verified]),
                              "verified_share": round(float(g.verified.mean()), 3)}
        print(fam, h, out[f"{fam}|x{h}"], flush=True)
    Path("spread_artifact_test.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
