import json,urllib.request,datetime,time
def hl(body):
    r=urllib.request.Request("https://api.hyperliquid.xyz/info",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=30))
def get(url): return json.load(urllib.request.urlopen(url,timeout=30))
D=lambda ms: datetime.datetime.fromtimestamp(ms/1000,datetime.UTC).strftime("%Y-%m-%d")
meta,ctx=json.load(open("hl_metaAndAssetCtxs.json"))
u=meta["universe"]
ei=json.load(open("bn_exchangeInfo.json")); syms={s["symbol"]:s for s in ei["symbols"]}
fim={f["symbol"]:f for f in json.load(open("bn_fundingInfo.json"))}
sp=get("https://api.binance.com/api/v3/exchangeInfo?permissions=SPOT"); json.dump([s["symbol"] for s in sp["symbols"] if s["status"]=="TRADING"],open("bn_spot_trading.json","w"))
spot=set(s["symbol"] for s in sp["symbols"] if s["status"]=="TRADING")
hs=hl({"type":"spotMeta"}); json.dump(hs,open("hl_spotMeta.json","w"))
tok={t["index"]:t["name"] for t in hs["tokens"]}
hlspot=set(tok[p["tokens"][0]] for p in hs["universe"] if tok[p["tokens"][1]] in("USDC","USDH","USDT0","USDE"))
live=[(i,a) for i,a in enumerate(u) if not a.get("isDelisted")]
top=sorted(live,key=lambda t:-float(ctx[t[0]]["openInterest"])*float(ctx[t[0]]["markPx"] or 0))[:60]
rows=[];nohedge=[]
def bnsym(n):
    for c in [n+"USDT","1000"+n+"USDT",n[1:]+"USDT" if n.startswith("k") else None, "1000000"+n+"USDT"]:
        if c and c in syms and syms[c]["contractType"]=="PERPETUAL": return c
for i,a in top:
    n=a["name"]; b=bnsym(n)
    ob=D(syms[b]["onboardDate"]) if b else None
    iv=fim.get(b,{}).get("fundingIntervalHours",8 if b else None) if b else None
    rows.append(dict(coin=n,maxLev=a["maxLeverage"],onlyIso=a.get("onlyIsolated",False),marginMode=a.get("marginMode"),bn=b,bn_status=syms[b]["status"] if b else None,bn_onboard=ob,bn_int_h=iv,bn_spot=(n+"USDT") in spot,hl_spot=n in hlspot))
    if not b: nohedge.append(n)
json.dump(rows,open("top60_hedge_map.json","w"),indent=0)
for r in rows: print(r)
print("NO BN PERP:",nohedge)
print("BN perp onboard after 2024-10-01:",[r["coin"] for r in rows if r["bn_onboard"] and r["bn_onboard"]>"2024-10-01"])
print("BN perp onboard after 2025-10-01:",[r["coin"] for r in rows if r["bn_onboard"] and r["bn_onboard"]>"2025-10-01"])
# HL first-funding timestamp (listing proxy) for top-funding names + delisted retrieval test
for n in ["USELESS","XMR","PONS","PURR","GRASS","VVV","JELLY","MATIC","YZY","FTM"]:
    try:
        f=hl({"type":"fundingHistory","coin":n,"startTime":0})
        last=hl({"type":"fundingHistory","coin":n,"startTime":int(time.time()*1000)-86400000*3})
        print(n,"first_row",D(f[0]["time"]) if f else None,"page_rows",len(f),"rows_last3d",len(last), "last_row",D(last[-1]["time"]) if last else None)
    except Exception as e: print(n,"ERR",e)
