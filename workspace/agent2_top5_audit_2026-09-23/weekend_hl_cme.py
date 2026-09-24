"""Free falsification of Agent-3 candidate 4: HL weekend price discovery -> CME Sunday 18:00 ET open.
HL: xyz:SP500 / xyz:XYZ100 1h candles (API keeps last 5000 -> since ~2026-02-26).
CME: MES / MNQ 1m (Databento continuous to 2026-06-30; Sierra continuous 90d archive afterwards).
Per weekend: fri = last CME close <= Fri 17:00 ET; open = first CME 1m open >= Sun 18:00 ET;
hl_move = log(HL close of the hour ending Sun 18:00 ET / HL close of the hour ending Fri 17:00 ET).
Tests: (1) incorporation: gap vs hl_move; (2) does hl_move, gap, or residual (hl_move-gap) predict CME
open->+15m/+60m/+120m? n = number of weekends (each an independent event)."""
import json, time, urllib.request, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; NY = "America/New_York"
def post(b):
    r = urllib.request.Request("https://api.hyperliquid.xyz/info", data=json.dumps(b).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=30))
def cme(sym):
    a = pd.read_parquet(ROOT / "data" / f"{sym}_1m.parquet")[["open", "close", "symbol"]]
    b = pd.read_parquet(ROOT / "data" / "sierra" / f"{sym}_continuous_1m_latest_90d.parquet")
    b = b.rename(columns=str.lower)[["open", "close"]].assign(symbol="sierra_cont")
    b = b[b.index > a.index.max()]
    return pd.concat([a, b]).sort_index()
now = int(time.time() * 1000)
res = {}
for hl_coin, cme_sym in (("xyz:SP500", "MES"), ("xyz:XYZ100", "MNQ")):
    c = pd.DataFrame(post({"type": "candleSnapshot", "req": {"coin": hl_coin, "interval": "1h", "startTime": now - 5000 * 3600000, "endTime": now}}))
    hl = pd.Series(c.c.astype(float).values, index=pd.to_datetime(c["T"].astype("int64") + 1, unit="ms", utc=True))  # candle close time
    x = cme(cme_sym); x.index = pd.to_datetime(x.index, utc=True)
    rows = []
    for sun in pd.date_range(hl.index.min().tz_convert(NY).normalize() + pd.Timedelta(days=7), pd.Timestamp.now(tz=NY), freq="W-SUN"):
        so = (sun + pd.Timedelta(hours=18)).tz_convert("UTC"); fc = (sun - pd.Timedelta(days=2) + pd.Timedelta(hours=17)).tz_convert("UTC")
        pre = x[(x.index <= fc) & (x.index > fc - pd.Timedelta(hours=2))]; post_ = x[(x.index >= so) & (x.index < so + pd.Timedelta(hours=3))]
        if pre.empty or len(post_) < 121: continue
        if pre.symbol.iloc[-1] != post_.symbol.iloc[0]: rows.append({"sunday": str(sun.date()), "skip": "roll"}); continue
        h_fri = hl[(hl.index <= fc)].iloc[-1] if (hl.index <= fc).any() else np.nan
        h_sun = hl[(hl.index <= so)].iloc[-1] if (hl.index <= so).any() else np.nan
        o = post_.open.iloc[0]; f = pre.close.iloc[-1]
        at = lambda m: post_.close.iloc[m - 1]
        rows.append({"sunday": str(sun.date()), "hl_move_bp": 1e4 * np.log(h_sun / h_fri), "gap_bp": 1e4 * np.log(o / f),
                     "r15_bp": 1e4 * np.log(at(15) / o), "r60_bp": 1e4 * np.log(at(60) / o), "r120_bp": 1e4 * np.log(at(120) / o)})
    d = pd.DataFrame(rows); ok = d.dropna(subset=["hl_move_bp"]) if "hl_move_bp" in d else d
    ok = ok[ok.get("skip").isna()] if "skip" in ok else ok
    ok["resid_bp"] = ok.hl_move_bp - ok.gap_bp
    def cor(a, b): return round(float(np.corrcoef(ok[a], ok[b])[0, 1]), 3)
    slope = float(np.polyfit(ok.hl_move_bp, ok.gap_bp, 1)[0])
    r = {"weekends_used": int(len(ok)), "skipped_roll": int((d.get("skip") == "roll").sum()) if "skip" in d else 0,
         "first": ok.sunday.min(), "last": ok.sunday.max(),
         "incorporation_slope_gap_on_hlmove": round(slope, 3), "corr_gap_hlmove": cor("gap_bp", "hl_move_bp"),
         "median_abs_resid_bp": round(float(ok.resid_bp.abs().median()), 1), "median_abs_hlmove_bp": round(float(ok.hl_move_bp.abs().median()), 1)}
    for h in ("r15_bp", "r60_bp", "r120_bp"):
        r[f"corr_{h}_vs_hlmove"] = cor(h, "hl_move_bp"); r[f"corr_{h}_vs_gap"] = cor(h, "gap_bp"); r[f"corr_{h}_vs_resid"] = cor(h, "resid_bp")
        s = np.sign(ok.gap_bp) * ok[h]; r[f"gap_continuation_mean_{h}"] = round(float(s.mean()), 2); r[f"gap_continuation_t_{h}"] = round(float(s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))), 2)
    res[f"{hl_coin}->{cme_sym}"] = r; print(hl_coin, cme_sym, r)
    ok.to_csv(f"weekend_{cme_sym}.csv", index=False)
json.dump(res, open("weekend_hl_cme.json", "w"), indent=1)
