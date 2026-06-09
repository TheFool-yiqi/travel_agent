"""Slice 5 tool enrichment integration smoke tests."""

from __future__ import annotations

import pytest

from app.runtime.context.assembler import ContextAssembler
from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.stages.base import build_default_stage_handlers
from app.runtime.stages.tool_enrich import ToolEnrichStageHandler
from app.runtime.state import RuntimeState, set_planning_need
from app.runtime.tools.service import ToolService
from app.runtime.tools.weather_adapter import WeatherToolAdapter

from .test_collect_context_smoke import _COLLECT_TURN_SEQUENCE, _run_collect_sequence


@pytest.mark.asyncio
async def test_collect_ready_path_runs_tool_enrich_with_weather_context() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    assert ready_turn.status == "ready"

    state = set_planning_need(state, ready_turn.planning_need)
    service = ToolService(
        weather_adapter=WeatherToolAdapter(
            fetch_forecast=lambda _city: "成都 多云\n7月2日可能有阵雨",
        ),
    )
    result = await ToolEnrichStageHandler(tool_service=service).handle(
        RuntimeState(**{**state, "input_message": "确认"}),
    )

    assert result["status"] == "completed"
    assert result["data"]["tool_context"]["weather"]["status"] == "available"
    assert result["data"]["tool_context"]["weather"]["summary"]


@pytest.mark.asyncio
async def test_full_runtime_runs_through_tool_enrich_and_completes() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    assert ready_turn.status == "ready"

    state = set_planning_need(state, ready_turn.planning_need)
    state = RuntimeState(**{**state, "input_message": "确认"})

    handlers = list(build_default_stage_handlers())
    tool_index = next(index for index, handler in enumerate(handlers) if handler.stage_name == "tool_enrich")
    handlers[tool_index] = ToolEnrichStageHandler(
        tool_service=ToolService(
            weather_adapter=WeatherToolAdapter(fetch_forecast=lambda _city: ""),
        ),
    )

    events = [event async for event in PlanningRuntime(handlers).run(state)]

    assert [event.stage for event in events if event.type == "stage_started"] == list(V1_STAGE_NAMES)
    assert events[-1].type == "runtime_completed"

    tool_completed = next(
        event for event in events if event.type == "stage_completed" and event.stage == "tool_enrich"
    )
    output = tool_completed.payload["output"]
    assert output["status"] == "completed"
    assert output["data"]["tool_context"]["weather"]["status"] == "unavailable"

    agent_context = ContextAssembler().assemble(
        "itinerary_integrator",
        RuntimeState(**output["data"]["state"]),
    )
    assert agent_context["weather_summary"]["status"] == "unavailable"
    assert "collect_context" not in agent_context
