"""高德地图 MCP 工具加载。"""

from __future__ import annotations

from langchain_core.tools import BaseTool
from loguru import logger

from app.mcp.client import AMAP_SERVER
from app.mcp.manager import get_mcp_manager
from app.mcp.registry import run_async
from app.settings import settings

AMAP_TOOL_KEYWORDS = (
    "maps_direction_driving",
    "maps_geo",
    "direction",
    "driving",
    "geo",
)


async def get_amap_mcp_tools() -> list[BaseTool]:
    """从高德 HTTP MCP 加载驾车/地理编码工具。"""
    if not settings.amap_api_key:
        return []

    try:
        manager = await get_mcp_manager(servers=[AMAP_SERVER])
        tools = await manager.get_tools_by_server(AMAP_SERVER)
    except Exception as exc:
        logger.warning("加载高德 MCP 工具失败: {}", exc)
        return []

    amap_tools = [
        tool
        for tool in tools
        if any(keyword in tool.name.lower() for keyword in AMAP_TOOL_KEYWORDS)
    ]
    if not amap_tools and tools:
        amap_tools = list(tools)

    logger.info("高德 MCP 工具: {}", [tool.name for tool in amap_tools])
    return amap_tools


def get_amap_mcp_tools_sync() -> list[BaseTool]:
    return run_async(get_amap_mcp_tools())
