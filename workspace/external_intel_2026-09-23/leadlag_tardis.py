"""Binance-futures vs Hyperliquid BTC lead-lag + public-feed delivery latency.
Free Tardis.dev first-of-month sample (no API key). One day = descriptive only.
Usage: python leadlag_tardis.py 2026/09/01
"""
import sys, urllib.request, numpy as np, pandas as pd
day = sys.argv[1] if len(sys.argv) > 1 else "2026/09/01"
SRC = {"hl": f"https://datasets.tardis.dev/v1/hyperliquid/trades/{day}/BTC.csv.gz",
       "bn": f"https://datasets.tardis.dev/v1/binance-futures/trades/{day}/BTCUSDT.csv.gz"}
D = {}
for k, u in SRC.items():
    fn = f"{k}_{day.replace('/', '')}.csv.gz"
    urllib.request.urlretrieve(u, fn)
    d = pd.read_csv(fn, usecols=["timestamp", "local_timestamp", "price"])
    lat = (d.local_timestamp - d.timestamp) / 1000
    print(k, "rows", len(d), "delivery ms p1/p10/p50/p90/p99", np.round(np.percentile(lat, [1, 10, 50, 90, 99]), 1))
    D[k] = d
STEP = 100_000  # 100 ms in microseconds
H = D["hl"].groupby(D["hl"].timestamp // STEP).price.last()
B = D["bn"].groupby(D["bn"].timestamp // STEP).price.last()
idx = np.arange(max(H.index.min(), B.index.min()), min(H.index.max(), B.index.max()) + 1)
M = pd.DataFrame({"h": H.reindex(idx).ffill(), "b": B.reindex(idx).ffill()}).dropna()
lh, lb = np.diff(np.log(M.h.values)), np.diff(np.log(M.b.values))
res = []
for k in range(-30, 31):  # k>0: Binance return at t vs HL return at t+k
    c = np.corrcoef(lb[:len(lb) - k], lh[k:])[0, 1] if k >= 0 else np.corrcoef(lb[-k:], lh[:len(lh) + k])[0, 1]
    res.append((k * 100, round(float(c), 3)))
print("n", len(lh), "argmax lag_ms/corr", max(res, key=lambda r: r[1]))
print([r for r in res if r[0] in (-500, -200, 0, 200, 300, 500, 1000)])
