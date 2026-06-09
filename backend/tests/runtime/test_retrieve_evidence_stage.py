"""Retrieve-evidence stage tests."""

from __future__ import annotations

import pytest

from app.knowledge.evidence_engine import EvidenceEngine
from app.runtime.collect.schemas import PlanningFact, PlanningNeed
from app.runtime.context.schemas import BaseContext
from app.runtime.stages.retrieve_evidence import RetrieveEvidenceStageHandler
from app.runtime.state import create_initial_runtime_state, set_base_context, set_planning_need


def _planning_need_dict() -> dict:
    return PlanningNeed(
        confirmed_facts=[
            PlanningFact(
                field="destination",
                value="成都",
                fact_type="confirmed",
                source="user",
            ),
            PlanningFact(
                field="travel_days",
                value=3,
                fact_type="confirmed",
                source="user",
            ),
        ],
        preferences=[{"field": "travel_styles", "value": ["food"]}],
    ).to_runtime_dict()


@pytest.mark.asyncio
async def test_retrieve_evidence_stage_writes_context_and_sufficiency() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_planning_need(state, _planning_need_dict())
    state = set_base_context(
        state,
        BaseContext(planning_need_summary={"destination": "成都", "travel_days": 3}).to_runtime_dict(),
    )

    result = await RetrieveEvidenceStageHandler().handle(state)

    assert result["status"] == "completed"
    assert result["data"]["evidence_context"]["card_ids"]
    assert result["data"]["sufficiency_result"]["suggested_action"] == "mark_assumptions_and_continue"
    assert result["data"]["state"]["evidence_context"]["card_ids"]
    assert all(
        card["status"] == "approved"
        for card in result["data"]["evidence_context"]["cards"]
    )


@pytest.mark.asyncio
async def test_retrieve_evidence_stage_fails_without_planning_need() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )

    result = await RetrieveEvidenceStageHandler().handle(state)

    assert result["status"] == "failed"
    assert result["data"]["error"]["type"] == "missing_planning_need"


@pytest.mark.asyncio
async def test_retrieve_evidence_stage_does_not_read_collect_context() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_planning_need(state, _planning_need_dict())

    result = await RetrieveEvidenceStageHandler(evidence_engine=EvidenceEngine()).handle(state)

    card_cities = {card["city"] for card in result["data"]["evidence_context"]["cards"]}
    assert card_cities == {"成都"}
