"""Failure diagnosis: re-simulate every trial with ALL modelled costs set to zero (spread, slippage, commission).
Separates NO_SIGNAL (frictionless mean <= 0) from EXECUTION_KILLS_EDGE (frictionless > 0, net <= 0).
Also reports how many stop-entry fills gapped beyond their trigger by > 1 tick."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as hz  # noqa: E402
import registry as rg  # noqa: E402

rows = []
for fam, cfg, inst, spec_name, dfn, gfn in rg.jobs():
    m1 = dfn()
    spec = hz.SPECS[spec_name]
    ods = gfn(m1)
    tr0 = hz.run_sequenced(hz.Book(m1, hz.scaled_spec(spec, 0.0)), ods)
    df0 = hz.trades_frame(tr0, spec)
    gapped = None
    if ods and ods[0].entry_type == "stop":
        by_sig = {(o.t_signal, o.side, o.stop, o.entry_px): o for o in ods}
        g = 0
        for t in tr0:
            o = next((v for k, v in by_sig.items() if k[0] == t.t_signal and k[1] == t.side and k[2] == t.stop0), None)
            if o is not None and abs(t.entry_fill - o.entry_px) > spec.tick + 1e-9:
                g += 1
        gapped = g / max(1, len(tr0))
    r = dict(family=fam, cfg=cfg.name, inst=inst, n0=len(df0), mean_R_zero_cost=float(df0["R"].mean()) if len(df0) else None,
             gapped_stop_entry_frac=gapped)
    rows.append(r)
    print(json.dumps(r), flush=True)
(rg.BASE / "_program" / "zero_cost.json").write_text(json.dumps(rows, indent=1))
