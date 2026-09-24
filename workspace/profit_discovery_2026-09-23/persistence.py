"""Source-level wallet persistence on the FomoPulse tape (read-only, offline).
Average-cost realized PnL; sells beyond bought amount (handouts / pre-window inventory) are not realized."""
import os, numpy as np, pandas as pd
SP = os.path.dirname(os.path.abspath(__file__))
d = pd.read_parquet(os.path.join(SP, "fomopulse_tape.parquet"))
for c in ["ts", "id", "block"]: d[c] = d[c].astype(float).astype("int64")
for c in ["usd", "amount", "followers"]: d[c] = pd.to_numeric(d[c], errors="coerce")
d = d[(d.is_dust != "1") & (d.is_stock != "1") & (d.priced != "unpriced") & d.usd.gt(0) & d.amount.gt(0)]
d = d.sort_values(["ts", "id"])
T0, T1 = d.ts.min(), d.ts.max(); MID = T0 + (T1 - T0) / 2

def realized(frame):
    book = {}; rows = []
    for r in frame.itertuples(index=False):
        k = (r.wallet, r.token); b = book.setdefault(k, [0.0, 0.0])   # amount, cost
        if r.side == "buy":
            b[0] += r.amount; b[1] += r.usd
        else:
            q = min(r.amount, b[0])
            if q <= 0: continue
            cost = b[1] * q / b[0]; proceeds = r.usd * q / r.amount
            b[0] -= q; b[1] -= cost
            rows.append((r.wallet, r.token, r.ts, cost, proceeds - cost))
    open_cost = {}
    for (w, t), (a, c) in book.items():
        if a > 0: open_cost[w] = open_cost.get(w, 0) + c
    return pd.DataFrame(rows, columns=["wallet", "token", "ts", "cost", "pnl"]), open_cost

halves = {}
for name, lo, hi in [("H1", T0, MID), ("H2", MID, T1 + 1)]:
    # each half is walked independently so H2 never uses H1 cost basis (strict separation)
    r, oc = realized(d[(d.ts >= lo) & (d.ts < hi)])
    g = r.groupby("wallet").agg(pnl=("pnl", "sum"), cost=("cost", "sum"), n=("pnl", "size"),
                                wins=("pnl", lambda s: (s > 0).sum()))
    g["ret"] = g.pnl / g.cost
    g["open_cost"] = pd.Series(oc)
    halves[name] = g
    print(f"{name}: realized sells {len(r)}  wallets {len(g)}  total realized ${g.pnl.sum():,.0f} on cost ${g.cost.sum():,.0f}"
          f"  -> {g.pnl.sum()/g.cost.sum():+.2%}  win-rate {g.wins.sum()/g.n.sum():.1%}  open cost left ${sum(oc.values()):,.0f}")

j = halves["H1"].join(halves["H2"], lsuffix="_1", rsuffix="_2", how="inner")
j = j[(j.n_1 >= 5) & (j.n_2 >= 5)]
print("wallets with >=5 realized sells in both halves:", len(j))
for col in ["pnl", "ret"]:
    print(f"  Spearman H1 {col} vs H2 {col}: {j[col+'_1'].corr(j[col+'_2'], method='spearman'):+.3f}")
q = j.ret_1.quantile(0.8)
top, rest = j[j.ret_1 >= q], j[j.ret_1 < q]
for nm, g in [("top-quintile H1 ret", top), ("rest", rest)]:
    print(f"  {nm}: n={len(g)}  H1 ret {g.pnl_1.sum()/g.cost_1.sum():+.2%}  H2 ret {g.pnl_2.sum()/g.cost_2.sum():+.2%}"
          f"  H2 median wallet ret {g.ret_2.median():+.2%}  H2 frac wallets positive {(g.pnl_2>0).mean():.0%}")
# followers vs H2 realized return
f = d.groupby("wallet").followers.max()
j["followers"] = f
print("  Spearman followers vs H2 ret:", round(j.followers.corr(j.ret_2, method="spearman"), 3))
print("MID split at", pd.to_datetime(MID, unit="s"))
