"""Run Jev research triage over explicitly supplied local strategy documents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from meta.jev_strategy_triage import StrategyCandidate, build_questions, build_state, triage_strategies


DEFAULT_PROJECT_CONTEXT = {
    "primary_target": "LucidTrading 50K FLEX using CME index futures, especially MNQ/NQ and MES/ES",
    "available_data": "MNQ, MES, and ES one-minute OHLCV from 2024-07-01 through 2026-06-30",
    "constraints": [
        "deterministic core; meta may not enter the money path",
        "no live orders until validation",
        "pre-registered thresholds, untouched holdout, and walk-forward testing",
        "no paid data purchase without a quoted cost and explicit approval",
    ],
}


def _load_env_file(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name in {"TYPESAFE_API_KEY", "TYPESAFE_BASE_URL", "TYPESAFE_DEFAULT_MODEL"}:
            os.environ.setdefault(name, value.strip())


def _candidate_id(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "candidate"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    return f"{slug[:55]}_{digest}"


def _trim_evidence(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    headings = [line for line in text.splitlines() if line.startswith("#")]
    tail = text[-max_chars // 3 :]
    head = text[: max_chars - len(tail)]
    return head + "\n\n[HEADINGS]\n" + "\n".join(headings) + "\n\n[TAIL]\n" + tail


def _document_candidates(path: Path, max_chars: int) -> list[StrategyCandidate]:
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"(?m)^## Rule Sheet \d+:\s*(.+)$", text))
    if not matches:
        return [
            StrategyCandidate(
                candidate_id=_candidate_id(path.stem),
                name=path.stem,
                evidence=_trim_evidence(text, max_chars),
            )
        ]
    candidates = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        name = match.group(1).strip()
        candidates.append(
            StrategyCandidate(
                candidate_id=_candidate_id(f"{path.stem} {name}"),
                name=name,
                evidence=_trim_evidence(text[match.start() : end], max_chars),
            )
        )
    return candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="Strategy Markdown files to compare")
    parser.add_argument("--env-file", type=Path, help="Optional environment file containing TYPESAFE_API_KEY")
    parser.add_argument("--max-chars", type=int, default=12_000, help="Maximum evidence characters per file")
    parser.add_argument("--dry-run", action="store_true", help="Print request structure without calling Jev")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.env_file:
        _load_env_file(args.env_file)
    candidates = []
    seen_ids: set[str] = set()
    for path in args.files:
        resolved = path.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        for candidate in _document_candidates(resolved, args.max_chars):
            if candidate.candidate_id in seen_ids:
                raise ValueError(f"duplicate candidate id derived from {resolved}")
            seen_ids.add(candidate.candidate_id)
            candidates.append(candidate)
    if args.dry_run:
        payload = {
            "state": build_state(DEFAULT_PROJECT_CONTEXT, candidates),
            "question_ids": list(build_questions(candidates)),
        }
    else:
        payload = triage_strategies(DEFAULT_PROJECT_CONTEXT, candidates).as_dict()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
