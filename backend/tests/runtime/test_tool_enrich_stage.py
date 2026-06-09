"""Tool-enrich stage tests."""

from __future__ import annotations

import pytest

from app.runtime.collect.schemas import PlanningFact, PlanningNeed
from app.runtime.context.schemas import BaseContext
from app.runtime.stages.tool_enrich import ToolEnrichStageHandler
from app.runtime.state import create_initial_runtime_state, set_base_context, set_planning_need
from app.runtime.tools.service import ToolService
from app.runtime.tools.weather_adapter import WeatherToolAdapter


def _planning_need_dict() -> dict:
    return PlanningNeed(
        confirmed_facts=[
            PlanningFact(
                field="destination",
                value="成都",
                fact_type="confirmed",
                source="user",
            ),
        ],
    ).to_runtime_dict()


@pytest.mark.asyncio
async def test_tool_enrich_stage_writes_tool_context() -> None:
    service = ToolService(
        weather_adapter=WeatherToolAdapter(
            fetch_forecast=lambda _city: "成都 多云 26°C",
        ),
    )
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_planning_need(state, _planning_need_dict())
    state = set_base_context(
        state,
        BaseContext(planning_need_summary={"destination": "成都"}).to_runtime_dict(),
    )

    result = await ToolEnrichStageHandler(tool_service=service).handle(state)

    assert result["status"] == "completed"
    assert result["data"]["tool_context"]["weather"]["status"] == "available"
    assert result["data"]["state"]["tool_context"]["weather"]["destination"] == "成都"


@pytest.mark.asyncio
async def test_tool_enrich_stage_fails_without_planning_need() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )

    result = await ToolEnrichStageHandler().handle(state)

    assert result["status"] == "failed"
    assert result["data"]["error"]["type"] == "missing_planning_need"


@pytest.mark.asyncio
async def test_tool_enrich_stage_completes_when_weather_unavailable() -> None:
    service = ToolService(
        weather_adapter=WeatherToolAdapter(fetch_forecast=lambda _city: ""),
    )
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_planning_need(state, _planning_need_dict())

    result = await ToolEnrichStageHandler(tool_service=service).handle(state)

    assert result["status"] == "completed"
    assert result["data"]["tool_context"]["weather"]["status"] == "unavailable"
