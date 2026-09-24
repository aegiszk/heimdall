"""Offline check of FOMO Amendment 1 plumbing: mock RPC with 429 bursts + a range limit. No network."""
import importlib.util, json, os, sys, tempfile, threading, time, collections

spec = importlib.util.spec_from_file_location("rec", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fomo_recorder.py"))
rec = importlib.util.module_from_spec(spec); spec.loader.exec_module(rec)
rec.OUT = tempfile.mkdtemp()
rec.WARMUP_CHUNK0 = 20_000

HEAD = 3_000_000
CALLS = collections.Counter()
LOCK = threading.Lock()
EXEC_TOPIC = "0x" + "0" * 24 + rec.EXECUTOR[2:]
WALLETS = ["0x" + f"{i:040x}" for i in range(1, 6)]


class Resp:
    def __init__(self, code, body): self.status_code, self._b = code, body
    def json(self): return self._b


def fake_post(url, json=None, timeout=None):
    m, p = json["method"], json["params"]
    with LOCK:
        CALLS[m] += 1; n = CALLS[m]
    if m == "eth_getLogs":
        if n % 7 == 0:                                   # periodic throttling
            return Resp(429, None)
        a, b = int(p[0]["fromBlock"], 16), int(p[0]["toBlock"], 16)
        if b - a + 1 > 50_000:                           # range limit -> non-rate error
            return Resp(200, {"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": "block range too large"}})
        logs = [{"topics": [rec.T_TRANSFER, EXEC_TOPIC, "0x" + "0" * 24 + WALLETS[x % 5][2:]], "blockNumber": hex(x)}
                for x in range(a, b + 1) if x % 10_000 == 0]
        return Resp(200, {"jsonrpc": "2.0", "id": 1, "result": logs})
    if m == "eth_getCode":
        return Resp(200, {"jsonrpc": "2.0", "id": 1, "result": "0xef0100" + rec.S7702})
    return Resp(200, {"jsonrpc": "2.0", "id": 1, "result": hex(HEAD)})


rec.SESSION.post = fake_post
rec.UNIVERSE_WINDOW = 36000                               # 367,200 blocks: exercises range halving + 429s
start = HEAD - int(rec.UNIVERSE_WINDOW * 10.2)
t0 = time.time(); rec.warmup(HEAD); dt = time.time() - t0
expected = len([x for x in range(start, HEAD + 1) if x % 10_000 == 0])
buys = sum(len(v) for v in rec.BUYS.values())
rows = [json.loads(l) for f in os.listdir(os.path.join(rec.OUT, "rtt")) for l in open(os.path.join(rec.OUT, "rtt", f))]
print("warm_done", rec.WARM_DONE[0], "buys", buys, "expected", expected, "getLogs calls", CALLS["eth_getLogs"],
      "429 rows", sum("rpc_429" in r for r in rows), "gaps", sum("warmup_gap" in r for r in rows), f"{dt:.1f}s")
assert rec.WARM_DONE[0] and buys == expected

# rate-limited getLogs must not bisect
rec._LOW.on = False
CALLS.clear()
def always_429(url, json=None, timeout=None):
    with LOCK: CALLS[json["method"]] += 1
    return Resp(429, None)
rec.SESSION.post = always_429
rec.GATES["logs"].cool_until = 0; rec.GATES["logs"].backoff = 0.01
orig = rec._Gate.limited
def fast_limited(self):
    orig(self); self.cool_until = 0; self.backoff = 0.01; self.rate = 1000.0; self.tokens = 1000.0
rec._Gate.limited = fast_limited
try:
    rec.get_logs({"topics": []}, 0, 1_000_000)
except rec.RateLimited:
    pass
print("always-429 getLogs calls", CALLS["eth_getLogs"], "(no bisection => == rate_tries 40)")
assert CALLS["eth_getLogs"] == 40

# low priority blocks while the live loop lags
rec.MAIN_LAG[0] = 10_000
g = rec._Gate("t", 100.0, 1, 100)
th = threading.Thread(target=g.acquire, args=(True,), daemon=True); th.start(); th.join(1.5)
blocked = th.is_alive()
rec.MAIN_LAG[0] = 0; th.join(2.0)
print("low blocked while lagging", blocked, "released", not th.is_alive())
assert blocked and not th.is_alive()
# Amendment 1b: feed reconnect backs off exponentially and honours Retry-After on 403
import asyncio, aiohttp
waits = []
class _Blocked(Exception): pass
async def fake_sleep(w):
    waits.append(w)
    if len(waits) >= 4: raise _Blocked()
def fake_ws_connect(self, *a, **k):
    raise aiohttp.WSServerHandshakeError(__import__("types").SimpleNamespace(real_url="wss://mock"), (), status=403 if len(waits) == 0 else 502, message="x",
                                         headers={"Retry-After": "3576"} if len(waits) == 0 else {})
rec.asyncio.sleep = fake_sleep
aiohttp.ClientSession.ws_connect = fake_ws_connect
try:
    rec.feed_thread()
except _Blocked:
    pass
print("feed reconnect waits", waits)
assert waits == [3576.0, 4.0, 8.0, 16.0]
print("ALL OK")
