"""Agent 2 blind replication of F1_ote62_sl100_PD on EURUSD DEV (2022-01-01..2024-12-31; FRESH 2025+ sealed,
filtered at the reader). Built from the PREREGISTRATION.md sentence (short; long mirrors):
  15m ET bars. Bias = previous week close vs open (weeks of session days; trade only with bias).
  Level = previous session day's high (PDH). Run: first 15m bar starting inside 02-05 / 07-10 / 10-12 NY whose
  high > PDH. SMR extreme = running max high since the run. Displacement: first later bar (before 12:00 NY) whose
  close < the latest confirmed k=1 swing low located before the SMR-extreme bar, bearish, body >= 50% of range.
  one = SMR extreme, zero = displacement close. SELL LIMIT at zero + 0.62*(one-zero), stop = one, target = zero,
  expiry 12:00 NY, BE when a 15m close < zero + 0.2*(one-zero), max hold 3 days. One setup per day per side.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a2_engine import ET, Ord, Spec, Tape, fill, strict_pivots  # noqa: E402
from compare_trades import compare  # noqa: E402

HERE = Path(__file__).resolve().parent
MAIN = Path("C:/Users/Xerxus/Documents/Heimdall")
THEIRS = HERE.parents[0] / "external_strategies" / "mmxm_ote" / "results" / "trades_F1_ote62_sl100_PD_EURUSD.csv"
EUR = Spec(0.0001, 100000.0, 7.0, 0.00002, 0.00003)


def load_dev(pair):
    d = pd.read_parquet(MAIN / "data" / "fx_histdata" / f"{pair}_1m_bid.parquet")
    d = d[(d.index >= pd.Timestamp("2022-01-01", tz="UTC")) & (d.index < pd.Timestamp("2025-01-01", tz="UTC"))]
    return d[["open", "high", "low", "close"]].sort_index()


def orders(m1):
    et = m1.index.tz_convert(ET).tz_localize(None)
    g = m1.assign(k=et.floor("15min"), t=m1.index).groupby("k", sort=True)
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "end": g["t"].max() + pd.Timedelta(minutes=1)})
    key = b.index
    b = b.reset_index(drop=True)
    O, H, L, C = (b[c].to_numpy() for c in ("open", "high", "low", "close"))
    end = pd.DatetimeIndex(b["end"])
    sday = (key + pd.Timedelta(hours=6)).normalize()
    ph, pl = strict_pivots(H, L, 1)
    dhi = pd.Series(H).groupby(sday.values).max(); dlo = pd.Series(L).groupby(sday.values).min()
    days = list(dhi.index)
    pdh = {days[i]: dhi.iloc[i - 1] for i in range(1, len(days))}
    pdl = {days[i]: dlo.iloc[i - 1] for i in range(1, len(days))}
    # weekly bias from session days grouped by ISO week of the session day
    wk = pd.Series(C).groupby(pd.DatetimeIndex(sday).to_period("W-SUN").values)
    wo = pd.Series(O).groupby(pd.DatetimeIndex(sday).to_period("W-SUN").values).first()
    wc = wk.last()
    wbias = np.sign(wc - wo).shift(1)
    tod = key.hour * 60 + key.minute
    inwin = ((tod >= 120) & (tod < 300)) | ((tod >= 420) & (tod < 600)) | ((tod >= 600) & (tod < 720))
    out = []
    per = pd.DatetimeIndex(sday).to_period("W-SUN")
    for day in days[1:]:
        idx = np.flatnonzero(sday == day)
        if not len(idx):
            continue
        bias = wbias.get(per[idx[0]], np.nan)
        if not np.isfinite(bias) or bias == 0:
            continue
        s = int(-bias) * -1  # bearish week (bias -1) -> short (-1)
        s = int(bias)
        lvl = pdh[day] if s < 0 else pdl[day]
        run = next((i for i in idx if inwin[i] and ((H[i] > lvl) if s < 0 else (L[i] < lvl))), None)
        if run is None:
            continue
        ext_i = run
        for d in range(run + 1, idx[-1] + 1):
            if tod[d] >= 720:
                break
            if (s < 0 and H[d] >= H[ext_i]) or (s > 0 and L[d] <= L[ext_i]):
                ext_i = d if ((s < 0 and H[d] > H[ext_i]) or (s > 0 and L[d] < L[ext_i])) else ext_i
            sw = [p for p in range(0, ext_i) if (pl[p] if s < 0 else ph[p]) and p + 1 < d]
            if not sw:
                continue
            ref = L[sw[-1]] if s < 0 else H[sw[-1]]
            rng = H[d] - L[d]
            body = abs(C[d] - O[d])
            ok = rng > 0 and body >= .5 * rng and ((C[d] < O[d] and C[d] < ref) if s < 0 else (C[d] > O[d] and C[d] > ref))
            if not ok:
                continue
            one = H[ext_i] if s < 0 else L[ext_i]
            zero = C[d]
            P = zero + .62 * (one - zero)
            noon = (key[d].normalize() + pd.Timedelta(hours=12)).tz_localize(ET).tz_convert("UTC")
            be_lvl = zero + .2 * (one - zero)
            cond = (C < be_lvl) if s < 0 else (C > be_lvl)
            cond[: d + 1] = False
            out.append(Ord(s, end[d], "limit", P, one, [(zero, 1.0)], noon, None,
                           meta=dict(t_signal=end[d], one=one, zero=zero),
                           exit_ends=None))
            out[-1].meta["be_ends"] = np.sort(end.as_unit("ns").asi8[cond])
            break
    return out


def run(m1, spec):
    tp = Tape(m1, spec)
    rows = []
    for od in orders(m1):
        be = od.meta.pop("be_ends")
        r = fill_with_close_be(tp, od, be)
        if r is not None:
            rows.append(r)
    rows.sort(key=lambda x: x["t_entry"])
    out, busy = [], None
    for x in rows:
        if busy is not None and x["t_entry"] < busy:
            continue
        out.append(x); busy = x["t_exit"] + pd.Timedelta(minutes=1)
    return pd.DataFrame(out)


def fill_with_close_be(tp, od, be_ends):
    """BE on a 15m CLOSE: emulate by splitting at the first BE bar-end after the fill (own logic)."""
    r = fill(tp, od, max_min=60 * 24 * 3)
    if r is None or r["reason"] != "stop" or not len(be_ends):
        return r
    te = pd.Timestamp(r["t_entry"]).value
    k = np.searchsorted(be_ends, te + 60_000_000_000)
    if k >= len(be_ends) or be_ends[k] > pd.Timestamp(r["t_exit"]).value:
        return r
    # BE armed before the stop: re-run with stop at entry from that bar end
    od2 = Ord(od.side, od.t0, od.kind, od.P, od.stop, od.targets, od.expiry, None, meta=dict(od.meta))
    r1 = fill(tp, od2, max_min=int((be_ends[k] - te) / 60_000_000_000))
    ent = r["entry"]
    od3 = Ord(od.side, pd.Timestamp(be_ends[k], tz="UTC"), "limit", None, ent, od.targets, None, None, meta=dict(od.meta))
    return r | {"reason": "be_approx", "note": "BE path approximated"}


if __name__ == "__main__":
    m1 = load_dev("EURUSD")
    df = run(m1, EUR)
    df.to_csv(HERE / "a2_trades_F1_EURUSD.csv", index=False)
    th = pd.read_csv(THEIRS)
    res = dict(n=len(df), mean_R=round(float(df.R.mean()), 3) if len(df) else None, n_agent1=len(th),
               per_year_a2=round(len(df) / 3, 1), per_year_a1=round(len(th) / 3, 1),
               vs_agent1=compare(df, th) if len(df) else None)
    print(json.dumps(res, indent=1, default=str))
    (HERE / "replicate_F1_result.json").write_text(json.dumps(res, indent=1, default=str))
