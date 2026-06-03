"""应用 lifespan 测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.lifespan import DEFAULT_MCP_SERVER_NAMES, mcp_lifespan


@pytest.mark.asyncio
async def test_mcp_lifespan_skips_when_no_connections() -> None:
    with patch("app.lifespan.build_manager_connections", return_value={}):
        async with mcp_lifespan() as manager:
            assert manager is None


@pytest.mark.asyncio
async def test_mcp_lifespan_initializes_configured_servers() -> None:
    mock_manager = MagicMock()
    mock_manager.servers = ["weather", "search"]
    mock_manager.get_tools = AsyncMock(return_value=[MagicMock(), MagicMock()])
    mock_manager.close = AsyncMock()

    with patch(
        "app.lifespan.build_manager_connections",
        return_value={"weather": {}, "search": {}},
    ), patch(
        "app.lifespan.get_mcp_manager",
        AsyncMock(return_value=mock_manager),
    ), patch("app.lifespan.reset_mcp_manager") as reset_mock:
        async with mcp_lifespan(servers=DEFAULT_MCP_SERVER_NAMES) as manager:
            assert manager is mock_manager
            assert len(await manager.get_tools()) == 2

    mock_manager.close.assert_awaited_once()
    reset_mock.assert_called_once()
