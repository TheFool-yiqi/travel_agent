"""step_config 与 MCP 工具注入测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.step_config import (
    get_step_config,
    get_step_config_sync,
    get_step_tools,
    reset_step_mcp_cache,
)
from app.graph.step_context import run_step_tools
from app.mcp.manager import reset_mcp_manager
from app.tools.datetime_tools import get_current_date


@pytest.fixture(autouse=True)
def reset_mcp() -> None:
    reset_mcp_manager()
    reset_step_mcp_cache()
    yield
    reset_mcp_manager()
    reset_step_mcp_cache()


def test_sync_step_config_has_core_tools() -> None:
    config = get_step_config_sync()
    assert "get-current-date" in {t.name for t in config["collect_requirements"]["tools"]}
    dest_tools = {t.name for t in config["plan_destination"]["tools"]}
    assert "query_destination_info" in dest_tools
    assert "search_web_travel_info" in dest_tools
    assert "query_transport_options" in {t.name for t in config["plan_transport"]["tools"]}


@pytest.mark.asyncio
async def test_async_get_step_config_loads_mcp_tools() -> None:
    hotel = MagicMock()
    hotel.name = "find-hotels"
    search = MagicMock()
    search.name = "search_travel_info"

    with patch(
        "app.tools.mcp_tools.get_hotel_tools",
        AsyncMock(return_value=[hotel]),
    ), patch(
        "app.tools.mcp_tools.get_search_tools",
        AsyncMock(return_value=[search]),
    ), patch(
        "app.tools.mcp_tools.get_date_tools",
        AsyncMock(return_value=[get_current_date]),
    ):
        config = await get_step_config()

    hotel_names = {t.name for t in config["plan_stay_and_food"]["tools"]}
    assert "find-hotels" in hotel_names
    search_names = {t.name for t in config["plan_destination"]["tools"]}
    assert "search_travel_info" in search_names


def test_run_step_tools_search_runner() -> None:
    state = {
        "user_requirement": {"destination": "西安"},
        "selected_destination": "西安",
    }
    with patch(
        "app.graph.step_context.fetch_destination_info",
        return_value="mock destination report",
    ), patch(
        "app.graph.step_context.fetch_travel_search",
        return_value='{"query":"西安"}',
    ):
        text = run_step_tools("plan_destination", state)
    assert "mock destination report" in text
    assert "西安" in text
