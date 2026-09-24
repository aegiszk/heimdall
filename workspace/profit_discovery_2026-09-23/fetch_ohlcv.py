"""Read-only: GeckoTerminal USD minute OHLCV around each K>=3 cluster event. Cached per event."""
import os, json, time, requests, pandas as pd
SP = os.path.dirname(os.path.abspath(__file__))
e = pd.read_parquet(os.path.join(SP, "cluster_events.parquet"))
e = e[e.K == 3].sample(n=200, random_state=20260923).sort_values("ts").reset_index(drop=True)
os.makedirs(os.path.join(SP, "ohlcv"), exist_ok=True)
H = {"accept": "application/json"}
for i, r in e.iterrows():
    path = os.path.join(SP, "ohlcv", f"{r.pool}_{r.ts}.json")
    if os.path.exists(path): continue
    url = f"https://api.geckoterminal.com/api/v2/networks/robinhood/pools/{r.pool}/ohlcv/minute"
    for k in range(6):
        try:
            resp = requests.get(url, params={"aggregate": 1, "limit": 1000, "currency": "usd", "token": "base",
                                             "before_timestamp": int(r.ts) + 7 * 3600}, headers=H, timeout=30)
            if resp.status_code == 429: time.sleep(15); continue
            j = resp.json()
            body = {"status": resp.status_code,
                    "ohlcv": j.get("data", {}).get("attributes", {}).get("ohlcv_list", []) if resp.ok else [],
                    "meta": j.get("meta") if resp.ok else None}
            json.dump(body, open(path, "w")); break
        except Exception as ex:
            time.sleep(10)
    time.sleep(2.2)
    if i % 50 == 0: print(i, len(e), flush=True)
print("done")
