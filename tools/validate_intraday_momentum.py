"""One-shot validation for INTRADAY_MOMENTUM_PREREGISTRATION.md. No network, no tuning."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import skew


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.intraday_momentum import daily_trades
from core.config import DEFAULT_GATE_CFG
from core.validation.battery import run_gate


OUT = ROOT / "data" / "strategy_research"
RESULT = OUT / "intraday_momentum_validation_2026-09-22.json"
CAPITAL = 50_000.0
TRAIN_FRACTION = 0.60
FRESH_FIRST = pd.Timestamp("2026-07-01").date()
FRESH_LAST = pd.Timestamp("2026-09-18").date()


def metrics(t: pd.DataFrame, col: str = "pnl") -> dict:
    t = t[t["traded"]] if col == "pnl" else t
    p = t[col].to_numpy(float)
    if len(p) == 0:
        return {"trades": 0}
    wins, losses = p[p > 0], p[p < 0]
    equity = np.cumsum(p)
    streak = best = 0
    for v in p:
        streak = streak + 1 if v < 0 else 0
        best = max(best, streak)
    daily_sd = float(np.std(p, ddof=1)) if len(p) > 1 else 0.0
    return {
        "trades": int(len(p)),
        "longs": int((t["side"] > 0).sum()) if "side" in t else None,
        "shorts": int((t["side"] < 0).sum()) if "side" in t else None,
        "win_rate": float(np.mean(p > 0)),
        "mean_pnl": float(np.mean(p)),
        "median_pnl": float(np.median(p)),
        "total_pnl": float(p.sum()),
        "avg_win": float(wins.mean()) if len(wins) else None,
        "avg_loss": float(losses.mean()) if len(losses) else None,
        "payoff": float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses) else None,
        "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) else None,
        "skew": float(skew(p, bias=False)) if len(p) >= 3 else None,
        "max_consecutive_losses": int(best),
        "max_drawdown_usd": float(np.min(equity - np.maximum.accumulate(equity))),
        "mean_bps_of_notional": float(np.mean(p / t["notional"].to_numpy(float)) * 1e4),
        "annualised_sharpe": float(np.mean(p) / daily_sd * np.sqrt(252)) if daily_sd > 0 else None,
    }


def buckets(t: pd.DataFrame, sessions) -> list[dict]:
    rows = []
    for n, part in enumerate(np.array_split(np.asarray(sessions, dtype=object), 4), start=1):
        sub = t[t["session"].isin(set(part))]
        rows.append({"bucket": n, "start": str(part[0]), "end": str(part[-1]), **metrics(sub)})
    return rows


def gate(t: pd.DataFrame) -> dict:
    r = t.loc[t["traded"], "pnl"].to_numpy(float) / CAPITAL
    g = run_gate(r, DEFAULT_GATE_CFG, nb_trials=1, sr_trials_var=0.0, active_returns=r, n_params=0)
    return asdict(g)


def load(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    idx = pd.DatetimeIndex(df.index)
    print(f"STEP0 {path.relative_to(ROOT)} rows={len(df)} start={idx.min()} end={idx.max()} "
          f"dup={int(idx.duplicated().sum())} nan_close={int(df['close'].isna().sum())}")
    if idx.duplicated().any() or df["close"].isna().any():
        raise SystemExit(f"data sanity failed for {path}")
    return df


def main() -> int:
    if RESULT.exists():
        raise SystemExit(f"refusing to overwrite existing one-shot result {RESULT}")
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict = {"preregistration": "INTRADAY_MOMENTUM_PREREGISTRATION.md", "screen_holdout": {}, "fresh": {}}

    for contract in ("MNQ", "MES", "ES"):
        t = daily_trades(load(ROOT / "data" / f"{contract}_1m.parquet"), contract)
        t2 = daily_trades(load(ROOT / "data" / f"{contract}_1m.parquet"), contract, slip_ticks=2)
        sessions = list(t["session"])
        cut = int(len(sessions) * TRAIN_FRACTION)
        train, hold = sessions[:cut], sessions[cut:]
        tr, ho = t[t["session"].isin(set(train))], t[t["session"].isin(set(hold))]
        ho2 = t2[t2["session"].isin(set(hold))]
        report["screen_holdout"][contract] = {
            "sessions": len(sessions), "holdout_start": str(hold[0]),
            "train": metrics(tr), "holdout": metrics(ho), "holdout_buckets": buckets(ho, hold),
            "holdout_gate": gate(ho), "holdout_two_tick_stress": metrics(ho2),
            "holdout_always_long_last_half_hour": metrics(ho, "always_long_pnl"),
            "holdout_onfh_diagnostic": metrics(ho.assign(pnl=ho["onfh_pnl"], traded=ho["onfh_pnl"] != 0)),
        }
        t.to_csv(OUT / f"intraday_momentum_{contract}_databento_trades.csv", index=False)

    for contract in ("MNQ", "MES", "ES", "NQ", "M2K", "MYM"):
        path = ROOT / "data" / "sierra" / f"{contract}_continuous_1m_latest_90d.parquet"
        t = daily_trades(load(path), contract)
        f = t[(t["session"] >= FRESH_FIRST) & (t["session"] <= FRESH_LAST)]
        report["fresh"][contract] = {"sessions": int(len(f)), **metrics(f)}
        f.to_csv(OUT / f"intraday_momentum_{contract}_fresh_trades.csv", index=False)

    mnq = report["screen_holdout"]["MNQ"]
    reasons = []
    if not mnq["holdout_gate"]["passed"]:
        reasons.append("MNQ holdout run_gate failed: " + ",".join(mnq["holdout_gate"]["reasons"]))
    if not (mnq["holdout"].get("mean_pnl", 0) > 0):
        reasons.append("MNQ holdout mean <= 0")
    if sum(1 for b in mnq["holdout_buckets"] if b.get("total_pnl", -1) >= 0) < 3:
        reasons.append("fewer than 3/4 MNQ holdout buckets >= 0")
    if not (report["fresh"]["MNQ"].get("mean_pnl", 0) > 0):
        reasons.append("MNQ fresh-window mean <= 0")
    report["verdict"] = "FAIL" if reasons else "PASS (paper-trading research candidate only)"
    report["fail_reasons"] = reasons
    RESULT.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
