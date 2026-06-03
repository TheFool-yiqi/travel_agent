"""MCP 工具筛选器单元测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.mcp.tool_filters import (
    get_all_mcp_tools,
    get_date_tools,
    get_hotel_tools,
    get_search_tools,
    get_weather_tools,
)
from app.mcp.manager import reset_mcp_manager


@pytest.fixture(autouse=True)
def reset_manager() -> None:
    reset_mcp_manager()
    yield
    reset_mcp_manager()


def _mock_tool(name: str) -> MagicMock:
    tool = MagicMock()
    tool.name = name
    return tool


@pytest.mark.asyncio
async def test_get_all_mcp_tools() -> None:
    tools = [
        _mock_tool("get_weather_forecast"),
        _mock_tool("search_travel_info"),
    ]
    with patch("app.mcp.tool_filters._load_tools", AsyncMock(return_value=tools)):
        result = await get_all_mcp_tools()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_hotel_tools_filters_keywords() -> None:
    tools = [
        _mock_tool("find-hotels"),
        _mock_tool("maps_around_search"),
        _mock_tool("get-tickets"),
    ]
    with patch("app.mcp.tool_filters._load_tools", AsyncMock(return_value=tools)):
        result = await get_hotel_tools()
    assert {tool.name for tool in result} == {"find-hotels", "maps_around_search"}


@pytest.mark.asyncio
async def test_get_weather_tools() -> None:
    tools = [_mock_tool("get_weather_forecast"), _mock_tool("search_travel_info")]
    with patch("app.mcp.tool_filters._load_tools", AsyncMock(return_value=tools)):
        result = await get_weather_tools()
    assert [tool.name for tool in result] == ["get_weather_forecast"]


@pytest.mark.asyncio
async def test_get_search_tools() -> None:
    tools = [_mock_tool("search_travel_info")]
    with patch("app.mcp.tool_filters._load_tools", AsyncMock(return_value=tools)):
        result = await get_search_tools()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_date_tools_defaults_to_local_only() -> None:
    with patch("app.mcp.tool_filters._load_tools", AsyncMock()) as load_mock:
        result = await get_date_tools()
    load_mock.assert_not_called()
    assert len(result) == 1
    assert result[0].name == "get-current-date"


@pytest.mark.asyncio
async def test_get_date_tools_can_include_mcp_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.settings import settings

    monkeypatch.setattr(settings, "mcp_include_date_tools", True)
    tools = [_mock_tool("gettodaydate"), _mock_tool("get-current-date")]
    with patch("app.mcp.tool_filters._load_tools", AsyncMock(return_value=tools)):
        result = await get_date_tools()
    names = [tool.name for tool in result]
    assert names[0] == "get-current-date"
    assert "gettodaydate" in names
    assert names.count("get-current-date") == 1
