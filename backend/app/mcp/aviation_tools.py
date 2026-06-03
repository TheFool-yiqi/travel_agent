"""Variflight Aviation MCP 工具加载。"""

from __future__ import annotations

from langchain_core.tools import BaseTool
from loguru import logger

from app.mcp.client import VARIFLIGHT_SERVER
from app.mcp.manager import get_mcp_manager
from app.mcp.registry import run_async
from app.settings import settings

AVIATION_TOOL_KEYWORDS = (
    "flight",
    "aviation",
    "searchflights",
    "gettodaydate",
    "itinerar",
    "transfer",
)


async def get_aviation_mcp_tools() -> list[BaseTool]:
    """从 Variflight MCP 加载航班相关 LangChain 工具。"""
    if not settings.variflight_api_key:
        return []

    try:
        manager = await get_mcp_manager(servers=[VARIFLIGHT_SERVER])
        tools = await manager.get_tools_by_server(VARIFLIGHT_SERVER)
    except Exception as exc:
        logger.warning("加载 Variflight MCP 工具失败: {}", exc)
        return []

    aviation_tools = [
        tool
        for tool in tools
        if any(keyword in tool.name.lower() for keyword in AVIATION_TOOL_KEYWORDS)
    ]
    if not aviation_tools and tools:
        aviation_tools = list(tools)

    logger.info("航班 MCP 工具: {}", [tool.name for tool in aviation_tools])
    return aviation_tools


def get_aviation_mcp_tools_sync() -> list[BaseTool]:
    return run_async(get_aviation_mcp_tools())
