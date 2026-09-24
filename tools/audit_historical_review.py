"""V11 validation audit: frozen-rule historical false-negative review.

Reads FROZEN trade logs only (no strategy is re-run, nothing is tuned) and asks, per experiment:
  - how much evidence did the sample actually contain (per-trade Sharpe, t, 95% CI of mean)?
  - how many trades would a t > 2 test need for 80% power at the observed (or a useful) edge?
  - gross edge vs execution tax (where nominal prices are recoverable)
  - how many stop exits were same-bar-ambiguous (target also inside the exit bar)?

Selection (per the audit brief): terrible = vwap_reversion MES; borderline = Casper FVG MNQ;
sparse promising = Dhesi inversion v2 MNQ; execution-sensitive = time_structured_scalp MES;
order-flow = initiative v3 NQ.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TICK = 0.25
Z = 2.0 + 0.8416  # t > 2 at 80% power (normal approx)

CASES = [
    ("terrible", "vwap_reversion_hard_stop_MES", "data/prop_futures/vwap_reversion_hard_stop_MES_1m_trades.csv", "MES", 5.0, 1.0),
    ("borderline", "youtube_opening_fvg_scalp_MNQ", "data/strategy_research/youtube_opening_fvg_scalp_trades.csv", "MNQ", 2.0, 1.0),
    ("sparse_promising", "inversion_model_v2_MNQ", "data/prop_futures/inversion_model_MNQ_1m_trades.csv", "MNQ", 2.0, 1.0),
    ("execution_sensitive", "time_structured_scalp_MES", "data/prop_futures/time_structured_scalp_MES_1m_trades.csv", "MES", 5.0, 1.0),
    ("orderflow", "orderflow_initiative_v3_NQ", "data/prop_futures/orderflow_initiative_v3_NQ_trades.csv", None, 2.0, 1.0),
]
HOLDOUT_START = {
    "MES": None, "MNQ": pd.Timestamp("2025-09-11").date(), None: pd.Timestamp("2026-06-16").date(),
}


def _holdout_start_mes() -> object:
    idx = pd.read_parquet(ROOT / "data/MES_1m.parquet", columns=["close"]).index.tz_convert("America/New_York")
    days = sorted(set(idx.date))
    return days[int(len(days) * 0.6)]


def _stats(pnl: np.ndarray) -> dict:
    n = len(pnl)
    if n < 3:
        return {"n": n}
    mu, sd = pnl.mean(), pnl.std(ddof=1)
    sr = mu / sd
    return {"n": n, "mean": mu, "sd": sd, "per_trade_sr": sr, "t": sr * np.sqrt(n),
            "mean_ci95": [mu - 1.96 * sd / np.sqrt(n), mu + 1.96 * sd / np.sqrt(n)],
            "n_needed_80pct_power_at_observed_sr": int(np.ceil((Z / sr) ** 2)) if sr > 0 else None,
            "n_needed_80pct_power_at_sr_0.10": int(np.ceil((Z / 0.10) ** 2))}


def _ambiguity(t: pd.DataFrame, bars: pd.DataFrame | None) -> dict:
    if bars is None or not {"stop_price", "target_price", "exit_ts"}.issubset(t.columns):
        return {"checked": False}
    stops = t[t["reason"] == "stop"]
    amb = 0
    for r in stops.itertuples(index=False):
        ts = pd.Timestamp(r.exit_ts)
        ts = ts.tz_convert("America/New_York").tz_localize(None) if ts.tzinfo else ts
        if ts not in bars.index:
            continue
        b = bars.loc[ts]
        side = 1 if r.side in (1, "long") else -1
        amb += bool(b.high >= r.target_price) if side > 0 else bool(b.low <= r.target_price)
    return {"checked": True, "stop_exits": int(len(stops)), "ambiguous_stop_exits": int(amb)}


def _gross(t: pd.DataFrame, pv: float, comm: float) -> np.ndarray | None:
    need = {"entry_price", "stop_price", "target_price", "exit_price", "reason"}
    if not need.issubset(t.columns):
        return None
    side = t["side"].map({"long": 1, "short": -1, 1: 1, -1: -1}).astype(int)
    entry_nom = t["entry_price"] - side * TICK
    exit_nom = np.select(
        [t["reason"] == "stop", t["reason"] == "target", t["reason"].isin(["session_flatten", "session_flat"])],
        [t["stop_price"], t["target_price"], t["exit_price"] + side * TICK], default=t["exit_price"])
    return (side * (exit_nom - entry_nom) * pv).to_numpy(float)


def main() -> int:
    HOLDOUT_START["MES"] = _holdout_start_mes()
    bar_cache: dict[str, pd.DataFrame] = {}
    out = []
    for label, name, path, contract, pv, comm in CASES:
        t = pd.read_csv(ROOT / path)
        date_col = "session" if "session" in t.columns else "entry_ts"
        t["_date"] = pd.to_datetime(t[date_col].astype(str).str[:10]).dt.date
        ho = t["_date"] >= HOLDOUT_START[contract]
        bars = None
        if contract and contract not in bar_cache:
            b = pd.read_parquet(ROOT / f"data/{contract}_1m.parquet", columns=["high", "low"])
            b.index = b.index.tz_convert("America/New_York").tz_localize(None)
            bar_cache[contract] = b
        bars = bar_cache.get(contract)
        rec = {"label": label, "name": name, "holdout_start": str(HOLDOUT_START[contract]),
               "full": _stats(t["pnl"].to_numpy(float)), "holdout": _stats(t.loc[ho, "pnl"].to_numpy(float))}
        if "gross_pnl" in t.columns:  # inversion logs carry gross directly
            g = t["gross_pnl"].to_numpy(float)
        else:
            g = _gross(t, pv, comm)
        if g is not None:
            rec["holdout_gross"] = _stats(g[ho.to_numpy()])
            rec["holdout_execution_tax_per_trade"] = float((g[ho.to_numpy()] - t.loc[ho, "pnl"].to_numpy(float)).mean())
        rec["same_bar_ambiguity_holdout"] = _ambiguity(t.loc[ho], bars)
        if name.startswith("inversion"):
            wrong = ((t.side == 1) & (t.stop_price >= t.entry_price)) | ((t.side == -1) & (t.stop_price <= t.entry_price))
            rec["wrong_side_stop_trades_full"] = int(wrong.sum())
            rec["holdout_excluding_wrong_side"] = _stats(t.loc[ho & ~wrong, "pnl"].to_numpy(float))
        out.append(rec)
    path = ROOT / "data/validation_audit/historical_review_2026-09-22.json"
    path.write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps(out, indent=1, default=lambda v: round(float(v), 3)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
