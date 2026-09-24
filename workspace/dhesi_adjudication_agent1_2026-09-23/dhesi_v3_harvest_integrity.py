"""Protocol §2.4 integrity gates for the harvested NQ series. NO OUTCOMES.

Revision 2 (2026-09-24, pre-validation hardening; fixes Agent 2 finding D4):
the frozen engine (`InversionModel._prepare_frame`) raises on ANY non-finite value in open/high/low/close/VOLUME,
but revision 1 checked only OHLC NaNs. Revision 2 adds volume and full row-validity checks.

What this tool reports is COUNTS ONLY (never a statistic of prices or volume, per protocol §2.4):
  - timestamps: invalid (NaT), duplicates, non-monotonic steps, index timezone;
  - non-finite cells per column (NaN or +/-inf) for open/high/low/close/volume, negative volume, zero-volume rows;
  - OHLC geometry violations (high < low, high < max(open, close), low > min(open, close));
  - per-session RTH row counts (coverage gate), sessions below 370 rows, intra-RTH gaps > 1 minute;
  - Sierra roll dates supplied by the operator (listed, checked to lie inside the file range);
  - series-equivalence on the already-contaminated window 2024-07-01..2024-09-30 against data/MNQ_1m.parquet,
    at minute lags -1, 0, +1 (a 1-minute stamp shift or a timezone error makes lag 0 lose to a neighbour or fall
    below 95%).
Missing volume is never imputed. Any non-finite or negative volume in a row the run consumes FAILS the harvest.

usage: python dhesi_v3_harvest_integrity.py <NQ parquet> [--roll-dates YYYY-MM-DD,...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ET = "America/New_York"
OHLC = ["open", "high", "low", "close"]
OHLCV = OHLC + ["volume"]
UNTOUCHED_END_ET = pd.Timestamp("2024-06-29 00:00", tz=ET)   # identical to the validator's hard cut
EQ_LO, EQ_HI = pd.Timestamp("2024-07-01", tz=ET), pd.Timestamp("2024-10-01", tz=ET)
MIN_RTH_ROWS, MIN_COVERAGE_SHARE, EQ_TOL_PTS, EQ_MIN_SHARE, BURN_IN = 370, 0.95, 2.0, 0.95, 20


def _utc_index(df: pd.DataFrame) -> tuple[pd.DatetimeIndex, str]:
    idx = pd.DatetimeIndex(df.index)
    tzname = "naive" if idx.tz is None else str(idx.tz)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    return idx, tzname


def row_integrity(df: pd.DataFrame) -> dict:
    """Gate 1 (row validity). Counts only. Evaluated on EVERY row of the file (a superset of the rows consumed)."""
    missing_cols = sorted(set(OHLCV).difference(df.columns))
    out: dict = {"missing_columns": missing_cols}
    if missing_cols:
        out["gate1_rows_valid"] = False
        return out
    raw_idx = pd.DatetimeIndex(df.index)
    idx, tzname = _utc_index(df)
    vals = {c: pd.to_numeric(df[c], errors="coerce").to_numpy(float) for c in OHLCV}
    nonfinite = {c: int((~np.isfinite(v)).sum()) for c, v in vals.items()}
    v = vals["volume"]
    o, h, lo, c = vals["open"], vals["high"], vals["low"], vals["close"]
    with np.errstate(invalid="ignore"):
        geom = int(np.sum((h < lo) | (h < np.maximum(o, c)) | (lo > np.minimum(o, c))))
        neg_vol = int(np.sum(v < 0))
        zero_vol = int(np.sum(v == 0))
    ts_ns = idx.as_unit("ns").asi8
    steps = np.diff(ts_ns)
    untouched = idx < UNTOUCHED_END_ET.tz_convert("UTC")
    out.update({
        "index_timezone": tzname,
        "invalid_timestamps": int(raw_idx.isna().sum()),
        "duplicate_timestamps": int(idx.duplicated().sum()),
        "non_monotonic_steps": int((steps <= 0).sum()) if len(steps) else 0,
        "nonfinite_cells": nonfinite,
        "negative_volume_rows": neg_vol,
        "zero_volume_rows": zero_vol,
        "ohlc_geometry_violations": geom,
        "rows_total": int(len(df)),
        "rows_consumed_by_run": int(untouched.sum()),
        "nonfinite_ohlcv_rows_consumed": int((~np.isfinite(np.column_stack([vals[k] for k in OHLCV])).all(1) & untouched).sum()),
    })
    out["gate1_rows_valid"] = bool(
        out["invalid_timestamps"] == 0 and out["duplicate_timestamps"] == 0 and out["non_monotonic_steps"] == 0
        and sum(nonfinite.values()) == 0 and neg_vol == 0 and geom == 0)
    return out


def coverage(df: pd.DataFrame) -> dict:
    """Gate 2: >= 95% of evaluated untouched sessions have >= 370 RTH rows. Counts only."""
    idx, _ = _utc_index(df)
    et = idx.tz_convert(ET)
    rth = (et.weekday < 5) & (et.time >= pd.Timestamp("09:30").time()) & (et.time <= pd.Timestamp("16:00").time())
    untouched = et < UNTOUCHED_END_ET
    sel = et[rth & untouched]
    per_session = pd.Series(1, index=sel.date).groupby(level=0).sum()
    sessions = per_session.iloc[BURN_IN:]
    share = float((sessions >= MIN_RTH_ROWS).mean()) if len(sessions) else 0.0
    gaps = 0
    if len(sel):
        s = pd.Series(sel.as_unit("ns").asi8, index=sel.date)
        d = s.groupby(level=0).diff().dropna()
        gaps = int((d > 60_000_000_000).sum())
    return {
        "untouched_rth_sessions": int(len(per_session)), "evaluated_sessions_after_burn_in": int(len(sessions)),
        "first_evaluated_session": str(sessions.index.min()) if len(sessions) else None,
        "sessions_below_370_rth_rows": int((sessions < MIN_RTH_ROWS).sum()),
        "intra_rth_gaps_gt_1min": gaps,
        "share_sessions_ge_370_rth_rows": share, "gate2_coverage": bool(share >= MIN_COVERAGE_SHARE),
    }


def equivalence(df: pd.DataFrame, ref_close: pd.Series, roll_dates: list, lags=(-1, 0, 1)) -> dict:
    """Gate 3 (series equivalence) on the CONTAMINATED window only; also the timestamp-shift / timezone check."""
    idx, _ = _utc_index(df)
    et = idx.tz_convert(ET)
    nq = pd.Series(pd.to_numeric(df["close"], errors="coerce").to_numpy(float), index=idx).loc[(et >= EQ_LO) & (et < EQ_HI)]
    ref = ref_close.copy()
    ref.index = pd.DatetimeIndex(ref.index).tz_convert("UTC")
    res = {}
    for lag in lags:
        shifted = nq.copy()
        shifted.index = shifted.index + pd.Timedelta(minutes=lag)
        j = pd.concat([shifted.rename("nq"), ref.rename("ref")], axis=1, join="inner").dropna()
        if roll_dates:
            d = j.index.tz_convert(ET).date
            near = np.array([any(abs((pd.Timestamp(x) - pd.Timestamp(r)).days) <= 1 for r in roll_dates) for x in d], bool)
            j = j.loc[~near] if len(j) else j
        res[lag] = (int(len(j)), float(((j["nq"] - j["ref"]).abs() <= EQ_TOL_PTS).mean()) if len(j) else 0.0)
    n0, s0 = res[0]
    better = [k for k in res if k != 0 and res[k][1] > s0]   # a strictly better neighbouring lag = stamp shift
    return {
        "equivalence_minutes": n0, "equivalence_share_le_2pts": s0,
        "equivalence_share_by_lag_minutes": {str(k): v[1] for k, v in res.items()},
        "lags_strictly_better_than_0": [int(k) for k in better],
        "gate3_series_equivalence": bool(n0 > 0 and s0 >= EQ_MIN_SHARE and not better),
    }


def rolls_check(df: pd.DataFrame, roll_dates: list) -> dict:
    idx, _ = _utc_index(df)
    lo, hi = (idx.min().date(), idx.max().date()) if len(idx) else (None, None)
    outside = [str(r) for r in roll_dates if lo is None or not (lo <= r <= hi)]
    return {"roll_dates_reported": [str(r) for r in roll_dates], "roll_dates_outside_file_range": outside,
            "gate4_roll_dates_consistent": len(outside) == 0}


def run_all(df: pd.DataFrame, ref_close: pd.Series, roll_dates: list) -> dict:
    out = {}
    out.update(row_integrity(df))
    if not out.get("missing_columns"):
        out.update(coverage(df))
        out.update(equivalence(df, ref_close, roll_dates))
        out.update(rolls_check(df, roll_dates))
    gates = ("gate1_rows_valid", "gate2_coverage", "gate3_series_equivalence", "gate4_roll_dates_consistent")
    out["all_gates_pass"] = bool(all(out.get(g, False) for g in gates))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("nq", type=Path)
    ap.add_argument("--roll-dates", default="")
    a = ap.parse_args()
    df = pd.read_parquet(a.nq)
    rolls = [pd.Timestamp(x).date() for x in a.roll_dates.split(",") if x]
    mnq = pd.read_parquet(ROOT / "data" / "MNQ_1m.parquet", columns=["close"])["close"]
    out = {"file": str(a.nq), "sha256": hashlib.sha256(a.nq.read_bytes()).hexdigest(),
           "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    idx, _ = _utc_index(df)
    out.update({"first_utc": str(idx.min()), "last_utc": str(idx.max())})
    out.update(run_all(df, mnq, rolls))
    (HERE / "DHESI_V3_HARVEST_INTEGRITY.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if out["all_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
