"""Re-run the four Family-A trials affected by the entry-type bug (see _program/BUGFIX_A_ENTRY.md)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as hz, registry as rg, stats as stx  # noqa: E401,E402
import pandas as pd
rows = json.loads((rg.BASE / "_program" / "dev_rows.json").read_text())
for r in rows:
    if r["family"] == "liquidity_trap" and r["cfg"] != "A4_k1_close_nearest" and "_fix1" not in r["cfg"]:
        r["status"] = "INVALID_IMPLEMENTATION"
for fam, cfg, inst, sn, dfn, gfn in rg.jobs():
    if fam != "liquidity_trap" or cfg.name == "A4_k1_close_nearest":
        continue
    m1 = dfn(); spec = hz.SPECS[sn]; ods = gfn(m1)
    df = hz.trades_frame(hz.run_sequenced(hz.Book(m1, spec), ods), spec)
    name = cfg.name + "_fix1"
    df.to_csv(rg.BASE / fam / "results" / f"trades_{name}_{inst}.csv", index=False)
    s = stx.summarize(df)
    s["cost_scaled_mean_R"] = {str(k): float(hz.trades_frame(hz.run_sequenced(hz.Book(m1, hz.scaled_spec(spec, k)), ods), spec)["R"].mean()) for k in (0.0, 1.25, 1.5, 2.0)}
    s["drop_top1pct_mean_R"] = stx.drop_top(df, frac=0.01); s["drop_top5_mean_R"] = stx.drop_top(df, k=5)
    dd = pd.to_datetime(df["t_entry"]).dt.tz_convert(hz.ET)
    s["tue_thu_mean_R"] = float(df.loc[dd.dt.dayofweek.isin([1, 2, 3]).to_numpy(), "R"].mean())
    trig = df["m_internal"] + df["side"].map({-1: 0.25, 1: -0.25}) * (1.0 if inst == "MNQ" else 4.0)
    s["wrong_side_fill_frac"] = float((df["side"] * (df["entry"] - trig) > 0.5).mean())
    row = dict(family=fam, cfg=name, inst=inst, n_orders=len(ods), **s); rows.append(row)
    print(json.dumps({k: row.get(k) for k in ("cfg", "inst", "n", "win_rate", "mean_R", "nw_t", "boot95_lo", "boot95_hi", "cost_scaled_mean_R", "wrong_side_fill_frac")}), flush=True)
(rg.BASE / "_program" / "dev_rows.json").write_text(json.dumps(rows, indent=1, default=str))
