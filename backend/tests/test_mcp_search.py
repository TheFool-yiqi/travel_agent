"""MCP 搜索层测试。"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

import app.mcp.adapters.search_adapter as search_adapter_module
import app.mcp.client as mcp_client_module
from app.mcp.adapters.search_adapter import search_travel_info
from app.mcp.client import build_mcp_connections
from app.mcp.providers.tavily import fetch_travel_search_json
from app.mcp.registry import reset_registry
from app.mcp.servers.search_server import search_travel_info as server_search_travel_info
from app.settings import settings
from app.tools.search import fetch_travel_search


@pytest.fixture(autouse=True)
def reset_mcp_caches() -> None:
    reset_registry()
    mcp_client_module.reset_mcp_client()
    yield
    reset_registry()
    mcp_client_module.reset_mcp_client()


def test_build_mcp_connections_search_stdio() -> None:
    with patch.object(settings, "mcp_search_transport", "stdio"):
        mcp_client_module.reset_mcp_client()
        connections = build_mcp_connections()
        assert "search" in connections
        assert connections["search"]["transport"] == "stdio"


def test_search_travel_info_inprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "mcp_search_transport", "inprocess")
    monkeypatch.setattr(
        search_adapter_module,
        "fetch_travel_search_json",
        lambda query, max_results=5: json.dumps({"query": query}),
    )
    result = search_travel_info("西安旅游攻略")
    assert json.loads(result)["query"] == "西安旅游攻略"


def test_search_travel_info_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "mcp_search_transport", "stdio")
    mock_registry = MagicMock()
    mock_registry.call_tool_sync.return_value = '{"query":"mcp"}'
    monkeypatch.setattr(search_adapter_module, "get_registry", lambda: mock_registry)

    assert search_travel_info("西安", max_results=3) == '{"query":"mcp"}'
    mock_registry.call_tool_sync.assert_called_once_with(
        "search",
        "search_travel_info",
        {"query": "西安", "max_results": 3},
    )


def test_tools_search_delegates_to_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.tools.search.search_travel_info",
        lambda query, max_results=5: f"tool:{query}",
    )
    assert fetch_travel_search("成都美食") == "tool:成都美食"


def test_tavily_unconfigured_returns_error_json() -> None:
    with patch.object(settings, "tavily_api_key", ""):
        payload = json.loads(fetch_travel_search_json("西安"))
        assert "error" in payload


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.tavily_api_key, reason="需要 TAVILY_API_KEY")
async def test_search_server_travel_query() -> None:
    result = await server_search_travel_info("西安旅游攻略", max_results=3)
    payload = json.loads(result)
    assert payload.get("query") == "西安旅游攻略"
    assert "results" in payload


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.tavily_api_key, reason="需要 TAVILY_API_KEY")
async def test_search_server_attractions() -> None:
    """景点搜索（参考 Handoffs：西安必去景点推荐）。"""
    result = await server_search_travel_info("西安必去景点推荐")
    payload = json.loads(result)
    assert payload.get("query") == "西安必去景点推荐"
    assert "results" in payload
    assert isinstance(payload["results"], list)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.tavily_api_key, reason="需要 TAVILY_API_KEY")
async def test_search_server_food() -> None:
    """美食搜索（参考 Handoffs：西安特色美食小吃，max_results=3）。"""
    result = await server_search_travel_info("西安特色美食小吃", max_results=3)
    payload = json.loads(result)
    assert payload.get("query") == "西安特色美食小吃"
    assert "results" in payload
    assert len(payload["results"]) <= 3


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.tavily_api_key, reason="需要 TAVILY_API_KEY")
@pytest.mark.skipif(
    settings.mcp_search_transport != "stdio",
    reason="需要 MCP_SEARCH_TRANSPORT=stdio",
)
async def test_mcp_stdio_search_roundtrip() -> None:
    """stdio 模式下 registry 调用本地 search_server。"""
    from app.mcp.registry import get_registry

    text = await get_registry().call_tool(
        "search",
        "search_travel_info",
        {"query": "西安旅游攻略", "max_results": 3},
    )
    payload = json.loads(text)
    assert payload.get("query") == "西安旅游攻略"
    assert "results" in payload


async def _run_manual_search_demo() -> None:
    """参考 Handoffs 脚本：直接 await server 函数（非 .fn）。"""
    print("=== 测试景点搜索 ===")
    print(await server_search_travel_info("西安必去景点推荐"))

    print("\n=== 测试美食搜索 ===")
    print(await server_search_travel_info("西安特色美食小吃", 3))


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_manual_search_demo())
