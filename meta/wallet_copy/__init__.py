"""Read-only wallet observation and deterministic replay tools.

This package intentionally contains no RPC, key, signing, transaction, or order
capabilities.  It records already-observed public events and evaluates hypothetical
copies after those observations.
"""

from .models import CopySignal, EvmLogIdentity, HypotheticalCopy, WalletTradeObservation
from .recorder import ObservationRecorder, load_observations
from .replay import ReplayMetric, evaluate_copy, replay_copies

__all__ = [
    "CopySignal",
    "EvmLogIdentity",
    "HypotheticalCopy",
    "ObservationRecorder",
    "ReplayMetric",
    "WalletTradeObservation",
    "evaluate_copy",
    "load_observations",
    "replay_copies",
]
