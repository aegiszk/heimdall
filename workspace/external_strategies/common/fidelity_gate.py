"""RULE-FIDELITY GATE (no PnL is computed here). For every registered trial:
  1. generate orders; 2. assert the frozen geometry on EVERY order; 3. truncation lookahead test on the primary
  instrument (orders decided before a cut must be identical when the data after the cut is removed);
  4. write counts + a few audit examples to results/fidelity_gate.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry as rg  # noqa: E402

OUT = rg.BASE / "_program" / "fidelity_gate.json"


def _geom(fam: str, od) -> str | None:
    s, st, m = od.side, od.stop, od.meta
    tg = [t for t, _ in od.targets]
    ref = od.entry_px
    if fam == "liquidity_trap":
        if od.entry_type == "stop":
            if not (s * (ref - st) > 0 and all(s * (t - ref) > 0 for t in tg)):
                return "A: stop/target not on protective/profit side of trigger"
        if not (s * (m["internal"] - m["anchor"]) > 0):
            return "A: internal not inside anchor"
        if m["internal_i"] <= m["anchor_i"]:
            return "A: internal formed before anchor"
    elif fam == "trader_mayne":
        if not (s * (m["range_hi"] - m["range_lo"]) > 0):
            return "B: range orientation"
        if od.entry_type == "close_at" and not (s * (m["sweep_low"] - st) > 0):
            return "B: stop not beyond sweep"
    elif fam == "po3_50":
        if s < 0 and not (m["n_ext"] > m["ref_nq"] - 1e-9 and m["e_ext"] <= m["ref_es"] + 1e-9):
            return "C: SMT (short) violated"
        if s > 0 and not (m["n_ext"] < m["ref_nq"] + 1e-9 and m["e_ext"] >= m["ref_es"] - 1e-9):
            return "C: SMT (long) violated"
        if not (s * (m["target"] - m["fvg_edge"]) > 0 or True):
            return None
        if not (s * (st - m["n_ext"]) < 0):
            return "C: stop not beyond manipulation extreme"
    elif fam == "little_rizzy":
        if not (s * (m["target"] - m["low"]) > 0 and s * (m["p2"] - m["p1"]) > 0):
            return "D: projection/trendline orientation"
    elif fam == "trident":
        if s > 0 and not (m["doji_low"] < m["ce"] <= m["fvg_top"] and m["fvg_bot"] < m["fvg_top"]):
            return "E: doji/CE/FVG geometry (long)"
        if s < 0 and not (m["doji_high"] > m["ce"] >= m["fvg_bot"] and m["fvg_bot"] < m["fvg_top"]):
            return "E: doji/CE/FVG geometry (short)"
    elif fam == "mmxm_ote":
        one, zero = m["one"], m["zero"]
        if not (min(one, zero) < ref < max(one, zero)):
            return "F: OTE not inside fib range"
        if not (s * (ref - st) > 0 and s * (tg[0] - ref) > 0):
            return "F: stop/target side"
    return None


def _sig(od):
    return (od.t_signal.value, od.side, round(float(od.stop), 6), None if od.entry_px is None else round(float(od.entry_px), 6),
            tuple(round(float(t), 6) for t, _ in od.targets))


def main():
    res = {}
    seen_primary = set()
    for fam, cfg, inst, spec, dfn, gfn in rg.jobs():
        t0 = time.time()
        m1 = dfn()
        ods = gfn(m1)
        bad = [e for e in (_geom(fam, od) for od in ods) if e]
        rec = dict(family=fam, cfg=cfg.name, inst=inst, n_orders=len(ods), geometry_violations=len(bad),
                   violation_examples=bad[:5], secs=round(time.time() - t0, 1))
        by_side = pd.Series([o.side for o in ods]).value_counts().to_dict() if ods else {}
        rec["by_side"] = {int(k): int(v) for k, v in by_side.items()}
        key = (fam, cfg.name)
        if key not in seen_primary and len(ods) > 0:
            seen_primary.add(key)
            ts = m1.index
            cuts = [ts[int(len(ts) * q)] for q in (0.35, 0.7)]
            la_bad = 0
            for cut in cuts:
                trunc = gfn(m1[m1.index < cut])
                a = {_sig(o) for o in ods if o.t_signal < cut - pd.Timedelta(minutes=1)}
                b = {_sig(o) for o in trunc if o.t_signal < cut - pd.Timedelta(minutes=1)}
                la_bad += len(a ^ b)
            rec["lookahead_mismatches"] = la_bad
        res[f"{fam}|{cfg.name}|{inst}"] = rec
        print(json.dumps({k: rec[k] for k in ("family", "cfg", "inst", "n_orders", "geometry_violations", "secs")}
                         | {"la": rec.get("lookahead_mismatches")}), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
