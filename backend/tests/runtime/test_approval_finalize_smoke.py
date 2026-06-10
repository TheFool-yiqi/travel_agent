"""Slice 8 approval and finalize integration smoke tests."""

from __future__ import annotations

import pytest

from app.runtime.finalization.persistence import StubItineraryPersistenceAdapter
from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.stages.base import build_default_stage_handlers
from app.runtime.stages.finalize import FinalizeStageHandler
from app.runtime.stages.tool_enrich import ToolEnrichStageHandler
from app.runtime.state import RuntimeState, set_planning_need
from app.runtime.tools.service import ToolService
from app.runtime.tools.weather_adapter import WeatherToolAdapter

from .test_collect_context_smoke import _COLLECT_TURN_SEQUENCE, _run_collect_sequence


def _handlers_with_stub_weather_and_persistence(
    persistence: StubItineraryPersistenceAdapter,
) -> list:
    handlers = list(build_default_stage_handlers())
    tool_index = next(index for index, handler in enumerate(handlers) if handler.stage_name == "tool_enrich")
    handlers[tool_index] = ToolEnrichStageHandler(
        tool_service=ToolService(
            weather_adapter=WeatherToolAdapter(fetch_forecast=lambda _city: "成都 多云"),
        ),
    )
    finalize_index = next(
        index for index, handler in enumerate(handlers) if handler.stage_name == "finalize"
    )
    handlers[finalize_index] = FinalizeStageHandler(persistence=persistence)
    return handlers


@pytest.mark.asyncio
async def test_runtime_pauses_at_approval_until_user_confirms() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    state = set_planning_need(state, ready_turn.planning_need)
    state = RuntimeState(**{**state, "input_message": "请先给我看看"})

    events = [
        event
        async for event in PlanningRuntime(
            _handlers_with_stub_weather_and_persistence(StubItineraryPersistenceAdapter()),
        ).run(state)
    ]

    assert not any(event.type == "runtime_completed" for event in events)
    approval_event = next(
        event for event in events if event.type == "stage_completed" and event.stage == "approve_or_revise"
    )
    assert approval_event.payload["output"]["status"] == "waiting"


@pytest.mark.asyncio
async def test_runtime_completes_with_order_after_user_confirms() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    state = set_planning_need(state, ready_turn.planning_need)
    state = RuntimeState(
        **{
            **state,
            "input_message": "确认",
            "conversation_id": "conv_1",
            "user_id": "user_1",
        },
    )

    persistence = StubItineraryPersistenceAdapter()
    events = [
        event
        async for event in PlanningRuntime(
            _handlers_with_stub_weather_and_persistence(persistence),
        ).run(state)
    ]

    assert events[-1].type == "runtime_completed"
    finalize_event = next(
        event for event in events if event.type == "stage_completed" and event.stage == "finalize"
    )
    assert finalize_event.payload["output"]["data"]["order_id"].startswith("ORDER-")
    assert persistence.records
