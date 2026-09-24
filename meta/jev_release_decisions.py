"""Jev (TypeSafe System One) DECIDES the judgment calls of the 2026-09-24 pre-validation hardening release
(owner instruction: "use jev to take decisions"). Code supplies only verified facts as state, and applies each
decision with an explicit confidence threshold; below it the item is ESCALATED to the owner (never overridden).

Boundary kept (HEIMDALL_MEMORY Jev rule): Jev decides process/release questions; it is never the source of facts
(hashes, test results, trades), never touches the money path, and cannot certify the Dhesi validation.

Outputs workspace/dhesi_adjudication_agent1_2026-09-23/JEV_RELEASE_DECISIONS_2026-09-24.json. `--apply` performs the
junk-file deletions Jev decided (git rm), which the work order permits only for unambiguously generated junk.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "workspace" / "dhesi_adjudication_agent1_2026-09-23" / "JEV_RELEASE_DECISIONS_2026-09-24.json"
CHOICE_MIN_CONF = 0.80     # act on a Choice only at or above this confidence
JUNK_DELETE_MIN = 0.90     # delete a file only if P(unambiguous generated junk) >= this
JUNK = ["$50k", "HL", "Stage", "TAKER", "tuple[float", "tuple[int"]


def _key() -> str:
    k = os.environ.get("TYPESAFE_API_KEY")
    if not k and (ROOT / ".env").exists():
        m = re.search(r"^TYPESAFE_API_KEY\s*=\s*['\"]?([^'\"\r\n]+)", (ROOT / ".env").read_text(encoding="utf-8"), re.M)
        k = m.group(1).strip() if m else None
    if not k:
        raise SystemExit("TYPESAFE_API_KEY not available")
    return k


def git(*a) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def facts() -> dict:
    changed = [l[3:] for l in git("status", "--porcelain", "-uall").splitlines() if l.strip()]
    junk = []
    for f in JUNK:
        p = ROOT / f
        log = git("log", "--format=%h %s", "--", f).splitlines()
        junk.append({"name": f, "size_bytes": p.stat().st_size if p.exists() else None, "tracked": bool(log),
                     "added_by_commit": log[-1] if log else None, "has_file_extension": "." in f,
                     "location": "repository root"})
    return {
        "work_order": "Pre-validation hardening: D3 dual-engine trade persistence + INVALID on disagreement; D4 volume/row "
                      "integrity; spec/code consistency re-check; refreeze infrastructure hashes; split ledger test into "
                      "historical snapshot vs live invariants; external-8 checker handoff; secret/junk scan; tests; PR.",
        "verified_facts": {
            "frozen_code_spec_protocol_ref_engine_hash_identical_to_base": True,
            "validator_rule_and_statistics_functions_byte_identical_to_base": True,
            "validator_functions_changed": ["check_authorization", "primary", "secondary"],
            "validator_primary_change": "persists both engines' trade ledgers and a comparison before statistics; if engines "
                                        "disagree the result is INVALID and no verdict is computed (was: verdict stands on "
                                        "frozen code). Declared in PROTOCOL_AMENDMENT_1.md which supersedes Protocol V1 §4.5.",
            "harvest_integrity_change": "adds volume/row-validity/geometry/monotonic/timezone/stamp-shift/roll-range checks; counts only",
            "authorization_request_change": "only binding hashes updated (validator, integrity tool, amendment)",
            "tests": "279 passed, 1 skipped, 2 failed; both failures are live-network tests (OKX API unreachable): "
                     "test_connectors_live::test_live_public_connectors, test_history_real::test_btc_real_history_and_funnel_verdicts",
            "d3_dev_end_to_end": "frozen vs reference 49/49 trades, 0 field mismatches, max numeric diff 0.0",
            "d3_synthetic_comparator": "231/231 trades, all 16 fields identical",
            "d4_synthetic_tests": "26 passed (NaN/inf/negative/zero volume, OHLC NaN, geometry, duplicate, missing row, "
                                  "non-monotonic, 1-minute shift, wrong timezone, naive index, roll range)",
            "ledger_tests": "historical snapshot pinned by hash-chain prefix passes with 65 configs and variance 0.003449473183343993; "
                            "live invariants pass; append regression passes",
            "external8_handoff": "generated; 0 missing references; 0 hash drift; 4/4 core documents identical to base",
            "secret_scan": "1 finding: an authorization sentinel phrase (TOKEN = <redacted>) in Agent 2's harness that its "
                           "script requires as a line in the owner's authorization file; no API keys, AWS, GitHub, private keys, "
                           "bearer tokens or committed .env files",
            "dhesi_validation_run": "not run; no reserved data read",
            "remaining_items_outside_this_PR": ["owner Sierra harvest of NQ history", "ledger registration of three Dhesi trials",
                                                "owner authorization file", "Agent 2 certification incl. acceptance of Protocol "
                                                "Amendment 1", "D2 reporting gap", "D5 converter freeze", ".dly quarantine decision"],
        },
        "changed_files": changed,
        "junk_candidates": junk,
    }


FILE_CLASSES = {
    "strategy_logic_change": "changes which trades the strategy takes, their prices, sizes, exits, costs or statistics",
    "validation_decision_rule_change": "changes how the validation decides its result (e.g. when a result is INVALID) "
                                       "without changing trades or statistics",
    "validation_infrastructure_change": "changes validation plumbing: integrity checks, persistence, hashing, authorization binding",
    "tests_or_tooling": "adds or changes tests, scanners or helper scripts that do not run in the validation",
    "evidence_or_documentation": "records results, hashes, decisions, reports or self-test outputs",
}


def questions(fx: dict) -> dict:
    q = {}
    groups = {}
    for f in fx["changed_files"]:
        key = re.sub(r"/(selftest_engines_(dev|synthetic))/.*", r"/\1/*", f)
        groups.setdefault(key, []).append(f)
    for i, g in enumerate(sorted(groups)):
        q[f"cls_{i:02d}"] = {"type": "choice",
                             "instructions": f"Given `verified_facts` and `work_order`, classify the change to `{g}` in this release.",
                             "criteria": FILE_CLASSES, "_file": g}
    for i, j in enumerate(fx["junk_candidates"]):
        q[f"junk_{i}"] = {"type": "noul",
                          "instructions": (f"`junk_candidates[{i}]` is a file in the repository root. Is it unambiguously an "
                                           "accidentally generated artifact (for example a shell redirect or glob mistake) with no "
                                           "content and no purpose, so that deleting it cannot lose information?"),
                          "criteria": {"true": "unambiguous generated junk, safe to delete",
                                       "false": "could be intentional or its purpose is unclear"}, "_file": j["name"]}
    q["secret_status"] = {"type": "choice",
                          "instructions": ("The work order defines likely credentials to include Databento keys, AWS keys, API keys, "
                                           "tokens, AUTHORIZATION STRINGS and .env contents. Given `verified_facts.secret_scan`, which "
                                           "status must be reported?"),
                          "criteria": {"SECRET_SCAN_PASS": "nothing that meets the work order's definition was found",
                                       "SECRET_SCAN_FINDINGS": "at least one item meeting the work order's definition was found"}}
    q["release_status"] = {"type": "choice",
                           "instructions": ("Decide the release status of this pull request for independent checker certification, "
                                            "using `verified_facts` against `work_order`."),
                           "criteria": {
                               "READY_FOR_CHECKER": "every repair the work order asks this PR to make is implemented and tested, "
                                                    "all test failures are explained network-only failures, and the remaining "
                                                    "items are owner/checker steps outside this PR",
                               "BLOCKED": "a required repair is missing or failing, a test failure is unexplained, or strategy "
                                          "logic or reserved data was touched"}}
    return q


def main(apply: bool) -> int:
    fx = facts()
    qs = questions(fx)
    payload_q = {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in qs.items()}
    body = json.dumps({"model": "jev-latest", "state": fx, "questions": payload_q}).encode()
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
    ans = resp["answers"]
    decisions = {"file_classification": {}, "junk": {}, "escalations": []}
    for k, q in qs.items():
        a = ans[k]
        if k.startswith("cls_"):
            ok = a["confidence"] >= CHOICE_MIN_CONF
            decisions["file_classification"][q["_file"]] = {"class": a["choice"] if ok else "ESCALATED_TO_OWNER",
                                                           "jev_choice": a["choice"], "confidence": a["confidence"]}
            if not ok:
                decisions["escalations"].append(f"classification of {q['_file']} (confidence {a['confidence']})")
        elif k.startswith("junk_"):
            p = a["noul"]
            decisions["junk"][q["_file"]] = {"p_unambiguous_junk": p, "action": "DELETE" if p >= JUNK_DELETE_MIN else "KEEP_LIST_FOR_OWNER"}
    for k in ("secret_status", "release_status"):
        a = ans[k]
        ok = a["confidence"] >= CHOICE_MIN_CONF
        decisions[k] = {"decision": a["choice"] if ok else "ESCALATED_TO_OWNER", "jev_choice": a["choice"],
                        "confidence": a["confidence"], "probabilities": a.get("probabilities")}
        if not ok:
            decisions["escalations"].append(f"{k} (confidence {a['confidence']})")
    out = {"decider": "Jev (TypeSafe System One)", "model": resp.get("model"), "thresholds":
           {"choice_min_confidence": CHOICE_MIN_CONF, "junk_delete_min_noul": JUNK_DELETE_MIN},
           "decisions": decisions, "state_facts": fx, "usage": resp.get("usage")}
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(decisions, indent=1))
    if apply:
        for f, d in decisions["junk"].items():
            if d["action"] == "DELETE":
                git("rm", "-q", "--", f)
                print("git rm", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--apply" in sys.argv))
