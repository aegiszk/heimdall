"""Dhesi ONE-SHOT validation harness (Agent 2). Built before any untouched-data outcome exists.

Refuses to run a FINAL validation unless ALL of the following hold:
  1. AUTH file (written by Agent 1 / owner) contains the exact line `REOPEN_APPROVED` and a `SPEC_SHA256=<hex>` line;
  2. the canonical spec file hashes to that SPEC_SHA256, and every source file it lists matches its recorded hash;
  3. the freshness manifest lists the dataset with matching SHA-256, `previously_read: NO`, and trial_ledger_overlap 0;
  4. no RUN_LOCK exists (one run only). A second run requires --software-defect-rerun "<description>" and preserves the
     failed run directory untouched.
--dry-run-dev runs the same pipeline on ALREADY-SEEN development data only (plumbing test), labelled DRY_RUN_DEV;
it never reads the untouched dataset.

ALPHA and PROP are separate outputs. The prop Monte Carlo can never change the ALPHA verdict.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TICK = 0.25


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- gates
def check_gates(spec_path: Path, auth_path: Path, manifest_path: Path, dataset: Path) -> dict:
    problems = []
    auth = auth_path.read_text(encoding="utf-8") if auth_path.exists() else ""
    if "REOPEN_APPROVED" not in auth.split():
        problems.append("AUTH missing REOPEN_APPROVED")
    want = next((ln.split("=", 1)[1].strip() for ln in auth.splitlines() if ln.startswith("SPEC_SHA256=")), None)
    got = sha256(spec_path) if spec_path.exists() else None
    if not want or want.lower() != (got or "").lower():
        problems.append(f"spec hash mismatch: auth={want} file={got}")
    spec = json.loads(spec_path.read_text(encoding="utf-8")) if spec_path.exists() else {}
    for rel, h in spec.get("source_sha256", {}).items():
        if sha256(ROOT / rel).lower() != h.lower():
            problems.append(f"source changed after freeze: {rel}")
    man = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    entry = next((e for e in man.get("datasets", []) if Path(e["path"]).name == dataset.name), None)
    if entry is None:
        problems.append("dataset not in freshness manifest")
    else:
        if entry.get("previously_read") != "NO":
            problems.append("dataset previously read -> cannot be final validation")
        if int(entry.get("trial_ledger_overlap", 1)) != 0:
            problems.append("trial-ledger overlap nonzero")
        if sha256(dataset).lower() != entry.get("sha256", "").lower():
            problems.append("dataset hash differs from manifest")
    return {"ok": not problems, "problems": problems, "spec": spec, "manifest_entry": entry}


# --------------------------------------------------------------------------- strategy
def run_strategy(spec: dict, bars: pd.DataFrame) -> pd.DataFrame:
    sys.path.insert(0, str(ROOT))
    mod = importlib.import_module(spec["module"])
    model = getattr(mod, spec["class"])(**spec.get("kwargs", {}))
    res = model._run_backtest(bars)
    t = pd.DataFrame(res.trades)
    if t.empty:
        return t
    t["entry_ts"] = pd.to_datetime(t["entry_ts"])
    t["exit_ts"] = pd.to_datetime(t["exit_ts"])
    return t.sort_values("entry_ts").reset_index(drop=True)


# --------------------------------------------------------------------------- metrics
def mae_mfe(t: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    idx = bars.index
    out_mae, out_mfe = [], []
    for r in t.itertuples():
        w = bars[(idx >= r.entry_ts) & (idx <= r.exit_ts)]
        if w.empty:
            out_mae.append(np.nan); out_mfe.append(np.nan); continue
        s = 1 if r.side > 0 else -1
        fav = (w.high.max() - r.entry_price) if s > 0 else (r.entry_price - w.low.min())
        adv = (r.entry_price - w.low.min()) if s > 0 else (w.high.max() - r.entry_price)
        out_mae.append(adv); out_mfe.append(fav)
    return t.assign(mae_pts=out_mae, mfe_pts=out_mfe)


def boot_ci(x: np.ndarray, B: int = 10000, seed: int = 11) -> list:
    rng = np.random.default_rng(seed)
    m = [rng.choice(x, len(x)).mean() for _ in range(B)] if len(x) else [np.nan]
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def cluster_boot_ci(x: pd.Series, groups: pd.Series, B: int = 10000, seed: int = 13) -> list:
    rng = np.random.default_rng(seed)
    g = pd.DataFrame({"x": x, "g": groups}).groupby("g").x.agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy()
    if len(g) < 2:
        return [np.nan, np.nan]
    m = []
    for _ in range(B):
        i = rng.integers(0, len(g), len(g))
        m.append(s[i].sum() / c[i].sum())
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def stats(p: pd.Series) -> dict:
    p = p.astype(float)
    if p.empty:
        return {"n": 0}
    wins, losses = p[p > 0], p[p < 0]
    eq = p.cumsum()
    return {"n": int(len(p)), "net_expectancy": float(p.mean()), "median": float(p.median()),
            "win_rate": float((p > 0).mean()),
            "payoff": float(wins.mean() / -losses.mean()) if len(wins) and len(losses) else None,
            "skew": float(p.skew()) if len(p) > 2 else None, "total": float(p.sum()),
            "max_dd": float((eq - eq.cummax()).min())}


def legs(t: pd.DataFrame) -> pd.Series:
    """Fills per trade: entry + exit, plus one extra exit leg when TP1 trimmed half."""
    return 2 + t.get("tp1_hit", pd.Series(False, index=t.index)).astype(bool).astype(int)


def analyze(t: pd.DataFrame, bars: pd.DataFrame, spec: dict) -> dict:
    t = mae_mfe(t, bars)
    t["year"] = t.entry_ts.dt.year
    tv = spec.get("tick_value", 0.5)
    comm = spec.get("commission_rt_per_contract", 1.0)
    out = {"overall": stats(t.pnl)}
    out["per_year"] = {int(y): stats(g.pnl) for y, g in t.groupby("year")}
    out["per_instrument_family"] = {spec.get("instrument_family", "MNQ"): stats(t.pnl)}
    out["bootstrap_ci95_iid"] = boot_ci(t.pnl.to_numpy(float))
    out["bootstrap_ci95_year_cluster"] = cluster_boot_ci(t.pnl, t.year)
    yrs = out["per_year"]
    out["year_consistency"] = {"years": len(yrs), "positive_years": int(sum(1 for v in yrs.values() if v.get("total", 0) > 0))}
    out["mae_mfe_points"] = {"mae_median": float(t.mae_pts.median()), "mae_p90": float(t.mae_pts.quantile(.9)),
                             "mfe_median": float(t.mfe_pts.median()), "mfe_p90": float(t.mfe_pts.quantile(.9))}
    fills = legs(t)
    out["cost_sensitivity"] = {f"commission_x{k}": float((t.pnl - (k - 1) * comm * t.contracts).mean()) for k in (0, 1, 2, 3)}
    out["slippage_sensitivity"] = {f"extra_ticks_per_fill_{k}": float((t.pnl - k * tv * t.contracts * fills).mean()) for k in (0, 1, 2, 3)}
    vol = bars.volume.reindex(t.entry_ts.dt.floor("min")).to_numpy()
    out["capacity"] = {"median_contracts": float(t.contracts.median()),
                       "median_entry_bar_volume": float(np.nanmedian(vol)) if len(vol) else None,
                       "median_share_of_entry_bar_volume": float(np.nanmedian(t.contracts.to_numpy() / np.maximum(vol, 1)))}
    crit = spec.get("alpha_pass_criteria", {})
    reasons = []
    ov = out["overall"]
    if ov["n"] < crit.get("min_trades", 30):
        verdict = "INCONCLUSIVE_UNDERPOWERED"
    else:
        if ov["net_expectancy"] <= crit.get("min_net_expectancy_usd", 20.0):
            reasons.append("net_expectancy")
        if out["bootstrap_ci95_year_cluster"][0] <= 0:
            reasons.append("year_cluster_ci_lower<=0")
        if out["year_consistency"]["positive_years"] < crit.get("min_positive_years", 4):
            reasons.append("year_consistency")
        verdict = "ALPHA_PASS" if not reasons else "ALPHA_FAIL"
    out["ALPHA_VERDICT"] = {"verdict": verdict, "fail_reasons": reasons, "criteria": crit}
    return out, t


def prop_sim(t: pd.DataFrame, spec: dict) -> dict:
    """Separate Lucid simulation: session-block bootstrap of daily PnL (not iid trades). Never feeds ALPHA."""
    daily = t.groupby(t.entry_ts.dt.date).pnl.sum().to_numpy(float)
    if len(daily) == 0:
        return {"note": "no trades"}
    rng = np.random.default_rng(17)
    target, mll, days_max = spec.get("lucid_target", 3000.0), spec.get("lucid_mll", 2000.0), spec.get("lucid_max_days", 250)
    sessions = pd.bdate_range(t.entry_ts.min().date(), t.entry_ts.max().date())
    p_trade = len(daily) / max(len(sessions), 1)
    res = {"pass": 0, "fail_mll": 0, "timeout": 0}
    for _ in range(10000):
        bal, peak, floor = 0.0, 0.0, -mll
        for _d in range(days_max):
            if rng.random() < p_trade:
                bal += rng.choice(daily)
            peak = max(peak, bal)
            floor = max(floor, min(peak - mll, 0.0))
            if bal >= target: res["pass"] += 1; break
            if bal <= floor: res["fail_mll"] += 1; break
        else:
            res["timeout"] += 1
    return {k: v / 10000 for k, v in res.items()} | {"sizing": "as produced by the frozen strategy (not rescaled)",
                                                     "note": "PROP only; cannot alter ALPHA_VERDICT"}


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--eval-start", required=True)
    ap.add_argument("--eval-end", required=True)
    ap.add_argument("--auth", default=str(HERE / "AUTHORIZATION.txt"))
    ap.add_argument("--manifest", default=str(HERE / "FRESHNESS_MANIFEST.json"))
    ap.add_argument("--dry-run-dev", action="store_true")
    ap.add_argument("--software-defect-rerun", default=None)
    a = ap.parse_args()
    spec_p, ds = Path(a.spec), Path(a.dataset)
    lock = HERE / "RUN_LOCK.json"
    if not a.dry_run_dev:
        g = check_gates(spec_p, Path(a.auth), Path(a.manifest), ds)
        if not g["ok"]:
            print(json.dumps({"REFUSED": g["problems"]}, indent=1)); sys.exit(2)
        if lock.exists() and not a.software_defect_rerun:
            print(json.dumps({"REFUSED": ["RUN_LOCK exists: final validation already run once"]})); sys.exit(3)
        spec = g["spec"]
    else:
        spec = json.loads(spec_p.read_text(encoding="utf-8"))
    run_id = ("DRY_RUN_DEV_" if a.dry_run_dev else "FINAL_") + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = HERE / "runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=False)
    if not a.dry_run_dev:
        lock.write_text(json.dumps({"run_id": run_id, "spec_sha256": sha256(spec_p), "dataset_sha256": sha256(ds),
                                    "software_defect_rerun": a.software_defect_rerun}, indent=1))
    bars = pd.read_parquet(ds)
    bars.index = pd.to_datetime(bars.index, utc=True)
    t = run_strategy(spec, bars)
    lo, hi = pd.Timestamp(a.eval_start, tz="UTC"), pd.Timestamp(a.eval_end, tz="UTC")
    if not t.empty:
        et = t.entry_ts.dt.tz_convert("UTC") if t.entry_ts.dt.tz is not None else t.entry_ts.dt.tz_localize("UTC")
        t = t[(et >= lo) & (et <= hi)].reset_index(drop=True)
    report = {"run_id": run_id, "spec_sha256": sha256(spec_p), "dataset": str(ds), "dataset_sha256": sha256(ds),
              "eval_window": [a.eval_start, a.eval_end], "label": "DRY_RUN_DEV (already-seen data; NOT evidence)" if a.dry_run_dev else "FINAL"}
    if t.empty:
        report["ALPHA_VERDICT"] = {"verdict": "INCONCLUSIVE_UNDERPOWERED", "fail_reasons": ["0 trades"]}
    else:
        alpha, t = analyze(t, bars, spec)
        report["ALPHA"] = alpha
        report["PROP_LUCID_SEPARATE"] = prop_sim(t, spec)
        t.to_csv(out_dir / "trade_ledger.csv", index=False)
    (out_dir / "report.json").write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps({"run_id": run_id, "alpha": (report.get("ALPHA") or report).get("ALPHA_VERDICT"),
                      "prop": report.get("PROP_LUCID_SEPARATE")}, indent=1, default=str))


if __name__ == "__main__":
    main()
