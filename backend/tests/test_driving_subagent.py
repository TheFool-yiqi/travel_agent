"""自驾 Subagent + 高德 MCP 测试。"""

from __future__ import annotations

import pytest
from langchain_core.tools import tool

import app.agents.transport.driving_subagent as driving_module
from app.agents.transport.driving_subagent import (
    clear_driving_subagent_cache,
    create_driving_subagent,
    run_driving_subagent,
)


@pytest.fixture(autouse=True)
def reset_driving_cache() -> None:
    clear_driving_subagent_cache()
    yield
    clear_driving_subagent_cache()


@tool
def mock_amap_tool(query: str) -> str:
    """mock amap tool"""
    return f"mock:{query}"


def test_create_driving_subagent_uses_mock_without_amap_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(driving_module.settings, "amap_api_key", "")
    monkeypatch.setattr(driving_module, "get_amap_mcp_tools_sync", lambda: [])

    assert create_driving_subagent() is not None


def test_create_driving_subagent_with_mcp_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(driving_module.settings, "amap_api_key", "test-key")
    monkeypatch.setattr(
        driving_module,
        "get_amap_mcp_tools_sync",
        lambda: [mock_amap_tool],
    )

    assert create_driving_subagent() is not None


def test_run_driving_subagent_fallback_without_mimo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(driving_module.settings, "mimo_api_key", "")
    report = run_driving_subagent("北京", "上海")
    assert "路线" in report or "公里" in report


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not driving_module.settings.amap_api_key, reason="需要 AMAP_API_KEY")
async def test_amap_mcp_tools_load() -> None:
    from app.mcp.amap_tools import get_amap_mcp_tools

    tools = await get_amap_mcp_tools()
    assert len(tools) > 0
    names = [tool.name.lower() for tool in tools]
    assert any("geo" in name or "driving" in name for name in names)


async def _run_manual_driving_demo() -> None:
    print("=" * 50)
    print("初始化自驾 Subagent...")
    agent = await driving_module.create_driving_subagent_async()
    query = "帮我规划一下从北京天安门到上海东方明珠的自驾路线"
    print(f"用户: {query}")
    result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_manual_driving_demo())
