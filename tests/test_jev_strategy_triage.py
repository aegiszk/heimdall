from types import SimpleNamespace

import pytest

from meta.jev_strategy_triage import StrategyCandidate, build_state, triage_strategies
from tools.jev_triage_strategies import _document_candidates


def _candidate(candidate_id="absorption"):
    return StrategyCandidate(candidate_id, "Absorption", "Explicit footprint evidence")


def test_build_state_rejects_duplicate_ids():
    with pytest.raises(ValueError, match="unique"):
        build_state({"primary_target": "CME"}, [_candidate(), _candidate()])


def test_triage_is_advisory_and_parses_typed_answers():
    class FakeClient:
        def system_one(self, state, questions):
            assert state["decision_policy"]["purpose"] == "research triage only"
            assert "next_candidate" in questions
            return SimpleNamespace(
                answers={
                    "next_candidate": SimpleNamespace(
                        choice="absorption",
                        confidence=0.91,
                        probabilities={"absorption": 0.93, "none": 0.07},
                    ),
                    "codifiability__absorption": SimpleNamespace(score=1.5, confidence=0.82),
                    "data_ready__absorption": SimpleNamespace(noul=0.15),
                    "target_fit__absorption": SimpleNamespace(noul=0.98),
                }
            )

    report = triage_strategies(
        {"primary_target": "CME", "available_data": "OHLCV"},
        [_candidate()],
        client=FakeClient(),
    )

    assert report.selected_candidate == "absorption"
    assert report.selected_candidate_name == "Absorption"
    assert report.human_review_required is True
    assert report.assessments[0].name == "Absorption"
    assert report.assessments[0].data_ready_probability == 0.15
    assert report.assessments[0].target_fit_probability == 0.98


def test_triage_rejects_unknown_selection():
    class FakeClient:
        def system_one(self, state, questions):
            return SimpleNamespace(
                answers={
                    "next_candidate": SimpleNamespace(
                        choice="unseen", confidence=1.0, probabilities={"unseen": 1.0}
                    )
                }
            )

    with pytest.raises(ValueError, match="unknown candidate"):
        triage_strategies(
            {"primary_target": "CME", "available_data": "OHLCV"},
            [_candidate()],
            client=FakeClient(),
        )


def test_document_candidates_split_rule_sheets(tmp_path):
    path = tmp_path / "rules.md"
    path.write_text(
        "# Collection\n## Rule Sheet 1: First\nFirst body\n## Rule Sheet 2: Second\nSecond body\n",
        encoding="utf-8",
    )

    candidates = _document_candidates(path, max_chars=1_000)

    assert [candidate.name for candidate in candidates] == ["First", "Second"]
    assert "First body" in candidates[0].evidence
    assert "Second body" not in candidates[0].evidence
    assert len({candidate.candidate_id for candidate in candidates}) == 2
