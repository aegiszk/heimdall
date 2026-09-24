"""Read-only latency benchmark: Robinhood Chain sequencer feed vs public RPC.
No keys, no signing, no transactions sent. Records per-tx first-seen times."""
import asyncio, aiohttp, base64, json, time, sys, struct, statistics

FEED = "wss://feed.mainnet.chain.robinhood.com"
RPC = "https://rpc.mainnet.chain.robinhood.com"

# ---------- pure-python keccak256 ----------
RC = [0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,
      0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,
      0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,
      0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,
      0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,
      0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008]
ROT = [[0,36,3,41,18],[1,44,10,45,2],[62,6,43,15,61],[28,55,25,21,56],[27,20,39,8,14]]
M = (1 << 64) - 1
def _rol(x, n): return ((x << n) | (x >> (64 - n))) & M if n else x
def _f(A):
    for rc in RC:
        C = [A[x][0]^A[x][1]^A[x][2]^A[x][3]^A[x][4] for x in range(5)]
        D = [C[(x-1)%5] ^ _rol(C[(x+1)%5], 1) for x in range(5)]
        A = [[A[x][y]^D[x] for y in range(5)] for x in range(5)]
        B = [[0]*5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                B[y][(2*x+3*y)%5] = _rol(A[x][y], ROT[x][y])
        A = [[B[x][y] ^ ((~B[(x+1)%5][y]) & B[(x+2)%5][y]) for y in range(5)] for x in range(5)]
        A[0][0] ^= rc
    return A
def keccak256(data: bytes) -> bytes:
    rate = 136
    if len(data) % rate == rate - 1:
        p = bytearray(data) + b"\x81"
    else:
        p = bytearray(data) + b"\x01" + b"\x00" * ((-len(data) - 2) % rate) + b"\x80"
    A = [[0]*5 for _ in range(5)]
    for off in range(0, len(p), rate):
        blk = p[off:off+rate]
        for i in range(rate // 8):
            x, y = i % 5, i // 5
            A[x][y] ^= int.from_bytes(blk[8*i:8*i+8], "little")
        A = _f(A)
    out = b"".join(A[i % 5][i // 5].to_bytes(8, "little") for i in range(4))
    return out

assert keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"

# ---------- minimal RLP ----------
def rlp_item(b, i):
    p = b[i]
    if p < 0x80: return b[i:i+1], i+1, False
    if p < 0xb8: n = p-0x80; return b[i+1:i+1+n], i+1+n, False
    if p < 0xc0: ll = p-0xb7; n = int.from_bytes(b[i+1:i+1+ll], "big"); s = i+1+ll; return b[s:s+n], s+n, False
    if p < 0xf8: n = p-0xc0; return b[i+1:i+1+n], i+1+n, True
    ll = p-0xf7; n = int.from_bytes(b[i+1:i+1+ll], "big"); s = i+1+ll; return b[s:s+n], s+n, True
def rlp_list(payload):
    out, i = [], 0
    while i < len(payload):
        v, i, _ = rlp_item(payload, i); out.append(v)
    return out

def parse_tx(raw: bytes):
    """Return (to, selector) for legacy / 2930 / 1559 txs."""
    try:
        if raw[0] >= 0xc0:  # legacy
            f = rlp_list(rlp_item(raw, 0)[0]); to, data = f[3], f[5]
        else:
            t = raw[0]; f = rlp_list(rlp_item(raw, 1)[0])
            if t == 2: to, data = f[5], f[7]
            elif t == 1: to, data = f[4], f[6]
            else: return None, None
        return ("0x" + to.hex()) if to else None, ("0x" + data[:4].hex()) if len(data) >= 4 else None
    except Exception:
        return None, None

def extract_txs(l2msg: bytes):
    """Arbitrum L2 message: kind 3 = batch of (u64 len, sub-msg), kind 4 = signed tx."""
    out = []
    def walk(m, depth=0):
        if not m or depth > 3: return
        k = m[0]
        if k == 4: out.append(m[1:])
        elif k == 3:
            i = 1
            while i + 8 <= len(m):
                n = struct.unpack(">Q", m[i:i+8])[0]; i += 8
                walk(m[i:i+n], depth+1); i += n
    walk(l2msg)
    return out

feed_raw = []    # (t_recv, seq, l2msg) -- decoded after capture to keep hot loop cheap
feed_seen = {}   # txhash -> (t_recv, feed_block, to, selector)
rpc_seen = {}    # txhash -> (t_seen_via_rpc, block)
feed_block_first = {}  # block -> first feed recv time
rpc_block_first = {}   # block -> time block first visible via RPC poll

async def feed_task(duration):
    t_end = time.time() + duration
    async with aiohttp.ClientSession() as s:
        async with s.ws_connect(FEED, compress=15, headers={"Arbitrum-Feed-Client-Version": "2"},
                                heartbeat=30, max_msg_size=0) as ws:
            async for msg in ws:
                t = time.time()
                d = json.loads(msg.data)
                for m in d.get("messages", []):
                    inner = m["message"]["message"]
                    blk = inner["header"].get("blockNumber")  # L1 block number, not L2
                    raw = base64.b64decode(inner["l2Msg"])
                    feed_raw.append((t, m["sequenceNumber"], raw))
                if t > t_end: break

async def rpc_call(s, method, params):
    async with s.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                      timeout=aiohttp.ClientTimeout(total=5)) as r:
        return (await r.json()).get("result")

async def rpc_task(duration, poll=0.1):
    t_end = time.time() + duration
    last = None; errors = 0
    async with aiohttp.ClientSession() as s:
        while time.time() < t_end:
            try:
                bn = int(await rpc_call(s, "eth_blockNumber", []), 16)
                t = time.time()
                if last is None: last = bn
                for b in range(last + 1, bn + 1):
                    rpc_block_first[b] = t
                    blk = await rpc_call(s, "eth_getBlockByNumber", [hex(b), False])
                    for h in (blk or {}).get("transactions", []):
                        rpc_seen.setdefault(h, (t, b))
                last = bn
            except Exception:
                errors += 1
            await asyncio.sleep(poll)
    print("rpc errors:", errors)

def pct(v, q):
    v = sorted(v); return v[min(len(v)-1, int(q*len(v)))]

async def main(duration):
    await asyncio.gather(feed_task(duration), rpc_task(duration))
    td = time.time()
    for t, seq, raw in feed_raw:
        for tx in extract_txs(raw):
            h = "0x" + keccak256(tx).hex()
            to, sel = parse_tx(tx)
            feed_seen.setdefault(h, (t, seq, to, sel))
    print(f"offline decode+hash: {len(feed_seen)} txs in {(time.time()-td)*1000:.0f} ms "
          f"({(time.time()-td)*1000/max(1,len(feed_seen)):.2f} ms/tx pure-python)")
    both = [h for h in feed_seen if h in rpc_seen]
    deltas = [(rpc_seen[h][0] - feed_seen[h][0]) * 1000 for h in both]
    print(f"feed txs: {len(feed_seen)}  rpc txs: {len(rpc_seen)}  matched: {len(both)}")
    if deltas:
        print("RPC-poll first-seen MINUS feed first-seen (ms): p10 %.0f p50 %.0f p90 %.0f p99 %.0f min %.0f max %.0f" % (
            pct(deltas,.1), pct(deltas,.5), pct(deltas,.9), pct(deltas,.99), min(deltas), max(deltas)))
        print("fraction feed-first:", sum(d > 0 for d in deltas) / len(deltas))
    rpc_only = [h for h in rpc_seen if h not in feed_seen]
    print("rpc-only txs (not decoded from feed):", len(rpc_only))
    blocks = sorted(rpc_block_first)
    if len(blocks) > 2:
        span = rpc_block_first[blocks[-1]] - rpc_block_first[blocks[0]]
        print(f"L2 blocks observed: {len(blocks)}  approx block interval {span/(len(blocks)-1)*1000:.0f} ms")
    tos = {}
    for h, (_, _, to, sel) in feed_seen.items():
        tos[(to, sel)] = tos.get((to, sel), 0) + 1
    print("top (to, selector) by count:")
    for (to, sel), c in sorted(tos.items(), key=lambda x: -x[1])[:15]:
        print(f"  {c:6d}  {to}  {sel}")
    json.dump({"feed": feed_seen, "rpc": rpc_seen}, open(sys.argv[2] if len(sys.argv) > 2 else "bench.json", "w"))

asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 60))
