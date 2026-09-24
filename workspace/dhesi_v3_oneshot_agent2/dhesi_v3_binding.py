"""VALIDATION_BINDING_V2 for the Dhesi v3 one-shot (Agent 2, 2026-09-24).

  make     : write VALIDATION_BINDING_V2.json (hashes of every validation input) and print its SHA-256.
  preflight: refuse unless EVERY bound input is unchanged, the append-only ledger still holds the bound PENDING
             trial at the bound position, the harvest integrity JSON passed with the bound tool on the named
             dataset, and the OWNER-created, git-untracked DHESI_V3_RUN_AUTHORIZATION.txt names the binding SHA and
             the integrity-JSON SHA (plus the five hashes the validator itself enforces).

Security model (not a secret string): the authorization file is created by the owner, is git-ignored and must
not be tracked, and must quote hashes that only exist after the harvest passed. An agent could still write it;
that is prohibited procedurally (protocol V1 section 4.2, AGENTS.md section 8) and every run records who/when.

usage: python dhesi_v3_binding.py make
       python dhesi_v3_binding.py preflight --nq <dataset.parquet>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
A1 = ROOT / "workspace" / "dhesi_adjudication_agent1_2026-09-23"
BINDING = HERE / "VALIDATION_BINDING_V2.json"
AUTH = ROOT / "DHESI_V3_RUN_AUTHORIZATION.txt"
INTEGRITY_JSON = A1 / "DHESI_V3_HARVEST_INTEGRITY.json"
UNTOUCHED_ID = "NQ-dhesi-inversion-v3-untouched"
ROLL_EXCLUSION_DATES = "2024-09-12,2024-09-13,2024-09-16,2024-09-17,2024-09-18"   # frozen before any Sierra data

FILES = {
    "canonical_spec": A1 / "DHESI_V3_CANONICAL_SPEC_V1.md",
    "protocol_v1": A1 / "DHESI_V3_VALIDATION_PROTOCOL_V1.md",
    "protocol_amendment_1": A1 / "PROTOCOL_AMENDMENT_1.md",
    "validator_and_reference_engine": A1 / "dhesi_v3_validator.py",
    "harvest_integrity": A1 / "dhesi_v3_harvest_integrity.py",
    "converter": HERE / "dhesi_v3_sierra_convert.py",
    "report_tool": HERE / "dhesi_v3_report.py",
    "binding_tool": Path(__file__).resolve(),
    "strategy_v2_base": ROOT / "core/alpha/inversion_model.py",
    "strategy_v3": ROOT / "core/alpha/inversion_model_v3.py",
    "risk_engine": ROOT / "core/risk/prop_engine.py",
    "alpha_base": ROOT / "core/alpha/base.py",
    "prop_montecarlo": ROOT / "tools/prop_montecarlo.py",
    "daily_counts": ROOT / "tools/validate_inversion_model.py",
    "trials_ledger_tool": ROOT / "tools/trials_ledger.py",
    "equivalence_reference_dev_MNQ": ROOT / "data/MNQ_1m.parquet",
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ledger_anchor() -> dict:
    sys.path.insert(0, str(ROOT / "tools"))
    import trials_ledger as tl
    led = tl.load_ledger()
    assert tl.verify_ledger(led) == [], "ledger chain broken"
    pos = next(i for i, e in enumerate(led["entries"]) if e["id"] == UNTOUCHED_ID)
    e = led["entries"][pos]
    assert e["verdict"] == "PENDING" and e["window_status"] == "FRESH"
    return {"trial_id": UNTOUCHED_ID, "index": pos, "entry_hash": e["entry_hash"],
            "ledger_file_sha256_at_binding": sha(ROOT / "data/trials_ledger.json"),
            "rule": "append-only: preflight requires the same entry_hash at the same index and a valid chain; later appends allowed"}


def make() -> str:
    body = {"binding": "VALIDATION_BINDING_V2", "hypothesis": "Dhesi v3 (canonical spec V1), one-shot primary on untouched NQ",
            "files": {k: {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p)} for k, p in FILES.items()},
            "trials_ledger": ledger_anchor(),
            "frozen_parameters": {"gate3_roll_exclusion_dates": ROLL_EXCLUSION_DATES,
                                  "untouched_hard_cut_et": "2024-06-29 00:00 (validator UNTOUCHED_END_ET)",
                                  "sierra_convention": "NQ continuous, Volume Based Rollover, back-adjust None, 1 minute, chart TZ UTC, bar-start"},
            "dataset": "bound indirectly: DHESI_V3_HARVEST_INTEGRITY.json (produced by the bound harvest_integrity tool) "
                       "records the dataset SHA-256; the owner authorization quotes that JSON's SHA-256."}
    BINDING.write_text(json.dumps(body, indent=1) + "\n", encoding="utf-8")
    return sha(BINDING)


def preflight(nq: Path) -> dict:
    errs = []
    b = json.loads(BINDING.read_text(encoding="utf-8"))
    bsha = sha(BINDING)
    for k, v in b["files"].items():
        p = ROOT / v["path"]
        if not p.exists() or sha(p) != v["sha256"]:
            errs.append(f"bound file changed or missing: {k} ({v['path']})")
    sys.path.insert(0, str(ROOT / "tools"))
    import trials_ledger as tl
    led = tl.load_ledger()
    a = b["trials_ledger"]
    if tl.verify_ledger(led):
        errs.append("ledger chain broken")
    elif len(led["entries"]) <= a["index"] or led["entries"][a["index"]]["entry_hash"] != a["entry_hash"]:
        errs.append("bound PENDING trial not at its bound ledger position (ledger rewritten?)")
    if not INTEGRITY_JSON.exists():
        errs.append("DHESI_V3_HARVEST_INTEGRITY.json missing")
    else:
        ij = json.loads(INTEGRITY_JSON.read_text(encoding="utf-8"))
        if not ij.get("all_gates_pass"):
            errs.append("harvest integrity did not pass")
        if ij.get("tool_sha256") != b["files"]["harvest_integrity"]["sha256"]:
            errs.append("integrity JSON produced by a different integrity tool")
        if ij.get("sha256") != sha(nq):
            errs.append("dataset differs from the one the integrity gate checked")
        if ij.get("roll_dates_reported") != ROLL_EXCLUSION_DATES.split(","):
            errs.append("integrity run did not use the frozen roll-exclusion dates")
    conv = Path(str(nq) + ".convert.json")
    if not conv.exists() or json.loads(conv.read_text())["output_sha256"] != sha(nq) \
            or json.loads(conv.read_text())["converter_sha256"] != b["files"]["converter"]["sha256"]:
        errs.append("dataset was not produced by the bound converter")
    if not AUTH.exists():
        errs.append("owner authorization file absent")
    else:
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", AUTH.name], cwd=ROOT, capture_output=True).returncode == 0
        if tracked:
            errs.append("authorization file is tracked by git (must be owner-local)")
        t = AUTH.read_text(encoding="utf-8")
        need = {"AUTHORIZED_BY_OWNER": "AUTHORIZED_BY_OWNER", "binding": bsha}
        if INTEGRITY_JSON.exists():
            need["integrity_json"] = sha(INTEGRITY_JSON)
        for k in ("validator_and_reference_engine", "canonical_spec", "protocol_v1", "protocol_amendment_1", "harvest_integrity"):
            need[k] = b["files"][k]["sha256"]
        errs += [f"authorization lacks {k}" for k, v in need.items() if v not in t]
    return {"binding_sha256": bsha, "preflight": "PASS" if not errs else "REFUSED", "errors": errs}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["make", "preflight"])
    ap.add_argument("--nq", type=Path)
    a = ap.parse_args()
    if a.mode == "make":
        print(make())
    else:
        r = preflight(a.nq.resolve())
        print(json.dumps(r, indent=1))
        raise SystemExit(0 if r["preflight"] == "PASS" else 2)
