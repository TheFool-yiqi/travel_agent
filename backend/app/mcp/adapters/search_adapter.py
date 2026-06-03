"""搜索 MCP 适配器。"""

from __future__ import annotations

from app.mcp.providers.tavily import fetch_travel_search_json
from app.mcp.registry import get_registry
from app.settings import settings

SEARCH_SERVER = "search"
SEARCH_TOOL = "search_travel_info"


def search_travel_info(query: str, max_results: int = 5) -> str:
    """
    搜索旅游相关信息。

    - inprocess：直连 Tavily provider
    - stdio：经 MCP registry 调用本地 search_server
    """
    if settings.mcp_search_transport == "stdio":
        return get_registry().call_tool_sync(
            SEARCH_SERVER,
            SEARCH_TOOL,
            {"query": query, "max_results": max_results},
        )
    return fetch_travel_search_json(query, max_results=max_results)
