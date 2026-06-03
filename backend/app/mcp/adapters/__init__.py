"""MCP 协议适配层。"""

from app.mcp.adapters.search_adapter import search_travel_info
from app.mcp.adapters.weather_adapter import get_weather_forecast

__all__ = ["get_weather_forecast", "search_travel_info"]
