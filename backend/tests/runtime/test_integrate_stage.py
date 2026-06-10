"""Integrate stage tests."""

from __future__ import annotations

import pytest

from app.runtime.stages.domain_plan import DomainPlanStageHandler
from app.runtime.stages.integrate import IntegrateStageHandler
from app.runtime.state import create_initial_runtime_state

from .test_domain_planner_group import _state_with_chengdu_context


@pytest.mark.asyncio
async def test_integrate_stage_writes_itinerary_draft() -> None:
    domain_result = await DomainPlanStageHandler().handle(_state_with_chengdu_context())
    state = domain_result["data"]["state"]

    result = await IntegrateStageHandler().handle(state)

    assert result["status"] == "completed"
    assert result["data"]["itinerary_draft"]["travel_days"] == 3
    assert len(result["data"]["itinerary_draft"]["days"]) == 3
    assert result["data"]["state"]["itinerary_draft"]["destination"] == "成都"


@pytest.mark.asyncio
async def test_integrate_stage_fails_without_plan_proposals() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )

    result = await IntegrateStageHandler().handle(state)

    assert result["status"] == "failed"
    assert result["data"]["error"]["type"] == "missing_plan_proposals"
