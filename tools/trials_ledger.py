"""Global, machine-readable, APPEND-ONLY trials ledger (data/trials_ledger.json).

Every strategy configuration that read a data window's outcomes is a trial. The ledger feeds the
DEPLOYMENT gate (core/validation/gates.py): nb_trials, empirical sr_trials_var, and whether the
candidate's data window is FRESH (never read) or already REUSED.

Append-only: register_trial() refuses an existing id; each entry carries prev_hash/entry_hash (SHA-256
hash chain) so verify_ledger() detects any in-place edit, deletion or reorder.

Window semantics: windows are compared within a `dataset_group` (e.g. all CME equity-index futures share
one group: reading ES outcomes over a period contaminates an MNQ holdout over the same period; this is the
grouping used by VALIDATION_COMPLETION_2026-09-23.md section 7, which counted MNQ+MES+ES reads together).
Date-only bounds are inclusive whole days.

CLI:  python tools/trials_ledger.py --seed      (write the seed ledger; refuses to overwrite)
      python tools/trials_ledger.py --summary   (print per-window counts / variance)
      python tools/trials_ledger.py --verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "data" / "trials_ledger.json"
SCHEMA_VERSION = 1
WINDOW_STATUSES = ("DEV", "REUSED_HOLDOUT", "FRESH", "PROSPECTIVE")
REQUIRED = ("id", "family", "dataset", "dataset_group", "data_window", "window_status", "n_configs", "verdict")

IDX = "CME_EQUITY_INDEX"
HOLDOUT_6040 = {"start": "2025-09-11", "end": "2026-06-30"}


# --------------------------------------------------------------------------- windows
def _bounds(window) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Half-open [start, end_excl) in naive UTC. Date-only end is inclusive of that whole day."""
    if isinstance(window, dict):
        s, e = window["start"], window["end"]
    else:
        s, e = window
    ts = pd.Timestamp(s)
    te = pd.Timestamp(e)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    if te.tzinfo is not None:
        te = te.tz_convert("UTC").tz_localize(None)
    if len(str(e)) == 10:
        te = te + pd.Timedelta(days=1)
    if te <= ts:
        raise ValueError(f"empty/inverted window {window}")
    return ts, te


def windows_overlap(a, b) -> bool:
    a0, a1 = _bounds(a)
    b0, b1 = _bounds(b)
    return a0 < b1 and b0 < a1


# --------------------------------------------------------------------------- hashing / io
def _entry_hash(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "entry_hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_ledger(path: Path | str = LEDGER_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        return {"schema_version": SCHEMA_VERSION, "entries": []}
    return json.loads(p.read_text(encoding="utf-8"))


def verify_ledger(ledger: dict) -> list[str]:
    """Return a list of integrity problems (empty = OK)."""
    problems, prev, seen = [], "GENESIS", set()
    for i, e in enumerate(ledger.get("entries", [])):
        if e.get("id") in seen:
            problems.append(f"duplicate id {e.get('id')} at {i}")
        seen.add(e.get("id"))
        if e.get("prev_hash") != prev:
            problems.append(f"broken chain at {i} ({e.get('id')})")
        if _entry_hash(e) != e.get("entry_hash"):
            problems.append(f"hash mismatch at {i} ({e.get('id')}): entry edited")
        prev = e.get("entry_hash")
    return problems


def _atomic_write(path: Path, ledger: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def _validate(entry: dict) -> None:
    missing = [k for k in REQUIRED if k not in entry]
    if missing:
        raise ValueError(f"trial missing fields {missing}")
    if entry["window_status"] not in WINDOW_STATUSES:
        raise ValueError(f"window_status must be one of {WINDOW_STATUSES}")
    _bounds(entry["data_window"])
    if int(entry["n_configs"]) < 1:
        raise ValueError("n_configs must be >= 1")


def register_trial(entry: dict, path: Path | str = LEDGER_PATH, registered_at: str | None = None) -> dict:
    """Append one trial. Refuses an existing id (no edits) and refuses a ledger whose chain is broken."""
    p = Path(path)
    ledger = load_ledger(p)
    problems = verify_ledger(ledger)
    if problems:
        raise RuntimeError(f"ledger integrity failure, refusing to append: {problems[:3]}")
    if any(e["id"] == entry["id"] for e in ledger["entries"]):
        raise ValueError(f"trial id {entry['id']!r} already registered; ledger is append-only")
    e = {"sr_per_trade": None, "n_trades": None, "is_null_control": False, "source": None, "notes": None,
         **{k: v for k, v in entry.items() if k not in ("prev_hash", "entry_hash")}}
    _validate(e)
    e["registered_at"] = registered_at or e.get("registered_at") or pd.Timestamp.now("UTC").isoformat()
    e["prev_hash"] = ledger["entries"][-1]["entry_hash"] if ledger["entries"] else "GENESIS"
    e["entry_hash"] = _entry_hash(e)
    ledger["entries"].append(e)
    _atomic_write(p, ledger)
    return e


# --------------------------------------------------------------------------- queries
def trials_for_window(window, dataset_group: str, ledger: dict | None = None, *,
                      include_null_controls: bool = False, exclude_ids=()) -> list[dict]:
    led = ledger if ledger is not None else load_ledger()
    out = []
    for e in led["entries"]:
        if e["dataset_group"] != dataset_group or e["id"] in exclude_ids:
            continue
        if e.get("is_null_control") and not include_null_controls:
            continue
        if windows_overlap(e["data_window"], window):
            out.append(e)
    return out


def nb_trials(window, dataset_group: str, ledger: dict | None = None, mode: str = "configs",
              exclude_ids=()) -> int:
    """Trials that read an overlapping window. mode='configs' (sum n_configs; conservative, larger SR0)
    or 'families' (distinct families). Null controls are looks, not candidates, and are excluded."""
    ts = trials_for_window(window, dataset_group, ledger, exclude_ids=exclude_ids)
    if mode == "configs":
        return int(sum(int(e["n_configs"]) for e in ts))
    if mode == "families":
        return int(len({e["family"] for e in ts}))
    raise ValueError("mode must be 'configs' or 'families'")


def empirical_sr_trials_var(window, dataset_group: str, ledger: dict | None = None, min_n: int = 30,
                            exclude_ids=()) -> float | None:
    """Sample variance (ddof=1) of per-trade Sharpe across overlapping trials with n_trades >= min_n and a
    known SR. None if fewer than 2 such trials. Callers floor it at 1/N (gates.deployment_gate does)."""
    ts = trials_for_window(window, dataset_group, ledger, exclude_ids=exclude_ids)
    srs = [float(e["sr_per_trade"]) for e in ts
           if e.get("sr_per_trade") is not None and (e.get("n_trades") or 0) >= min_n]
    return float(np.var(srs, ddof=1)) if len(srs) >= 2 else None


def window_is_fresh(window, dataset_group: str, ledger: dict | None = None, exclude_ids=()) -> bool:
    """True iff no ledger trial (null controls included: they are looks) read an overlapping window in
    this dataset_group. Pass the candidate's own id in exclude_ids once it is registered."""
    return not trials_for_window(window, dataset_group, ledger, include_null_controls=True,
                                 exclude_ids=exclude_ids)


def gate_inputs(window, dataset_group: str, ledger: dict | None = None, declared_status: str | None = None,
                mode: str = "configs", candidate_id: str | None = None) -> dict:
    """Inputs for core.validation.gates.deployment_gate. window_status is DERIVED: a window any other trial
    has read is REUSED_HOLDOUT regardless of what the caller declares; PROSPECTIVE is honoured only on a
    fresh window."""
    excl = (candidate_id,) if candidate_id else ()
    fresh = window_is_fresh(window, dataset_group, ledger, exclude_ids=excl)
    if not fresh:
        status = "DEV" if declared_status == "DEV" else "REUSED_HOLDOUT"
    else:
        status = "PROSPECTIVE" if declared_status == "PROSPECTIVE" else "FRESH"
    n_cand = 0 if candidate_id else 1  # count the candidate itself if it is not registered yet
    return {"window_status": status,
            "nb_trials": nb_trials(window, dataset_group, ledger, mode, ()) + n_cand,
            "ledger_sr_trials_var": empirical_sr_trials_var(window, dataset_group, ledger, exclude_ids=excl),
            "declared_status": declared_status, "mode": mode}


# --------------------------------------------------------------------------- seed (historical trials)
_EMP = "workspace/validation_completion_2026-09-23/trials_ledger_empirical.csv"
_VC = "VALIDATION_COMPLETION_2026-09-23.md section 7"
_REUSED_NOTE = ("historical read of the shared 60/40 index-futures holdout; order of first read not "
                "reconstructed, so all are labelled REUSED_HOLDOUT (conservative)")


def _seed_entries() -> list[dict]:
    emp = pd.read_csv(ROOT / _EMP).set_index("trial")

    def sr(name):
        r = emp.loc[name]
        return float(r["sr_per_trade"]), int(r["n_holdout"])

    E: list[dict] = []

    def add(id_, family, dataset, window, n_configs, verdict, *, sr_n=None, status="REUSED_HOLDOUT",
            group=IDX, source=_VC, notes=_REUSED_NOTE, null=False):
        s, n = sr_n if sr_n else (None, None)
        E.append({"id": id_, "family": family, "dataset": dataset, "dataset_group": group,
                  "data_window": dict(window), "window_status": status, "n_configs": int(n_configs),
                  "sr_per_trade": s, "n_trades": n, "verdict": verdict, "is_null_control": null,
                  "source": source, "notes": notes})

    W = HOLDOUT_6040
    src_emp = f"{_VC}; SR/N from {_EMP}"
    # ---- MNQ_1m file: 12 configs (VALIDATION_COMPLETION section 7)
    add("MNQ-dhesi-inversion-v1", "dhesi_inversion", "data/MNQ_1m.parquet", W, 1, "DEAD")
    add("MNQ-dhesi-inversion-v2", "dhesi_inversion", "data/MNQ_1m.parquet", W, 1, "INCONCLUSIVE (13 tr)",
        sr_n=sr("inversion_v2_MNQ"), source=src_emp)
    add("MNQ-okala-v1", "okala8020", "data/MNQ_1m.parquet", W, 1, "DEAD (0 trades)", sr_n=(None, 0))
    add("MNQ-okala-v2", "okala8020", "data/MNQ_1m.parquet", W, 1, "DEAD (0 trades)", sr_n=(None, 0))
    add("MNQ-fabio-orb-delta", "fabio_orb", "data/MNQ_1m.parquet", W, 1, "DEAD",
        sr_n=sr("fabio_orb_delta_MNQ"), source=src_emp)
    add("MNQ-fabio-orb-nodelta-baseline", "fabio_orb", "data/MNQ_1m.parquet", W, 1, "baseline")
    add("MNQ-luxalgo-poc", "luxalgo_poc", "data/MNQ_1m.parquet", W, 1, "DEAD",
        sr_n=sr("luxalgo_poc_MNQ"), source=src_emp)
    add("MNQ-casper-fvg", "casper_fvg", "data/MNQ_1m.parquet", W, 1, "DEAD",
        sr_n=sr("casper_fvg_MNQ"), source=src_emp)
    add("MNQ-imom-primary", "intraday_momentum", "data/MNQ_1m.parquet (databento log)", W, 1, "DEAD",
        sr_n=sr("intraday_mom_MNQ"), source=src_emp)
    add("MNQ-imom-diag-long-last-half-hour", "intraday_momentum", "data/MNQ_1m.parquet", W, 1, "diagnostic")
    add("MNQ-imom-diag-onfh", "intraday_momentum", "data/MNQ_1m.parquet", W, 1, "diagnostic")
    add("MNQ-imom-fade-rROD", "intraday_momentum_fade", "data/MNQ_1m.parquet", W, 1,
        "CONTAMINATED (discovered from this data)")
    # ---- same window on MES/ES: 53 configs
    add("MES-dhesi-inversion-v1", "dhesi_inversion", "data/MES_1m.parquet", W, 1, "DEAD")
    add("ES-dhesi-inversion-v1", "dhesi_inversion", "data/ES_1m.parquet", W, 1, "DEAD")
    add("MES-dhesi-inversion-v2", "dhesi_inversion", "data/MES_1m.parquet", W, 1, "DEAD",
        sr_n=sr("inversion_v2_MES"), source=src_emp)
    add("ES-dhesi-inversion-v2", "dhesi_inversion", "data/ES_1m.parquet", W, 1, "DEAD")
    add("MES-imom-primary", "intraday_momentum", "MES databento log", W, 1, "DEAD",
        sr_n=sr("intraday_mom_MES"), source=src_emp)
    add("ES-imom-primary", "intraday_momentum", "ES databento log", W, 1, "DEAD",
        sr_n=sr("intraday_mom_ES"), source=src_emp)
    add("MES-imom-diagnostics", "intraday_momentum", "MES databento log", W, 2, "diagnostic")
    add("ES-imom-diagnostics", "intraday_momentum", "ES databento log", W, 2, "diagnostic")
    grid = pd.read_csv(ROOT / "data/target_sweep/target_sweep_grid.csv")
    for _, r in grid[grid["split"] == "holdout"].iterrows():
        key = f"tsweep_{r['strategy']}_{r['instrument']}_target{int(r['target_ticks'])}"
        has = key in emp.index
        add(f"{r['instrument']}-tsweep-{r['strategy']}-t{int(r['target_ticks'])}s{int(r['stop_ticks'])}",
            "target_sweep", f"data/{r['instrument']}_1m.parquet", W, 1, "DEAD (grid cell)",
            sr_n=sr(key) if has else (None, int(r["n_trades"])),
            source=f"{_VC}; data/target_sweep/target_sweep_grid.csv" + (f"; SR from {_EMP}" if has else ""))
    for key in [k for k in emp.index if k.startswith("qfilter_")]:
        add(f"ES-{key.replace('_', '-')}", "quality_filter", "data/ES_1m.parquet", W, 1, "DEAD",
            sr_n=sr(key), source=src_emp)
    add("ES-swing-trend", "swing_trend", "data/ES_1m.parquet", W, 1, "DEAD", sr_n=sr("swing_ES"), source=src_emp)
    for key, fam in [("vwap_rev_MES_full", "vwap_reversion"), ("time_scalp_MES_full", "time_scalp"),
                     ("trend_pullback_MES_full", "trend_pullback")]:
        add(f"MES-{key.replace('_', '-')}", fam, "data/MES_1m.parquet (full sample)", W, 1, "DEAD",
            sr_n=sr(key), source=src_emp)
    add("MES-null-entry-controls", "null_control", "data/MES_1m.parquet", W, 140,
        "null controls (20 seeds + 60 slippage + 60 stop-limit)", null=True,
        notes="true nulls: looks, not candidates; excluded from nb_trials. Window INFERRED from "
              "tools/null_entry_test.py (MES_1m, 60/40 cut).")
    # ---- Sierra NQ/MNQ windows
    add("MNQ-orderflow-absorption-v1", "orderflow_absorption", "data/sierra/MNQ_continuous_1m_latest_90d.parquet",
        {"start": "2026-06-23", "end": "2026-09-21"}, 1, "DEAD (0 trades)", sr_n=(None, 0),
        source="HEIMDALL_MEMORY.md absorption v1; window = file min/max ts",
        notes="0 trades: read the window, no returns")
    add("NQ-orderflow-footprint-v2", "orderflow_footprint", "data/sierra/tick/NQ_continuous_1m_footprint.parquet",
        {"start": "2026-02-27", "end": "2026-09-21"}, 1, "DEAD (0 trades)", sr_n=(None, 0),
        source="HEIMDALL_MEMORY.md footprint v2 (146 RTH sessions); window = file min/max",
        notes="0 trades: read the window, no returns")
    add("NQ-orderflow-initiative-v3", "orderflow_initiative", "data/sierra/tick/NQ_continuous_1m_footprint.parquet",
        {"start": "2026-06-16", "end": "2026-09-21"}, 1, "INCONCLUSIVE/FAILED holdout (28 tr)",
        sr_n=(-0.19293131705548763, 28),
        source="HEIMDALL_MEMORY.md initiative v3; SR from data/prop_futures/orderflow_initiative_v3_NQ_trades.csv "
               "sessions >= 2026-06-16",
        notes="DISPUTED STATUS: memory calls this an 'untouched holdout'; ledger labels it REUSED_HOLDOUT "
              "because footprint v2 (0 trades) and the 60/40 holdout (to 2026-06-30) overlap it")
    fresh_sr = {"MNQ": 0.08642434620805486, "MES": -0.25525436143741115, "ES": -0.24273685286426105,
                "NQ": 0.04990310918802928, "M2K": -0.23098830696403036, "MYM": -0.09468413480566518}
    for c, s in fresh_sr.items():
        add(f"{c}-imom-fresh", "intraday_momentum", f"data/strategy_research/intraday_momentum_{c}_fresh_trades.csv",
            {"start": "2026-07-01", "end": "2026-09-18"}, 1, "DEAD", sr_n=(s, 56),
            source="tools/validate_intraday_momentum.py FRESH_FIRST=2026-07-01; SR/N from the fresh trade logs",
            notes="DISPUTED STATUS: declared FRESH by its prereg; ledger labels REUSED_HOLDOUT because "
                  "initiative v3 / footprint v2 / absorption v1 had read NQ/MNQ over the same period")
    # ---- FOMO lane (all DEV)
    fomo = json.loads((ROOT / "workspace/fomo_lane/fomo_trials_dev.json").read_text(encoding="utf-8"))
    fw = {"start": "2026-09-05T07:38Z", "end": "2026-09-22T19:42Z"}
    for t in fomo["trials"]:
        add(f"FOMO-{t['id']}", t["family"], "fomopulse_tape_dev", fw, int(t["configs"]), t["verdict"],
            status="DEV", group="ROBINHOOD_CHAIN_FOMO",
            source="workspace/fomo_lane/fomo_trials_dev.json",
            notes=f"{t['rule']} | {t.get('result', '')}")
    return E


def seed_ledger(path: Path | str = LEDGER_PATH, registered_at: str = "2026-09-23T00:00:00+00:00") -> int:
    p = Path(path)
    if p.exists() and load_ledger(p)["entries"]:
        raise FileExistsError(f"{p} already has entries; seeding refused (append-only)")
    for e in _seed_entries():
        register_trial(e, p, registered_at=registered_at)
    return len(load_ledger(p)["entries"])


def summary(ledger: dict | None = None) -> dict:
    led = ledger if ledger is not None else load_ledger()
    out = {}
    for name, (w, g) in {"index_6040_holdout": (HOLDOUT_6040, IDX),
                         "index_post_2026_07_01": ({"start": "2026-07-01", "end": "2026-09-21"}, IDX),
                         "fomo_dev": ({"start": "2026-09-05T07:38Z", "end": "2026-09-22T19:42Z"},
                                      "ROBINHOOD_CHAIN_FOMO")}.items():
        out[name] = {"nb_trials_configs": nb_trials(w, g, led, "configs"),
                     "nb_trials_families": nb_trials(w, g, led, "families"),
                     "sr_trials_var": empirical_sr_trials_var(w, g, led),
                     "is_fresh": window_is_fresh(w, g, led)}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.seed:
        print("seeded entries:", seed_ledger())
    if a.verify:
        pr = verify_ledger(load_ledger())
        print("ledger integrity OK" if not pr else pr)
        sys.exit(1 if pr else 0)
    if a.summary:
        print(json.dumps(summary(), indent=1))
