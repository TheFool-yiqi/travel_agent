"""MCP 工具筛选器：按需获取特定类型的 LangChain Tool。"""

from __future__ import annotations

from collections.abc import Sequence

from langchain_core.tools import BaseTool
from loguru import logger

from app.mcp.client import (
    AIGOHOTEL_SERVER,
    AMAP_SERVER,
    SEARCH_SERVER,
    TRAIN_SERVER,
    VARIFLIGHT_SERVER,
    WEATHER_SERVER,
    build_manager_connections,
)
from app.mcp.manager import get_mcp_manager
from app.mcp.registry import run_async
from app.settings import settings
from app.tools.datetime_tools import get_current_date

HOTEL_TOOL_KEYWORDS = (
    "find-hotels",
    "find_hotels",
    "hotel",
    "maps_around_search",
)

WEATHER_TOOL_KEYWORDS = (
    "get_weather_forecast",
    "getfutureweather",
    "weather",
)

SEARCH_TOOL_KEYWORDS = (
    "search_travel_info",
    "search",
)

DATE_MCP_KEYWORDS = (
    "gettodaydate",
    "todaydate",
)


def _configured_server_names() -> list[str]:
    """当前 .env 下实际可连的 MCP 服务名。"""
    return list(build_manager_connections().keys())


def _filter_tools(tools: Sequence[BaseTool], keywords: Sequence[str]) -> list[BaseTool]:
    lowered = tuple(k.lower() for k in keywords)
    return [
        tool
        for tool in tools
        if any(keyword in tool.name.lower() for keyword in lowered)
    ]


async def _load_tools(servers: list[str] | None = None) -> list[BaseTool]:
    if servers is not None:
        selected = [name for name in servers if name in build_manager_connections(servers)]
        if not selected:
            return []
    else:
        selected = _configured_server_names()
    if not selected:
        return []

    try:
        manager = await get_mcp_manager(servers=selected)
        return await manager.get_tools()
    except Exception as exc:
        logger.warning("加载 MCP 工具失败 servers={}: {}", selected, exc)
        return []


async def get_all_mcp_tools() -> list[BaseTool]:
    """获取所有已配置 MCP 服务上的工具。"""
    tools = await _load_tools()
    logger.info("获取了 {} 个 MCP 工具", len(tools))
    return tools


async def get_hotel_tools() -> list[BaseTool]:
    """酒店搜索、周边 POI 等工具（aigohotel + 高德）。"""
    servers = [name for name in (AIGOHOTEL_SERVER, AMAP_SERVER) if name in _configured_server_names()]
    tools = _filter_tools(await _load_tools(servers or None), HOTEL_TOOL_KEYWORDS)
    logger.info("酒店工具: {}", [tool.name for tool in tools])
    return tools


async def get_weather_tools() -> list[BaseTool]:
    """天气查询工具（本地 weather MCP Server）。"""
    tools = _filter_tools(
        await _load_tools([WEATHER_SERVER] if WEATHER_SERVER in _configured_server_names() else []),
        WEATHER_TOOL_KEYWORDS,
    )
    logger.info("天气工具: {}", [tool.name for tool in tools])
    return tools


async def get_search_tools() -> list[BaseTool]:
    """旅游信息搜索工具（本地 search MCP Server）。"""
    tools = _filter_tools(
        await _load_tools([SEARCH_SERVER] if SEARCH_SERVER in _configured_server_names() else []),
        SEARCH_TOOL_KEYWORDS,
    )
    logger.info("搜索工具: {}", [tool.name for tool in tools])
    return tools


async def get_date_tools() -> list[BaseTool]:
    """
    日期工具：默认仅本地 get-current-date（北京时间）。

    设置 MCP_INCLUDE_DATE_TOOLS=true 时，额外追加 12306/飞常准 MCP 日期工具。
    """
    tools: list[BaseTool] = [get_current_date]

    if settings.mcp_include_date_tools:
        servers = [
            name
            for name in (TRAIN_SERVER, VARIFLIGHT_SERVER)
            if name in _configured_server_names()
        ]
        for tool in _filter_tools(await _load_tools(servers or None), DATE_MCP_KEYWORDS):
            if tool.name != get_current_date.name:
                tools.append(tool)

    logger.info("日期工具: {}", [tool.name for tool in tools])
    return tools


def get_all_mcp_tools_sync() -> list[BaseTool]:
    return run_async(get_all_mcp_tools())


def get_hotel_tools_sync() -> list[BaseTool]:
    return run_async(get_hotel_tools())


def get_weather_tools_sync() -> list[BaseTool]:
    return run_async(get_weather_tools())


def get_search_tools_sync() -> list[BaseTool]:
    return run_async(get_search_tools())


def get_date_tools_sync() -> list[BaseTool]:
    return run_async(get_date_tools())
