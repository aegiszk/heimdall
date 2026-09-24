"""Read-only backfill feasibility probe: ERC-20 Transfer logs to/from a seeded sample of FomoPulse
tracked wallets for 2026-08-05 .. 2026-09-04 (before FomoPulse's first indexed fill).
Counts transfers and distinct tokens; saves raw logs. No USD reconstruction here."""
import json, os, random, time, requests
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
RPC = "https://rpc.mainnet.chain.robinhood.com"
TR = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
FROM_B, TO_B = 29_300_000, 54_947_973          # ~2026-08-05 .. 2026-09-05 07:38 UTC
CHUNK = 3_000_000

def rpc(m, p):
    for k in range(8):
        try:
            j = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": m, "params": p}, timeout=90).json()
        except requests.RequestException:
            time.sleep(3 * (k + 1)); continue
        e = str(j.get("error", ""))
        if "429" in e or "Too Many" in e: time.sleep(3 * (k + 1)); continue
        if "timed out" in e or "limit" in e.lower(): raise TimeoutError(e)
        if "error" in j: raise RuntimeError(e)
        return j["result"]
    raise RuntimeError("gave up")

def logs(topics, a, b):
    try:
        return rpc("eth_getLogs", [{"topics": topics, "fromBlock": hex(a), "toBlock": hex(b)}])
    except TimeoutError:
        if b - a < 2000: return None
        m = (a + b) // 2; time.sleep(0.5)
        x, y = logs(topics, a, m), logs(topics, m + 1, b)
        return None if x is None or y is None else x + y

tape = pd.read_parquet(os.path.join(HERE, "fomopulse_tape.parquet"))
wallets = sorted(tape.wallet.unique())
random.seed(20260923); sample = random.sample(wallets, 20)
out, t0 = {}, time.time()
for w in sample:
    t = "0x" + "0" * 24 + w[2:].lower(); rec = {"in": [], "out": [], "failed": 0}
    for side, topics in (("in", [TR, None, t]), ("out", [TR, t, None])):
        a = FROM_B
        while a <= TO_B:
            b = min(TO_B, a + CHUNK)
            r = logs(topics, a, b)
            if r is None: rec["failed"] += 1
            else: rec[side] += [{"b": int(l["blockNumber"], 16), "tx": l["transactionHash"], "token": l["address"]} for l in r]
            a = b + 1; time.sleep(0.3)
    out[w] = rec
    print(w, "in", len(rec["in"]), "out", len(rec["out"]), "failed chunks", rec["failed"], f"{time.time()-t0:.0f}s", flush=True)
json.dump(out, open(os.path.join(HERE, "backfill_probe_logs.json"), "w"))
tot_in = sum(len(v["in"]) for v in out.values()); tot_out = sum(len(v["out"]) for v in out.values())
fails = sum(v["failed"] for v in out.values())
toks = {x["token"] for v in out.values() for x in v["in"] + v["out"]}
txs = {x["tx"] for v in out.values() for x in v["in"] + v["out"]}
cur = tape[tape.wallet.isin(sample) & (tape.is_dust != "1")]
print(f"SUMMARY 20 wallets, 2026-08-05..09-05: transfers in {tot_in}, out {tot_out}, distinct tx {len(txs)}, tokens {len(toks)}, failed chunks {fails}")
print(f"compare: same 20 wallets, FomoPulse 09-05..09-22 non-dust fills {len(cur)}")
