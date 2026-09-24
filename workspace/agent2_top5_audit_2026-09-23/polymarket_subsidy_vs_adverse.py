"""Agent-3 candidate 2 (Polymarket liquidity rewards): subsidy is GROSS revenue, not net edge.
(1) Sum live rewardsDailyRate over active markets; per-market gross subsidy yield = dailyRate / liquidityClob
    (UPPER bound: assumes every posted dollar is in-band and scores equally).
(2) Maker adverse selection from public trades (data-api): for each trade, maker PnL per $1 notional at +h =
    -(taker sign) * (p_{t+h} - p_t), p from the last trade at or before t+h (same token).
(3) Adverse cost per posted $ per day ~= turnover (volume24hr / liquidityClob) * mean maker markout.
Read-only public endpoints; no account, no orders."""
import json, time, urllib.request, numpy as np, pandas as pd
def get(u):
    for k in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40))
        except Exception: time.sleep(2 * (k + 1))
rows, off = [], 0
while True:
    page = get(f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={off}")
    if not page: break
    for x in page:
        rate = sum(float(r.get("rewardsDailyRate") or 0) for r in (x.get("clobRewards") or []))
        rows.append(dict(cid=x.get("conditionId"), q=(x.get("question") or "")[:70], rate=rate, liq=float(x.get("liquidityClob") or 0),
                         vol24=float(x.get("volume24hrClob") or 0), spread=x.get("spread"), fees=x.get("feesEnabled"),
                         maxspread=x.get("rewardsMaxSpread"), minsize=x.get("rewardsMinSize")))
    off += len(page)
    if len(page) < 100 or off > 40000: break
M = pd.DataFrame(rows); R = M[M.rate > 0].copy()
R["gross_yield_ann_%"] = 100 * R.rate / R.liq.clip(lower=1) * 365; R["turnover_per_day"] = R.vol24 / R.liq.clip(lower=1)
summary = {"active_markets": int(len(M)), "markets_with_rewards": int(len(R)), "total_daily_rewards_usd": round(R.rate.sum(), 0),
           "fees_enabled_share_rewarded": round(float((R.fees == True).mean()), 3),
           "median_gross_yield_ann_%": round(float(R["gross_yield_ann_%"].median()), 1)}
print(summary)
top = R.sort_values("rate", ascending=False).head(8)
res = []
for r in top.itertuples():
    tr = get(f"https://data-api.polymarket.com/trades?market={r.cid}&limit=1000&takerOnly=true") or []
    if len(tr) < 50: continue
    t = pd.DataFrame(tr); t["ts"] = t.timestamp.astype(int); t = t.sort_values("ts")
    out = {}
    for h, sec in (("5m", 300), ("1h", 3600)):
        mk = []
        for asset, g in t.groupby("asset"):
            ts, px = g.ts.to_numpy(), g.price.astype(float).to_numpy(); sgn = np.where(g.side.to_numpy() == "BUY", 1.0, -1.0)
            j = np.searchsorted(ts, ts + sec, side="right") - 1
            valid = ts[-1] >= ts + sec
            mk += list((-(sgn) * (px[j] - px) / np.maximum(px, 1e-9))[valid])
        out[h] = float(np.mean(mk)) if mk else np.nan
    span_h = (t.ts.max() - t.ts.min()) / 3600
    res.append(dict(q=r.q, daily_reward=r.rate, liq=round(r.liq), vol24=round(r.vol24), turnover=round(r.turnover_per_day, 3),
                    gross_subsidy_bps_per_day=round(1e4 * r.rate / max(r.liq, 1), 2),
                    maker_total_markout_1h_bps_bounce_incl=round(1e4 * out["1h"], 1), maker_total_markout_5m_bps_bounce_incl=round(1e4 * out["5m"], 1),
                    markout_bps_per_posted_dollar_day=round(1e4 * r.turnover_per_day * out["1h"], 2), trades=len(t), trade_span_h=round(span_h, 1)))
P = pd.DataFrame(res); pd.set_option("display.width", 250); print(P.to_string())
json.dump({"summary": summary, "top_markets": res}, open("polymarket_subsidy_vs_adverse.json", "w"), indent=1, default=str)
