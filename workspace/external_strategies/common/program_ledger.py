"""Program-level multiple-testing + ledger outputs.
- Reads _program/dev_rows.json.
- Holm and Benjamini-Hochberg on one-sided NW p-values across ALL trials in the program.
- DSR per trial with n_trials = program trials and sr_trials_var = empirical variance of per-trade SRs.
- White Reality Check on daily R series (per trial; session days).
- Writes EXTERNAL_8_STRATEGIES_MASTER_LEDGER.json and EXTERNAL_8_STRATEGIES_TEST_MATRIX.csv at repo root, and
  (with --register) appends every trial to data/trials_ledger.json (append-only hash chain).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import registry as rg  # noqa: E402
import stats as stx  # noqa: E402

ROOT = rg.BASE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def verdict(r: dict) -> str:
    if r.get("status") == "INVALID_IMPLEMENTATION":
        return "INVALID_IMPLEMENTATION"
    n = r.get("n", 0) or 0
    if n < 30:
        return "INCONCLUSIVE"
    m, hi = r["mean_R"], r["boot95_hi"]
    c15 = (r.get("cost_scaled_mean_R") or {}).get("1.5")
    if m <= 0 and hi < 0.05:
        return "ROBUSTLY_REJECTED"
    ypos = r.get("pos_years", 0) / max(1, r.get("n_years", 1))
    if m > 0 and r["nw_t"] > 2 and (c15 or -1) > 0 and (r.get("drop_top5_mean_R") or -1) > 0 and ypos >= 2 / 3:
        return "CANDIDATE"
    return "INCONCLUSIVE"


def daily_series(fam, cfg, inst) -> pd.Series | None:
    p = rg.BASE / fam / "results" / f"trades_{cfg}_{inst}.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p, parse_dates=["t_entry"])
    day = (pd.to_datetime(df["t_entry"], utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
           + pd.Timedelta(hours=6)).dt.normalize()
    return df.groupby(day)["R"].sum()


def main(register: bool = False):
    rows = json.loads((rg.BASE / "_program" / "dev_rows.json").read_text())
    ok = [r for r in rows if r.get("status") != "INVALID_IMPLEMENTATION" and (r.get("n") or 0) >= 3 and r.get("p_one_sided") is not None and np.isfinite(r["p_one_sided"])]
    p = np.array([r["p_one_sided"] for r in ok])
    holm, bh = stx.holm(p), stx.bh(p)
    srs = np.array([r["sharpe_per_trade"] for r in ok if r.get("n", 0) >= 30 and np.isfinite(r["sharpe_per_trade"])])
    srv = float(np.var(srs, ddof=1)) if len(srs) > 1 else 0.0
    K = len([r for r in rows if r.get("status") != "INVALID_IMPLEMENTATION"]) + 4   # +4: invalid runs still count as looks
    for r, h, q in zip(ok, holm, bh):
        r["p_holm"], r["q_bh"] = float(h), float(q)
        tp = rg.BASE / r["family"] / "results" / f"trades_{r['cfg']}_{r['inst']}.csv"
        if tp.exists() and r["n"] >= 10:
            R = pd.read_csv(tp)["R"].to_numpy()
            r["dsr_program"] = stx.dsr(R, srv, K)
    for r in rows:
        r["verdict_rule"] = verdict(r)
    # White RC on daily R for trials with >= 30 trades, separately per data group (common calendars)
    rc = {}
    for grp, pred in (("CME", lambda r: r["inst"] in ("MNQ", "ES")), ("FX_XAU", lambda r: r["inst"] not in ("MNQ", "ES", "YM_S"))):
        cols = {}
        for r in rows:
            if pred(r) and (r.get("n") or 0) >= 30 and r.get("status") != "INVALID_IMPLEMENTATION":
                s = daily_series(r["family"], r["cfg"], r["inst"])
                if s is not None:
                    cols[f"{r['cfg']}|{r['inst']}"] = s
        if cols:
            M = pd.DataFrame(cols).fillna(0.0)
            rc[grp] = stx.white_reality_check(M, B=2000)
    out = {"program": "EXTERNAL_8_STRATEGIES", "n_trials": K, "sr_trials_var_empirical": srv,
           "white_reality_check": rc, "trials": rows}
    (ROOT / "EXTERNAL_8_STRATEGIES_MASTER_LEDGER.json").write_text(json.dumps(out, indent=1, default=str))
    cols = ["family", "cfg", "inst", "n_orders", "n", "trades_per_year", "win_rate", "mean_R", "median_R", "mean_gross_R",
            "payoff", "profit_factor", "nw_t", "p_one_sided", "p_holm", "q_bh", "dsr_program", "boot95_lo", "boot95_hi",
            "max_dd_R", "worst_R", "top1_share", "top5_share", "top10_share", "drop_top5_mean_R", "mean_net_usd_1lot",
            "long_n", "long_mean_R", "short_n", "short_mean_R", "pos_years", "n_years", "pos_months_frac",
            "tue_thu_mean_R", "verdict_rule"]
    df = pd.DataFrame(rows)
    for c in ("1.25", "1.5", "2.0"):
        df[f"cost_x{c}_mean_R"] = [((r.get("cost_scaled_mean_R") or {}).get(c)) for r in rows]
    df.reindex(columns=cols + [f"cost_x{c}_mean_R" for c in ("1.25", "1.5", "2.0")]).to_csv(
        ROOT / "EXTERNAL_8_STRATEGIES_TEST_MATRIX.csv", index=False)
    print(json.dumps(rc, indent=1), "srv", srv)
    if register:
        import trials_ledger as tl
        import trials_ledger as _tl
        have = {e["id"] for e in _tl.load_ledger()["entries"]}
        for r in rows:
            if f"EXT8-{r['cfg']}-{r['inst']}" in have:
                if r.get("status") == "INVALID_IMPLEMENTATION" and f"EXT8-{r['cfg']}-{r['inst']}-INVALIDATED" not in have:
                    _tl.register_trial({"id": f"EXT8-{r['cfg']}-{r['inst']}-INVALIDATED", "family": f"ext8_{r['family']}",
                        "dataset": "see original entry", "dataset_group": "CME_EQUITY_INDEX",
                        "data_window": ({"start": "2024-07-01", "end": "2026-06-30"} if r["inst"] == "MNQ" else {"start": "2026-06-24", "end": "2026-09-21"}),
                        "window_status": "REUSED_HOLDOUT", "n_configs": 1, "verdict": "INVALID_IMPLEMENTATION", "is_null_control": True,
                        "source": "workspace/external_strategies/_program/BUGFIX_A_ENTRY.md",
                        "notes": "correction marker: original entry's verdict void (entry-order-type bug); corrected run = _fix1"})
                continue
            fut = r["inst"] in ("MNQ", "ES", "YM_S")
            win = ({"start": "2024-07-01", "end": "2026-06-30"} if r["inst"] in ("MNQ", "ES") else
                   {"start": "2026-06-24", "end": "2026-09-21"} if r["inst"] == "YM_S" else
                   {"start": "2022-01-01", "end": "2024-12-31"})
            tl.register_trial({
                "id": f"EXT8-{r['cfg']}-{r['inst']}", "family": f"ext8_{r['family']}",
                "dataset": {"MNQ": "data/MNQ_1m.parquet", "ES": "data/ES_1m.parquet",
                            "YM_S": "data/sierra/YM_continuous_1m_latest_90d.parquet"}.get(
                                r["inst"], f"data/fx_histdata/{r['inst']}_1m_bid.parquet"),
                "dataset_group": "CME_EQUITY_INDEX" if fut else "FX_SPOT_HISTDATA",
                "data_window": win, "window_status": "REUSED_HOLDOUT" if fut else "DEV", "n_configs": 1,
                "verdict": r["verdict_rule"], "n_trades": r.get("n"),
                "sr_per_trade": r.get("sharpe_per_trade") if (r.get("n") or 0) > 2 else None,
                "source": "EXTERNAL_8_STRATEGIES_MASTER_LEDGER.json; prereg aggregate 067f073c3857",
                "notes": "external 8-strategy program, development run 2026-09-24"})
        print("registered", len(rows))


if __name__ == "__main__":
    main(register="--register" in sys.argv)
