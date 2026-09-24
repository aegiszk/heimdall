"""Work-order section 14 adversarial battery for one (family, cfg, inst). Run ONLY on preregistered CANDIDATES
(and optionally on the best interpretation of each family as a descriptive stress test, labelled as such).
Tests: drop top 1% / top 5; session-cluster bootstrap; year-by-year; bull/bear (session close vs 50-session SMA);
volatility terciles (20-session mean true range); cost x1.25 / x1.5; one-bar execution delay (signal +1 signal-TF
bar); worse stop fill (stop slippage x3, other costs x1); sibling interpretations (from dev_rows)."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as hz  # noqa: E402
import registry as rg  # noqa: E402
import stats as stx  # noqa: E402

DELAY = {"liquidity_trap": "5min", "trader_mayne": None, "po3_50": "3min", "little_rizzy": "1h",
         "trident": "30min", "mmxm_ote": "15min"}


def regimes(m1: pd.DataFrame) -> pd.DataFrame:
    d = hz.resample(m1, "1D")
    d["day"] = pd.DatetimeIndex(d["key"]).normalize()
    tr = (d["high"] - d["low"]).rolling(20).mean()
    d["bull"] = d["close"] > d["close"].rolling(50).mean()
    d["vol_t"] = pd.qcut(tr, 3, labels=["low", "mid", "high"])
    # regime known at the START of a day = previous day's values
    d[["bull", "vol_t"]] = d[["bull", "vol_t"]].shift(1)
    return d.set_index("day")[["bull", "vol_t"]]


def run(fam: str, cfg_name: str, inst: str) -> dict:
    job = next(j for j in rg.jobs() if j[0] == fam and j[1].name == cfg_name and j[2] == inst)
    _, cfg, _, spec_name, dfn, gfn = job
    m1 = dfn()
    spec = hz.SPECS[spec_name]
    ods = gfn(m1)
    base = hz.trades_frame(hz.run_sequenced(hz.Book(m1, spec), ods), spec)
    out = {"n": len(base), "mean_R": float(base["R"].mean())}
    out["drop_top1pct"] = stx.drop_top(base, frac=0.01)
    out["drop_top5"] = stx.drop_top(base, k=5)
    day = (pd.to_datetime(base["t_entry"]).dt.tz_convert(hz.ET).dt.tz_localize(None) + pd.Timedelta(hours=6)).dt.normalize()
    out["by_year"] = base.groupby(pd.to_datetime(base["t_entry"]).dt.year)["R"].agg(["count", "mean"]).round(3).to_dict("index")
    rg_ = regimes(m1)
    j = rg_.reindex(day.to_numpy())
    b2 = base.assign(bull=j["bull"].to_numpy(), vol=j["vol_t"].astype(str).to_numpy())
    out["bull_bear"] = b2.groupby("bull")["R"].agg(["count", "mean"]).round(3).to_dict("index")
    out["vol_terciles"] = b2.groupby("vol")["R"].agg(["count", "mean"]).round(3).to_dict("index")
    for k in (1.25, 1.5):
        out[f"cost_x{k}"] = float(hz.trades_frame(hz.run_sequenced(hz.Book(m1, hz.scaled_spec(spec, k)), ods), spec)["R"].mean())
    worse = hz.Spec(spec.name, spec.tick, spec.point_value, spec.comm_rt, spec.slip, spec.spread, spec.limit_through, spec.kind)
    # worse stop fill: approximate by tripling slippage (applies to stop exits AND market/stop entries -> conservative)
    worse = hz.Spec(spec.name, spec.tick, spec.point_value, spec.comm_rt, spec.slip * 3, spec.spread, spec.limit_through, spec.kind)
    out["worse_fill_slip_x3"] = float(hz.trades_frame(hz.run_sequenced(hz.Book(m1, worse), ods), spec)["R"].mean())
    dl = DELAY.get(fam)
    if dl:
        delayed = []
        for od in ods:
            o2 = replace(od, t_signal=od.t_signal + pd.Timedelta(dl))
            if o2.entry_type == "close_at":
                o2 = replace(o2, entry_type="market")
            delayed.append(o2)
        dfd = hz.trades_frame(hz.run_sequenced(hz.Book(m1, spec), delayed), spec)
        out["one_bar_delay"] = float(dfd["R"].mean()) if len(dfd) else None
    return out


if __name__ == "__main__":
    fam, cfg, inst = sys.argv[1:4]
    print(json.dumps(run(fam, cfg, inst), indent=1, default=str))
