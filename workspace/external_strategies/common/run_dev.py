"""DEVELOPMENT run for every registered trial (frozen preregistration; see _program/PREREG_MANIFEST.json).
Outputs per family: results/trades_<cfg>_<inst>.csv and results/dev_summary.json; global rows in
_program/dev_rows.json."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as hz  # noqa: E402
import registry as rg  # noqa: E402
import stats as stx  # noqa: E402


def main():
    rows = []
    for fam, cfg, inst, spec_name, dfn, gfn in rg.jobs():
        t0 = time.time()
        m1 = dfn()
        spec = hz.SPECS[spec_name]
        ods = gfn(m1)
        book = hz.Book(m1, spec)
        trades = hz.run_sequenced(book, ods)
        df = hz.trades_frame(trades, spec)
        outd = rg.BASE / fam / "results"
        outd.mkdir(parents=True, exist_ok=True)
        if len(df):
            df.to_csv(outd / f"trades_{cfg.name}_{inst}.csv", index=False)
        s = stx.summarize(df)
        cost = {}
        for k in (1.25, 1.5, 2.0):
            dfk = hz.trades_frame(hz.run_sequenced(hz.Book(m1, hz.scaled_spec(spec, k)), ods), spec)
            cost[str(k)] = float(dfk["R"].mean()) if len(dfk) else None
        s["cost_scaled_mean_R"] = cost
        if len(df):
            s["drop_top1pct_mean_R"] = stx.drop_top(df, frac=0.01)
            s["drop_top5_mean_R"] = stx.drop_top(df, k=5)
            dd = pd.to_datetime(df["t_entry"]).dt.tz_convert(hz.ET)
            s["tue_thu_mean_R"] = float(df.loc[dd.dt.dayofweek.isin([1, 2, 3]).to_numpy(), "R"].mean())
        row = dict(family=fam, cfg=cfg.name, inst=inst, n_orders=len(ods), secs=round(time.time() - t0, 1), **s)
        rows.append(row)
        print(json.dumps({k: row.get(k) for k in ("family", "cfg", "inst", "n", "win_rate", "mean_R", "nw_t",
                                                   "boot95_lo", "boot95_hi", "cost_scaled_mean_R", "secs")},
                         default=str), flush=True)
    (rg.BASE / "_program").mkdir(exist_ok=True)
    (rg.BASE / "_program" / "dev_rows.json").write_text(json.dumps(rows, indent=1, default=str))


if __name__ == "__main__":
    main()
