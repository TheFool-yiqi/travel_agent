"""Planning schema contract tests."""

from __future__ import annotations

from app.runtime.planning.schemas import ItineraryDraft, PlanProposal


def test_plan_proposal_round_trip() -> None:
    proposal = PlanProposal(
        agent_name="destination_planner",
        summary="成都 3天策略",
        recommendations=["低强度文化游"],
        evidence_card_ids=["card_1"],
        detail={"destination": "成都"},
    )
    restored = PlanProposal.from_runtime_dict(proposal.to_runtime_dict())
    assert restored == proposal


def test_itinerary_draft_round_trip() -> None:
    draft = ItineraryDraft(
        destination="成都",
        travel_days=3,
        days=[{"day_number": 1, "theme": "文化游"}],
        summary="成都 3天草案",
        evidence_card_ids=["card_1"],
    )
    restored = ItineraryDraft.from_runtime_dict(draft.to_runtime_dict())
    assert restored == draft
