"""Stage 2 (offline): replay each sampled source BUY and simulate a follower.

Model (INFERRED approximations, stated):
- Pool state = post-swap (sqrtPriceX96, liquidity, lpFee) of the last v4 Swap log at or before the
  follower's position. Follower at delay d blocks sees the state at END of block (b_src + d - 1),
  i.e. it lands first in block b_src + d (optimistic within-block). d = 0 = state immediately after the
  source's own swap: a pre-sequencing ceiling that a feed follower CANNOT achieve.
- Swap output uses constant-liquidity math inside the current tick (tick crossings ignored), lpFee from
  the log, and a per-pool output-side hook tax measured from the source's own trade (tape amount vs
  event amount). Input-side hook fees are not observable and are NOT modelled (optimistic).
- Returns are in the pool's quote currency (quote/USD drift over the hold ignored). Gas added in USD.
"""
import os, json, math, sys, requests
import numpy as np, pandas as pd

SP = os.path.dirname(os.path.abspath(__file__))
Q96 = 2 ** 96
DELAYS = [0, 1, 3, 5, 10, 20, 50, 150, 600]
SIZES = [100, 500, 2000]
HORIZONS = {"1m": 600, "5m": 3000, "30m": 18000, "60m": 35000}
GAS_USD_PER_TX = float(sys.argv[1]) if len(sys.argv) > 1 else 0.02

def s256(h):
    v = int(h, 16); return v - (1 << 256) if v >> 255 else v

def decode(l):
    w = [l["data"][2 + 64 * k: 2 + 64 * (k + 1)] for k in range(6)]
    return dict(b=l["b"], i=l["i"], tx=l["tx"].lower(), a0=s256(w[0]), a1=s256(w[1]),
                sp=int(w[2], 16) / Q96, L=int(w[3], 16), fee=int(w[5], 16) / 1e6)

def buy_out(st, x, tok_c1):
    L, sp = st["L"], st["sp"]; x = x * (1 - st["fee"])
    if L <= 0: return 0.0
    if tok_c1:
        sp2 = 1 / (1 / sp + x / L); return L * (sp - sp2)
    sp2 = sp + x / L; return L * (1 / sp - 1 / sp2)

def sell_out(st, t, tok_c1):
    L, sp = st["L"], st["sp"]; t = t * (1 - st["fee"])
    if L <= 0: return 0.0
    if tok_c1:
        sp2 = sp + t / L; return L * (1 / sp - 1 / sp2)
    sp2 = 1 / (1 / sp + t / L); return L * (sp - sp2)

def tok_price(st, tok_c1):  # quote per token, raw units
    p = st["sp"] ** 2  # c1 per c0
    return 1 / p if tok_c1 else p

decimals_cache_path = os.path.join(SP, "decimals.json")
decs = json.load(open(decimals_cache_path)) if os.path.exists(decimals_cache_path) else {}
def decimals(token):
    if token in decs: return decs[token]
    try:
        r = requests.post("https://rpc.mainnet.chain.robinhood.com", timeout=20, json={
            "jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": token, "data": "0x313ce567"}, "latest"]}).json()
        decs[token] = int(r["result"], 16)
    except Exception:
        decs[token] = None
    return decs[token]

sample = pd.read_pickle(os.path.join(SP, "sample.pkl"))
out, skips = [], {}
def skip(k): skips[k] = skips.get(k, 0) + 1

for r in sample.itertuples(index=False):
    path = os.path.join(SP, "logs", r.pool + ".json")
    if not os.path.exists(path): skip("pool not fetched"); continue
    blob = json.load(open(path))
    if blob.get("failed"): skip("pool range failed"); continue
    logs = sorted((decode(l) for l in blob["logs"]), key=lambda z: (z["b"], z["i"]))
    keys = [(z["b"], z["i"]) for z in logs]
    src = [k for k, z in enumerate(logs) if z["tx"] == r.tx.lower()]
    if not src: skip("source swap not in pool logs (routed elsewhere)"); continue
    k = src[-1]
    if k == 0 or logs[k - 1]["b"] < r.block - 3000: skip("no pre-state"); continue
    pre, post = logs[k - 1], logs[k]
    if post["sp"] == pre["sp"]: skip("no price move"); continue
    tok_c1 = post["sp"] < pre["sp"]          # buying token pushed sqrtP down => token is currency1
    q_in = abs(post["a0"] if tok_c1 else post["a1"])
    t_out_evt = abs(post["a1"] if tok_c1 else post["a0"])
    if q_in == 0 or t_out_evt == 0: skip("zero amounts"); continue
    usd_per_q = r.usd / q_in
    dec = decimals(r.token)
    hook_tax = 0.0
    if dec is not None:
        ratio = (r.amount * 10 ** dec) / t_out_evt
        hook_tax = min(max(0.0, 1 - ratio), 0.5) if 0.3 < ratio < 1.5 else 0.0

    def state_end_of_block(B):
        j = int(np.searchsorted([kk[0] for kk in keys], B, side="right")) - 1
        return logs[j] if j >= 0 else None

    ex = r.exit
    for d in DELAYS:
        eb = r.block + d
        st_in = post if d == 0 else state_end_of_block(eb - 1)
        if st_in is None or (d > 0 and st_in["b"] < r.block): skip("entry state"); continue
        entry_drift = tok_price(st_in, tok_c1) / tok_price(post, tok_c1) - 1
        for S in SIZES:
            x = S / usd_per_q
            toks = buy_out(st_in, x, tok_c1) * (1 - hook_tax)
            if toks <= 0: continue
            row = dict(wallet=r.wallet, token=r.token, pool=r.pool, block=r.block, followers=r.followers,
                       src_usd=r.usd, d=d, S=S, entry_drift=entry_drift, hook_tax=hook_tax,
                       lp_fee=st_in["fee"])
            # mirror exit
            if ex is not None:
                sb = int(ex["block"])
                sidx = [kk for kk, z in enumerate(logs) if z["tx"] == str(ex["tx"]).lower()]
                if d == 0:
                    st_out = logs[sidx[-1]] if sidx else state_end_of_block(sb)
                else:
                    st_out = state_end_of_block(sb + d - 1)
                covered = any(a <= sb + d <= b for a, b in blob["intervals"])
                # USD per quote unit at exit, from the source's own sell swap in this pool (VERIFIED leg);
                # without it the return stays quote-denominated and is flagged.
                usd_per_q_exit, conv = usd_per_q, "quote"
                if sidx:
                    zs = logs[sidx[-1]]; q_out = abs(zs["a0"] if tok_c1 else zs["a1"])
                    if q_out > 0 and float(ex["usd"]) > 0:
                        usd_per_q_exit, conv = float(ex["usd"]) / q_out, "usd"
                if st_out is not None and covered and st_out["b"] >= sb - 3000:
                    row["exit_conv"] = conv
                    proceeds = sell_out(st_out, toks, tok_c1) * (1 - hook_tax) * usd_per_q_exit
                    row["mirror_ret"] = (proceeds - S - 2 * GAS_USD_PER_TX) / S
                    row["src_ret_tape"] = float(ex["price"]) / r.price - 1 if r.price else np.nan
                    row["hold_blocks"] = sb - r.block
            for h, H in HORIZONS.items():
                st_out = state_end_of_block(eb + H)
                if st_out is None or eb + H > blob["intervals"][0][1] and not any(a <= eb + H <= b for a, b in blob["intervals"]):
                    continue
                proceeds = sell_out(st_out, toks, tok_c1) * (1 - hook_tax) * usd_per_q
                row[f"ret_{h}"] = (proceeds - S - 2 * GAS_USD_PER_TX) / S
            out.append(row)

json.dump(decs, open(decimals_cache_path, "w"))
res = pd.DataFrame(out)
res.to_parquet(os.path.join(SP, "copy_sim_results.parquet"))
print("skips:", skips)
n_src = res[(res.d == 0) & (res.S == 100)].shape[0]
print(f"simulated source buys: {n_src}  rows: {len(res)}  gas/tx ${GAS_USD_PER_TX}")
print("median output-side hook tax:", round(res.hook_tax.median(), 4), " median lp fee:", round(res.lp_fee.median(), 4))

def summ(col, S):
    g = res[res.S == S].groupby("d")[col]
    return pd.DataFrame({"n": g.count(), "mean": g.mean(), "median": g.median(),
                         "win": g.apply(lambda s: (s > 0).mean()),
                         "trim5_mean": g.apply(lambda s: s.clip(s.quantile(.05), s.quantile(.95)).mean())})

pd.set_option("display.width", 200)
print("\nENTRY DRIFT (token price at follower entry state vs source post-trade price), S=$100")
g = res[res.S == 100].groupby("d").entry_drift
print(pd.DataFrame({"n": g.count(), "median": g.median(), "mean": g.mean(), "p90": g.quantile(.9)}).round(4))
for S in SIZES:
    print(f"\nMIRROR-EXIT follower net return, S=${S}")
    print(summ("mirror_ret", S).round(4))
print("\nSource's own round trip on the same trades (tape prices, before gas):",
      res[(res.d == 0) & (res.S == 100)].src_ret_tape.describe().round(4).to_dict())
for h in HORIZONS:
    print(f"\nFIXED {h} exit, S=$500")
    print(summ(f"ret_{h}", 500).round(4))
