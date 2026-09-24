"""Jev-assisted strategy research triage, isolated from the money path.

This module may classify research evidence and surface missing data. It cannot
emit trading signals, change risk limits, or place orders. ``/core`` must never
import it; that boundary is enforced by ``tools/check_core_purity.py``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol, Sequence

from typesafe_sdk import Choice, Noul, RetryPolicy, Score, TypeSafeClient


@dataclass(frozen=True)
class StrategyCandidate:
    candidate_id: str
    name: str
    evidence: str

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.candidate_id.replace("_", "").isalnum():
            raise ValueError("candidate_id must contain only letters, numbers, and underscores")
        if self.candidate_id == "none":
            raise ValueError("candidate_id 'none' is reserved")
        if not self.name.strip() or not self.evidence.strip():
            raise ValueError("candidate name and evidence are required")


@dataclass(frozen=True)
class CandidateAssessment:
    candidate_id: str
    name: str
    codifiability_score: float
    codifiability_confidence: float
    data_ready_probability: float
    target_fit_probability: float


@dataclass(frozen=True)
class TriageReport:
    selected_candidate: str
    selected_candidate_name: str | None
    selection_confidence: float
    selection_probabilities: Mapping[str, float]
    assessments: tuple[CandidateAssessment, ...]
    human_review_required: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class SystemOneClient(Protocol):
    def system_one(self, state: Any, questions: Mapping[str, Any], **kwargs: Any) -> Any: ...


CODIFIABILITY_LEVELS = [
    "Not mechanically codifiable: defining entry, exit, or risk rules depend on unstated discretion.",
    "Partly codifiable: core rules exist, but material decisions still need pre-registration or human review.",
    "Mechanically codifiable: defining signals, timing, exits, and risk inputs are explicit and testable.",
]


def build_state(project_context: Mapping[str, Any], candidates: Sequence[StrategyCandidate]) -> dict[str, Any]:
    if not candidates:
        raise ValueError("at least one strategy candidate is required")
    ids = [candidate.candidate_id for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate_id values must be unique")
    return {
        "project": dict(project_context),
        "candidates": {
            candidate.candidate_id: {"name": candidate.name, "evidence": candidate.evidence}
            for candidate in candidates
        },
        "decision_policy": {
            "purpose": "research triage only",
            "forbidden": [
                "placing or approving orders",
                "emitting live entry or exit signals",
                "changing risk limits",
                "treating a model judgment as backtest evidence",
            ],
            "required_next_step": "human review followed by deterministic implementation and holdout validation",
        },
    }


def build_questions(candidates: Sequence[StrategyCandidate]) -> dict[str, Any]:
    options = {
        candidate.candidate_id: {
            "candidate": candidate.name,
            "choose_when": "Best supported next candidate for a bounded, falsifiable test under the project constraints.",
        }
        for candidate in candidates
    }
    options["none"] = "No supplied candidate has enough explicit evidence for the next bounded test."

    questions: dict[str, Any] = {
        "next_candidate": Choice(
            instructions={
                "question": "Which candidate should receive the next bounded research test?",
                "focus": "Prefer target-market fit, mechanical codifiability, available data, and falsifiability. Do not infer profitability.",
            },
            criteria=options,
        )
    }
    for candidate in candidates:
        candidate_ref = f"`candidates.{candidate.candidate_id}`"
        questions[f"codifiability__{candidate.candidate_id}"] = Score(
            instructions={
                "question": "How mechanically codifiable is this candidate from the supplied evidence?",
                "inspect": candidate_ref,
                "focus": "Judge completeness of entry, exit, timing, and risk rules; do not judge profitability.",
            },
            criteria=CODIFIABILITY_LEVELS,
        )
        questions[f"data_ready__{candidate.candidate_id}"] = Noul(
            instructions={
                "question": "Can the candidate's defining signal be tested with the data explicitly listed as available?",
                "compare": [candidate_ref, "`project.available_data`"],
                "focus": "Answer no when the defining signal requires an unlisted data class.",
            }
        )
        questions[f"target_fit__{candidate.candidate_id}"] = Noul(
            instructions={
                "question": "Does this candidate trade an instrument and venue compatible with the stated primary target?",
                "compare": [candidate_ref, "`project.primary_target`"],
            }
        )
    return questions


def _answer(response: Any, question_id: str) -> Any:
    try:
        return response.answers[question_id]
    except (AttributeError, KeyError, TypeError) as exc:
        raise ValueError(f"Jev response is missing answer {question_id!r}") from exc


def triage_strategies(
    project_context: Mapping[str, Any],
    candidates: Sequence[StrategyCandidate],
    *,
    client: SystemOneClient | None = None,
    model: str = "jev-latest",
) -> TriageReport:
    """Ask Jev for advisory research classifications and always require review."""
    state = build_state(project_context, candidates)
    questions = build_questions(candidates)
    owns_client = client is None
    if client is None:
        client = TypeSafeClient(
            model=model,
            timeout=15.0,
            retry=RetryPolicy(max_retries=2, backoff_max=1.0, timeout=15.0),
        )
    try:
        response = client.system_one(state=state, questions=questions)
    finally:
        if owns_client and hasattr(client, "close"):
            client.close()

    selection = _answer(response, "next_candidate")
    valid_ids = {candidate.candidate_id for candidate in candidates} | {"none"}
    if selection.choice not in valid_ids:
        raise ValueError(f"Jev selected unknown candidate {selection.choice!r}")

    assessments = []
    candidates_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    for candidate in candidates:
        codifiability = _answer(response, f"codifiability__{candidate.candidate_id}")
        data_ready = _answer(response, f"data_ready__{candidate.candidate_id}")
        target_fit = _answer(response, f"target_fit__{candidate.candidate_id}")
        assessments.append(
            CandidateAssessment(
                candidate_id=candidate.candidate_id,
                name=candidate.name,
                codifiability_score=float(codifiability.score),
                codifiability_confidence=float(codifiability.confidence),
                data_ready_probability=float(data_ready.noul),
                target_fit_probability=float(target_fit.noul),
            )
        )

    return TriageReport(
        selected_candidate=str(selection.choice),
        selected_candidate_name=(
            candidates_by_id[selection.choice].name if selection.choice in candidates_by_id else None
        ),
        selection_confidence=float(selection.confidence),
        selection_probabilities={key: float(value) for key, value in selection.probabilities.items()},
        assessments=tuple(assessments),
    )
