"""12306 高铁 MCP 工具加载。"""

from __future__ import annotations

from langchain_core.tools import BaseTool
from loguru import logger

from app.mcp.client import TRAIN_SERVER
from app.mcp.manager import get_mcp_manager
from app.mcp.registry import run_async
from app.settings import settings

RAILWAY_TOOL_KEYWORDS = (
    "station",
    "ticket",
    "train",
    "get-current-date",
    "interline",
    "route",
)


async def get_railway_mcp_tools() -> list[BaseTool]:
    """从 12306 MCP（ModelScope streamable_http）加载高铁工具。"""
    if not settings.mcp_train_url:
        return []

    try:
        manager = await get_mcp_manager(servers=[TRAIN_SERVER])
        tools = await manager.get_tools_by_server(TRAIN_SERVER)
    except Exception as exc:
        logger.warning("加载 12306 MCP 工具失败: {}", exc)
        return []

    railway_tools = [
        tool
        for tool in tools
        if any(keyword in tool.name.lower() for keyword in RAILWAY_TOOL_KEYWORDS)
    ]
    if not railway_tools and tools:
        railway_tools = list(tools)

    logger.info("高铁 MCP 工具: {}", [tool.name for tool in railway_tools])
    return railway_tools


def get_railway_mcp_tools_sync() -> list[BaseTool]:
    return run_async(get_railway_mcp_tools())
