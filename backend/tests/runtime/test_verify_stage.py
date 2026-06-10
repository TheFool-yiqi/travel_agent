"""Verify stage tests."""

from __future__ import annotations

import pytest

from app.runtime.stages.domain_plan import DomainPlanStageHandler
from app.runtime.stages.integrate import IntegrateStageHandler
from app.runtime.stages.verify import VerifyStageHandler
from app.runtime.state import create_initial_runtime_state

from .test_domain_planner_group import _state_with_chengdu_context


async def _state_after_integrate():
    domain_result = await DomainPlanStageHandler().handle(_state_with_chengdu_context())
    integrate_result = await IntegrateStageHandler().handle(domain_result["data"]["state"])
    return integrate_result["data"]["state"]


@pytest.mark.asyncio
async def test_verify_stage_writes_quality_report() -> None:
    state = await _state_after_integrate()

    result = await VerifyStageHandler().handle(state)

    assert result["status"] == "completed"
    assert result["data"]["quality_report"]["verified_at"]
    assert result["data"]["state"]["quality_report"]


@pytest.mark.asyncio
async def test_verify_stage_applies_auto_revision_for_blocking_issues() -> None:
    state = await _state_after_integrate()
    draft = dict(state["itinerary_draft"])
    draft["assumptions"] = []
    state = {**state, "itinerary_draft": draft}

    result = await VerifyStageHandler().handle(state)

    assert result["status"] == "completed"
    assert result["data"]["quality_report"]["revision_applied"] is True
    assert result["data"]["state"]["itinerary_draft"]["assumptions"]


@pytest.mark.asyncio
async def test_verify_stage_fails_without_itinerary_draft() -> None:
    result = await VerifyStageHandler().handle(
        create_initial_runtime_state(
            run_id="run_1",
            conversation_id="conv_1",
            input_message="成都",
        ),
    )

    assert result["status"] == "failed"
