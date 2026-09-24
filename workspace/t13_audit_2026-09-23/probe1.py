import json,urllib.request
def hl(body):
    r=urllib.request.Request("https://api.hyperliquid.xyz/info",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=30))
def bn(path):
    return json.load(urllib.request.urlopen("https://fapi.binance.com"+path,timeout=30))
m=hl({"type":"metaAndAssetCtxs"})
meta,ctx=m
u=meta["universe"]
json.dump(m,open("hl_metaAndAssetCtxs.json","w"))
print("HL universe n=",len(u)," keys seen:",sorted({k for a in u for k in a}))
dl=[a for a in u if a.get("isDelisted")]
iso=[a for a in u if a.get("onlyIsolated")]
print("delisted:",len(dl)," onlyIsolated:",len(iso))
print("delisted names sample:",[a["name"] for a in dl][:80])
print("marginTables:",json.dumps(meta.get("marginTables"))[:800])
names=["USELESS","XMR","PONS","PURR","GRASS","VVV","BTC","ETH"]
for i,a in enumerate(u):
    if a["name"] in names:
        print(a, {k:ctx[i].get(k) for k in ["funding","openInterest","markPx","oraclePx","dayNtlVlm","premium"]})
ei=bn("/fapi/v1/exchangeInfo"); json.dump(ei,open("bn_exchangeInfo.json","w"))
fi=bn("/fapi/v1/fundingInfo"); json.dump(fi,open("bn_fundingInfo.json","w"))
syms={s["symbol"]:s for s in ei["symbols"]}
fim={f["symbol"]:f for f in fi}
import datetime
from collections import Counter
print("BN fundingInfo entries:",len(fi)," interval counts:",Counter(f["fundingIntervalHours"] for f in fi))
for n in names:
    for cand in [n+"USDT","1000"+n+"USDT",n+"USDC"]:
        if cand in syms:
            s=syms[cand]; print(cand,s["status"],s["contractType"],datetime.datetime.utcfromtimestamp(s["onboardDate"]/1000).date(),fim.get(cand))
