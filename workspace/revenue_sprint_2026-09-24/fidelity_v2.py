"""Pre-PnL fidelity gate for TRIDENT_V2 and MMXM_V2 on the FX/XAU DEV window only (2022-01-01..2024-12-31).
Signals only: counts, per-year frequency, geometry assertions, truncation lookahead. NO fills, NO PnL."""
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "external_strategies" / "common"))
import registry as rg  # noqa: E402  (fx_dev enforces the DEV window)


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / name / "strategy.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


T, M = load("trident_v2"), load("mmxm_v2")
DEV_END = pd.Timestamp("2025-01-01", tz="UTC")


def geom_t(o):
    m = o.meta
    ok = m["doji_low"] < m["ce"] < m["fvg_top"] and m["fvg_bot"] < m["fvg_top"] and m["ctx_ema_stack"]
    return ok and o.side == 1


def geom_m(o):
    m, s = o.meta, o.side
    lo, hi = min(m["one"], m["zero"]), max(m["one"], m["zero"])
    return lo < o.entry_px < hi and s * (o.entry_px - o.stop) > 0 and s * (o.targets[0][0] - o.entry_px) > 0


def sig(o):
    return (o.t_signal.value, o.side, round(float(o.stop), 8), None if o.entry_px is None else round(float(o.entry_px), 8))


out = {}
for fam, mod, pairs, gen, geom in (
        ("TRIDENT_V2", T, T.PAIRS, lambda m, p: T.generate(m, T.Cfg(), p, rg.PIP[p]), geom_t),
        ("MMXM_V2", M, M.PAIRS, lambda m, p: M.generate(m, M.Cfg()), geom_m)):
    rows = {}
    for p in pairs:
        m1 = rg.fx_dev(p)
        assert m1.index.max() < DEV_END, "sealed window leaked into DEV"
        ods = gen(m1, p)
        bad = sum(not geom(o) for o in ods)
        cut = m1.index[int(len(m1) * 0.6)]
        tr = gen(m1[m1.index < cut], p)
        la = len({sig(o) for o in ods if o.t_signal < cut} ^ {sig(o) for o in tr if o.t_signal < cut})
        years = (m1.index.max() - m1.index.min()).days / 365.25
        rows[p] = {"setups": len(ods), "per_year": round(len(ods) / years, 2), "geometry_violations": bad,
                   "lookahead_mismatches": la}
        if fam == "TRIDENT_V2":
            rows[p]["ctx_above_ema200"] = sum(o.meta["ctx_above_ema200"] for o in ods)
        else:
            rows[p]["ctx_disp_in_kz"] = sum(o.meta["ctx_disp_in_kz"] for o in ods)
            rows[p]["short"] = sum(o.side < 0 for o in ods)
    out[fam] = rows
    print(fam, json.dumps(rows))
(HERE / "FIDELITY_V2_DEV_COUNTS.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
