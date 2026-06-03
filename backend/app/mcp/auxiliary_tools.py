"""协调器辅助 MCP 工具（日期、周边搜索等）。"""

from __future__ import annotations

from langchain_core.tools import BaseTool
from loguru import logger

from app.mcp.client import AMAP_SERVER, TRAIN_SERVER, VARIFLIGHT_SERVER
from app.mcp.manager import get_mcp_manager
from app.mcp.registry import run_async
from app.settings import settings

AUXILIARY_TOOL_KEYWORDS = (
    "getfutureweather",
    "maps_around_search",
)


def _auxiliary_server_names() -> list[str]:
    servers: list[str] = []
    if settings.mcp_train_url:
        servers.append(TRAIN_SERVER)
    if settings.amap_api_key:
        servers.append(AMAP_SERVER)
    if settings.variflight_api_key:
        servers.append(VARIFLIGHT_SERVER)
    return servers


async def get_auxiliary_mcp_tools() -> list[BaseTool]:
    """从 train / amap / variflight MCP 加载协调器辅助工具。"""
    servers = _auxiliary_server_names()
    if not servers:
        return []

    try:
        manager = await get_mcp_manager(servers=servers)
        all_tools = await manager.get_tools()
    except Exception as exc:
        logger.warning("加载辅助 MCP 工具失败: {}", exc)
        return []

    auxiliary = [
        tool
        for tool in all_tools
        if any(keyword in tool.name.lower() for keyword in AUXILIARY_TOOL_KEYWORDS)
    ]
    logger.info("协调器辅助 MCP 工具: {}", [tool.name for tool in auxiliary])
    return auxiliary


def get_auxiliary_mcp_tools_sync() -> list[BaseTool]:
    return run_async(get_auxiliary_mcp_tools())
