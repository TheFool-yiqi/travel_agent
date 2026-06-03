"""高铁 Subagent + 12306 MCP 测试。"""

from __future__ import annotations

import pytest
from langchain_core.tools import tool

import app.agents.transport.train_subagent as train_module
from app.agents.transport.train_subagent import (
    clear_train_subagent_cache,
    create_train_subagent,
    run_train_subagent,
)


@pytest.fixture(autouse=True)
def reset_train_cache() -> None:
    clear_train_subagent_cache()
    yield
    clear_train_subagent_cache()


@tool
def mock_railway_tool(query: str) -> str:
    """mock 12306 tool"""
    return f"mock:{query}"


def test_create_train_subagent_uses_mock_without_mcp_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(train_module.settings, "mcp_train_url", "")
    monkeypatch.setattr(train_module, "get_railway_mcp_tools_sync", lambda: [])

    assert create_train_subagent() is not None


def test_create_train_subagent_with_mcp_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        train_module.settings,
        "mcp_train_url",
        "https://example.com/mcp",
    )
    monkeypatch.setattr(
        train_module,
        "get_railway_mcp_tools_sync",
        lambda: [mock_railway_tool],
    )

    assert create_train_subagent() is not None


def test_run_train_subagent_fallback_without_mimo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(train_module.settings, "mimo_api_key", "")
    report = run_train_subagent("北京", "上海", "2026-01-17")
    assert "G123" in report or "车次" in report


@pytest.mark.integration
@pytest.mark.asyncio
async def test_railway_mcp_tools_load() -> None:
    from app.mcp.railway_tools import get_railway_mcp_tools

    if not train_module.settings.mcp_train_url:
        pytest.skip("需要 MCP_TRAIN_URL")

    tools = await get_railway_mcp_tools()
    assert len(tools) > 0
    names = [tool.name for tool in tools]
    assert any("ticket" in name.lower() or "station" in name.lower() for name in names)


async def _run_manual_train_demo() -> None:
    print("=" * 50)
    print("初始化高铁 Subagent...")
    agent = await train_module.create_train_subagent_async()
    query = "帮我查一下2026-1-17从北京到上海的火车票"
    print(f"用户: {query}")
    result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_manual_train_demo())
