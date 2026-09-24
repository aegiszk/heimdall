"""Lane B independent audit of Lane A's RH-chain copy replay (read-only; never edits Lane A files).
Inputs: ../profit_discovery_2026-09-23/{copy_sim_results.parquet, sample.pkl, logs/*.json}
"""
import json, os, numpy as np, pandas as pd
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profit_discovery_2026-09-23")
Q96 = 2 ** 96
res = pd.read_parquet(os.path.join(A, "copy_sim_results.parquet"))
sample = pd.read_pickle(os.path.join(A, "sample.pkl"))

def s256(h):
    v = int(h, 16); return v - (1 << 256) if v >> 255 else v
def dec(l):
    w = [l["data"][2 + 64 * k: 2 + 64 * (k + 1)] for k in range(6)]
    return (l["b"], l["i"], l["tx"].lower(), int(w[2], 16) / Q96)

logs_cache = {}
def pool_logs(pool):
    if pool not in logs_cache:
        b = json.load(open(os.path.join(A, "logs", pool + ".json")))
        logs_cache[pool] = sorted((dec(l) for l in b["logs"]), key=lambda z: (z[0], z[1]))
    return logs_cache[pool]

# ---------- 1. activity after source buy (explains "latency insensitivity") ----------
base = res[(res.d == 0) & (res.S == 500)].drop_duplicates(["pool", "block", "wallet"])
tx_of = {(r.pool, r.block, r.wallet): r.tx.lower() for r in sample.itertuples()}
rows = []
for r in base.itertuples():
    L = pool_logs(r.pool); src_tx = tx_of.get((r.pool, r.block, r.wallet))
    post_idx = [k for k, z in enumerate(L) if z[2] == src_tx]
    if not post_idx: continue
    k = post_idx[-1]
    after = [z for z in L[k + 1:] if z[0] <= r.block + 600]
    rows.append(dict(pool=r.pool, block=r.block, n3=sum(z[0] <= r.block + 3 for z in after),
                     n50=sum(z[0] <= r.block + 50 for z in after), n600=len(after)))
act = pd.DataFrame(rows)
activity = {"buys": int(len(act)),
            "share_zero_other_swaps_within_d": {d: round(float((act[f"n{d}"] == 0).mean()), 4) for d in (3, 50, 600)},
            "median_other_swaps_within_60s": float(act.n600.median())}

# ---------- 2. point-in-time sell-activity filter (Lane A rule b) ----------
def prior_sells(pool, block, src_tx, tok_c1):
    L = pool_logs(pool); cnt = 0
    for j in range(1, len(L)):
        b = L[j][0]
        if b < block - 3000 or b >= block: continue
        # token price falls on a sell: token c1 -> sqrtP rises; token c0 -> sqrtP falls
        up = L[j][3] > L[j - 1][3]
        cnt += (up if tok_c1 else not up)
    return cnt

def tok_is_c1(pool, src_tx):
    L = pool_logs(pool); idx = [k for k, z in enumerate(L) if z[2] == src_tx]
    if not idx or idx[-1] == 0: return None
    k = idx[-1]; return L[k][3] < L[k - 1][3]

w1 = res[(res.S == 500) & (res.d == 3)].dropna(subset=["ret_30m"]).copy()
flags = []
for r in w1.itertuples():
    tx = tx_of.get((r.pool, r.block, r.wallet)); c1 = tok_is_c1(r.pool, tx)
    flags.append(None if c1 is None else prior_sells(r.pool, r.block, tx, c1))
w1["prior_sells_5m"] = flags
ts = {}
for _r in sample.itertuples():
    ts.setdefault((_r.pool, _r.block, _r.wallet), _r.ts)
w1["ts"] = [ts.get((r.pool, r.block, r.wallet)) for r in w1.itertuples()]
w1["day"] = pd.to_datetime(w1.ts, unit="s").dt.date.astype(str)

def tails(x, pnl_usd):
    x = np.asarray(x); s = np.sort(x)[::-1]; tot = x.sum()
    es5 = np.sort(x)[: max(1, int(0.05 * len(x)))].mean()
    cum = np.cumsum(pnl_usd); dd = float((cum - np.maximum.accumulate(cum)).min())
    trim = x[(x >= np.quantile(x, .05)) & (x <= np.quantile(x, .95))].mean()
    return {"n": int(len(x)), "mean": round(float(x.mean()), 4), "median": round(float(np.median(x)), 4),
            "trim5_mean": round(float(trim), 4), "win": round(float((x > 0).mean()), 4),
            "top1_share_of_total": round(float(s[:1].sum() / tot), 3) if tot else None,
            "top5_share": round(float(s[:5].sum() / tot), 3) if tot else None,
            "top10_share": round(float(s[:10].sum() / tot), 3) if tot else None,
            "mean_ex_top10": round(float(s[10:].mean()), 4), "worst": round(float(x.min()), 4),
            "ES5": round(float(es5), 4), "p_total_loss(<=-90%)": round(float((x <= -0.9).mean()), 4),
            "max_drawdown_usd_seq_$500": round(dd, 1)}

def cluster_boot(df, col, key, B=4000, seed=7):
    rng = np.random.default_rng(seed); g = df.groupby(key)[col].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy(); k = len(g); means = []
    for _ in range(B):
        i = rng.integers(0, k, k); means.append(s[i].sum() / c[i].sum())
    lo, hi = np.percentile(means, [2.5, 97.5]); return {"clusters": int(k), "ci95": [round(lo, 4), round(hi, 4)]}

def inference(df, col):
    out = {"iid": cluster_boot(df.assign(_i=np.arange(len(df))), col, "_i")}
    for key in ("token", "pool", "day", "wallet"):
        out[key] = cluster_boot(df, col, key)
    # design effect for token clustering
    n = len(df); m = df.groupby("token").size(); out["n_eff_token_kish"] = round(float(n ** 2 / (m ** 2).sum()), 1)
    return out

report = {"activity_after_source_buy": activity}
for name, df in {"W1_raw_30m_S500_d3": w1, "W1_pit_filter_ge5_prior_sells": w1[w1.prior_sells_5m >= 5]}.items():
    df = df.sort_values("block")
    report[name] = {"tails": tails(df.ret_30m, df.ret_30m.to_numpy() * 500), "inference": inference(df, "ret_30m")}
m = res[(res.S == 500) & (res.d == 3)].dropna(subset=["mirror_ret"]).copy()
m["day"] = [pd.to_datetime(ts.get((r.pool, r.block, r.wallet)), unit="s").date().isoformat() for r in m.itertuples()]
m = m.sort_values("block")
report["mirror_S500_d3"] = {"tails": tails(m.mirror_ret, m.mirror_ret.to_numpy() * 500), "inference": inference(m, "mirror_ret")}
report["lane_a_filter_reproduction"] = {"n_pit_ge5": int((w1.prior_sells_5m >= 5).sum()), "lane_a_reported_n": 530}
json.dump(report, open("audit_fomo_lane.json", "w"), indent=1, default=str)
print(json.dumps(report, indent=1, default=str))
