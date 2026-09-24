# METADATA ONLY: first fundingHistory timestamp (listing proxy) and last daily candle (delisting proxy). No rate levels read.
import json,urllib.request,datetime,time
def hl(body):
    for k in range(4):
        try:
            r=urllib.request.Request("https://api.hyperliquid.xyz/info",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
            return json.load(urllib.request.urlopen(r,timeout=30))
        except Exception as e: time.sleep(2)
D=lambda ms: datetime.datetime.fromtimestamp(ms/1000,datetime.UTC).strftime("%Y-%m-%d")
meta,ctx=json.load(open("hl_metaAndAssetCtxs.json")); u=meta["universe"]
now=int(time.time()*1000)
rows=[]
for a in u:
    n=a["name"]; f=hl({"type":"fundingHistory","coin":n,"startTime":0}) or []
    first=D(f[0]["time"]) if f else None
    last=None
    if a.get("isDelisted"):
        c=hl({"type":"candleSnapshot","req":{"coin":n,"interval":"1d","startTime":now-86400000*1800,"endTime":now}}) or []
        last=D(c[-1]["t"]) if c else None
    rows.append(dict(coin=n,delisted=bool(a.get("isDelisted")),first_funding=first,last_candle=last,maxLev=a["maxLeverage"],onlyIso=a.get("onlyIsolated",False)))
    time.sleep(0.15)
json.dump(rows,open("hl_universe_dates.json","w"),indent=0)
def alive(r,d): return r["first_funding"] and r["first_funding"]<=d and (not r["delisted"] or (r["last_candle"] and r["last_candle"]>=d))
for d in ["2024-10-01","2025-04-01","2025-10-01","2026-04-01","2026-08-31"]:
    print(d,"listed&alive:",sum(alive(r,d) for r in rows))
dl=[r for r in rows if r["delisted"]]
print("delisted total",len(dl),"; delisted with last_candle in 2024-10..2026-08:",sum(1 for r in dl if r["last_candle"] and "2024-10-01"<=r["last_candle"]<="2026-08-31"))
print("delisted no candles:",[r["coin"] for r in dl if not r["last_candle"]])
print("live listed after 2024-10-01:",sum(1 for r in rows if not r["delisted"] and r["first_funding"] and r["first_funding"]>"2024-10-01"),"of",sum(1 for r in rows if not r["delisted"]))
print("onlyIsolated:",[(r["coin"],r["delisted"]) for r in rows if r["onlyIso"]])
print("maxLev dist live:",sorted(__import__("collections").Counter(r["maxLev"] for r in rows if not r["delisted"]).items()))
