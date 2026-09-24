"""Free HistData.com 1-minute BID bars (ASCII M1) for FX majors + XAUUSD.

Flow verified live 2026-09-24: GET the year page, read hidden form (tk,date,datemonth,platform,timeframe,fxpair),
POST to https://www.histdata.com/get.php -> zip containing DAT_ASCII_{PAIR}_M1_{YYYY}.csv
Row format: 'YYYYMMDD HHMMSS;open;high;low;close;volume'. HistData documents the timestamps as EST WITHOUT
daylight saving (fixed UTC-05:00); converted here to UTC. Prices are BID only -> spread is modelled separately.
Past years are yearly files; the current year is served per month (datemonth=YYYYMM).
"""
from __future__ import annotations

import http.cookiejar
import io
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "fx_histdata"


def _get(pair: str, period: str) -> bytes:
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    if len(period) == 4:
        url = f"https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair.lower()}/{period}"
    else:
        url = (f"https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/"
               f"{pair.lower()}/{period[:4]}/{int(period[4:])}")
    html = op.open(url, timeout=60).read().decode("utf-8", "ignore")
    form = dict(re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]+" value="([^"]*)"', html))
    req = urllib.request.Request("https://www.histdata.com/get.php", data=urllib.parse.urlencode(form).encode(),
                                 headers={"Referer": url, "User-Agent": "Mozilla/5.0"})
    return op.open(req, timeout=300).read()


def pull(pair: str, periods: list[str]) -> pd.DataFrame:
    frames = []
    for p in periods:
        raw_path = OUT / "raw" / f"{pair}_{p}.zip"
        if not raw_path.exists():
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            b = _get(pair, p)
            if b[:2] != b"PK":
                print(pair, p, "NOT A ZIP", len(b)); continue
            raw_path.write_bytes(b)
        z = zipfile.ZipFile(raw_path)
        name = [n for n in z.namelist() if n.endswith(".csv")][0]
        d = pd.read_csv(io.BytesIO(z.read(name)), sep=";", header=None,
                        names=["ts", "open", "high", "low", "close", "volume"])
        d.index = (pd.to_datetime(d.pop("ts"), format="%Y%m%d %H%M%S") + pd.Timedelta(hours=5)).dt.tz_localize("UTC")
        frames.append(d.drop(columns="volume"))
        print(pair, p, len(d), d.index.min(), d.index.max(), flush=True)
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="first")]
    df.to_parquet(OUT / f"{pair}_1m_bid.parquet")
    return df


if __name__ == "__main__":
    pairs = sys.argv[1:] or ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "NZDUSD", "XAUUSD"]
    periods = ["2022", "2023", "2024", "2025"] + [f"2026{m:02d}" for m in range(1, 9)]
    for pr in pairs:
        pull(pr, periods)
