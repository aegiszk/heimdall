import json,urllib.request,datetime,time
def hl(body):
    r=urllib.request.Request("https://api.hyperliquid.xyz/info",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=30))
def get(url): return json.load(urllib.request.urlopen(url,timeout=30))
def depth(bids,asks):
    bb,ba=bids[0][0],asks[0][0]; mid=(bb+ba)/2; out={"spread_bps":round((ba-bb)/mid*1e4,1)}
    for w in (10,50,100):
        out[f"bid{w}"]=round(sum(p*q for p,q in bids if p>=mid*(1-w/1e4)))
        out[f"ask{w}"]=round(sum(p*q for p,q in asks if p<=mid*(1+w/1e4)))
    out["bid_last_bps"]=round((mid-bids[-1][0])/mid*1e4); out["ask_last_bps"]=round((asks[-1][0]-mid)/mid*1e4)
    return out
res={}
for n,b in [("USELESS","USELESSUSDT"),("XMR","XMRUSDT"),("PONS","PONSUSDT"),("PURR",None),("GRASS","GRASSUSDT"),("VVV","VVVUSDT"),("BTC","BTCUSDT")]:
    books=[]
    for sig in (None,4,3):
        body={"type":"l2Book","coin":n}; 
        if sig: body["nSigFigs"]=sig
        L=hl(body)["levels"]; books.append((sig,[(float(x["px"]),float(x["sz"])) for x in L[0]],[(float(x["px"]),float(x["sz"])) for x in L[1]]))
    # use finest for 10bps, coarser for wider if full book doesn't reach
    hd={f"sig{s}":depth(bi,as_) for s,bi,as_ in books}
    bd=None
    if b:
        d=get(f"https://fapi.binance.com/fapi/v1/depth?symbol={b}&limit=1000")
        bd=depth([(float(p),float(q)) for p,q in d["bids"]],[(float(p),float(q)) for p,q in d["asks"]])
    res[n]={"hl":hd,"bn":bd}
    print(n,"HL",hd,"\n   BN",bd)
json.dump({"ts_utc":datetime.datetime.now(datetime.UTC).isoformat(),"depth":res},open("depth_snapshot.json","w"),indent=1)
# delist dates via last daily candle (metadata only)
now=int(time.time()*1000)
for n in ["JELLY","YZY","MATIC"]:
    c=hl({"type":"candleSnapshot","req":{"coin":n,"interval":"1d","startTime":now-86400000*1500,"endTime":now}})
    print(n,"candles",len(c),"first",datetime.datetime.fromtimestamp(c[0]["t"]/1000,datetime.UTC).date() if c else None,"last",datetime.datetime.fromtimestamp(c[-1]["t"]/1000,datetime.UTC).date() if c else None)
