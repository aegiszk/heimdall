"""Diagnose where the MNQ InversionModel funnel loses sessions.

Measurement only. Uses existing data/MNQ_1m.parquet and the current
core.alpha.inversion_model mechanics. No network calls, no parameter changes,
no alternate configs.
"""
from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.alpha.inversion_model import (  # noqa: E402
    DAILY_BUFFER,
    ENTRY_START,
    HTF_DISPLACEMENT_MIN_POINTS,
    SESSION_CLOSE,
    TICK_SIZE,
    InversionEvent,
    InversionModel,
    LTFEvent,
    SweepEvent,
    ranges_overlap,
)


DATA_PATH = ROOT / "data" / "MNQ_1m.parquet"
FAIL_RANK = {
    "no_5m_fvg_formed": 0,
    "5m_fvg_formed_no_htf_zone_overlap": 1,
    "5m_fvg_overlap_never_inverted": 2,
    "5m_fvg_inverted_but_trade_rejected": 3,
}


@dataclass(frozen=True)
class FvgFormation:
    formed_ts: pd.Timestamp
    session: object
    bias: int
    zone_low: float
    zone_high: float
    formation_low: float
    formation_high: float


@dataclass(frozen=True)
class Step3Candidate:
    session: object
    sweep: SweepEvent
    inversion: InversionEvent
    retrace: pd.Series
    timeframe: str


@dataclass(frozen=True)
class Step4Failure:
    category: str
    subreason: str = ""


def main() -> int:
    ensure_data_present()
    raw = pd.read_parquet(DATA_PATH)[["open", "high", "low", "close", "volume"]].copy()
    model = InversionModel(contract="MNQ")
    frame = model._prepare_frame(raw)

    sessions = list(frame["_session"].drop_duplicates())
    session_ord = {session: idx for idx, session in enumerate(sessions)}
    pools_by_session = model._build_session_pools(frame, session_ord)
    htf_4h = model._resample_bars(frame, "4h")
    htf_1h = model._resample_bars(frame, "1h")
    bars_15m = model._resample_bars(frame, "15min")
    bars_5m = model._resample_bars(frame, "5min")
    fvgs_4h, inversions_4h = model._build_inversion_events(htf_4h, "4H", session_ord)
    _, inversions_1h = model._build_inversion_events(htf_1h, "1H", session_ord)
    ltf_events = model._build_ltf_events(bars_5m)
    ltf_formations = build_ltf_formations(model, bars_5m)
    swings_15m = model._build_swings(bars_15m)

    inv4_by_key = model._events_by_session_bias(inversions_4h)
    inv1_by_key = model._events_by_session_bias(inversions_1h)
    ltf_by_key = model._ltf_by_session_bias(ltf_events)
    formations_by_key = formations_by_session_bias(ltf_formations)
    bars15_by_session = {session: day.reset_index(drop=True) for session, day in bars_15m.groupby("session", sort=True)}
    swings15_by_session: dict[object, list[Any]] = {}
    for swing in swings_15m:
        swings15_by_session.setdefault(swing.session, []).append(swing)
    idx_by_ts = {ts: idx for idx, ts in enumerate(frame["_ts_et"])}

    eligible_sessions: set[object] = set(sessions)
    step1_sessions: set[object] = set()
    step2_sessions: set[object] = set()
    step3_sessions: set[object] = set()
    step4_sessions: set[object] = set()
    pool_type_sessions: dict[str, set[object]] = {"session": set(), "day": set(), "20d": set(), "equal": set()}
    timeframe_sessions: dict[str, set[object]] = {"4H": set(), "1H": set()}
    step3_candidates_by_session: dict[object, list[Step3Candidate]] = {}
    failure_counter: Counter[str] = Counter()
    rejection_counter: Counter[str] = Counter()

    for session in sessions:
        day = frame[frame["_session"] == session]
        if day.empty:
            continue
        pools = pools_by_session.get(session, {"high": [], "low": [], "major_high": [], "major_low": []})
        all_sweeps = model._detect_sweeps(day, pools)
        post_10_sweeps = [sweep for sweep in all_sweeps if pd.Timestamp(sweep.ts).time() >= ENTRY_START]
        sweeps = post_10_sweeps
        if not sweeps:
            continue
        step1_sessions.add(session)
        for sweep in sweeps:
            pool_type_sessions[pool_group(sweep.pool_kind)].add(session)

        for sweep in sweeps:
            timeframe = "4H" if model._has_4h_fvg(fvgs_4h, sweep.ts, session, session_ord) else "1H"
            inversion = model._first_inversion(
                (inv4_by_key if timeframe == "4H" else inv1_by_key).get((session, sweep.bias), []),
                sweep.ts,
            )
            if inversion is None:
                continue
            if inversion.displacement_points < HTF_DISPLACEMENT_MIN_POINTS:
                continue
            step2_sessions.add(session)
            timeframe_sessions[timeframe].add(session)

            retrace = model._first_retracement(bars15_by_session.get(session), inversion)
            if retrace is None:
                continue
            step3_sessions.add(session)
            candidate = Step3Candidate(session, sweep, inversion, retrace, timeframe)
            step3_candidates_by_session.setdefault(session, []).append(candidate)

            trade = model._first_entry_trade(
                frame,
                idx_by_ts,
                ltf_by_key.get((session, sweep.bias), []),
                swings15_by_session.get(session, []),
                pools,
                sweep,
                inversion,
                retrace,
            )
            if trade is not None:
                step4_sessions.add(session)

    for session in sorted(step3_sessions - step4_sessions):
        failures = [
            classify_step4_failure(
                model,
                frame,
                idx_by_ts,
                formations_by_key,
                ltf_by_key,
                swings15_by_session,
                pools_by_session,
                candidate,
            )
            for candidate in step3_candidates_by_session.get(session, [])
        ]
        if not failures:
            failure = Step4Failure("no_5m_fvg_formed")
        else:
            failure = max(failures, key=lambda item: FAIL_RANK[item.category])
        failure_counter[failure.category] += 1
        if failure.subreason:
            rejection_counter[failure.subreason] += 1

    print_header(raw, frame)
    print_funnel(
        total=len(sessions),
        eligible=len(eligible_sessions),
        step1=len(step1_sessions),
        step2=len(step2_sessions),
        step3=len(step3_sessions),
        step4=len(step4_sessions),
    )
    print_pool_breakdown("STEP1_POOL_TYPE_BREAKDOWN_ACTUAL_MODEL", pool_type_sessions, len(step1_sessions))
    print_timeframe_breakdown(timeframe_sessions, len(step2_sessions))
    print_step4_failures(failure_counter, rejection_counter, len(step3_sessions - step4_sessions))
    print_consistency(len(step4_sessions))
    return 0


def ensure_data_present() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Required local parquet missing; refusing to pull data: {DATA_PATH}")


def build_ltf_formations(model: InversionModel, bars_5m: pd.DataFrame) -> list[FvgFormation]:
    formations: list[FvgFormation] = []
    fvgs_by_idx = model._detect_fvgs(bars_5m, "5M")
    for idx, fvgs in fvgs_by_idx.items():
        c3 = bars_5m.iloc[idx]
        for fvg in fvgs:
            formations.append(
                FvgFormation(
                    formed_ts=fvg.formed_ts,
                    session=fvg.session,
                    bias=-fvg.direction,
                    zone_low=fvg.zone_low,
                    zone_high=fvg.zone_high,
                    formation_low=float(c3["low"]),
                    formation_high=float(c3["high"]),
                )
            )
    return sorted(formations, key=lambda item: item.formed_ts)


def formations_by_session_bias(formations: list[FvgFormation]) -> dict[tuple[object, int], list[FvgFormation]]:
    out: dict[tuple[object, int], list[FvgFormation]] = {}
    for formation in formations:
        out.setdefault((formation.session, formation.bias), []).append(formation)
    return out


def classify_step4_failure(
    model: InversionModel,
    frame: pd.DataFrame,
    idx_by_ts: dict[pd.Timestamp, int],
    formations_by_key: dict[tuple[object, int], list[FvgFormation]],
    ltf_by_key: dict[tuple[object, int], list[LTFEvent]],
    swings15_by_session: dict[object, list[Any]],
    pools_by_session: dict[object, dict[str, list[Any]]],
    candidate: Step3Candidate,
) -> Step4Failure:
    session = candidate.session
    bias = candidate.sweep.bias
    retrace_ts = candidate.retrace["ts"]
    formations = [
        formation
        for formation in formations_by_key.get((session, bias), [])
        if formation.formed_ts >= retrace_ts and formation.formed_ts.time() <= SESSION_CLOSE
    ]
    if not formations:
        return Step4Failure("no_5m_fvg_formed")

    overlapping_formations = [
        formation
        for formation in formations
        if ranges_overlap(
            formation.formation_low,
            formation.formation_high,
            candidate.inversion.zone_low,
            candidate.inversion.zone_high,
        )
    ]
    if not overlapping_formations:
        return Step4Failure("5m_fvg_formed_no_htf_zone_overlap")

    inverted_events = [
        event
        for event in ltf_by_key.get((session, bias), [])
        if event.formed_ts >= retrace_ts
        and event.inverted_ts > retrace_ts
        and ENTRY_START <= event.inverted_ts.time() <= SESSION_CLOSE
        and ranges_overlap(
            event.formation_low,
            event.formation_high,
            candidate.inversion.zone_low,
            candidate.inversion.zone_high,
        )
    ]
    if not inverted_events:
        return Step4Failure("5m_fvg_overlap_never_inverted")

    subreason = first_trade_rejection(
        model,
        frame,
        idx_by_ts,
        inverted_events,
        swings15_by_session.get(session, []),
        pools_by_session.get(session, {"high": [], "low": [], "major_high": [], "major_low": []}),
        candidate,
    )
    return Step4Failure("5m_fvg_inverted_but_trade_rejected", subreason)


def first_trade_rejection(
    model: InversionModel,
    frame: pd.DataFrame,
    idx_by_ts: dict[pd.Timestamp, int],
    events: list[LTFEvent],
    swings_15m: list[Any],
    pools: dict[str, list[Any]],
    candidate: Step3Candidate,
) -> str:
    for event in sorted(events, key=lambda item: item.inverted_ts):
        if event.inverted_ts not in idx_by_ts:
            return "no_matching_1m_bar_at_5m_inversion_close"
        stop = model._stop_from_recent_swing(
            swings_15m,
            event.bias,
            candidate.inversion.ts,
            event.inverted_ts,
            candidate.session,
        )
        if stop is None:
            return "no_confirmed_15m_swing_for_stop"
        entry = model._entry_price(event.bias, float(event.close))
        stop_ticks = abs(entry - stop) / TICK_SIZE
        contracts = model._allowed_contracts(stop_ticks)
        if contracts <= 0:
            return "stop_too_wide_allowed_size_zero"
        risk_dollars = contracts * abs(entry - stop) * model.point_value
        if risk_dollars <= 0 or risk_dollars > DAILY_BUFFER + 1e-9:
            return "risk_exceeds_daily_buffer"
        targets = model._targets(entry, stop, event.bias, pools)
        if targets is None:
            return "no_opposing_pool_for_tp1"
        return "should_have_entered_check_diag"
    return "no_inverted_event_after_filters"


def pool_group(pool_kind: str) -> str:
    if pool_kind.startswith("prior_rth"):
        return "session"
    if pool_kind.startswith("prior_day"):
        return "day"
    if pool_kind.startswith("rolling20"):
        return "20d"
    if pool_kind.startswith("equal"):
        return "equal"
    return "other"


def print_header(raw: pd.DataFrame, frame: pd.DataFrame) -> None:
    idx = pd.DatetimeIndex(raw.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    gaps = int(idx.to_series().diff().dropna().gt(pd.Timedelta(minutes=1.5)).sum())
    print("INVERSION FUNNEL DIAGNOSTIC — MNQ")
    print("mode=measurement_only network_calls=0 data=data/MNQ_1m.parquet")
    print(
        f"rows_1m={len(raw)} rth_rows={len(frame)} rth_sessions={frame['_session'].nunique()} "
        f"start_utc={idx[0].isoformat()} end_utc={idx[-1].isoformat()} gaps_gt_1m={gaps}"
    )
    print(
        "constants=no_threshold_changes "
        "entry_start=10:00ET session=RTH_09:30_16:00ET htf=4H_else_1H "
        "htf_displacement_body_min=30_raw_points ltf_retrace=15m entry_trigger=5m_fvg_inversion"
    )
    print()


def print_funnel(total: int, eligible: int, step1: int, step2: int, step3: int, step4: int) -> None:
    rows = [
        ["step", "definition", "sessions", "conditional", "of_total"],
        ["0", "RTH sessions total", str(total), "100.00%", "100.00%"],
        ["filter", "no session-level filter", str(eligible), pct(eligible, total), pct(eligible, total)],
        ["1", ">=1 post-10:00 liquidity sweep", str(step1), pct(step1, eligible), pct(step1, total)],
        ["2", "HTF FVG inversion + >=30pt displacement", str(step2), pct(step2, step1), pct(step2, total)],
        ["3", "15m retrace into HTF iFVG zone", str(step3), pct(step3, step2), pct(step3, total)],
        ["4", "5m FVG formed+inversed; actual entry", str(step4), pct(step4, step3), pct(step4, total)],
    ]
    print("FUNNEL_TABLE_ACTUAL_MODEL")
    print_table(rows)
    print()


def print_pool_breakdown(title: str, groups: dict[str, set[object]], denominator: int) -> None:
    print(title)
    rows = [["pool_group", "sessions", "pct_of_sweep_sessions"]]
    for name in ("session", "day", "20d", "equal"):
        count = len(groups.get(name, set()))
        rows.append([name, str(count), pct(count, denominator)])
    print_table(rows)
    print()


def print_timeframe_breakdown(groups: dict[str, set[object]], denominator: int) -> None:
    print("STEP2_TIMEFRAME_BREAKDOWN")
    rows = [["timeframe", "sessions", "pct_of_step2"]]
    for name in ("4H", "1H"):
        count = len(groups.get(name, set()))
        rows.append([name, str(count), pct(count, denominator)])
    print_table(rows)
    print()


def print_step4_failures(failures: Counter[str], rejections: Counter[str], denominator: int) -> None:
    print("STEP3_TO_STEP4_FAILURE_CLOSENESS")
    rows = [["category", "sessions", "pct_of_step3_failures"]]
    for category in (
        "no_5m_fvg_formed",
        "5m_fvg_formed_no_htf_zone_overlap",
        "5m_fvg_overlap_never_inverted",
        "5m_fvg_inverted_but_trade_rejected",
    ):
        count = failures.get(category, 0)
        rows.append([category, str(count), pct(count, denominator)])
    print_table(rows)
    print()
    if rejections:
        print("STEP4_TRADE_REJECTION_SUBREASONS")
        sub_rows = [["subreason", "sessions"]]
        for reason, count in rejections.most_common():
            sub_rows.append([reason, str(count)])
        print_table(sub_rows)
        print()


def print_consistency(step4_sessions: int) -> None:
    print("CONSISTENCY_CHECK")
    print(f"actual_entry_sessions={step4_sessions}")
    print("note=This should match MNQ full-period trade count from current InversionModel mechanics.")


def pct(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.00%"
    return f"{100.0 * numerator / denominator:.2f}%"


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        print("  ".join(str(row[i]).rjust(widths[i]) for i in range(len(row))))
        if idx == 0:
            print("  ".join("-" * widths[i] for i in range(len(row))))


if __name__ == "__main__":
    sys.exit(main())
