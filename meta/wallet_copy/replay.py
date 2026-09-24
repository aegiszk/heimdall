"""Deterministic metrics for hypothetical copies made after observation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .models import CopySignal, HypotheticalCopy


NANOSECONDS_PER_MILLISECOND = Decimal(1_000_000)
BASIS_POINTS = Decimal(10_000)


@dataclass(frozen=True, slots=True)
class ReplayMetric:
    signal: CopySignal
    copy: HypotheticalCopy
    latency_ms: Decimal
    price_drift_bps: Decimal
    adverse_drift_bps: Decimal


def evaluate_copy(signal: CopySignal, copy: HypotheticalCopy) -> ReplayMetric:
    if copy.identity != signal.identity:
        raise ValueError("copy identity does not match signal identity")
    if copy.copied_at_ns < signal.observed_at_ns:
        raise ValueError("hypothetical copy cannot precede observation")
    latency_ms = Decimal(copy.copied_at_ns - signal.observed_at_ns) / NANOSECONDS_PER_MILLISECOND
    price_drift_bps = ((copy.copy_price / signal.reference_price) - Decimal(1)) * BASIS_POINTS
    adverse_drift_bps = price_drift_bps if signal.side == "buy" else -price_drift_bps
    return ReplayMetric(
        signal=signal,
        copy=copy,
        latency_ms=latency_ms,
        price_drift_bps=price_drift_bps,
        adverse_drift_bps=adverse_drift_bps,
    )


def replay_copies(
    signals: Iterable[CopySignal], copies: Iterable[HypotheticalCopy]
) -> tuple[ReplayMetric, ...]:
    signals_by_id: dict[tuple[int, str, int], CopySignal] = {}
    for signal in signals:
        key = signal.identity.as_key()
        if key in signals_by_id:
            raise ValueError("duplicate signal identity")
        signals_by_id[key] = signal

    copies_by_id: dict[tuple[int, str, int], HypotheticalCopy] = {}
    for copy in copies:
        key = copy.identity.as_key()
        if key in copies_by_id:
            raise ValueError("duplicate hypothetical copy identity")
        copies_by_id[key] = copy

    unknown = copies_by_id.keys() - signals_by_id.keys()
    missing = signals_by_id.keys() - copies_by_id.keys()
    if unknown:
        raise ValueError("hypothetical copy has no matching signal")
    if missing:
        raise ValueError("signal has no hypothetical copy")

    ordered_signals = sorted(
        signals_by_id.values(),
        key=lambda item: (item.observed_at_ns, item.identity.as_key()),
    )
    return tuple(evaluate_copy(signal, copies_by_id[signal.identity.as_key()]) for signal in ordered_signals)
