"""V5 + V6 validation audit on FROZEN trade logs (no strategy re-run, no tuning).

Inputs (produced earlier by tools/validate_research_candidates.py, unchanged):
  data/strategy_research/luxalgo_poc_sweep_reclaim_trades.csv   (5-minute parent bars)
  data/strategy_research/youtube_opening_fvg_scalp_trades.csv   (1-minute bars)

V5  Decompose each trade into GROSS edge (nominal prices, zero cost) and EXECUTION TAX, then
    re-price the SAME exits under three labelled cost models. Stops/targets are absolute prices,
    so exit paths do not change; only fills shift. (Target distance for POC is defined from the
    slipped entry, a <=1-tick second-order effect that is ignored and stated.)
      optimistic : 0 tick entry, 0 tick stop/flatten, commission $1.00 RT
      base       : 1 tick entry, 1 tick stop/flatten, commission $1.00 RT  (Heimdall default)
      stress     : 2 tick entry, 3 tick stop, 2 tick flatten, commission $1.00 RT
V6  For every stop exit, test whether the TARGET was also inside the exit bar (ordering unknown).
    Resolve with finer data already owned: 1-minute bars for the 5-minute strategy; NQ one-tick
    trade prints (Sierra, same index/price scale) where dates overlap. Report worst / resolved / best.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

ROOT = Path(__file__).resolve().parents[1]
TICK, PV, COMM = 0.25, 2.0, 1.0
HOLDOUT_START = pd.Timestamp("2025-09-11").date()  # from validation_2026-09-22.json walk-forward bucket 1
SCEN = {"optimistic": (0, 0, 0), "base": (1, 1, 1), "stress": (2, 3, 2)}  # entry, stop, flatten ticks
TICK_FILES = [ROOT / "data/sierra/tick/NQM26_CME_1tick_full.parquet", ROOT / "data/sierra/tick/NQU26_CME_1tick_full.parquet"]


def _nominal(t) -> tuple[float, float]:
    side = t.side
    entry_nom = t.entry_price - side * TICK
    if t.reason == "stop":
        exit_nom = t.stop_price
    elif t.reason == "gap_stop":
        exit_nom = t.exit_price  # filled at the gapped open; nominal = open (already the market)
    elif t.reason == "session_flatten":
        exit_nom = t.exit_price + side * TICK
    else:
        exit_nom = t.target_price
    return entry_nom, exit_nom


def _price(t, entry_nom, exit_nom, scen) -> float:
    e_t, s_t, f_t = SCEN[scen]
    entry = entry_nom + t.side * e_t * TICK
    if t.reason == "stop":
        exit_ = exit_nom - t.side * s_t * TICK
    elif t.reason == "session_flatten":
        exit_ = exit_nom - t.side * f_t * TICK
    elif t.reason == "gap_stop":
        exit_ = exit_nom - t.side * max(s_t - 1, 0) * TICK  # base already filled at open
    else:
        exit_ = exit_nom
    return t.side * (exit_ - entry) * PV - COMM


def _minute_bars() -> pd.DataFrame:
    df = pd.read_parquet(ROOT / "data/MNQ_1m.parquet", columns=["open", "high", "low", "close"])
    df.index = df.index.tz_convert("America/New_York").tz_localize(None)
    return df


def _tick_window(start_et: pd.Timestamp, end_et: pd.Timestamp, ref_price: float) -> pd.DataFrame | None:
    s = start_et.tz_localize("America/New_York").tz_convert("UTC")
    e = end_et.tz_localize("America/New_York").tz_convert("UTC")
    for f in TICK_FILES:
        d = ds.dataset(f).to_table(filter=(ds.field("ts") >= s) & (ds.field("ts") < e), columns=["ts", "close"]).to_pandas()
        if len(d) and abs(float(d["close"].iloc[0]) - ref_price) <= 5.0:  # same contract as the MNQ.v.0 bar
            return d
    return None


def _first_touch(prices: np.ndarray, side: int, stop: float, target: float) -> str | None:
    for p in prices:
        if (side > 0 and p <= stop) or (side < 0 and p >= stop):
            return "stop"
        if (side > 0 and p >= target) or (side < 0 and p <= target):
            return "target"
    return None


def analyse(name: str, parent_minutes: int, bars: pd.DataFrame) -> dict:
    trades = pd.read_csv(ROOT / f"data/strategy_research/{name}_trades.csv", parse_dates=["entry_ts", "exit_ts"])
    trades["session"] = pd.to_datetime(trades["session"]).dt.date
    rows = []
    for t in trades.itertuples(index=False):
        entry_nom, exit_nom = _nominal(t)
        gross = t.side * (exit_nom - entry_nom) * PV
        rec = {"session": t.session, "reason": t.reason, "pnl_logged": t.pnl, "gross": gross,
               **{f"pnl_{k}": _price(t, entry_nom, exit_nom, k) for k in SCEN}}
        rec["base_matches_log"] = abs(rec["pnl_base"] - t.pnl) < 1e-6
        # --- V6 ordering ---
        rec["ambiguous_bar"] = False
        rec["resolution"] = "n/a"
        if t.reason == "stop":
            window = bars.loc[t.exit_ts: t.exit_ts + pd.Timedelta(minutes=parent_minutes) - pd.Timedelta(seconds=1)]
            tgt_in = (window["high"].max() >= t.target_price) if t.side > 0 else (window["low"].min() <= t.target_price)
            if tgt_in:
                rec["ambiguous_bar"] = True
                order = None
                if parent_minutes > 1:  # resolve 5m bar with 1m bars
                    for _, b in window.iterrows():
                        s_hit = b.low <= t.stop_price if t.side > 0 else b.high >= t.stop_price
                        g_hit = b.high >= t.target_price if t.side > 0 else b.low <= t.target_price
                        if s_hit and g_hit:
                            order = None
                            break
                        if s_hit or g_hit:
                            order = "stop" if s_hit else "target"
                            break
                    if order:
                        rec["resolution"] = f"1m:{order}"
                if order is None:
                    ticks = _tick_window(t.exit_ts, t.exit_ts + pd.Timedelta(minutes=parent_minutes), float(window["open"].iloc[0]))
                    if ticks is not None:
                        order = _first_touch(ticks["close"].to_numpy(float), t.side, t.stop_price, t.target_price)
                        rec["resolution"] = f"tick:{order}" if order else "tick:none"
                    else:
                        rec["resolution"] = "unresolved"
                best = t.side * (t.target_price - entry_nom - t.side * TICK) * PV - COMM
                rec["pnl_best_order"] = best
                rec["pnl_resolved_order"] = best if order == "target" else t.pnl
        rows.append(rec)
    df = pd.DataFrame(rows)
    df["pnl_best_order"] = df.get("pnl_best_order", pd.Series(dtype=float)).fillna(df["pnl_logged"])
    df["pnl_resolved_order"] = df.get("pnl_resolved_order", pd.Series(dtype=float)).fillna(df["pnl_logged"])

    def summ(sub: pd.DataFrame) -> dict:
        n = len(sub)
        out = {"trades": n, "base_matches_log": bool(sub["base_matches_log"].all()),
               "gross_mean": sub["gross"].mean(), "gross_total": sub["gross"].sum(),
               "execution_tax_per_trade_base": (sub["gross"] - sub["pnl_base"]).mean()}
        for k in SCEN:
            out[f"net_mean_{k}"] = sub[f"pnl_{k}"].mean()
        out["ambiguous_stop_exits"] = int(sub["ambiguous_bar"].sum())
        out["resolution_counts"] = sub.loc[sub["ambiguous_bar"], "resolution"].value_counts().to_dict()
        out["net_mean_worst_order"] = sub["pnl_logged"].mean()
        out["net_mean_resolved_order"] = sub["pnl_resolved_order"].mean()
        out["net_mean_best_order"] = sub["pnl_best_order"].mean()
        # smallest per-trade t-stat style summary for context (not a gate)
        for col in ("pnl_optimistic", "pnl_base", "gross"):
            x = sub[col].to_numpy(float)
            out[f"tstat_{col}"] = float(x.mean() / (x.std(ddof=1) / np.sqrt(n))) if n > 2 else None
        return out

    return {"name": name, "full": summ(df), "holdout": summ(df[df["session"] >= HOLDOUT_START])}


def main() -> int:
    bars = _minute_bars()
    res = [analyse("luxalgo_poc_sweep_reclaim", 5, bars), analyse("youtube_opening_fvg_scalp", 1, bars)]
    out = ROOT / "data/validation_audit/execution_intrabar_2026-09-22.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps(res, indent=1, default=lambda v: round(v, 3) if isinstance(v, float) else str(v)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
