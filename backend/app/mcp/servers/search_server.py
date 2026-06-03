"""
搜索 MCP Server（FastMCP + stdio / Tavily）

独立运行：
  cd backend && uv run python -m app.mcp.servers.search_server
"""
from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.tools.tool import Tool

from app.mcp.providers.tavily import fetch_travel_search_json

mcp = FastMCP("search-service")


async def search_travel_info(query: str, max_results: int = 5) -> str:
    """
    搜索旅游相关信息（景点、攻略、美食、住宿等）。

    Args:
        query: 搜索关键词，如「西安旅游攻略」「成都美食推荐」
        max_results: 返回条数，默认 5，最多 10
    """
    return fetch_travel_search_json(query, max_results=max_results)


mcp.add_tool(Tool.from_function(search_travel_info))


if __name__ == "__main__":
    mcp.run(transport="stdio")
