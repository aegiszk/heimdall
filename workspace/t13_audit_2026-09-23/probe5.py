# INTERVAL METADATA ONLY: funding rate values are discarded, only timestamp gaps are kept.
import json,urllib.request,datetime
from collections import Counter
def get(url): return json.load(urllib.request.urlopen(url,timeout=30))
D=lambda ms: datetime.datetime.fromtimestamp(ms/1000,datetime.UTC).strftime("%Y-%m-%d %H:%M")
out={}
ei=json.load(open("bn_exchangeInfo.json")); ob={x["symbol"]:x["onboardDate"] for x in ei["symbols"]}
for s in ["GRASSUSDT","VVVUSDT","USELESSUSDT","XMRUSDT","FARTCOINUSDT"]:
    ts=[];start=0
    while True:
        r=get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={s}&startTime={start or ob[s]}&limit=1000")
        if not r: break
        ts+= [x["fundingTime"] for x in r]; 
        if len(r)<1000: break
        start=r[-1]["fundingTime"]+1
    ts=sorted(set(ts)); gaps=[round((b-a)/3.6e6) for a,b in zip(ts,ts[1:])]
    changes=[]; prev=None
    for t,g in zip(ts[1:],gaps):
        if g!=prev: changes.append((D(t),g)); prev=g
    out[s]={"n":len(ts),"first":D(ts[0]),"gap_counts":dict(Counter(gaps)),"regime_changes":changes[:40]}
    print(s,out[s]["n"],out[s]["first"],out[s]["gap_counts"],"\n  changes:",changes[:25])
json.dump(out,open("bn_interval_history.json","w"),indent=1)
