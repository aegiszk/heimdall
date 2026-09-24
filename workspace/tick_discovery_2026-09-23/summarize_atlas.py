"""Summarize nq_event_atlas_events.parquet. Inference clusters by trading day (t = mean of day means / SE across days)."""
import json, numpy as np, pandas as pd
A = pd.read_parquet("nq_event_atlas_events.parquet")
reg = json.load(open("nq_event_atlas_registry.json"))
H = reg["horizons_ms"]; FR = reg["friction_ticks"]["NQ"]; FRM = reg["friction_ticks"]["MNQ"]
ndays = reg["days"]
def dt(x, day):
    g = pd.DataFrame({"x": x, "d": day}).dropna().groupby("d").x.mean()
    return (g.mean(), g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 2 else np.nan, len(g))
rows = []
for fam, g in A.groupby("fam"):
    r = {"family": fam, "n": len(g), "per_day": round(len(g) / ndays, 1)}
    for h in H:
        m, t, _ = dt(g[f"m{h}"], g.day); r[f"m{h}"] = round(m, 3); r[f"t{h}"] = round(t, 1)
    for h in (1000, 5000, 10000, 30000, 60000):
        m, t, _ = dt(g[f"x{h}"], g.day); r[f"x{h}"] = round(m, 3); r[f"tx{h}"] = round(t, 1)
    r["mfe10s_med"] = round(g.mfe10000.median(), 2); r["mae10s_med"] = round(g.mae10000.median(), 2)
    r["mfe60s_med"] = round(g.mfe60000.median(), 2); r["mae60s_med"] = round(g.mae60000.median(), 2)
    r["p_reversal_60s"] = round(float((g.m60000 < 0).mean()), 3); r["p_cont_60s"] = round(float((g.m60000 > 0).mean()), 3)
    r["impact_ticks_per_100lots_1s"] = round(float(100 * g.m1000.sum() / max(g.absvol1s.sum(), 1)), 3)
    best = max((abs(r[f"x{h}"]), h) for h in (1000, 5000, 10000, 30000, 60000))
    r["best_abs_tradable_ticks"] = best[0]; r["best_h_ms"] = best[1]; r["best_over_friction_NQ"] = round(best[0] / FR, 3)
    mon = g.assign(mon=g.day.str[:7]).groupby("mon")[f"x{best[1]}"].mean()
    r["month_sign_consistency"] = f"{int((np.sign(mon) == np.sign(r[f'x{best[1]}'])).sum())}/{len(mon)}"
    st = g.groupby("stratum")[f"x{best[1]}"].agg(["mean", "size"]).round(3)
    r["strata_best_h"] = {k: {"mean": float(v["mean"]), "n": int(v["size"])} for k, v in st.iterrows()}
    rows.append(r)
S = pd.DataFrame(rows).sort_values("family")
S.to_csv("nq_event_atlas_summary.csv", index=False)
json.dump(rows, open("nq_event_atlas_summary.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(S[["family", "n", "per_day", "m50", "m250", "m1000", "t1000", "m10000", "t10000", "m60000", "t60000", "x10000", "tx10000", "x60000", "tx60000", "p_reversal_60s", "mae10s_med", "mfe10s_med", "best_abs_tradable_ticks", "best_h_ms", "best_over_friction_NQ", "month_sign_consistency"]].to_string(index=False))
