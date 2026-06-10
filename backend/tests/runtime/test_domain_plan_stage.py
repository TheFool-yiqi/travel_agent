"""Domain-plan stage tests."""

from __future__ import annotations

import pytest

from app.runtime.stages.domain_plan import DomainPlanStageHandler

from .test_domain_planner_group import _state_with_chengdu_context


@pytest.mark.asyncio
async def test_domain_plan_stage_writes_plan_proposals() -> None:
    result = await DomainPlanStageHandler().handle(_state_with_chengdu_context())

    assert result["status"] == "completed"
    assert len(result["data"]["plan_proposals"]) == 3
    assert result["data"]["state"]["plan_proposals"][0]["agent_name"] == "destination_planner"


@pytest.mark.asyncio
async def test_domain_plan_stage_fails_without_planning_need() -> None:
    from app.runtime.state import create_initial_runtime_state

    result = await DomainPlanStageHandler().handle(
        create_initial_runtime_state(
            run_id="run_1",
            conversation_id="conv_1",
            input_message="成都",
        ),
    )

    assert result["status"] == "failed"
