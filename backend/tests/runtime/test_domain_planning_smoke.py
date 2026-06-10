"""Slice 6 domain planning integration smoke tests."""

from __future__ import annotations

import pytest

from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.stages.base import build_default_stage_handlers
from app.runtime.stages.tool_enrich import ToolEnrichStageHandler
from app.runtime.state import RuntimeState, set_planning_need
from app.runtime.tools.service import ToolService
from app.runtime.tools.weather_adapter import WeatherToolAdapter

from .test_collect_context_smoke import _COLLECT_TURN_SEQUENCE, _run_collect_sequence


def _handlers_with_stub_weather() -> list:
    handlers = list(build_default_stage_handlers())
    tool_index = next(index for index, handler in enumerate(handlers) if handler.stage_name == "tool_enrich")
    handlers[tool_index] = ToolEnrichStageHandler(
        tool_service=ToolService(
            weather_adapter=WeatherToolAdapter(fetch_forecast=lambda _city: "成都 多云"),
        ),
    )
    return handlers


@pytest.mark.asyncio
async def test_full_runtime_runs_through_integrate_and_produces_itinerary_draft() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    assert ready_turn.status == "ready"

    state = set_planning_need(state, ready_turn.planning_need)
    state = RuntimeState(**{**state, "input_message": "确认"})

    events = [event async for event in PlanningRuntime(_handlers_with_stub_weather()).run(state)]

    assert [event.stage for event in events if event.type == "stage_started"] == list(V1_STAGE_NAMES)
    assert events[-1].type == "runtime_completed"

    integrate_completed = next(
        event for event in events if event.type == "stage_completed" and event.stage == "integrate"
    )
    draft = integrate_completed.payload["output"]["data"]["itinerary_draft"]
    assert draft["destination"] == "成都"
    assert draft["travel_days"] == 3
    assert len(draft["days"]) == 3

    domain_completed = next(
        event for event in events if event.type == "stage_completed" and event.stage == "domain_plan"
    )
    assert len(domain_completed.payload["output"]["data"]["plan_proposals"]) == 3
