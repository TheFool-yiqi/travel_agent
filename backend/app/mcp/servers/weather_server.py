"""
天气 MCP Server（FastMCP + stdio）

独立运行：
  cd backend && uv run python -m app.mcp.servers.weather_server

或在项目根：
  uv run python -m app.mcp.servers.weather_server
"""
from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.tools.tool import Tool

from app.mcp.providers.qweather import fetch_weather_markdown

mcp = FastMCP("weather-service")


async def get_weather_forecast(city: str) -> str:
    """
    查询城市天气预报（实时 + 未来 3 日）。

    Args:
        city: 中文城市名，如「西安」「北京」
    """
    return fetch_weather_markdown(city)


mcp.add_tool(Tool.from_function(get_weather_forecast))


if __name__ == "__main__":
    mcp.run(transport="stdio")
