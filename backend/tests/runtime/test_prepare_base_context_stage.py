"""Prepare-base-context stage tests."""

from __future__ import annotations

import pytest

from app.runtime.collect.schemas import PlanningFact, PlanningNeed
from app.runtime.stages.prepare_base_context import PrepareBaseContextStageHandler
from app.runtime.state import create_initial_runtime_state, set_collect_context, set_planning_need


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
        risk_flags=["explicit_draft_request"],
    ).to_runtime_dict()


@pytest.mark.asyncio
async def test_prepare_base_context_builds_from_planning_need() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_planning_need(state, _planning_need_dict())

    result = await PrepareBaseContextStageHandler().handle(state)

    assert result["status"] == "completed"
    assert result["data"]["base_context"]["planning_need_summary"]["destination"] == "成都"
    assert result["data"]["state"]["base_context"]["planning_need_summary"]["travel_days"] == 3
    assert len(result["data"]["base_context"]["session_facts"]) == 2


@pytest.mark.asyncio
async def test_prepare_base_context_fails_without_planning_need() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )

    result = await PrepareBaseContextStageHandler().handle(state)

    assert result["status"] == "failed"
    assert result["data"]["error"]["type"] == "missing_planning_need"


@pytest.mark.asyncio
async def test_prepare_base_context_does_not_read_collect_context() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_collect_context(
        state,
        {"trip_spec": {"destination": "上海", "secret": "should-not-leak"}},
    )
    state = set_planning_need(state, _planning_need_dict())

    result = await PrepareBaseContextStageHandler().handle(state)

    summary = result["data"]["base_context"]["planning_need_summary"]
    assert summary["destination"] == "成都"
    assert "secret" not in str(summary)


@pytest.mark.asyncio
async def test_prepare_base_context_accepts_injected_memory_snippets() -> None:
    async def loader(_state):
        return [{"type": "preference", "text": "不吃辣"}]

    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_planning_need(state, _planning_need_dict())

    result = await PrepareBaseContextStageHandler(memory_snippet_loader=loader).handle(state)

    assert result["data"]["base_context"]["memory_snippets"] == [
        {"type": "preference", "text": "不吃辣"},
    ]
