"""ADVISORY Jev (TypeSafe System One) second opinion for the 2026-09-24 pre-validation hardening release.

Jev is NOT evidence and cannot certify anything (HEIMDALL_MEMORY Jev boundary): the governing evidence is the
deterministic function-level hash diff and the dual-engine self-tests. This script only asks bounded yes/no and
choice judgments and records them for the checker.

Sent to the API: old/new text of the three changed validator functions, and a REDACTED description of the single
secret-scan finding (variable name, value shape, usage). The secret value itself is never read into the payload.
Key: TYPESAFE_API_KEY from the environment or the local, git-ignored .env; never printed.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "8f70789801a2fc02b94f3159ebf3bf1b583d347c"
V = "workspace/dhesi_adjudication_agent1_2026-09-23/dhesi_v3_validator.py"
CHANGED = ("check_authorization", "primary", "secondary")
OUT = ROOT / "workspace" / "dhesi_adjudication_agent1_2026-09-23" / "JEV_ADVISORY_REVIEW_2026-09-24.json"


def _key() -> str:
    k = os.environ.get("TYPESAFE_API_KEY")
    if not k and (ROOT / ".env").exists():
        m = re.search(r"^TYPESAFE_API_KEY\s*=\s*['\"]?([^'\"\r\n]+)", (ROOT / ".env").read_text(encoding="utf-8"), re.M)
        k = m.group(1).strip() if m else None
    if not k:
        raise SystemExit("TYPESAFE_API_KEY not available")
    return k


def _func(src: str, name: str) -> str:
    m = re.search(rf"^def {name}\(", src, re.M)
    nxt = re.search(r"^(def |# =====|if __name__)", src[m.end():], re.M)
    return src[m.start(): m.end() + (nxt.start() if nxt else len(src))].strip()


def main() -> int:
    old = subprocess.run(["git", "show", f"{BASE}:{V}"], cwd=ROOT, capture_output=True, check=True).stdout.decode()
    new = (ROOT / V).read_text(encoding="utf-8")
    state = {
        "context": ("Heimdall Dhesi v3 one-shot validator. A 'strategy-logic change' is any change to which trades "
                    "are taken, their entry/stop/target/exit prices, position size, costs, or the statistics and "
                    "PASS/FAIL/INCONCLUSIVE decision rule. Authorization checks, refusing to run on invalid input, "
                    "writing trade ledgers to disk, and comparing two engines are infrastructure, not strategy logic."),
        "changes": {f: {"old": _func(old, f).replace("\r\n", "\n"), "new": _func(new, f).replace("\r\n", "\n")}
                    for f in CHANGED},
        "secret_finding": {
            "file": "workspace/dhesi_replication_agent2_2026-09-23/dhesi_validation_harness.py",
            "variable": "TOKEN",
            "value_shape": "37 characters: 31 uppercase letters, 1 digit, underscores and one '=' (value redacted)",
            "usage": "if TOKEN not in auth.splitlines():  # the harness refuses to run unless the owner's "
                     "authorization text file contains this exact line",
            "note": "the harness is agent-written code committed to a private repo",
        },
    }
    questions = {}
    for f in CHANGED:
        questions[f"logic_change__{f}"] = {
            "type": "noul",
            "instructions": (f"Compare `changes.{f}.old` with `changes.{f}.new`. Using the definition in `context`, "
                             "does the new version change strategy logic?"),
            "criteria": {"true": "the new version changes which trades occur, their prices, sizes, exits, costs, "
                                 "or the statistics / decision rule",
                         "false": "only authorization, input refusal, persistence, reporting or engine-comparison "
                                  "plumbing changed"},
        }
    questions["invalid_blocks_verdict"] = {
        "type": "noul",
        "instructions": ("In `changes.primary.new`, when the engine comparison result is not PASS, is it impossible "
                         "for the function to compute or report a PASS/FAIL/INCONCLUSIVE strategy verdict?"),
        "criteria": {"true": "a failed comparison always yields INVALID and evaluate() is not called",
                     "false": "a strategy verdict can still be computed or reported after a failed comparison"},
    }
    questions["secret_kind"] = {
        "type": "choice",
        "instructions": "Classify `secret_finding` by what disclosure of the redacted value would enable.",
        "criteria": {
            "external_credential": "an API key, password or token that grants access to an external service or account",
            "authorization_sentinel": "an agreed phrase that an internal script looks for in an owner-written file; "
                                      "it grants no external access, but anyone who can read it could imitate the owner's file",
            "placeholder": "a dummy, example or test value with no effect",
        },
    }
    body = json.dumps({"model": "jev-latest", "state": state, "questions": questions}).encode()
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
    out = {"advisory_only": True, "model": resp.get("model"), "answers": resp.get("answers"), "usage": resp.get("usage"),
           "payload_contains_secret_value": False, "base_commit": BASE}
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
