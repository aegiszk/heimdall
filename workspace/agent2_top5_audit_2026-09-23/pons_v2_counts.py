"""Count Pons v2 launches (factory TokenLaunched) and graduations (hook PoolRegistered) since v2 go-live,
from the public Robinhood Chain RPC (free, read-only). Also decodes graduationThreshold from TokenLaunched."""
import json, time, requests
RPC = "https://rpc.mainnet.chain.robinhood.com"
FACTORY = "0x7ed598bcef8bd9edd8c97a195c6d13f40801ec7e"; HOOK = "0xe5e702641ea86f4ae6cc3cdaed2b886f976be044"
T_LAUNCH = "0x8d4aad4953d0ca700d468f3753aa14432d1b35b43ec6409f051fb6aa43a89607"
T_REG = "0x01bf263a1db1652580721573296e1a1fa70b3d4c87f61d02a69c4e1109d2d573"
def rpc(m, p):
    for k in range(12):
        try:
            j = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": m, "params": p}, timeout=90).json()
            if "result" in j: return j["result"]
            if "error" in j and (j["error"].get("code") == 429 or "too many requests" in str(j["error"]).lower()):
                time.sleep(3 * (k + 1)); continue
            if "error" in j and any(s in str(j["error"]).lower() for s in ("timed out", "query returned more", "limit", "range")): raise TimeoutError(j["error"])
        except requests.RequestException: pass
        time.sleep(2 * (k + 1))
    raise RuntimeError("rpc")
def logs(addr, topic, a, b):
    try: return rpc("eth_getLogs", [{"address": addr, "topics": [topic], "fromBlock": hex(a), "toBlock": hex(b)}])
    except TimeoutError:
        m = (a + b) // 2; time.sleep(0.5); return logs(addr, topic, a, m) + logs(addr, topic, m + 1, b)
head = int(rpc("eth_blockNumber", []), 16)
def block_at(ts):
    lo, hi = 1, head
    while lo < hi:
        mid = (lo + hi) // 2
        if int(rpc("eth_getBlockByNumber", [hex(mid), False])["timestamp"], 16) < ts: lo = mid + 1
        else: hi = mid
    return lo
start = block_at(1785801600)  # 2026-08-04 00:00 UTC
out = {"head": head, "start_block_2026_08_04": start}
for name, addr, topic in (("launches", FACTORY, T_LAUNCH), ("graduations", HOOK, T_REG)):
    allz, x, CH = [], start, 2_000_000
    while x <= head:
        y = min(head, x + CH); allz += logs(addr, topic, x, y); x = y + 1; time.sleep(0.4)
    out[name] = len(allz)
    if name == "launches":
        thr = {}
        for l in allz:
            pair = "0x" + l["data"][26:66]; th = int(l["data"][2 + 128: 2 + 192], 16)
            thr[(pair, th)] = thr.get((pair, th), 0) + 1
        out["launch_threshold_configs"] = sorted(([p, t / 1e18, n] for (p, t), n in thr.items()), key=lambda z: -z[2])[:8]
    else:
        ts = [int(rpc("eth_getBlockByNumber", [l["blockNumber"], False])["timestamp"], 16) for l in allz[-60:]]
        out["graduation_blocks_sample_last"] = [int(l["blockNumber"], 16) for l in allz[-5:]]
        out["graduations_per_day_recent"] = round(len(ts) / max((ts[-1] - ts[0]) / 86400, 1e-9), 2) if len(ts) > 1 else None
    print(name, out[name], flush=True)
out["graduation_rate"] = round(out["graduations"] / max(out["launches"], 1), 4)
json.dump(out, open("pons_v2_counts.json", "w"), indent=1); print(json.dumps(out, indent=1))
