"""Dhesi v3 ONE-SHOT validation harness, v2 (Agent 2). FIREWALLED.

A FINAL run executes only if EVERY check passes; any mismatch -> ABORT (exit 2) before the strategy is imported.

Chain of custody (one hash binds everything):
  BINDING = VALIDATION_BINDING_V1.json, written after Agent 1 freezes the spec/protocol:
    spec_path, spec_sha256              -> DHESI_V3_CANONICAL_SPEC_V1.md (+ its .sha256 file must agree)
    protocol_path, protocol_sha256      -> DHESI_V3_VALIDATION_PROTOCOL_V1.md
    strategy {module, class, kwargs}, strategy_sources {path: sha256}
    validator_sha256                    -> sha256 of THIS file
    dataset {path, sha256, family}, eval_window {start, end}
    secondary [...] (optional, run only as the protocol lists them; reported separately; never pooled into primary)
    criteria {...} copied from the protocol (the harness applies them mechanically)
  AUTHORIZATION.txt (owner) must contain:  OWNER_AUTHORIZATION=DHESI_V3_ONE_SHOT   and   BINDING_SHA256=<sha of binding>
  FRESHNESS_MANIFEST.json entry for the dataset: previously_read = "NO", sha256 equal to the dataset file
  data/trials_ledger.json: 0 entries of the same dataset_group whose data_window overlaps eval_window
  RUN_LOCK.json absent (one shot). A software-defect rerun needs --software-defect-rerun "<why>" and keeps the old run.

No partial output: nothing is printed or written about outcomes until the whole run finishes. No early stopping.
ALPHA and PROP are separate sections; the prop simulation cannot change the ALPHA verdict.
--gates-only: evaluate every check and exit (never imports or runs the strategy). Used by the firewall tests.
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
TOKEN = "OWNER_AUTHORIZATION=DHESI_V3_ONE_SHOT"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def _abs(p: str, base: Path) -> Path:
    q = Path(p)
    return q if q.is_absolute() else (base / q)


def check_gates(binding_p: Path, auth_p: Path, manifest_p: Path, ledger_p: Path, lock_p: Path,
                repo: Path = ROOT, validator_p: Path = Path(__file__).resolve(), rerun: str | None = None) -> dict:
    P = []
    if not binding_p.exists():
        return {"ok": False, "problems": ["binding file missing (canonical spec/protocol not frozen yet)"]}
    b = json.loads(binding_p.read_text(encoding="utf-8"))
    bsha = sha256(binding_p)
    # authorization token + binding hash
    auth = auth_p.read_text(encoding="utf-8") if auth_p.exists() else ""
    if TOKEN not in auth.splitlines():
        P.append("owner authorization token missing")
    if f"BINDING_SHA256={bsha}" not in auth.splitlines():
        P.append("authorization does not bind this binding file (hash mismatch)")
    # canonical spec + its .sha256 + protocol
    for key in ("spec", "protocol"):
        fp = _abs(b.get(f"{key}_path", ""), repo)
        if not fp.exists():
            P.append(f"{key} file missing: {fp}")
            continue
        if sha256(fp) != b.get(f"{key}_sha256"):
            P.append(f"{key} hash mismatch")
    spec_fp = _abs(b.get("spec_path", ""), repo)
    side = spec_fp.with_suffix(".sha256")
    if spec_fp.exists() and (not side.exists() or sha256(spec_fp) not in side.read_text(encoding="utf-8").lower()):
        P.append("spec .sha256 sidecar missing or disagrees")
    # strategy sources + validator self-hash
    for rel, h in b.get("strategy_sources", {}).items():
        fp = _abs(rel, repo)
        if not fp.exists() or sha256(fp) != h:
            P.append(f"strategy source changed/missing: {rel}")
    if sha256(validator_p) != b.get("validator_sha256"):
        P.append("validator (this harness) hash mismatch")
    # dataset + freshness manifest
    ds = b.get("dataset", {})
    dsp = _abs(ds.get("path", ""), repo)
    if not dsp.exists():
        P.append("dataset missing")
    elif sha256(dsp) != ds.get("sha256"):
        P.append("dataset hash mismatch vs binding")
    man = json.loads(manifest_p.read_text(encoding="utf-8")) if manifest_p.exists() else {}
    ent = next((e for e in man.get("datasets", []) if Path(e.get("path", "")).name == dsp.name), None)
    if ent is None:
        P.append("dataset not in freshness manifest")
    else:
        if ent.get("previously_read") != "NO":
            P.append("freshness: dataset previously read")
        if dsp.exists() and ent.get("sha256") != sha256(dsp):
            P.append("freshness manifest hash differs from dataset")
    # trial-ledger overlap (same dataset group, overlapping window)
    ew = b.get("eval_window", {})
    lo, hi = pd.Timestamp(ew.get("start", "1900-01-01")), pd.Timestamp(ew.get("end", "1900-01-01"))
    led = json.loads(ledger_p.read_text(encoding="utf-8")) if ledger_p.exists() else {"entries": []}
    group = ds.get("dataset_group", "CME_EQUITY_INDEX")
    ov = [e["id"] for e in led.get("entries", []) if e.get("dataset_group") == group
          and pd.Timestamp(e["data_window"]["start"]) <= hi and pd.Timestamp(e["data_window"]["end"]) >= lo]
    if ov:
        P.append(f"trial-ledger overlap: {ov[:5]}")
    # one-shot lock
    if lock_p.exists() and not rerun:
        P.append("RUN_LOCK exists: the one-shot run already happened")
    return {"ok": not P, "problems": P, "binding": b, "binding_sha256": bsha}


# ------------------------------------------------------------------ analysis (unchanged logic from v1, verified by dry run)
def boot_ci(x, B=10000, seed=11):
    rng = np.random.default_rng(seed)
    m = [rng.choice(x, len(x)).mean() for _ in range(B)] if len(x) else [np.nan]
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def block_boot_ci(pnl_by_day: pd.Series, block=20, B=10000, seed=13):
    """Stationary block bootstrap over trading days (mean per trade)."""
    rng = np.random.default_rng(seed)
    v = pnl_by_day.to_numpy()
    n = len(v)
    if n < 2:
        return [np.nan, np.nan]
    means = []
    for _ in range(B):
        idx, i = [], rng.integers(n)
        while len(idx) < n:
            idx.append(i)
            i = rng.integers(n) if rng.random() < 1 / block else (i + 1) % n
        means.append(v[idx].mean())
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def stats(p: pd.Series) -> dict:
    p = p.astype(float)
    if p.empty:
        return {"n": 0}
    w, l_ = p[p > 0], p[p < 0]
    eq = p.cumsum()
    return {"n": int(len(p)), "net_expectancy": float(p.mean()), "median": float(p.median()), "win_rate": float((p > 0).mean()),
            "payoff": float(w.mean() / -l_.mean()) if len(w) and len(l_) else None,
            "skew": float(p.skew()) if len(p) > 2 else None, "total": float(p.sum()), "max_dd": float((eq - eq.cummax()).min()),
            "largest_trade_share_of_net": float(p.max() / p.sum()) if p.sum() > 0 else None}


def analyze(t: pd.DataFrame, bars: pd.DataFrame, b: dict) -> dict:
    idx = bars.index
    mae, mfe = [], []
    for r in t.itertuples():
        w = bars[(idx >= r.entry_ts) & (idx <= r.exit_ts)]
        s = 1 if r.side > 0 else -1
        mae.append(np.nan if w.empty else ((r.entry_price - w.low.min()) if s > 0 else (w.high.max() - r.entry_price)))
        mfe.append(np.nan if w.empty else ((w.high.max() - r.entry_price) if s > 0 else (r.entry_price - w.low.min())))
    t = t.assign(mae_pts=mae, mfe_pts=mfe, year=t.entry_ts.dt.year, day=t.entry_ts.dt.date)
    tv, comm = b.get("tick_value", 0.5), b.get("commission_rt_per_contract", 1.0)
    fills = 2 + t.get("tp1_hit", pd.Series(False, index=t.index)).astype(bool).astype(int)
    out = {"overall": stats(t.pnl), "per_year": {int(y): stats(g.pnl) for y, g in t.groupby("year")},
           "bootstrap_ci95_iid": boot_ci(t.pnl.to_numpy(float)),
           "bootstrap_ci95_block20_days": block_boot_ci(t.groupby("day").pnl.mean()),
           "mae_mfe_points": {"mae_median": float(t.mae_pts.median()), "mfe_median": float(t.mfe_pts.median()),
                              "mae_p90": float(t.mae_pts.quantile(.9)), "mfe_p90": float(t.mfe_pts.quantile(.9))},
           "cost_sensitivity": {f"commission_x{k}": float((t.pnl - (k - 1) * comm * t.contracts).mean()) for k in (0, 1, 2, 3)},
           "slippage_sensitivity": {f"extra_ticks_per_fill_{k}": float((t.pnl - k * tv * t.contracts * fills).mean()) for k in (0, 1, 2, 3)}}
    vol = bars.volume.reindex(t.entry_ts.dt.floor("min")).to_numpy()
    out["capacity"] = {"median_contracts": float(t.contracts.median()),
                       "median_share_of_entry_bar_volume": float(np.nanmedian(t.contracts.to_numpy() / np.maximum(vol, 1)))}
    yrs = [v for v in out["per_year"].values() if v["n"] >= b.get("criteria", {}).get("min_trades_per_year_counted", 10)]
    out["year_consistency"] = {"years_counted": len(yrs), "positive": int(sum(v["total"] > 0 for v in yrs))}
    out["achieved_power_note"] = "report only; see protocol"
    c = b.get("criteria", {})
    ov, lo, hi = out["overall"], *out["bootstrap_ci95_block20_days"]
    frac_pos = (out["year_consistency"]["positive"] / out["year_consistency"]["years_counted"]) if yrs else 0
    reasons = []
    if not (ov["net_expectancy"] > 0): reasons.append("mean<=0")
    if not (lo > 0): reasons.append("block_boot_lower<=0")
    if frac_pos < c.get("min_positive_year_fraction", 0.6): reasons.append("year_consistency")
    if (ov.get("largest_trade_share_of_net") or 0) > c.get("max_single_trade_share", 0.25): reasons.append("single_trade_dominance")
    if ov["net_expectancy"] <= 0 or hi < c.get("fail_if_upper_below", 20.0):
        verdict = "FAIL"
    elif not reasons:
        verdict = "PASS"
    else:
        verdict = "INCONCLUSIVE"
    out["ALPHA_VERDICT"] = {"verdict": verdict, "unmet": reasons, "criteria_applied": c}
    return out, t


def prop_sim(t: pd.DataFrame, b: dict) -> dict:
    daily = t.groupby(t.entry_ts.dt.date).pnl.sum().to_numpy(float)
    rng = np.random.default_rng(17)
    sessions = pd.bdate_range(t.entry_ts.min().date(), t.entry_ts.max().date())
    p_trade = len(daily) / max(len(sessions), 1)
    tgt, mll, days_max = b.get("lucid_target", 3000.0), b.get("lucid_mll", 2000.0), b.get("lucid_max_days", 250)
    r = {"pass": 0, "fail_mll": 0, "timeout": 0}
    for _ in range(10000):
        bal = peak = 0.0
        for _d in range(days_max):
            if rng.random() < p_trade:
                bal += rng.choice(daily)
            peak = max(peak, bal)
            if bal >= tgt: r["pass"] += 1; break
            floor = min(max(peak - mll, -mll), 0.0)          # EOD-trailing MLL; locks at starting balance
            if bal <= floor: r["fail_mll"] += 1; break
        else:
            r["timeout"] += 1
    return {k: v / 10000 for k, v in r.items()} | {"note": "PROP ONLY; cannot alter ALPHA_VERDICT"}


def run_market(b: dict, market: dict) -> dict:
    sys.path.insert(0, str(ROOT))
    s = b["strategy"]
    model = getattr(importlib.import_module(s["module"]), s["class"])(**{**s.get("kwargs", {}), **market.get("kwargs_override", {})})
    bars = pd.read_parquet(_abs(market["path"], ROOT))
    bars.index = pd.to_datetime(bars.index, utc=True)
    t = pd.DataFrame(model._run_backtest(bars).trades)
    ew = b["eval_window"]
    if not t.empty:
        t["entry_ts"] = pd.to_datetime(t["entry_ts"], utc=True); t["exit_ts"] = pd.to_datetime(t["exit_ts"], utc=True)
        t = t[(t.entry_ts >= pd.Timestamp(ew["start"], tz="UTC")) & (t.entry_ts <= pd.Timestamp(ew["end"], tz="UTC") + pd.Timedelta(days=1))]
        t = t.sort_values("entry_ts").reset_index(drop=True)
    if t.empty:
        return {"ALPHA": {"ALPHA_VERDICT": {"verdict": "INCONCLUSIVE", "unmet": ["0 trades"]}}, "trades": t}
    alpha, t = analyze(t, bars, b)
    return {"ALPHA": alpha, "PROP_LUCID_SEPARATE": prop_sim(t, b), "trades": t}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--binding", default=str(HERE / "VALIDATION_BINDING_V1.json"))
    ap.add_argument("--auth", default=str(HERE / "AUTHORIZATION.txt"))
    ap.add_argument("--manifest", default=str(HERE / "FRESHNESS_MANIFEST.json"))
    ap.add_argument("--ledger", default=str(ROOT / "data" / "trials_ledger.json"))
    ap.add_argument("--lock", default=str(HERE / "RUN_LOCK.json"))
    ap.add_argument("--gates-only", action="store_true")
    ap.add_argument("--software-defect-rerun", default=None)
    a = ap.parse_args()
    g = check_gates(Path(a.binding), Path(a.auth), Path(a.manifest), Path(a.ledger), Path(a.lock), rerun=a.software_defect_rerun)
    if not g["ok"]:
        print(json.dumps({"ABORT": g["problems"]}, indent=1)); sys.exit(2)
    if a.gates_only:
        print(json.dumps({"GATES": "ALL PASS", "binding_sha256": g["binding_sha256"]})); return
    b = g["binding"]
    run_id = "FINAL_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = HERE / "runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=False)
    Path(a.lock).write_text(json.dumps({"run_id": run_id, "binding_sha256": g["binding_sha256"],
                                        "software_defect_rerun": a.software_defect_rerun}, indent=1))
    report = {"run_id": run_id, "binding_sha256": g["binding_sha256"], "primary": {}, "secondary": {}}
    prim = run_market(b, b["dataset"])                        # PRIMARY: NQ/MNQ family only, run first
    prim["trades"].to_csv(out_dir / "PRIMARY_trade_ledger.csv", index=False)
    report["primary"] = {k: v for k, v in prim.items() if k != "trades"}
    for m in b.get("secondary", []):                          # SECONDARY: only as listed in the frozen protocol
        r = run_market(b, m)
        r["trades"].to_csv(out_dir / f"SECONDARY_{m['name']}_trade_ledger.csv", index=False)
        report["secondary"][m["name"]] = {k: v for k, v in r.items() if k != "trades"}
    (out_dir / "report.json").write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps({"run_id": run_id, "primary_alpha": report["primary"]["ALPHA"]["ALPHA_VERDICT"],
                      "secondary_alpha": {k: v["ALPHA"]["ALPHA_VERDICT"] for k, v in report["secondary"].items()}}, indent=1, default=str))


if __name__ == "__main__":
    main()
