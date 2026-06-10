"""QualityVerifier and RevisionAgent tests."""

from __future__ import annotations

from app.runtime.planning.schemas import ItineraryDraft
from app.runtime.quality.revision_agent import RevisionAgent
from app.runtime.quality.verifier import QualityVerifier
from app.runtime.state import create_initial_runtime_state, set_itinerary_draft, set_sufficiency_result


def _draft_dict(*, assumptions: list[str] | None = None, days: int = 3) -> dict:
    resolved_assumptions = ["证据不足假设"] if assumptions is None else list(assumptions)
    return ItineraryDraft(
        destination="成都",
        travel_days=3,
        days=[
            {
                "day_number": index,
                "theme": f"第{index}天",
                "activities": [f"活动{index}"],
            }
            for index in range(1, days + 1)
        ],
        summary="成都 3天草案",
        assumptions=resolved_assumptions,
        evidence_card_ids=["card_1"],
    ).to_runtime_dict()


def test_verifier_flags_missing_assumptions_when_evidence_insufficient() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_itinerary_draft(
        state,
        _draft_dict(assumptions=[]),
    )
    state = set_sufficiency_result(
        state,
        {
            "is_sufficient": False,
            "score": 0.5,
            "missing_evidence_types": ["area_strategy"],
            "suggested_action": "mark_assumptions_and_continue",
        },
    )

    report = QualityVerifier().verify(state)

    assert report.has_blocking_issues is True
    assert any(issue.code == "assumptions_missing" for issue in report.issues)


def test_revision_agent_adds_assumptions_and_normalizes_day_count() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_itinerary_draft(
        state,
        _draft_dict(assumptions=[], days=2),
    )
    state = set_sufficiency_result(
        state,
        {
            "is_sufficient": False,
            "missing_evidence_types": ["area_strategy"],
            "suggested_action": "mark_assumptions_and_continue",
        },
    )
    report = QualityVerifier().verify(state)

    revised = RevisionAgent().revise(state, report)

    assert revised.assumptions
    assert len(revised.days) == 3


def test_verifier_detects_unsupported_claims() -> None:
    draft = _draft_dict()
    draft["days"][0]["activities"] = ["上午参观故宫"]
    state = set_itinerary_draft(
        create_initial_runtime_state(
            run_id="run_1",
            conversation_id="conv_1",
            input_message="成都",
        ),
        draft,
    )

    report = QualityVerifier().verify(state)

    assert "故宫" in report.unsupported_claims
