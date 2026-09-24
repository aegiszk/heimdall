"""Stage 1 (read-only): sample source BUY fills from the FomoPulse tape and fetch the Uniswap v4
PoolManager Swap logs needed to replay each pool around the buy and around the source's exit.
No keys, no signing. Caches raw logs per pool to disk."""
import json, os, sys, time, random, requests
import pandas as pd

SP = os.path.dirname(os.path.abspath(__file__))
RPC = "https://rpc.mainnet.chain.robinhood.com"
PM = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 800
SEED = 20260923
PRE, POST_BUY, POST_SELL = 3000, 36000, 700   # blocks (~0.1s each): 5 min before, 60 min after buy
CHUNK = 900_000

def rpc(method, params, tries=8):
    for k in range(tries):
        try:
            j = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=90).json()
            if "error" in j:
                if j["error"].get("code") == 429 or "Too Many" in str(j["error"]):
                    time.sleep(3 * (k + 1)); continue
                if "timed out" in str(j["error"]) or "too many" in str(j["error"]).lower() or "limit" in str(j["error"]).lower():
                    raise TimeoutError(str(j["error"]))
                raise RuntimeError(j["error"])
            return j["result"]
        except requests.RequestException:
            time.sleep(3 * (k + 1))
    raise RuntimeError("rpc gave up")

def get_range(pool, x, y):
    try:
        return rpc("eth_getLogs", [{"address": PM, "topics": [SWAP, pool], "fromBlock": hex(x), "toBlock": hex(y)}])
    except TimeoutError:
        if y - x < 200: raise
        m = (x + y) // 2; time.sleep(0.5)
        return get_range(pool, x, m) + get_range(pool, m + 1, y)

d = pd.read_parquet(os.path.join(SP, "fomopulse_tape.parquet"))
for c in ["ts", "id", "block"]: d[c] = d[c].astype(float).astype("int64")
for c in ["usd", "amount", "price", "followers"]: d[c] = pd.to_numeric(d[c], errors="coerce")
d = d[(d.is_dust != "1") & (d.is_stock != "1")].sort_values(["ts", "id"])
d["pool"] = d.pair_url.str.rsplit("/", n=1).str[-1].str.lower()

buys = d[(d.side == "buy") & (d.dex == "uniswap v4") & (d.priced == "cash_leg") & (d.usd >= 100)
         & d.pool.str.len().eq(66)]
sells = d[d.side == "sell"]
random.seed(SEED)
idx = sorted(random.sample(list(buys.index), min(N, len(buys))))
sample = buys.loc[idx].copy()

# the source's exit: first sell of the same token by the same wallet after the buy
first_sell = []
sg = {k: g for k, g in sells.groupby(["wallet", "token"])}
for _, r in sample.iterrows():
    g = sg.get((r.wallet, r.token))
    s = g[g.block > r.block] if g is not None else None
    first_sell.append(None if s is None or s.empty else s.iloc[0].to_dict())
sample["exit"] = first_sell
sample.to_pickle(os.path.join(SP, "sample.pkl"))
print("universe buys", len(buys), "sampled", len(sample), "with source exit", sum(x is not None for x in first_sell))

# merged block intervals per pool
need = {}
for _, r in sample.iterrows():
    need.setdefault(r.pool, []).append((r.block - PRE, r.block + POST_BUY))
    if r.exit is not None:
        eb = int(r.exit["block"]); need[r.pool].append((eb - PRE, eb + POST_SELL))
os.makedirs(os.path.join(SP, "logs"), exist_ok=True)
calls = 0; t0 = time.time(); failed = {}
for i, (pool, ivs) in enumerate(need.items()):
    path = os.path.join(SP, "logs", pool + ".json")
    if os.path.exists(path): continue
    ivs.sort(); merged = []
    for a, b in ivs:
        if merged and a <= merged[-1][1] + 1: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    logs = []
    for a, b in merged:
        x = a
        while x <= b:
            y = min(b, x + CHUNK)
            try:
                res = get_range(pool, x, y)
            except Exception as e:
                print("SKIP range", pool, x, y, str(e)[:80], flush=True); res = []
                failed.setdefault(pool, []).append([x, y])
            calls += 1
            logs += [{"b": int(l["blockNumber"], 16), "i": int(l["logIndex"], 16), "tx": l["transactionHash"],
                      "data": l["data"]} for l in res]
            x = y + 1; time.sleep(0.35)
    json.dump({"intervals": merged, "logs": logs, "failed": failed.get(pool, [])}, open(path, "w"))
    if i % 25 == 0: print(f"pool {i}/{len(need)} calls {calls} elapsed {time.time()-t0:.0f}s", flush=True)
print("done pools", len(need), "calls", calls, "elapsed", round(time.time() - t0))
