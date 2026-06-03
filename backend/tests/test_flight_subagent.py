"""航班 Subagent + Aviation MCP 测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.tools import tool

import app.agents.transport.flight_subagent as flight_module
from app.agents.transport.flight_subagent import (
    clear_flight_subagent_cache,
    create_flight_subagent,
    run_flight_subagent,
)


@pytest.fixture(autouse=True)
def reset_flight_cache() -> None:
    clear_flight_subagent_cache()
    yield
    clear_flight_subagent_cache()


@tool
def mock_flight_tool(query: str) -> str:
    """mock aviation tool"""
    return f"mock:{query}"


def test_create_flight_subagent_uses_mock_without_variflight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(flight_module.settings, "variflight_api_key", "")
    monkeypatch.setattr(flight_module, "get_aviation_mcp_tools_sync", lambda: [])

    agent = create_flight_subagent()
    assert agent is not None


def test_create_flight_subagent_with_mcp_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(flight_module.settings, "variflight_api_key", "test-key")
    monkeypatch.setattr(
        flight_module,
        "get_aviation_mcp_tools_sync",
        lambda: [mock_flight_tool],
    )

    agent = create_flight_subagent()
    assert agent is not None


def test_run_flight_subagent_fallback_without_mimo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(flight_module.settings, "mimo_api_key", "")
    report = run_flight_subagent("北京", "上海", "2025-08-01")
    assert "CA1234" in report or "航班" in report


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not flight_module.settings.variflight_api_key, reason="需要 VARIFLIGHT_API_KEY")
async def test_aviation_mcp_tools_load() -> None:
    from app.mcp.aviation_tools import get_aviation_mcp_tools

    tools = await get_aviation_mcp_tools()
    assert len(tools) > 0
    names = [tool.name for tool in tools]
    assert any("flight" in name.lower() or "date" in name.lower() for name in names)


async def _run_manual_flight_demo() -> None:
    print("=" * 50)
    print("初始化航班 Subagent...")
    agent = await flight_module.create_flight_subagent_async()
    query = "帮我查一下明天从北京到上海的航班"
    print(f"用户: {query}")
    result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_manual_flight_demo())
