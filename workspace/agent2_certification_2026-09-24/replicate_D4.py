"""Agent 2 independent replication + fragility audit of D4_G_long_1h_pivot (Little Rizzy uptrend long).

Rule (PREREGISTRATION.md D4 row + SOURCE_MATRIX "uptrend inverse"; chain definition taken from the prereg'd
strategy docstring because the prereg table does not define it — disclosed as a fidelity finding):
  k=2 pivot LOWS on 1h ET bars (24h data). Consecutive pivot lows P1 < P2 (higher low), P2 - P1 >= 2 bars.
  H = highest high strictly between; TL through (P1 low, P2 low) extrapolated by bar index; D = high(H) - TL(H) > 0.
  Chain: a pattern whose P1 is the previous pattern's P2 increments count, else count = 1; trade count <= 2.
  Entry: market at close of confirmation bar P2+2 if TL < close < high(H). Stop: low(P2) - 1 tick.
  Loss exit: first 1h close below TL after entry. Target: high(H) + D. No flatten (12-day max hold).
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a2_engine import ES, ET, MNQ, XAU, Ord, Tape, bars, cluster_ci, load_cme, sequence, strict_pivots  # noqa: E402

HERE = Path(__file__).resolve().parent
MAIN = Path("C:/Users/Xerxus/Documents/Heimdall")          # bulk FX data lives only in the main tree
A1D = HERE.parents[0] / "external_strategies" / "little_rizzy" / "results"


def load_xau_dev() -> pd.DataFrame:
    """Read ONLY 2022-01-01 <= t < 2025-01-01 (FX FRESH 2025+ is sealed; filtered at the reader)."""
    f = MAIN / "data" / "fx_histdata" / "XAUUSD_1m_bid.parquet"
    t = pq.read_table(f)
    d = t.to_pandas()
    idx = pd.DatetimeIndex(d.index)
    keep = (idx >= pd.Timestamp("2022-01-01", tz="UTC")) & (idx < pd.Timestamp("2025-01-01", tz="UTC"))
    d = d.loc[keep, ["open", "high", "low", "close"]].sort_index()
    assert d.index.max() < pd.Timestamp("2025-01-01", tz="UTC")
    return d


def orders_d4(m1: pd.DataFrame, tick: float, delay_bars: int = 0) -> list[Ord]:
    b = bars(m1, 60)
    H, L, C = (b[c].to_numpy() for c in ("high", "low", "close"))
    end = pd.DatetimeIndex(b["end"])
    ends = end.as_unit("ns").asi8
    _, pl = strict_pivots(H, L, 2)
    piv = np.flatnonzero(pl)
    out, prev_p2, count = [], None, 0
    for p1, p2 in zip(piv[:-1], piv[1:]):
        p1, p2 = int(p1), int(p2)
        if not (L[p2] > L[p1]) or p2 - p1 < 2:
            prev_p2, count = None, 0
            continue
        count = count + 1 if prev_p2 == p1 else 1
        prev_p2 = p2
        seg = np.arange(p1 + 1, p2)
        hi_i = int(seg[np.argmax(H[seg])])
        slope = (L[p2] - L[p1]) / (p2 - p1)
        tl = L[p1] + slope * (np.arange(len(C)) - p1)
        D = H[hi_i] - tl[hi_i]
        if D <= 0 or count > 2:
            continue
        jc = p2 + 2
        if jc >= len(C):
            break
        if not (tl[jc] < C[jc] < H[hi_i]):
            continue
        je = min(jc + delay_bars, len(C) - 1)
        cond = C < tl
        cond[: je + 1] = False
        out.append(Ord(1, end[je], "close_at", None, L[p2] - tick, [(H[hi_i] + D, 1.0)], None, None,
                       meta=dict(t_signal=end[je], p1=L[p1], p2=L[p2], H=H[hi_i], D=D, count=count),
                       exit_ends=np.sort(ends[cond])))
    return out


def regime(m1: pd.DataFrame) -> pd.Series:
    et = m1.index.tz_convert(ET).tz_localize(None)
    day = (et + pd.Timedelta(hours=6)).normalize()
    cl = m1["close"].groupby(day).last()
    bull = (cl > cl.rolling(50).mean()).shift(1)
    return bull


def stats(df: pd.DataFrame, m1: pd.DataFrame | None = None) -> dict:
    r = df["R"].sort_values(ascending=False)
    lo, hi = cluster_ci(df)
    out = dict(n=len(df), mean_R=round(float(df.R.mean()), 4), median_R=round(float(df.R.median()), 3),
               win=round(float((df.R > 0).mean()), 3), ci95=[round(lo, 3), round(hi, 3)],
               drop_top5=round(float(r.iloc[5:].mean()), 4),
               drop_top1pct=round(float(r.iloc[int(np.ceil(0.01 * len(r))):].mean()), 4),
               top5_share_of_sumR=round(float(r.iloc[:5].sum() / df.R.sum()), 2) if df.R.sum() > 0 else None)
    if m1 is not None:
        bull = regime(m1)
        et = pd.to_datetime(df["t_entry"]).dt.tz_convert(ET).dt.tz_localize(None)
        d = (et + pd.Timedelta(hours=6)).dt.normalize()
        b = d.map(bull)
        out["bull"] = dict(n=int((b == True).sum()), mean_R=round(float(df.R[b == True].mean()), 3))   # noqa: E712
        out["bear"] = dict(n=int((b == False).sum()), mean_R=round(float(df.R[b == False].mean()), 3))  # noqa: E712
        yr = pd.to_datetime(df["t_entry"]).dt.year
        out["by_year"] = {int(k): round(float(v), 3) for k, v in df.R.groupby(yr.values).mean().items()}
    return out


def compare(mine: pd.DataFrame, f: Path) -> dict:
    th = pd.read_csv(f)
    a = mine.assign(k=pd.to_datetime(mine["t_entry"]).astype("int64"))
    t = th.assign(k=pd.to_datetime(th["t_entry"]).astype("int64"))
    j = a.merge(t, on="k", suffixes=("_a2", "_a1"))
    mm = {c: int((~np.isclose(j[f"{c}_a2"], j[f"{c}_a1"], atol=1e-6)).sum()) for c in ("entry", "stop0", "R")}
    mm["t_exit"] = int((pd.to_datetime(j["t_exit_a2"]) != pd.to_datetime(j["t_exit_a1"])).sum())
    return dict(n_a2=len(a), n_a1=len(t), matched=len(j), field_mismatch=mm)


def run(m1, spec, tick, **kw):
    return sequence(Tape(m1, spec), orders_d4(m1, tick, **kw))


if __name__ == "__main__":
    res = {}
    mnq = load_cme("MNQ")
    base = run(mnq, MNQ, 0.25)
    base.to_csv(HERE / "a2_trades_D4_MNQ.csv", index=False)
    res["MNQ"] = stats(base, mnq) | {"vs_agent1": compare(base, A1D / "trades_D4_G_long_1h_pivot_MNQ.csv")}
    res["MNQ_one_bar_delay"] = stats(run(mnq, MNQ, 0.25, delay_bars=1))
    res["MNQ_cost_x1.5"] = stats(run(mnq, replace(MNQ, comm=1.5, slip=0.375), 0.25))
    res["MNQ_slip_x3"] = stats(run(mnq, replace(MNQ, slip=0.75), 0.25))
    res["MNQ_frictionless"] = stats(run(mnq, replace(MNQ, comm=0.0, slip=0.0), 0.25))
    es = load_cme("ES")
    e = run(es, ES, 0.25)
    res["ES"] = stats(e, es) | {"vs_agent1": compare(e, A1D / "trades_D4_G_long_1h_pivot_ES.csv")}
    xau = load_xau_dev()
    x = run(xau, XAU, 0.01)
    res["XAUUSD"] = stats(x) | {"vs_agent1": compare(x, A1D / "trades_D4_G_long_1h_pivot_XAUUSD.csv")}
    (HERE / "replicate_D4_result.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str))
