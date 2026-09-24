"""Measurement-only condition funnel for the frozen absorption v1 rules."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.orderflow_absorption import (
    CONFIRMATION_BARS,
    ENTRY_CUTOFF,
    KEY_LEVEL_TOLERANCE,
    LOOKBACK_SESSIONS,
    MIN_BODY_FRACTION,
    OrderflowAbsorptionModel,
)


DATA = ROOT / "data" / "sierra" / "MNQ_continuous_1m_latest_90d.parquet"


def main() -> int:
    model = OrderflowAbsorptionModel()
    raw = pd.read_parquet(DATA)
    frame = model._prepare_frame(raw)
    grouped = [(session, day) for session, day in frame.groupby("_session", sort=True)]
    counts: Counter[str] = Counter()
    session_hits: dict[str, set[object]] = {}

    def hit(name: str, session: object) -> None:
        counts[name] += 1
        session_hits.setdefault(name, set()).add(session)

    for session_idx in range(LOOKBACK_SESSIONS, len(grouped)):
        session, day = grouped[session_idx]
        counts["eligible_sessions"] += 1
        val, vah = model._volume_area(grouped[session_idx - 1][1])
        baseline = model._effort_baselines(grouped[session_idx - LOOKBACK_SESSIONS : session_idx])
        indices = list(day.index)
        absorptions: list[tuple[int, int, float]] = []
        for local_pos, i in enumerate(indices):
            row = frame.loc[i]
            if row["_time"] > ENTRY_CUTOFF:
                break
            bar_range = float(row["high"] - row["low"])
            for side, level in ((-1, vah), (1, val)):
                near = float(row["high"]) >= level - KEY_LEVEL_TOLERANCE if side == -1 else float(row["low"]) <= level + KEY_LEVEL_TOLERANCE
                if not near:
                    continue
                hit("near_level", session)
                rejected = float(row["close"]) <= level if side == -1 else float(row["close"]) >= level
                if not rejected:
                    continue
                hit("close_rejection", session)
                effort = (float(row["delta"]) > 0 if side == -1 else float(row["delta"]) < 0) and abs(float(row["delta"])) >= baseline.abs_delta_q90
                if not effort:
                    continue
                hit("signed_q90_effort", session)
                if not (0 < bar_range <= baseline.range_median):
                    continue
                hit("absorption_all", session)
                absorptions.append((local_pos, side, (float(row["high"]) + float(row["low"])) / 2.0))

        for local_pos, side, midpoint in absorptions:
            confirmed = False
            for confirm_pos in range(local_pos + 1, min(local_pos + 1 + CONFIRMATION_BARS, len(indices))):
                row = frame.loc[indices[confirm_pos]]
                bar_range = float(row["high"] - row["low"])
                opposite_effort = (float(row["delta"]) > 0 if side == 1 else float(row["delta"]) < 0) and abs(float(row["delta"])) >= baseline.abs_delta_q75
                if opposite_effort:
                    hit("confirmation_opposite_q75", session)
                directional = (float(row["close"]) > float(row["open"])) if side == 1 else (float(row["close"]) < float(row["open"]))
                body = abs(float(row["close"] - row["open"]))
                full_body = bar_range > 0 and body >= MIN_BODY_FRACTION * bar_range
                midpoint_break = float(row["close"]) > midpoint if side == 1 else float(row["close"]) < midpoint
                if opposite_effort and directional:
                    hit("confirmation_directional", session)
                if opposite_effort and directional and full_body:
                    hit("confirmation_full_body", session)
                if opposite_effort and directional and full_body and midpoint_break:
                    hit("confirmation_all", session)
                    if confirm_pos + 1 < len(indices) and frame.loc[indices[confirm_pos + 1], "_time"] <= ENTRY_CUTOFF:
                        hit("entry_bar_available", session)
                    confirmed = True
                    break
            if confirmed:
                break

    order = [
        "eligible_sessions",
        "near_level",
        "close_rejection",
        "signed_q90_effort",
        "absorption_all",
        "confirmation_opposite_q75",
        "confirmation_directional",
        "confirmation_full_body",
        "confirmation_all",
        "entry_bar_available",
    ]
    print("ORDERFLOW ABSORPTION V1 CONDITION FUNNEL")
    print(f"preregistration_sha256={model.preregistration_sha256}")
    print("measurement_only=true thresholds_changed=false")
    for name in order:
        sessions = len(session_hits.get(name, set())) if name != "eligible_sessions" else counts[name]
        print(f"{name}: events={counts[name]} sessions={sessions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
