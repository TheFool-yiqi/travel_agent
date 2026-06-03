"""天气 MCP 适配器。"""

from __future__ import annotations

from app.mcp.providers.qweather import fetch_weather_markdown
from app.mcp.registry import get_registry
from app.settings import settings

WEATHER_SERVER = "weather"
WEATHER_TOOL = "get_weather_forecast"


def get_weather_forecast(city: str) -> str:
    """
    查询城市天气预报。

    - inprocess：直连 QWeather provider
    - stdio：经 MCP registry 调用本地 weather_server
    """
    if settings.mcp_weather_transport == "stdio":
        return get_registry().call_tool_sync(
            WEATHER_SERVER,
            WEATHER_TOOL,
            {"city": city},
        )
    return fetch_weather_markdown(city)
