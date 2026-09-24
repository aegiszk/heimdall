"""Read-only: how far does the public RPC head lag the sequencer feed? Plus endpoint RTTs.
No keys, no signing, no transactions sent."""
import asyncio, aiohttp, json, time, sys

FEED = "wss://feed.mainnet.chain.robinhood.com"
RPC = "https://rpc.mainnet.chain.robinhood.com"
SEQ = "https://sequencer.mainnet.chain.robinhood.com"

feed_t = {}      # sequenceNumber -> first recv time
feed_ts = {}     # sequenceNumber -> header timestamp (sec)
polls = []       # (t_after_response, rtt_ms, head)

async def feed_task(duration):
    t_end = time.time() + duration
    async with aiohttp.ClientSession() as s:
        async with s.ws_connect(FEED, compress=15, headers={"Arbitrum-Feed-Client-Version": "2"},
                                heartbeat=30, max_msg_size=0) as ws:
            async for msg in ws:
                t = time.time()
                for m in json.loads(msg.data).get("messages", []):
                    feed_t.setdefault(m["sequenceNumber"], t)
                    feed_ts[m["sequenceNumber"]] = m["message"]["message"]["header"]["timestamp"]
                if t > t_end: break

async def call(s, url, method, params):
    t0 = time.time()
    async with s.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                      timeout=aiohttp.ClientTimeout(total=5)) as r:
        j = await r.json()
    return j, (time.time() - t0) * 1000

async def poll_task(duration):
    t_end = time.time() + duration
    async with aiohttp.ClientSession() as s:
        while time.time() < t_end:
            try:
                j, rtt = await call(s, RPC, "eth_blockNumber", [])
                polls.append((time.time(), rtt, int(j["result"], 16)))
            except Exception:
                pass
            await asyncio.sleep(0.05)

def pct(v, q):
    v = sorted(v); return v[min(len(v) - 1, int(q * len(v)))]

async def rtts():
    out = {}
    async with aiohttp.ClientSession() as s:
        for name, url, method in [("rpc eth_chainId", RPC, "eth_chainId"),
                                  ("sequencer eth_chainId", SEQ, "eth_chainId")]:
            v = []
            for _ in range(15):
                try:
                    j, rtt = await call(s, url, method, []); v.append(rtt)
                    out[name + " result"] = j.get("result", j.get("error"))
                except Exception as e:
                    out[name + " err"] = str(e)[:80]
                await asyncio.sleep(0.1)
            if v: out[name] = f"p50 {pct(v,.5):.0f} ms  p90 {pct(v,.9):.0f} ms  min {min(v):.0f}"
    return out

async def main(duration):
    await asyncio.gather(feed_task(duration), poll_task(duration))
    # offset: L2 block = seq + off. Pick off that minimises median |lag| sign-consistently:
    # the RPC cannot report block N before the sequencer emitted it, so the correct offset
    # makes (t_poll - feed_t[head-off]) >= ~0 for nearly all polls.
    best = None
    for off in range(-5, 6):
        lags = [(tp - feed_t[h - off]) * 1000 for tp, _, h in polls if (h - off) in feed_t]
        if len(lags) < 50: continue
        neg = sum(l < -5 for l in lags) / len(lags)
        cand = (neg, abs(pct(lags, .5)), off, lags)
        if best is None or cand[:2] < best[:2]: best = cand
    neg, _, off, lags = best
    print(f"offset block = seq {off:+d}; polls={len(polls)}; frac negative={neg:.3f}")
    print("RPC head visible MINUS feed recv of same block (ms), upper bound incl. poll interval:")
    print("  p10 %.0f  p50 %.0f  p90 %.0f  p99 %.0f" % (pct(lags,.1), pct(lags,.5), pct(lags,.9), pct(lags,.99)))
    r = [p[1] for p in polls]
    print("RPC eth_blockNumber RTT ms: p50 %.0f p90 %.0f p99 %.0f" % (pct(r,.5), pct(r,.9), pct(r,.99)))
    seqs = sorted(feed_t)
    gaps = [(feed_t[b] - feed_t[a]) * 1000 for a, b in zip(seqs, seqs[1:]) if b == a + 1]
    print("feed inter-message gap ms: p50 %.0f p90 %.0f" % (pct(gaps,.5), pct(gaps,.9)))
    # header timestamp (1s resolution) vs local recv: clock-skew-contaminated, report only coarse
    sk = [feed_t[q] - feed_ts[q] for q in seqs]
    print("local recv - header timestamp (s, 1s resolution, includes clock skew): p50 %.2f p90 %.2f" % (pct(sk,.5), pct(sk,.9)))
    for k, v in (await rtts()).items(): print(" ", k, ":", v)

asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 60))
