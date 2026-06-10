"""PlanningRuntime resume behavior tests."""

from __future__ import annotations

import pytest

from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.stages.base import build_default_stage_handlers
from app.runtime.state import RuntimeState, create_initial_runtime_state, record_collect_waiting


@pytest.mark.asyncio
async def test_planning_runtime_resumes_at_collect_when_awaiting_user() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="3天",
    )
    state = record_collect_waiting(
        RuntimeState(
            **{
                **state,
                "current_stage": "collect",
                "completed_stages": ["collect"],
            },
        ),
    )

    runtime = PlanningRuntime(build_default_stage_handlers())
    started = [
        event.stage
        for event in [event async for event in runtime.run(state)]
        if event.type == "stage_started"
    ]

    assert started == ["collect"]


@pytest.mark.asyncio
async def test_planning_runtime_resumes_from_approve_or_revise() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="确认",
    )
    state = record_collect_waiting(
        RuntimeState(
            **{
                **state,
                "current_stage": "approve_or_revise",
                "completed_stages": [
                    "collect",
                    "prepare_base_context",
                    "retrieve_evidence",
                    "tool_enrich",
                    "domain_plan",
                    "integrate",
                    "verify",
                    "approve_or_revise",
                ],
                "itinerary_draft": {
                    "destination": "成都",
                    "travel_days": 3,
                    "days": [{"day_number": 1, "theme": "抵达", "activities": []}],
                },
                "approval_status": "pending",
            },
        ),
    )

    runtime = PlanningRuntime(build_default_stage_handlers())
    started = [
        event.stage
        for event in [event async for event in runtime.run(state)]
        if event.type == "stage_started"
    ]

    assert started == ["approve_or_revise", "finalize"]
