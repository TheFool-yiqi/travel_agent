"""天气查询（tools 层入口 → mcp/adapters）。"""



from __future__ import annotations



from langchain_core.tools import tool



from app.mcp.adapters.weather_adapter import get_weather_forecast





def fetch_weather_info(destination: str) -> str:

    """查询目的地天气（实时 + 3 日预报）。"""

    return get_weather_forecast(destination)





@tool

def query_destination_weather(destination: str) -> str:

    """

    查询目的地实时天气与未来 3 日预报。



    Args:

        destination: 城市名称，如「西安」

    """

    return fetch_weather_info(destination)

