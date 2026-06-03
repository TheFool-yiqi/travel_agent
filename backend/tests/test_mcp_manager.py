"""MCPClientManager 测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.mcp.manager as manager_module
from app.mcp.client import (
    AIGOHOTEL_SERVER,
    AMAP_SERVER,
    SEARCH_SERVER,
    TRAIN_SERVER,
    VARIFLIGHT_SERVER,
    WEATHER_SERVER,
    build_manager_connections,
)
from app.mcp.manager import MCPClientManager, get_mcp_manager, reset_mcp_manager
from app.settings import settings


@pytest.fixture(autouse=True)
def reset_manager() -> None:
    reset_mcp_manager()
    yield
    reset_mcp_manager()


def test_build_manager_connections_local_stdio_always() -> None:
    connections = build_manager_connections([WEATHER_SERVER, SEARCH_SERVER])
    assert WEATHER_SERVER in connections
    assert SEARCH_SERVER in connections
    assert connections[WEATHER_SERVER]["transport"] == "stdio"


def test_build_manager_connections_skips_amap_without_key() -> None:
    with patch.object(settings, "amap_api_key", ""):
        connections = build_manager_connections([AMAP_SERVER])
    assert AMAP_SERVER not in connections


def test_build_manager_connections_includes_amap_with_key() -> None:
    with patch.object(settings, "amap_api_key", "test-key"):
        connections = build_manager_connections([AMAP_SERVER])
    assert connections[AMAP_SERVER]["transport"] == "http"
    assert "test-key" in connections[AMAP_SERVER]["url"]


def test_build_manager_connections_train_url() -> None:
    with patch.object(settings, "mcp_train_url", "https://example.com/mcp"):
        connections = build_manager_connections([TRAIN_SERVER])
    assert connections[TRAIN_SERVER]["transport"] == "streamable_http"


def test_build_manager_connections_variflight() -> None:
    with patch.object(settings, "variflight_api_key", "vf-key"):
        connections = build_manager_connections([VARIFLIGHT_SERVER])
    assert "vf-key" in connections[VARIFLIGHT_SERVER]["url"]


def test_build_manager_connections_aigohotel() -> None:
    with patch.object(settings, "aigohotel_api_key", "hotel-key"):
        connections = build_manager_connections([AIGOHOTEL_SERVER])
    assert connections[AIGOHOTEL_SERVER]["headers"]["Authorization"] == "Bearer hotel-key"


@pytest.mark.asyncio
async def test_manager_initialize_and_get_tools() -> None:
    mock_tool = MagicMock()
    mock_tool.name = "get_weather_forecast"
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[mock_tool])

    with patch.object(
        manager_module,
        "build_manager_connections",
        return_value={"weather": {"transport": "stdio", "command": "python", "args": []}},
    ):
        with patch.object(manager_module, "MultiServerMCPClient", return_value=mock_client):
            manager = await get_mcp_manager(servers=["weather"])

    tools = await manager.get_tools()
    assert len(tools) == 1
    assert tools[0].name == "get_weather_forecast"
    mock_client.get_tools.assert_called_once()


@pytest.mark.asyncio
async def test_manager_singleton() -> None:
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[])

    with patch.object(
        manager_module,
        "build_manager_connections",
        return_value={"weather": {"transport": "stdio", "command": "python", "args": []}},
    ):
        with patch.object(manager_module, "MultiServerMCPClient", return_value=mock_client):
            first = await get_mcp_manager(servers=["weather"])
            second = await get_mcp_manager(servers=["weather"])

    assert first is second


@pytest.mark.asyncio
async def test_manager_reset_instance() -> None:
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[])

    with patch.object(
        manager_module,
        "build_manager_connections",
        return_value={"weather": {"transport": "stdio", "command": "python", "args": []}},
    ):
        with patch.object(manager_module, "MultiServerMCPClient", return_value=mock_client):
            first = await get_mcp_manager(servers=["weather"])
            reset_mcp_manager()
            second = await get_mcp_manager(servers=["weather"])

    assert first is not second
