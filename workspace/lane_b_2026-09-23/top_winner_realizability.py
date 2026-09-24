"""For W1's top winners (30m exit, S=$500, d=3), compare the modeled exit proceeds with the largest REAL
sell (token->quote) observed in that pool in the 10 minutes around the modeled exit block (USD, from logs)."""
import json, os, numpy as np, pandas as pd
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profit_discovery_2026-09-23")
Q96 = 2 ** 96
def s256(h):
    v = int(h, 16); return v - (1 << 256) if v >> 255 else v
res = pd.read_parquet(os.path.join(A, "copy_sim_results.parquet"))
sample = pd.read_pickle(os.path.join(A, "sample.pkl"))
tx_of = {}
for r in sample.itertuples(): tx_of.setdefault((r.pool, r.block, r.wallet), r.tx.lower())
w = res[(res.S == 500) & (res.d == 3)].dropna(subset=["ret_30m"]).sort_values("ret_30m", ascending=False).head(15)
rows = []
for r in w.itertuples():
    L = sorted(json.load(open(os.path.join(A, "logs", r.pool + ".json")))["logs"], key=lambda z: (z["b"], z["i"]))
    dl = [(z["b"], z["tx"].lower(), s256(z["data"][2:66]), s256(z["data"][66:130]), int(z["data"][130:194], 16) / Q96) for z in L]
    src = [k for k, z in enumerate(dl) if z[1] == tx_of[(r.pool, r.block, r.wallet)]]
    k = src[-1]; tok_c1 = dl[k][4] < dl[k - 1][4]
    q_in = abs(dl[k][2] if tok_c1 else dl[k][3]); usd_per_q = r.src_usd / q_in
    exit_b = r.block + 3 + 18000
    sells_usd, sells_n, buys_n = [], 0, 0
    for j in range(1, len(dl)):
        b = dl[j][0]
        if not (exit_b - 3000 <= b <= exit_b + 3000): continue
        token_price_down = (dl[j][4] > dl[j - 1][4]) if tok_c1 else (dl[j][4] < dl[j - 1][4])
        q = abs(dl[j][2] if tok_c1 else dl[j][3]) * usd_per_q
        if token_price_down: sells_usd.append(q); sells_n += 1
        else: buys_n += 1
    proceeds = 500 * (1 + r.ret_30m)
    rows.append(dict(pool=r.pool[:10], ret_30m=round(r.ret_30m, 3), modeled_exit_usd=round(proceeds),
                     real_sells_10min=sells_n, real_buys_10min=buys_n,
                     largest_real_sell_usd=round(max(sells_usd), 1) if sells_usd else 0.0,
                     total_real_sell_usd=round(sum(sells_usd), 1)))
out = pd.DataFrame(rows); out.to_csv("top_winner_realizability.csv", index=False); print(out.to_string())
print("\nexits larger than every real sell in the window:", int((out.modeled_exit_usd > out.largest_real_sell_usd).sum()), "of", len(out))
print("exits larger than ALL real sells combined:", int((out.modeled_exit_usd > out.total_real_sell_usd).sum()), "of", len(out))
