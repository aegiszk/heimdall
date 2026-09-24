"""Protocol §2.4 integrity gates for the harvested NQ series. NO OUTCOMES.

Computes only: hashes, row counts, first/last stamp, duplicates, NaN cells, per-session RTH row counts,
and the series-equivalence check on the already-contaminated window 2024-07-01..2024-09-30.
It never computes returns, ranges, volatility or any strategy quantity on pre-2024-07-01 rows.

usage: python dhesi_v3_harvest_integrity.py <NQ parquet> [--roll-dates YYYY-MM-DD,...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ET = "America/New_York"
OHLC = ["open", "high", "low", "close"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("nq", type=Path)
    ap.add_argument("--roll-dates", default="")
    a = ap.parse_args()
    df = pd.read_parquet(a.nq)
    idx = pd.DatetimeIndex(df.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    df = df.set_axis(idx)
    et = idx.tz_convert(ET)
    rth = (et.weekday < 5) & (et.time >= pd.Timestamp("09:30").time()) & (et.time <= pd.Timestamp("16:00").time())
    untouched = et < pd.Timestamp("2024-06-29 00:00", tz=ET)
    per_session = pd.Series(1, index=et[rth & untouched].date).groupby(level=0).sum()
    sessions = per_session.iloc[20:]
    g1 = bool(idx.duplicated().sum() == 0 and df[OHLC].isna().sum().sum() == 0)
    share370 = float((sessions >= 370).mean()) if len(sessions) else 0.0
    g2 = share370 >= 0.95

    # gate 3: contaminated window only
    lo, hi = pd.Timestamp("2024-07-01", tz=ET), pd.Timestamp("2024-10-01", tz=ET)
    nq = df.loc[(et >= lo) & (et < hi), "close"]
    mnq = pd.read_parquet(ROOT / "data" / "MNQ_1m.parquet", columns=["close"])["close"]
    mnq.index = pd.DatetimeIndex(mnq.index).tz_convert("UTC")
    j = pd.concat([nq.rename("nq"), mnq.rename("mnq")], axis=1, join="inner")
    rolls = [pd.Timestamp(x).date() for x in a.roll_dates.split(",") if x]
    if rolls:
        d = j.index.tz_convert(ET).date
        near = pd.Series(d).apply(lambda x: any(abs((pd.Timestamp(x) - pd.Timestamp(r)).days) <= 1 for r in rolls)).to_numpy()
        j = j.loc[~near]
    eq = float(((j["nq"] - j["mnq"]).abs() <= 2.0).mean()) if len(j) else 0.0
    g3 = len(j) > 0 and eq >= 0.95
    out = {
        "file": str(a.nq), "sha256": hashlib.sha256(a.nq.read_bytes()).hexdigest(), "rows": int(len(df)),
        "first_utc": str(idx.min()), "last_utc": str(idx.max()),
        "duplicates": int(idx.duplicated().sum()), "nan_ohlc_cells": int(df[OHLC].isna().sum().sum()),
        "untouched_rth_sessions": int(len(per_session)), "evaluated_sessions_after_burn_in": int(len(sessions)),
        "first_evaluated_session": str(sessions.index.min()) if len(sessions) else None,
        "share_sessions_ge_370_rth_rows": share370, "roll_dates_reported": [str(r) for r in rolls],
        "equivalence_minutes": int(len(j)), "equivalence_share_le_2pts": eq,
        "gate1_no_dup_no_nan": g1, "gate2_coverage": g2, "gate3_series_equivalence": g3,
        "all_gates_pass": bool(g1 and g2 and g3),
    }
    (HERE / "DHESI_V3_HARVEST_INTEGRITY.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if out["all_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
