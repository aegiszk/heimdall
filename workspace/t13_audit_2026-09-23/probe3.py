import json,urllib.request,datetime,time
def hl(body):
    r=urllib.request.Request("https://api.hyperliquid.xyz/info",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=30))
D=lambda ms: datetime.datetime.fromtimestamp(ms/1000,datetime.UTC).strftime("%Y-%m-%d %H:%M")
now=int(time.time()*1000)
for n in ["JELLY","MATIC","FTM","YZY"]:
    last=hl({"type":"fundingHistory","coin":n,"startTime":now-86400000*2})
    print(n,[(D(r["time"]),r["fundingRate"],r["premium"]) for r in last[-3:]])
    c=hl({"type":"candleSnapshot","req":{"coin":n,"interval":"1d","startTime":now-86400000*5,"endTime":now}})
    print("  candles last5d:",len(c), c[-1] if c else None)
# does delisted-only-api? try l2Book
for n in ["JELLY","MATIC"]:
    try: print(n,"l2Book",str(hl({"type":"l2Book","coin":n}))[:200])
    except Exception as e: print(n,"l2 ERR",e)
