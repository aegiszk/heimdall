"""Independent re-fetch of v4 Swap logs from the public RPC for a stratified sample of Lane A's replayed buys.
Compares: swap count in (b, b+d] and the pool sqrtPrice at end of block b+d-1 vs Lane A's cached logs."""
import json, os, time, requests, numpy as np, pandas as pd
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profit_discovery_2026-09-23")
RPC = "https://rpc.mainnet.chain.robinhood.com"
PM = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
def rpc(p):
    for k in range(6):
        try:
            j = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [p]}, timeout=60).json()
            if "result" in j: return j["result"]
        except requests.RequestException: pass
        time.sleep(2 * (k + 1))
    raise RuntimeError("rpc failed")
res = pd.read_parquet(os.path.join(A, "copy_sim_results.parquet"))
b = res[(res.d == 0) & (res.S == 500)].drop_duplicates(["pool", "block"]).copy()
b["liq_tercile"] = pd.qcut(b.src_usd.rank(method="first"), 3, labels=False)
rng = np.random.default_rng(20260923)
pick = pd.concat([g.sample(min(12, len(g)), random_state=int(rng.integers(1e9))) for _, g in b.groupby("liq_tercile")])
rows = []
for r in pick.itertuples():
    cached = json.load(open(os.path.join(A, "logs", r.pool + ".json")))["logs"]
    live = rpc({"address": PM, "topics": [SWAP, r.pool], "fromBlock": hex(r.block - 50), "toBlock": hex(r.block + 600)})
    for d in (3, 50, 600):
        lo, hi = r.block + 1, r.block + d
        c_n = sum(lo <= l["b"] <= hi for l in cached); l_n = sum(lo <= int(x["blockNumber"], 16) <= hi for x in live)
        def last_sp(ls, key):
            cand = [x for x in ls if key(x) <= r.block + d - 1]
            if not cand: return None
            x = max(cand, key=lambda z: (key(z), int(z["logIndex"], 16) if "logIndex" in z else z["i"]))
            return int(x["data"][2 + 128: 2 + 192], 16)
        c_sp = last_sp(cached, lambda z: z["b"]); l_sp = last_sp(live, lambda z: int(z["blockNumber"], 16))
        rows.append(dict(pool=r.pool[:12], block=r.block, tercile=r.liq_tercile, d=d, cached_swaps=c_n, live_swaps=l_n,
                         sqrtP_match=(c_sp == l_sp)))
    time.sleep(0.3)
out = pd.DataFrame(rows); out.to_csv("chain_recount.csv", index=False)
print(out.groupby("d").agg(n=("block", "size"), count_match=("cached_swaps", lambda s: None),
      ).drop(columns="count_match"))
out["count_match"] = out.cached_swaps == out.live_swaps
print(out.groupby("d")[["count_match", "sqrtP_match"]].mean().round(3), "\nmismatches:\n", out[~out.count_match | ~out.sqrtP_match].head(20))
