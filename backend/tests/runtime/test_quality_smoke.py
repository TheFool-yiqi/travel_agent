"""Slice 7 quality verification integration smoke tests."""

from __future__ import annotations

import pytest

from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.stages.base import build_default_stage_handlers
from app.runtime.stages.tool_enrich import ToolEnrichStageHandler
from app.runtime.state import RuntimeState, set_planning_need
from app.runtime.tools.service import ToolService
from app.runtime.tools.weather_adapter import WeatherToolAdapter

from .test_collect_context_smoke import _COLLECT_TURN_SEQUENCE, _run_collect_sequence
from .test_domain_planning_smoke import _handlers_with_stub_weather


@pytest.mark.asyncio
async def test_full_runtime_runs_through_verify_and_produces_quality_report() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    assert ready_turn.status == "ready"

    state = set_planning_need(state, ready_turn.planning_need)
    state = RuntimeState(**{**state, "input_message": "确认"})

    events = [event async for event in PlanningRuntime(_handlers_with_stub_weather()).run(state)]

    verify_completed = next(
        event for event in events if event.type == "stage_completed" and event.stage == "verify"
    )
    output = verify_completed.payload["output"]
    assert output["status"] == "completed"
    assert output["data"]["quality_report"]["verified_at"]
    assert events[-1].type == "runtime_completed"
