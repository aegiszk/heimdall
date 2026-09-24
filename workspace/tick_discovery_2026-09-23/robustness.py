"""Robustness for the candidate phenomena flagged by the atlas (tradable markouts from t+250 ms, ticks)."""
import json, numpy as np, pandas as pd
A = pd.read_parquet("nq_event_atlas_events.parquet")
FAMS = ["E4_large_print_ge100", "E4_large_print_ge50", "E1_same_side_run_k16", "E7_same_ms_sweep_k10", "E7_same_ms_sweep_k5",
        "E1_same_side_run_k8", "E6_small_seq_1lot_k20", "E10_failed_continuation_2s(dir=reverse)", "BASE_every1000th_trade_dir=aggr"]
rng = np.random.default_rng(7); out = {}
for fam in FAMS:
    g = A[A.fam == fam]
    for h in ("x10000", "x60000"):
        x = g[h].dropna(); dm = g.groupby("day")[h].mean(); days = dm.index.to_numpy()
        boots = [dm.loc[rng.choice(days, len(days))].mean() for _ in range(2000)]
        s = x.sort_values(ascending=False)
        trim = x[(x >= x.quantile(.05)) & (x <= x.quantile(.95))].mean()
        contract = np.where(g.day < "2026-06-16", "NQM26", np.where(g.day < "2026-09-15", "NQU26", "NQZ26"))
        out[f"{fam}|{h}"] = {"n": int(len(x)), "mean": round(x.mean(), 3), "median": round(x.median(), 3), "trim5": round(trim, 3),
            "top10_share_of_sum": round(float(s.head(10).sum() / x.sum()), 2) if x.sum() else None,
            "day_boot_ci95": [round(float(np.percentile(boots, 2.5)), 3), round(float(np.percentile(boots, 97.5)), 3)],
            "hit": round(float((x > 0).mean()), 3),
            "by_contract": g.assign(c=contract).groupby("c")[h].agg(["mean", "size"]).round(3).to_dict("index"),
            "by_stratum": g.groupby("stratum")[h].agg(["mean", "size"]).round(3).to_dict("index"),
            "by_month": g.assign(m=g.day.str[:7]).groupby("m")[h].mean().round(2).to_dict()}
        r = out[f"{fam}|{h}"]
        print(f"{fam:42} {h}: n={r['n']} mean={r['mean']} med={r['median']} trim5={r['trim5']} CI={r['day_boot_ci95']} hit={r['hit']} top10={r['top10_share_of_sum']}")
        print("     contract", {k: v["mean"] for k, v in r["by_contract"].items()}, "| stratum", {k: v["mean"] for k, v in r["by_stratum"].items()})
        print("     month", r["by_month"])
json.dump(out, open("robustness.json", "w"), indent=1, default=float)
