"""Frozen evaluator for TRIDENT_V2 / MMXM_V2. Written and hashed BEFORE any V2 PnL.

  python evaluate_v2.py dev    <MODEL>   FX/XAU DEV 2022-01-01..2024-12-31 (development gate)
  python evaluate_v2.py sealed <MODEL>   FX/XAU SEALED 2025-01-01..2026-08-31, ONE SHOT. Refuses unless:
        - DEV_RESULT_<MODEL>.json exists with dev_gate == "PASS";
        - AGENT2_V2_AUDIT.json exists with <MODEL> == "PASS" (independent spec-vs-transcript audit);
        - the trial id V2-<MODEL>-SEALED is registered in data/trials_ledger.json;
        - no SEALED_RESULT_<MODEL>.json exists yet (one shot);
        - the frozen hashes in V2_PREREG_MANIFEST.json match the current files.
Pooled evaluation: one model = one trial = all its instruments together (R units).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "external_strategies" / "common"))
import harness as hz  # noqa: E402
import registry as rg  # noqa: E402
import stats as stx  # noqa: E402

WINDOWS = {"dev": (pd.Timestamp("2022-01-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")),
           "sealed": (pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2026-09-01", tz="UTC"))}
WARMUP = pd.Timedelta(days=45)          # indicator warm-up rows before the window (signals only counted inside)
BAR = {"TRIDENT_V2": "30min", "MMXM_V2": "15min"}

# ------------------------------------------------------------------ frozen gates
DEV_GATE = dict(n_min=30, nw_t_min=1.5, boot_share_pos_min=0.80, median_floor_R=-1.05, year_pos_share=2 / 3,
                year_min_trades=5)
SEALED_GATE = dict(max_single_trade_share=0.25, period_pos_share=2 / 3, period_min_trades=3)


def load(model: str):
    d = HERE / model.lower()
    spec = importlib.util.spec_from_file_location(model.lower(), d / "strategy.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[model.lower()] = m
    spec.loader.exec_module(m)
    return m


def data(pair: str, window: str) -> pd.DataFrame:
    lo, hi = WINDOWS[window]
    d = hz.load_fx(pair)
    if window == "dev":
        assert d.index.max() >= lo
    return d[(d.index >= lo - WARMUP) & (d.index < hi)]


def orders(model: str, mod, m1: pd.DataFrame, pair: str):
    if model == "TRIDENT_V2":
        return mod.generate(m1, mod.Cfg(), pair, rg.PIP[pair])
    return mod.generate(m1, mod.Cfg())


def run(model: str, window: str, spec_k: float = 1.0, stop_slip_k: float = 1.0, delay: bool = False) -> pd.DataFrame:
    mod = load(model)
    lo, hi = WINDOWS[window]
    frames = []
    for pair in mod.PAIRS:
        m1 = data(pair, window)
        ods = [o for o in orders(model, mod, m1, pair) if lo <= o.t_signal < hi]
        if delay:
            ods = [replace(o, t_signal=o.t_signal + pd.Timedelta(BAR[model]),
                           entry_type="market" if o.entry_type == "close_at" else o.entry_type) for o in ods]
        base = hz.SPECS[pair]
        spec = hz.scaled_spec(base, spec_k)
        if stop_slip_k != 1.0:
            spec = hz.Spec(spec.name, spec.tick, spec.point_value, spec.comm_rt, spec.slip * stop_slip_k, spec.spread,
                           spec.limit_through, spec.kind)
        df = hz.trades_frame(hz.run_sequenced(hz.Book(m1, spec), ods), base)
        if len(df):
            frames.append(df.assign(pair=pair))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _boot_share_pos(df: pd.DataFrame) -> float:
    day = (pd.to_datetime(df["t_entry"], utc=True).dt.tz_convert(hz.ET).dt.tz_localize(None) + pd.Timedelta(hours=7)).dt.normalize()
    b = stx.cluster_bootstrap_mean_ci(df["R"].to_numpy(float), clusters=day.to_numpy(), n_boot=4000, seed=7, alpha=0.025)
    return float((b["_boot_means"] > 0).mean()), b["ci_lo"], b["ci_hi"]


def metrics(model: str, window: str) -> dict:
    df = run(model, window)
    if len(df) == 0:
        return {"n": 0}, df
    s = stx.summarize(df)
    R = np.sort(df["R"].to_numpy(float))
    k = int(len(R) * 0.10)
    share_pos, lo95, hi95 = _boot_share_pos(df)
    tot = df["R"].sum()
    s.update({
        "trimmed_mean_10pct": float(R[k:len(R) - k].mean()) if len(R) > 2 * k else None,
        "boot_share_means_pos": share_pos, "boot95_lo": lo95, "boot95_hi": hi95,
        "drop_top5_mean_R": stx.drop_top(df, k=5),
        "max_single_trade_share": float(df["R"].max() / tot) if tot > 0 else None,
        "cost_x1.5_mean_R": float(run(model, window, spec_k=1.5)["R"].mean()),
        "cost_x2_mean_R": float(run(model, window, spec_k=2.0)["R"].mean()),
        "one_bar_delay_mean_R": float(run(model, window, delay=True)["R"].mean()),
        "stop_slip_x3_mean_R": float(run(model, window, stop_slip_k=3.0)["R"].mean()),
        "by_pair": df.groupby("pair")["R"].agg(["count", "mean"]).round(4).to_dict("index"),
    })
    return s, df


def dev_gate(s: dict) -> dict:
    g = DEV_GATE
    years = [y for y in s.get("by_year", []) if y["count"] >= g["year_min_trades"]]
    ypos = (sum(y["sum"] > 0 for y in years) / len(years)) if years else 0.0
    checks = {
        "n_ge_30": s["n"] >= g["n_min"],
        "mean_R_gt_0": s["mean_R"] > 0,
        "median_not_catastrophic": s["median_R"] >= g["median_floor_R"],
        "drop_top5_gt_0": (s["drop_top5_mean_R"] or -1) > 0,
        "nw_t_gt_1_5": s["nw_t"] > g["nw_t_min"],
        "bootstrap_central_positive": s["boot_share_means_pos"] >= g["boot_share_pos_min"],
        "cost_x1_5_gt_0": s["cost_x1.5_mean_R"] > 0,
        "years_2_3_positive": len(years) >= 2 and ypos >= g["year_pos_share"],
    }
    return {"checks": checks, "eligible_years": len(years), "year_pos_share": ypos,
            "dev_gate": "PASS" if all(checks.values()) else "FAIL"}


def sealed_verdict(s: dict, df: pd.DataFrame) -> dict:
    g = SEALED_GATE
    half = pd.to_datetime(df["t_entry"], utc=True)
    per = (half.dt.year.astype(str) + "H" + np.where(half.dt.month <= 6, "1", "2"))
    ps = df.assign(p=per.to_numpy()).groupby("p")["R"].agg(["count", "sum"])
    ps = ps[ps["count"] >= g["period_min_trades"]]
    ppos = float((ps["sum"] > 0).mean()) if len(ps) else 0.0
    checks = {
        "mean_R_gt_0": s["mean_R"] > 0,
        "boot95_lo_gt_0": s["boot95_lo"] > 0,
        "drop_top5_gt_0": (s["drop_top5_mean_R"] or -1) > 0,
        "cost_x1_5_gt_0": s["cost_x1.5_mean_R"] > 0,
        "max_single_trade_share_le_25pct": s["max_single_trade_share"] is not None and s["max_single_trade_share"] <= g["max_single_trade_share"],
        "periods_mostly_positive": len(ps) >= 2 and ppos >= g["period_pos_share"],
    }
    if all(checks.values()):
        v = "PASS"
    elif s["mean_R"] <= 0 or s["boot95_hi"] < 0.05:
        v = "FAIL"
    else:
        v = "INCONCLUSIVE"
    return {"checks": checks, "eligible_half_years": int(len(ps)), "half_year_pos_share": ppos, "verdict": v,
            "execution_note": "FX costs are research assumptions (raw-ECN spread + 0.2 pip + $7/lot); plausibility to be "
                              "confirmed by the CME translation study before any deployment"}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_manifest():
    man = json.loads((HERE / "V2_PREREG_MANIFEST.json").read_text())
    bad = {k: v for k, v in man["files"].items() if _sha(ROOT / k) != v}
    if bad:
        raise SystemExit(f"FROZEN FILES CHANGED: {list(bad)}")
    return man


def main():
    mode, model = sys.argv[1], sys.argv[2]
    assert model in BAR
    man = check_manifest()
    if mode == "dev":
        s, df = metrics(model, "dev")
        res = {"model": model, "window": "dev", "prereg_aggregate": man["aggregate_sha256"], "metrics": s}
        res.update(dev_gate(s) if s.get("n") else {"dev_gate": "FAIL", "checks": {"n_ge_30": False}})
        df.to_csv(HERE / f"DEV_TRADES_{model}.csv", index=False)
        (HERE / f"DEV_RESULT_{model}.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        print(json.dumps({k: res[k] for k in ("model", "dev_gate", "checks")}, indent=1, default=str))
        return
    if mode == "sealed":
        out = HERE / f"SEALED_RESULT_{model}.json"
        if out.exists():
            raise SystemExit("ONE SHOT: sealed result already exists")
        dev = json.loads((HERE / f"DEV_RESULT_{model}.json").read_text())
        if dev.get("dev_gate") != "PASS":
            raise SystemExit("dev gate not PASS: sealed window stays sealed")
        audit = HERE / "AGENT2_V2_AUDIT.json"
        if not audit.exists() or json.loads(audit.read_text()).get(model) != "PASS":
            raise SystemExit("Agent 2 V2 audit PASS missing")
        led = json.loads((ROOT / "data" / "trials_ledger.json").read_text())["entries"]
        if not any(e["id"] == f"V2-{model}-SEALED" for e in led):
            raise SystemExit(f"trial V2-{model}-SEALED not registered")
        s, df = metrics(model, "sealed")
        res = {"model": model, "window": "sealed", "prereg_aggregate": man["aggregate_sha256"], "metrics": s}
        res.update(sealed_verdict(s, df) if s.get("n") else {"verdict": "INCONCLUSIVE", "reason": "zero trades"})
        df.to_csv(HERE / f"SEALED_TRADES_{model}.csv", index=False)
        out.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        print(json.dumps({k: res.get(k) for k in ("model", "verdict", "checks")}, indent=1, default=str))


if __name__ == "__main__":
    main()
