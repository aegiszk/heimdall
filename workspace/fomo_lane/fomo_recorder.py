"""FOMO prospective recorder (FOMO_PROSPECTIVE_PREREGISTRATION.md, SHA-256 902263424c17...).

READ-ONLY. No keys, no signing, no transactions. Records, append-only JSONL under data_amend1/ (Amendment 1; run 1-4 data/ kept):
  blocks/  L2 block arrival times on the sequencer feed (block = seq - 2)
  rtt/     sequencer / RPC round-trip probes
  logs/    raw swap/sync/UserOp/executor-Transfer logs (for offline pool-state replay)
  events/  every executor->FOMO-wallet buy with point-in-time decision record (universe, S1-S3, price)
  exits/   exit-time sellability checks scheduled 1800 s after each decision
Outcome P&L is NOT computed here (no interim peeking); see evaluate_prospective.py (run only at stopping time).
"""
import asyncio, aiohttp, json, os, sys, time, threading, heapq, collections, traceback
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data_amend1")          # Amendment 1: fresh sample; pre-amendment data/ kept for the record
RPC = "https://rpc.mainnet.chain.robinhood.com"
FEED = "wss://feed.mainnet.chain.robinhood.com"
SEQ = "https://sequencer.mainnet.chain.robinhood.com"
EXECUTOR = "0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f"
ENTRYPOINT = "0x4337084d9e255ff0702461cf8895ce9e3b5ff108"
S7702 = "e6cae83bde06e4c305530e199d7217f42808555b"
POOLMANAGER = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
T_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
T_SWAP4 = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
T_SWAP3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
T_SWAP2 = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
T_SYNC2 = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
T_UOE = "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"
T_INIT4 = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
Q96 = 2 ** 96
SIZE_USD, MIN_SRC_USD, UNIVERSE_MIN_BUYS, UNIVERSE_WINDOW = 500.0, 100.0, 10, 72 * 3600
S1_WINDOW, S1_MIN_SELLS, S3_MAX_IMPACT, EXIT_AFTER = 300, 5, 0.05, 1800

def day(): return time.strftime("%Y%m%d", time.gmtime())
WRITE_LOCK = threading.Lock()
def write(kind, obj):
    d = os.path.join(OUT, kind); os.makedirs(d, exist_ok=True)
    line = json.dumps(obj) + "\n"
    with WRITE_LOCK:
        with open(os.path.join(d, day() + ".jsonl"), "a") as f: f.write(line)

# ---------------- Amendment 1: RPC rate discipline (infrastructure only) ----------------
# The public RPC answers HTTP 429 on eth_getLogs under load. Before Amendment 1 a rate-limited call counted as a failure,
# get_logs() bisected the range and multiplied the load, and the 72 h warm-up never completed. Now: token bucket per
# method class with AIMD on 429, rate errors never bisect, and warm-up calls are low priority (they wait while the live
# poll loop lags). Decision logic, universe definition and all thresholds are unchanged.
MAIN_LAG = [0]                    # live poll loop: head - last processed block
WARMUP_MAX_MAIN_LAG = 300         # warm-up pauses while the poll loop is further behind than this (blocks)
WARMUP_CHUNK0, WARMUP_CHUNK_MIN, WARMUP_CHUNK_MAX = 20_000, 100, 200_000
_LOW = threading.local()          # _LOW.on = True marks warm-up threads

class RateLimited(RuntimeError): pass

class _Gate:
    def __init__(self, name, rate, lo, hi):
        self.name, self.rate, self.lo, self.hi = name, rate, lo, hi
        self.tokens, self.t, self.t_low, self.cool_until, self.backoff, self.ok = 1.0, time.time(), 0.0, 0.0, 5.0, 0
        self.lock = threading.Lock()
    def acquire(self, low):
        while True:
            with self.lock:
                now = time.time()
                self.tokens = min(max(1.0, self.rate), self.tokens + (now - self.t) * self.rate); self.t = now
                blocked = now < self.cool_until or (low and (MAIN_LAG[0] > WARMUP_MAX_MAIN_LAG
                                                             or now - self.t_low < 2.0 / self.rate))
                if not blocked and self.tokens >= 1.0:
                    self.tokens -= 1.0
                    if low: self.t_low = now
                    return
                wait = max(self.cool_until - now, (1.0 - self.tokens) / self.rate, 0.05)
            time.sleep(min(wait, 1.0))
    def limited(self):
        with self.lock:
            self.rate = max(self.lo, self.rate / 2); self.ok = 0
            self.cool_until = time.time() + self.backoff; cool = self.backoff; self.backoff = min(self.backoff * 2, 300.0)
        write("rtt", {"t": time.time(), "rpc_429": self.name, "rate_per_s": self.rate, "cooldown_s": cool})
    def success(self):
        with self.lock:
            self.backoff = 5.0; self.ok += 1
            if self.ok >= 50: self.rate = min(self.hi, self.rate + 0.25); self.ok = 0

GATES = {"logs": _Gate("eth_getLogs", 2.0, 0.5, 5.0), "other": _Gate("other", 10.0, 0.5, 20.0)}

SESSION = requests.Session()
def rpc(method, params, url=RPC, tries=6, rate_tries=40):
    gate = (GATES["logs"] if method == "eth_getLogs" else GATES["other"]) if url == RPC else None
    low = getattr(_LOW, "on", False); k = 0; r = 0
    while k < tries:
        if gate: gate.acquire(low)
        try:
            resp = SESSION.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=30)
            j = {} if resp.status_code == 429 else resp.json()
            e = str(j.get("error", ""))
            if resp.status_code == 429 or "429" in e or "Too Many" in e:
                r += 1
                if gate: gate.limited()
                else: time.sleep(1.5 * r)
                if r >= rate_tries: raise RateLimited(f"rpc {method} rate-limited")
                continue
            if "error" in j: raise RuntimeError(e)
            if gate: gate.success()
            return j["result"]
        except (requests.RequestException, ValueError):
            k += 1; time.sleep(1.5 * k)
    raise RuntimeError(f"rpc {method} gave up")

def get_logs(flt, a, b):
    try:
        return rpc("eth_getLogs", [dict(flt, fromBlock=hex(a), toBlock=hex(b))])
    except RateLimited:
        raise                                     # never bisect on a rate limit (that multiplies the load)
    except RuntimeError as ex:
        if b - a < 50: raise
        m = (a + b) // 2
        return get_logs(flt, a, m) + get_logs(flt, m + 1, b)

# ---------------- feed clock (thread) ----------------
BLOCK_T = {}                      # block -> arrival ns (in-memory recent)
def feed_thread():
    async def run():
        # Amendment 1b: exponential reconnect back-off (2 s .. 300 s, reset after a message) and Retry-After on 403/429.
        # A fixed 2 s retry after a rejected handshake got this host "Blocked for 1 hour after sustained feed connection
        # rejections" on 2026-09-24.
        backoff = 2.0
        while True:
            try:
                async with aiohttp.ClientSession() as s:
                    async with s.ws_connect(FEED, compress=15, headers={"Arbitrum-Feed-Client-Version": "2"},
                                            heartbeat=30, max_msg_size=0) as ws:
                        async for msg in ws:
                            t = time.time_ns(); backoff = 2.0
                            for m in json.loads(msg.data).get("messages", []):
                                b = m["sequenceNumber"] - 2
                                if b not in BLOCK_T:
                                    BLOCK_T[b] = t; write("blocks", {"b": b, "t_ns": t})
            except Exception as ex:
                wait = backoff
                if getattr(ex, "status", None) in (403, 429):
                    try: wait = max(wait, float((getattr(ex, "headers", None) or {}).get("Retry-After", 0)))
                    except (TypeError, ValueError): pass
                write("rtt", {"t": time.time(), "feed_error": str(ex)[:200], "retry_in_s": wait})
                await asyncio.sleep(wait); backoff = min(backoff * 2, 300.0)
    asyncio.run(run())

def rtt_probe():
    out = {"t": time.time()}
    for name, url, meth in (("seq", SEQ, "eth_chainId"), ("rpc", RPC, "eth_blockNumber")):
        v = []
        for _ in range(5):
            t0 = time.perf_counter()
            try: SESSION.post(url, json={"jsonrpc": "2.0", "id": 1, "method": meth, "params": []}, timeout=10)
            except Exception: continue
            v.append((time.perf_counter() - t0) * 1000); time.sleep(0.2)
        if v: out[name + "_rtt_ms_median"] = sorted(v)[len(v) // 2]
    write("rtt", out)

# ---------------- caches ----------------
CODE, TOK01, V4KEY, DEC = {}, {}, {}, {}
def is_fomo_wallet(a):
    if a not in CODE:
        c = rpc("eth_getCode", [a, "latest"]).lower()
        CODE[a] = c.startswith("0xef0100") and S7702 in c
    return CODE[a]
def pool_tokens(pool):
    if pool not in TOK01:
        t0 = "0x" + rpc("eth_call", [{"to": pool, "data": "0x0dfe1681"}, "latest"])[-40:]
        t1 = "0x" + rpc("eth_call", [{"to": pool, "data": "0xd21220a7"}, "latest"])[-40:]
        TOK01[pool] = (t0.lower(), t1.lower())
    return TOK01[pool]
def v4_key(pid):
    if pid not in V4KEY:
        r = get_logs({"address": POOLMANAGER, "topics": [T_INIT4, pid]}, 0, int(rpc("eth_blockNumber", []), 16))
        V4KEY[pid] = (("0x" + r[0]["topics"][2][-40:]).lower(), ("0x" + r[0]["topics"][3][-40:]).lower(),
                      "0x" + r[0]["data"][2 + 64 * 2: 2 + 64 * 3][-40:]) if r else None
    return V4KEY[pid]
def dexscreener_price(token):
    try:
        j = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token}", timeout=8).json()
        ps = [p for p in (j.get("pairs") or []) if p.get("chainId") == "robinhood" and p.get("priceUsd")]
        if not ps: return None
        p = max(ps, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
        return float(p["priceUsd"])
    except Exception:
        return None

def s256(h):
    v = int(h, 16); return v - (1 << 256) if v >> 255 else v

# rolling pool state + recent sells (from polled logs)
POOL_STATE = {}                                   # pool key -> dict(kind, sp/L/fee or r0/r1, b)
POOL_SELLS = collections.defaultdict(collections.deque)   # (pool key) -> deque[(t_sec, block, tx, dir)]
def ingest_pool_log(l, now):
    t0 = l["topics"][0]; b = int(l["blockNumber"], 16); tx = l["transactionHash"].lower()
    if t0 == T_SWAP4:
        d = l["data"][2:]; w = [d[64 * k:64 * (k + 1)] for k in range(6)]
        key = l["topics"][1].lower(); prev = POOL_STATE.get(key)
        st = {"kind": "v4", "sp": int(w[2], 16) / Q96, "L": int(w[3], 16), "fee": int(w[5], 16) / 1e6, "b": b}
    elif t0 == T_SWAP3:
        d = l["data"][2:]; w = [d[64 * k:64 * (k + 1)] for k in range(5)]
        key = l["address"].lower(); prev = POOL_STATE.get(key)
        st = {"kind": "v3", "sp": int(w[2], 16) / Q96, "L": int(w[3], 16), "fee": None, "b": b}
    elif t0 == T_SYNC2:
        d = l["data"][2:]; key = l["address"].lower(); prev = POOL_STATE.get(key)
        st = {"kind": "v2", "r0": int(d[:64], 16), "r1": int(d[64:128], 16), "b": b}
    else:
        return
    # direction of price move in c1-per-c0 terms (+1 up, -1 down); token-relative sell sign resolved at use time
    if prev and prev["kind"] == st["kind"]:
        if st["kind"] == "v2":
            p0 = prev["r1"] / prev["r0"] if prev["r0"] else 0; p1 = st["r1"] / st["r0"] if st["r0"] else 0
        else:
            p0, p1 = prev["sp"], st["sp"]
        if p1 != p0:
            q = POOL_SELLS[key]; q.append((now, b, tx, 1 if p1 > p0 else -1))
            while q and q[0][0] < now - 900: q.popleft()
    POOL_STATE[key] = st

# ---------------- universe (point-in-time) ----------------
BUYS = collections.defaultdict(collections.deque)          # wallet -> deque[t_sec]
WARM_LOCK = threading.Lock(); WARM_DONE = [False]
def universe_ok(wallet, now):
    with WARM_LOCK:
        return _universe_ok(wallet, now)
def _universe_ok(wallet, now):
    q = BUYS[wallet]
    while q and q[0] < now - UNIVERSE_WINDOW: q.popleft()
    return len(q) >= UNIVERSE_MIN_BUYS

def warmup(head):
    """72 h of executor transfers before start -> per-wallet buy timestamps (block time)."""
    _LOW.on = True                                                     # Amendment 1: low-priority RPC
    t_head = time.time(); start = head - int(UNIVERSE_WINDOW * 10.2)   # ~10 blocks/s measured
    flt = {"topics": [T_TRANSFER, "0x" + "0" * 24 + EXECUTOR[2:]]}
    # Amendment 1: adaptive chunks, no recursive bisection; a range that fails at the minimum chunk is a gap and is
    # retried until it succeeds, so warmup_complete is set only after a gap-free pass over the whole 72 h window.
    logs = []; todo = [(start, head)]; chunk = WARMUP_CHUNK0; calls = 0
    while todo:
        a, end = todo.pop(0)
        while a <= end:
            b = min(end, a + chunk - 1)
            try:
                logs += rpc("eth_getLogs", [dict(flt, fromBlock=hex(a), toBlock=hex(b))])
                a = b + 1; chunk = min(WARMUP_CHUNK_MAX, int(chunk * 1.5))
            except RateLimited:
                pass                                                   # the gate has cooled down; retry the range
            except Exception as ex:
                if chunk > WARMUP_CHUNK_MIN:
                    chunk = max(WARMUP_CHUNK_MIN, chunk // 2)
                else:
                    write("rtt", {"t": time.time(), "warmup_gap": [a, b], "err": str(ex)[:120]})
                    todo.append((a, b)); a = b + 1; time.sleep(5)
            calls += 1
            if calls % 25 == 0:
                write("rtt", {"t": time.time(), "warmup_progress": [a, end], "warmup_start": start, "warmup_logs": len(logs),
                              "chunk": chunk, "pending_gaps": len(todo)})
    from concurrent.futures import ThreadPoolExecutor
    rec = [(("0x" + l["topics"][2][-40:]).lower(), int(l["blockNumber"], 16)) for l in logs]
    addrs = sorted({a for a, _ in rec})
    def chk(a):
        _LOW.on = True
        for _ in range(3):
            try: return a, is_fomo_wallet(a)
            except Exception: time.sleep(5)
        return a, False
    with ThreadPoolExecutor(8) as pool:
        fomo = dict(pool.map(chk, addrs))
    n = 0; warm = collections.defaultdict(list)
    for to, bn in rec:
        if fomo.get(to):
            warm[to].append(t_head - (head - bn) / 10.0); n += 1     # approx block time (flagged)
    with WARM_LOCK:
        for w, ts in warm.items():
            merged = sorted(list(BUYS[w]) + ts); BUYS[w].clear(); BUYS[w].extend(merged)
        WARM_DONE[0] = True
    write("warmup", {"head": head, "buys": {w: [(b) for b in ts] for w, ts in warm.items()}})
    write("rtt", {"t": time.time(), "warmup_executor_transfers": len(logs), "warmup_fomo_buys": n,
                  "warmup_wallets": len(BUYS), "universe_now": sum(_universe_ok(w, t_head) for w in list(BUYS))})

# ---------------- decision on a buy event ----------------
EXIT_LOCK = threading.Lock()
EXITS = []                                                   # heap (due_ts, event_id, token, wallet, target, amount)
def handle_buy(l, now_detect):
    t_proc0 = time.perf_counter()
    token = l["address"].lower(); wallet = ("0x" + l["topics"][2][-40:]).lower()
    amount_raw = int(l["data"], 16); b = int(l["blockNumber"], 16); tx = l["transactionHash"].lower()
    ev = {"id": f"{tx}:{int(l['logIndex'],16)}", "tx": tx, "block": b, "token": token, "wallet": wallet,
          "amount_raw": amount_raw, "t_detect_rpc": now_detect, "t_arr_src_ns": BLOCK_T.get(b)}
    if not is_fomo_wallet(wallet):
        return None                                          # other Relay apps: not FOMO, not an event
    was_in_universe = universe_ok(wallet, now_detect)
    with WARM_LOCK: BUYS[wallet].append(now_detect)          # counts toward FUTURE universe only
    ev["universe"] = was_in_universe; ev["warmup_complete"] = WARM_DONE[0]
    rc = rpc("eth_getTransactionReceipt", [tx])
    swaps = []
    for x in rc["logs"]:
        t0 = x["topics"][0]
        if t0 == T_SWAP4: swaps.append(("v4", x["topics"][1].lower(), x))
        elif t0 == T_SWAP3: swaps.append(("v3", x["address"].lower(), x))
        elif t0 == T_SWAP2: swaps.append(("v2", x["address"].lower(), x))
    route = None
    for kind, key, x in swaps:
        try:
            if kind == "v4":
                k = v4_key(key)
                if k and token in (k[0], k[1]): route = (kind, key, k[0], k[1], k[2], x)
            else:
                t0_, t1_ = pool_tokens(key)
                if token in (t0_, t1_): route = (kind, key, t0_, t1_, None, x)
        except Exception:
            continue
    tok_out_evt = None
    if route:
        kind, key, c0, c1, hooks, x = route
        ev.update({"route": kind, "pool": key, "c0": c0, "c1": c1, "hooks": hooks, "token_is_c1": token == c1})
        dd = x["data"][2:]
        if kind in ("v3", "v4"):
            a0, a1 = s256(dd[:64]), s256(dd[64:128]); tok_out_evt = abs(a1 if token == c1 else a0)
        else:
            w = [int(dd[64 * i:64 * (i + 1)], 16) for i in range(4)]   # a0in,a1in,a0out,a1out
            tok_out_evt = w[3] if token == c1 else w[2]
        ev["output_tax"] = max(0.0, 1 - amount_raw / tok_out_evt) if tok_out_evt else None
    else:
        ev["route"] = "UNROUTABLE"
    if token not in DEC:
        try: DEC[token] = int(rpc("eth_call", [{"to": token, "data": "0x313ce567"}, "latest"]), 16)
        except Exception: DEC[token] = None
    px = dexscreener_price(token); ev["price_usd_detect"] = px
    ev["src_usd"] = (amount_raw / 10 ** DEC[token] * px) if (px and DEC[token] is not None) else None
    # S1: sell-direction swaps in pool, other txs, 300 s before detection
    if route:
        sell_sign = 1 if ev["token_is_c1"] else -1   # selling token raises c1-per-c0? token=c1 sold -> c1 up -> price(c1 per c0) up
        q = POOL_SELLS.get(route[1], ())
        # point-in-time: only blocks strictly BEFORE the source block, within ~300 s (10.2 blocks/s measured)
        ev["s1_sells"] = sum(1 for (ts, bb, t2, dr) in q if b - int(S1_WINDOW * 10.2) <= bb < b and t2 != tx and dr == sell_sign)
        ev["s1_coverage_s"] = now_detect - T_START
    # S2: transfer simulation from source wallet
    try:
        dest = POOLMANAGER if (route and route[0] == "v4") else (route[1] if route else POOLMANAGER)
        amt = max(1, amount_raw // 100)
        rpc("eth_call", [{"from": wallet, "to": token,
                          "data": "0xa9059cbb" + dest[2:].rjust(64, "0") + hex(amt)[2:].rjust(64, "0")}, "latest"])
        ev["s2_transfer_ok"] = True
    except Exception as ex:
        ev["s2_transfer_ok"] = False; ev["s2_err"] = str(ex)[:120]
    # S3: impact of a $500 buy at current pool state (constant-L / constant-product)
    # point-in-time: pool state emitted by the SOURCE's own swap (exact state at the source block)
    st = None
    if route:
        kind, key, x = route[0], route[1], route[5]
        dd = x["data"][2:]
        if kind in ("v3", "v4"):
            st = {"kind": kind, "sp": int(dd[128:192], 16) / Q96, "L": int(dd[192:256], 16), "b": b}
        else:
            syn = [y for y in rc["logs"] if y["topics"][0] == T_SYNC2 and y["address"].lower() == key]
            if syn:
                d2 = syn[-1]["data"][2:]; st = {"kind": "v2", "r0": int(d2[:64], 16), "r1": int(d2[64:128], 16), "b": b}
    if st and px and DEC[token] is not None:
        ev["entry_state_block_at_detect"] = st["b"]
        try:
            if st["kind"] == "v2":
                r_tok = st["r1"] if ev["token_is_c1"] else st["r0"]
                tok_usd_depth = r_tok / 10 ** DEC[token] * px
                ev["s3_impact"] = SIZE_USD / (tok_usd_depth + SIZE_USD) if tok_usd_depth > 0 else None
            else:
                sp, L = st["sp"], st["L"]
                # virtual token reserve inside tick: token=c1 -> L*sp ; token=c0 -> L/sp  (raw units)
                virt = (L * sp) if ev["token_is_c1"] else (L / sp)
                tok_usd_depth = virt / 10 ** DEC[token] * px
                ev["s3_impact"] = SIZE_USD / (tok_usd_depth + SIZE_USD) if tok_usd_depth > 0 else None
        except Exception:
            ev["s3_impact"] = None
    ev["eligible"] = bool(ev["universe"] and route and ev.get("src_usd") and ev["src_usd"] >= MIN_SRC_USD
                          and ev.get("s1_sells", 0) >= S1_MIN_SELLS and ev.get("s2_transfer_ok")
                          and ev.get("s3_impact") is not None and ev["s3_impact"] <= S3_MAX_IMPACT)
    ev["processing_ms"] = (time.perf_counter() - t_proc0) * 1000
    ev["t_decision"] = time.time()
    write("events", ev)
    ev["detect_lag_s"] = (now_detect - ev["t_arr_src_ns"] / 1e9) if ev.get("t_arr_src_ns") else None
    if ev["eligible"]:
      with EXIT_LOCK:
        heapq.heappush(EXITS, (ev["t_decision"] + EXIT_AFTER, ev["id"], token, wallet, route[1], amount_raw))
    return ev

def run_exit_checks(now):
    while True:
        with EXIT_LOCK:
            if not (EXITS and EXITS[0][0] <= now): break
            due, eid, token, wallet, dest, amt = heapq.heappop(EXITS)
        rec = {"id": eid, "t_exit_check": now, "due": due}
        try:
            bal = int(rpc("eth_call", [{"to": token, "data": "0x70a08231" + wallet[2:].rjust(64, "0")}, "latest"]), 16)
            rec["src_balance_raw"] = bal
            holder = wallet if bal > 0 else None
            if holder:
                rpc("eth_call", [{"from": holder, "to": token, "data": "0xa9059cbb" + (POOLMANAGER if dest.startswith("0x") and len(dest) == 66 else dest)[2:].rjust(64, "0")
                                  + hex(max(1, min(bal, amt) // 100))[2:].rjust(64, "0")}, "latest"])
                rec["exit_transfer_ok"] = True
            else:
                rec["exit_transfer_ok"] = None          # source exited; sellability checked offline via pool activity
        except Exception as ex:
            rec["exit_transfer_ok"] = False; rec["err"] = str(ex)[:120]
        write("exits", rec)

# ---------------- main poll loop ----------------
from concurrent.futures import ThreadPoolExecutor
WORKERS = ThreadPoolExecutor(12)
def safe_handle(l, now):
    try: handle_buy(l, now)
    except Exception as ex: write("events", {"error": str(ex)[:200], "tx": l["transactionHash"], "trace": traceback.format_exc()[-300:]})
T_START = time.time()
def main():
    threading.Thread(target=feed_thread, daemon=True).start()
    head = int(rpc("eth_blockNumber", []), 16)
    write("rtt", {"t": time.time(), "start_head": head, "prereg_sha256": "902263424c170fb7920c0a0880f056a8c7cc1b80e9a8dd5f2708a883c72fbc39",
                 "amendment": "FOMO_PROSPECTIVE_PREREGISTRATION_AMENDMENT_1.md"})
    threading.Thread(target=warmup, args=(head,), daemon=True).start()   # universe warm-up off the hot path
    last = head; last_rtt = 0
    while True:
        try:
            now = time.time()
            if now - last_rtt > 600: rtt_probe(); last_rtt = now
            head = int(rpc("eth_blockNumber", []), 16)
            MAIN_LAG[0] = head - last
            if head > last:
                a, b = last + 1, min(head, last + 100)
                pl = get_logs({"topics": [[T_SWAP4, T_SWAP3, T_SWAP2, T_SYNC2, T_UOE]]}, a, b)
                bl = get_logs({"topics": [T_TRANSFER, "0x" + "0" * 24 + EXECUTOR[2:]]}, a, b)
                now = time.time()
                for l in pl:
                    ingest_pool_log(l, now)
                    write("logs", {"b": int(l["blockNumber"], 16), "i": int(l["logIndex"], 16), "a": l["address"].lower(),
                                   "t": l["topics"], "d": l["data"], "tx": l["transactionHash"].lower()})
                for l in bl:
                    write("logs", {"b": int(l["blockNumber"], 16), "i": int(l["logIndex"], 16), "a": l["address"].lower(),
                                   "t": l["topics"], "d": l["data"], "tx": l["transactionHash"].lower()})
                    WORKERS.submit(safe_handle, l, now)
                last = b
            MAIN_LAG[0] = head - last
            run_exit_checks(time.time())
            if len(BLOCK_T) > 200_000:
                for k in sorted(BLOCK_T)[:-100_000]: BLOCK_T.pop(k, None)
            time.sleep(1.0)
        except Exception as ex:
            write("rtt", {"t": time.time(), "loop_error": str(ex)[:200]}); time.sleep(3)

if __name__ == "__main__":
    main()
