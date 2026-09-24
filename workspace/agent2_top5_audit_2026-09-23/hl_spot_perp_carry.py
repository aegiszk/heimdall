"""Free falsification of Agent-3 candidate 3 (HL intra-venue spot-perp carry): long HL spot, short HL perp.
Hourly: funding received by the short (fundingHistory), basis = log(perp) - log(spot) from 1h candle closes.
Net = funding - round-trip fees (spot taker 0.070% + perp taker 0.045% per side, base tier)
      - basis change (entry->exit) ; compared with HL USDC lending supply rate (opportunity cost).
Periods: every calendar month separately (enter first hour, exit last hour) + full window buy&hold."""
import json, time, urllib.request, numpy as np, pandas as pd
def post(b):
    for k in range(5):
        try:
            r = urllib.request.Request("https://api.hyperliquid.xyz/info", data=json.dumps(b).encode(), headers={"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(r, timeout=30))
        except Exception: time.sleep(2 * (k + 1))
PAIRS = {"HYPE": "@107", "BTC": "@142", "ETH": "@151", "SOL": "@156"}
now = int(time.time() * 1000); start = now - 5000 * 3600 * 1000
FEE_RT = 2 * (0.00070 + 0.00045)
out = {}
for coin, spot in PAIRS.items():
    cp = pd.DataFrame(post({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1h", "startTime": start, "endTime": now}}))
    cs = pd.DataFrame(post({"type": "candleSnapshot", "req": {"coin": spot, "interval": "1h", "startTime": start, "endTime": now}}))
    f, t = [], start
    while True:
        d = post({"type": "fundingHistory", "coin": coin, "startTime": t})
        if not d: break
        f += d; nt = d[-1]["time"] + 1
        if len(d) < 500 or nt <= t: break
        t = nt
    F = pd.Series({x["time"] // 3600000: float(x["fundingRate"]) for x in f})
    P = pd.Series(cp.c.astype(float).values, index=cp.t // 3600000); S = pd.Series(cs.c.astype(float).values, index=cs.t // 3600000)
    df = pd.DataFrame({"perp": P, "spot": S, "fund": F}).dropna()
    df["basis"] = np.log(df.perp) - np.log(df.spot)
    df["month"] = pd.to_datetime(df.index * 3600, unit="s").to_period("M").astype(str)
    months = {}
    for mth, g in df.groupby("month"):
        if len(g) < 24 * 20: continue
        fund = g.fund.sum(); dbasis = g.basis.iloc[-1] - g.basis.iloc[0]
        net = fund - FEE_RT - dbasis   # short perp gains when basis falls
        months[mth] = {"hours": len(g), "funding_%": round(100 * fund, 3), "basis_chg_%": round(100 * dbasis, 3), "net_%": round(100 * net, 3)}
    yrs = len(df) / 8760
    full_net = df.fund.sum() - FEE_RT - (df.basis.iloc[-1] - df.basis.iloc[0])
    out[coin] = {"spot_pair": spot, "hours": len(df), "from": str(pd.to_datetime(df.index.min() * 3600, unit="s")),
                 "to": str(pd.to_datetime(df.index.max() * 3600, unit="s")),
                 "funding_ann_%": round(100 * df.fund.sum() / yrs, 2), "hold_net_ann_%": round(100 * full_net / yrs, 2),
                 "basis_mean_bps": round(1e4 * df.basis.mean(), 1), "basis_p1_p99_bps": [round(1e4 * df.basis.quantile(.01), 1), round(1e4 * df.basis.quantile(.99), 1)],
                 "share_hours_funding_negative": round(float((df.fund < 0).mean()), 3),
                 "worst_month_net_%": min((v["net_%"] for v in months.values()), default=None), "months": months}
    print(coin, {k: v for k, v in out[coin].items() if k != "months"})
json.dump(out, open("hl_spot_perp_carry.json", "w"), indent=1)
