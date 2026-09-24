"""Repository secret scan (working tree + all git history). Prints ONLY commit / path / credential TYPE; values are
never printed. Exit 0 = SECRET_SCAN_PASS, 1 = SECRET_SCAN_FINDINGS.

usage: python tools/secret_scan.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "databento_api_key": r"\bdb-[A-Za-z0-9]{20,}\b",
    "aws_access_key_id": r"\b(AKIA|ASIA)[0-9A-Z]{16}\b",
    "aws_secret_access_key_assignment": r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+]{30,}",
    "github_token": r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
    "openai_style_key": r"\bsk-[A-Za-z0-9_-]{20,}\b",
    "private_key_block": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "slack_token": r"\bxox[abpors]-[A-Za-z0-9-]{10,}\b",
    "bearer_token": r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{24,}",
    "generic_secret_assignment": r"(?i)\b(api[_-]?key|secret|token|passwd|password)\b\s*[:=]\s*['\"][A-Za-z0-9._~+/=-]{16,}['\"]",
    "url_embedded_credentials": r"\b[a-z][a-z0-9+.-]*://[^/\s:@'\"]+:[^/\s@'\"]{6,}@",
}
# placeholders / documentation that are not credentials
ALLOW = re.compile(r"(?i)(example|placeholder|your[_-]?key|<[^>]+>|x{6,}|\*{6,}|dummy|redacted|changeme)")
SKIP_SUFFIX = (".parquet", ".zip", ".lottie", ".png", ".jpg", ".pdf", ".scid", ".npy", ".pyc")


def _scan_text(text: str):
    for kind, pat in PATTERNS.items():
        for m in re.finditer(pat, text):
            line = text[max(0, text.rfind("\n", 0, m.start())):text.find("\n", m.end())]
            if ALLOW.search(line):
                continue
            yield kind


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", check=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    findings = set()
    # 1) every blob reachable from any ref (history)
    blobs = {}
    for line in git("rev-list", "--all", "--objects").splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2 and not parts[1].endswith(SKIP_SUFFIX):
            blobs.setdefault(parts[0], parts[1])
    for sha, path in blobs.items():
        if git("cat-file", "-t", sha).strip() != "blob":
            continue
        size = int(git("cat-file", "-s", sha).strip())
        if size > 20_000_000:
            continue
        text = git("cat-file", "-p", sha)
        for kind in set(_scan_text(text)):
            commits = git("log", "--all", "--format=%h", "--find-object=" + sha).split()
            findings.add(("history", path, kind, commits[-1] if commits else "?"))
    # 2) working tree files git would track (tracked + untracked, not ignored)
    for rel in git("ls-files", "--cached", "--others", "--exclude-standard").splitlines():
        p = ROOT / rel
        if not p.is_file() or rel.endswith(SKIP_SUFFIX) or p.stat().st_size > 20_000_000:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for kind in set(_scan_text(text)):
            findings.add(("working_tree", rel, kind, "-"))
    # 3) env files ever committed
    env_hist = [l for l in git("log", "--all", "--name-only", "--format=").splitlines()
                if re.search(r"(^|/)\.env($|\.)", l) and not l.endswith(".env.example")]
    for pth in sorted(set(env_hist)):
        findings.add(("history", pth, "env_file_committed", "?"))
    rows = [dict(zip(("scope", "path", "credential_type", "first_commit"), f)) for f in sorted(findings)]
    status = "SECRET_SCAN_PASS" if not rows else "SECRET_SCAN_FINDINGS"
    out = {"status": status, "blobs_scanned": len(blobs), "findings": rows, "values_printed": False}
    print(json.dumps(out, indent=1))
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0 if not rows else 1


if __name__ == "__main__":
    sys.exit(main())
