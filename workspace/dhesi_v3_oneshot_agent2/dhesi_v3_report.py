"""D2 reporting for the Dhesi v3 one-shot (Agent 2, 2026-09-24). Hash-bound in VALIDATION_BINDING_V2.json.

Runs ONLY AFTER the validator's primary run. Reads ONLY:
  <dir>/dhesi_v3_untouched_primary.json            (validator output; the ALPHA verdict is copied, never recomputed)
  <dir>/primary_run/FROZEN_ENGINE_TRADES.csv       (normative ledger persisted before statistics)
  <dir>/primary_run/ENGINE_COMPARISON.json
  data/trials_ledger.json                          (global trial accounting)
No market data. Every number here is DESCRIPTIVE (protocol V1 section 9): nothing can change the ALPHA verdict.

Four independent axes: ALPHA (protocol verdict) | EXECUTION | RISK | PROP_ECONOMICS.
usage: python dhesi_v3_report.py <validator output dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import trials_ledger as tl  # noqa: E402

MU_MIN, SIGMA_DESIGN = 30.0, 290.0
MNQ_LISTED = pd.Timestamp("2019-05-06")
DAILY_BUFFER = 325.0
PROP_BREAKEVEN = 0.0396
DHESI_FAMILY = "dhesi_inversion"


def dsr(pnl: np.ndarray, sr_var: float, K: int) -> float:
    """Deflated Sharpe ratio (Bailey & Lopez de Prado 2014), per-trade SR."""
    n = len(pnl)
    if n < 3 or K < 2 or not sr_var or sr_var <= 0:
        return float("nan")
    sr = pnl.mean() / pnl.std(ddof=1)
    g3, g4 = st.skew(pnl), st.kurtosis(pnl, fisher=False)
    emc = 0.5772156649
    sr0 = np.sqrt(sr_var) * ((1 - emc) * st.norm.ppf(1 - 1 / K) + emc * st.norm.ppf(1 - 1 / (K * np.e)))
    return float(st.norm.cdf((sr - sr0) * np.sqrt(n - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)))


def achieved_power(n: int, sd: float) -> dict:
    """Protocol V1 section 7 normal approximation, at the realised N and realised sd."""
    se = sd / np.sqrt(n)
    thr = max(MU_MIN, 1.645 * se)
    return {"se": se, "P_pass_if_true_mu_eq_mu_min": float(1 - st.norm.cdf((thr - MU_MIN) / se)),
            "P_fail_if_true_mu_eq_0": float(st.norm.cdf((MU_MIN - 1.645 * se - 0.0) / se)),
            "P_pass_if_true_mu_eq_0": float(1 - st.norm.cdf(thr / se))}


def global_trials(led: dict) -> dict:
    voided = tl.voided_ids(led)
    looks = [e for e in led["entries"] if not e.get("is_null_control")]
    fam = [e for e in looks if e["family"] == DHESI_FAMILY]
    srs = [float(e["sr_per_trade"]) for e in looks if e.get("sr_per_trade") is not None and (e.get("n_trades") or 0) >= 30]
    return {"global_looks_configs": int(sum(int(e["n_configs"]) for e in looks)),
            "global_looks_entries": len(looks), "voided_entries_counted_as_looks": len(voided),
            "dhesi_family_configs": int(sum(int(e["n_configs"]) for e in fam)),
            "global_sr_var_n_ge_30": float(np.var(srs, ddof=1)) if len(srs) > 1 else None}


def main(d: Path) -> dict:
    rep = json.loads((d / "dhesi_v3_untouched_primary.json").read_text(encoding="utf-8"))
    cmp_ = json.loads((d / "primary_run" / "ENGINE_COMPARISON.json").read_text(encoding="utf-8"))
    res = rep["result"]
    out = {"ALPHA": {"verdict": res.get("verdict"), "source": "validator (protocol V1 + amendment 1); copied, not recomputed",
                     "engine_comparison": cmp_.get("result")}}
    if res.get("verdict") == "INVALID" or cmp_.get("result") != "PASS":
        out["note"] = "INVALID run: no strategy statistic is reported (protocol amendment 1 A1.4)"
        return out
    t = pd.read_csv(d / "primary_run" / "FROZEN_ENGINE_TRADES.csv")
    pnl = t["pnl"].astype(float).to_numpy()
    srt = np.sort(pnl)[::-1]
    tot = pnl.sum()
    led = tl.load_ledger()
    g = global_trials(led)
    alpha = out["ALPHA"]
    alpha.update({k: res.get(k) for k in ("n", "mean", "boot_lo95", "boot_hi95", "checks", "qualifying_years",
                                          "qualifying_years_positive_share", "top_trade_share")})
    alpha["top5_trades"] = t.loc[np.argsort(-pnl)[:5], ["trade_id", "session", "side", "pnl"]].to_dict("records")
    alpha["top5_share_of_total_pnl"] = float(srt[:5].sum() / tot) if tot > 0 else None
    alpha["dsr_descriptive"] = {"K_dhesi_family": g["dhesi_family_configs"], "K_global": g["global_looks_configs"],
                                "sr_var_global": g["global_sr_var_n_ge_30"],
                                "dsr_K_family": dsr(pnl, g["global_sr_var_n_ge_30"], g["dhesi_family_configs"]),
                                "dsr_K_global": dsr(pnl, g["global_sr_var_n_ge_30"], g["global_looks_configs"])}
    alpha["achieved_power"] = achieved_power(len(pnl), float(pnl.std(ddof=1)) if len(pnl) > 1 else SIGMA_DESIGN)
    alpha["trades_per_year"] = float(len(pnl) / max(1e-9, (pd.to_datetime(t["session"]).max() - pd.to_datetime(t["session"]).min()).days / 365.25))
    sess = pd.to_datetime(t["session"])
    pre = sess < MNQ_LISTED
    out["EXECUTION"] = {
        "stress_mean": res.get("stress_mean"), "stress_boot_lo95": res.get("stress_boot_lo95"),
        "pre_MNQ_listing_2019_05_06": {"n": int(pre.sum()), "mean": float(pnl[pre.to_numpy()].mean()) if pre.any() else None,
                                       "note": "MNQ did not exist: fills are HYPOTHETICAL (spec M2)"},
        "post_MNQ_listing": {"n": int((~pre).sum()), "mean": float(pnl[(~pre).to_numpy()].mean()) if (~pre).any() else None},
        "costs_total": float(t["costs"].astype(float).sum()), "mean_contracts": float(t["contracts"].astype(float).mean())}
    daily = t.groupby("session")["pnl"].sum()
    eq = daily.cumsum()
    out["RISK"] = {"worst_session_pnl": float(daily.min()), "sessions_below_minus_daily_buffer": int((daily < -DAILY_BUFFER).sum()),
                   "max_drawdown_usd": float((eq - eq.cummax()).min()),
                   "worst_year": min(res.get("years", []), key=lambda y: y["sum"]) if res.get("years") else None,
                   "max_consecutive_losses": int(max((len(list(g_)) for k, g_ in __import__("itertools").groupby(pnl < 0) if k), default=0))}
    pr = rep.get("prop_report_only", {})
    out["PROP_ECONOMICS"] = {**pr, "label": ("PROP_STANDALONE_PASSABLE" if (pr.get("pass_rate") or 0) >= PROP_BREAKEVEN
                                             else "PROP_PORTFOLIO_COMPONENT_ONLY"),
                             "caveat": "Lucid rules as recorded in CLAUDE.md (2026-07 screenshots); must be re-verified live "
                                       "before any prop decision. Never alters the ALPHA verdict."}
    return out


if __name__ == "__main__":
    d = Path(sys.argv[1]).resolve()
    r = main(d)
    (d / "DHESI_V3_FINAL_REPORT_AXES.json").write_text(json.dumps(r, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(r, indent=1, default=str))
