"""Append-only canonical JSONL storage for public wallet observations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from .models import WalletTradeObservation


def canonical_json(observation: WalletTradeObservation) -> str:
    return json.dumps(observation.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_observations(path: str | Path) -> tuple[WalletTradeObservation, ...]:
    source = Path(path)
    if not source.exists():
        return ()
    observations: list[WalletTradeObservation] = []
    identities: set[tuple[int, str, int]] = set()
    last_timestamp: int | None = None
    with source.open("r", encoding="utf-8", newline="") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.endswith("\n"):
                raise ValueError(f"line {line_number} is not newline-terminated")
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_number} contains invalid JSON") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"line {line_number} must contain a JSON object")
            observation = WalletTradeObservation.from_dict(payload)
            key = observation.identity.as_key()
            if key in identities:
                raise ValueError(f"line {line_number} duplicates transaction/log identity")
            if last_timestamp is not None and observation.observed_at_ns < last_timestamp:
                raise ValueError(f"line {line_number} breaks monotonic observed_at_ns order")
            identities.add(key)
            last_timestamp = observation.observed_at_ns
            observations.append(observation)
    return tuple(observations)


class ObservationRecorder:
    """Validate then append observations without modifying prior bytes."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        existing = load_observations(self.path)
        self._identities = {item.identity.as_key() for item in existing}
        self._last_timestamp = existing[-1].observed_at_ns if existing else None

    def append(self, observation: WalletTradeObservation) -> None:
        key = observation.identity.as_key()
        if key in self._identities:
            raise ValueError("duplicate transaction/log identity")
        if self._last_timestamp is not None and observation.observed_at_ns < self._last_timestamp:
            raise ValueError("observed_at_ns must be monotonic")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        encoded = (canonical_json(observation) + "\n").encode("ascii")
        with self.path.open("ab") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        self._identities.add(key)
        self._last_timestamp = observation.observed_at_ns

    def extend(self, observations: Iterable[WalletTradeObservation]) -> None:
        for observation in observations:
            self.append(observation)
