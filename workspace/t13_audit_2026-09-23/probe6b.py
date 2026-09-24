import json,collections
rows=json.load(open("hl_universe_dates.json"))
def alive(r,d): return bool(r["first_funding"] and r["first_funding"]<=d and (not r["delisted"] or (r["last_candle"] and r["last_candle"]>=d)))
for d in ["2024-10-01","2025-04-01","2025-10-01","2026-04-01","2026-08-31"]:
    print(d,"listed&alive:",sum(alive(r,d) for r in rows))
dl=[r for r in rows if r["delisted"]]
print("delisted total",len(dl),"; delisted with last_candle in 2024-10..2026-08:",sum(1 for r in dl if r["last_candle"] and "2024-10-01"<=r["last_candle"]<="2026-08-31"))
print("delisted no candles:",[r["coin"] for r in dl if not r["last_candle"]])
print("no funding rows:",[r["coin"] for r in rows if not r["first_funding"]])
print("live listed after 2024-10-01:",sum(1 for r in rows if not r["delisted"] and r["first_funding"] and r["first_funding"]>"2024-10-01"),"of",sum(1 for r in rows if not r["delisted"]))
print("onlyIsolated:",[(r["coin"],r["delisted"]) for r in rows if r["onlyIso"]])
print("maxLev dist live:",sorted(collections.Counter(r["maxLev"] for r in rows if not r["delisted"]).items()))
print("earliest first_funding:",min(r["first_funding"] for r in rows if r["first_funding"]))
print("sample delisted:",[(r["coin"],r["first_funding"],r["last_candle"]) for r in dl if r["last_candle"] and r["last_candle"]>="2024-10-01"])
